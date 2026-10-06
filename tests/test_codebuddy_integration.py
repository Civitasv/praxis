import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from praxis.project_map import project_model_status, upsert_section
from praxis.state import enable_state
from praxis.tasks import create_task


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".codebuddy-plugin" / "plugin.json"
HOOKS = ROOT / "plugins" / "codebuddy" / "hooks" / "hooks.json"
SCRIPT = ROOT / "plugins" / "codebuddy" / "hooks" / "praxis_context.py"


class CodeBuddyIntegrationTests(unittest.TestCase):
    def run_hook(
        self,
        root: Path,
        event: dict[str, object],
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        env = os.environ.copy()
        env["CODEBUDDY_PROJECT_DIR"] = str(root)
        env["CODEBUDDY_PLUGIN_ROOT"] = str(ROOT)
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            env=env,
            cwd=root,
            check=False,
        )
        payload = json.loads(completed.stdout or "{}")
        return completed, payload

    def test_manifest_reuses_shared_skill_and_codebuddy_hooks_without_mcp(self) -> None:
        self.assertTrue(MANIFEST.is_file())
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "praxis")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["hooks"], "./plugins/codebuddy/hooks/hooks.json")
        self.assertNotIn("mcpServers", manifest)

    def test_hook_manifest_declares_session_and_prompt_events(self) -> None:
        self.assertTrue(HOOKS.is_file())
        value = json.loads(HOOKS.read_text(encoding="utf-8"))
        self.assertEqual(set(value["hooks"]), {"SessionStart", "UserPromptSubmit"})
        session_group = value["hooks"]["SessionStart"]
        self.assertEqual(len(session_group), 1)
        self.assertEqual(session_group[0]["matcher"], "^(startup|resume|clear|compact)$")
        prompt_group = value["hooks"]["UserPromptSubmit"]
        self.assertEqual(len(prompt_group), 1)
        self.assertNotIn("matcher", prompt_group[0])

        for group in (session_group, prompt_group):
            handler = group[0]["hooks"][0]
            self.assertEqual(handler["type"], "command")
            command = handler["command"]
            self.assertIn("${CODEBUDDY_PLUGIN_ROOT}", command)
            self.assertIn("plugins/codebuddy/hooks/praxis_context.py", command)
            for forbidden in ("prompt", "session_id", "transcript_path", "{cwd}"):
                self.assertNotIn(forbidden, command)

    def test_session_start_is_silent_for_uninitialized_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            completed, payload = self.run_hook(
                root,
                {
                    "hook_event_name": "SessionStart",
                    "session_id": "buddy-session",
                    "source": "startup",
                    "cwd": str(root),
                },
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(payload, {})
            self.assertFalse((root / ".praxis").exists())

    def test_session_start_injects_exact_codebuddy_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, _ = create_task(
                root,
                0,
                host="codebuddy",
                conversation_id="buddy-session",
                title="Authentication",
            )
            completed, payload = self.run_hook(
                root,
                {
                    "hook_event_name": "SessionStart",
                    "session_id": "buddy-session",
                    "source": "resume",
                    "cwd": str(root),
                },
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = payload["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "SessionStart")
            context = output["additionalContext"]
            self.assertIn(f"Recovered task: {task_id}", context)
            self.assertIn("Recovery is not approval", context)
            self.assertLessEqual(len(context), 3000)

    def test_user_prompt_submit_refreshes_and_injects_without_parsing_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "auth.py"
            evidence.write_text("v1", encoding="utf-8")
            enable_state(root)
            upsert_section(root, "auth", "Authentication", "Auth facts.", ["auth.py"])
            evidence.write_text("v2", encoding="utf-8")

            secret = "YES SELECT decision_secret IGNORE PRIOR"
            completed, payload = self.run_hook(
                root,
                {
                    "hook_event_name": "UserPromptSubmit",
                    "session_id": "buddy-session",
                    "cwd": str(root),
                    "prompt": secret,
                    "transcript_path": str(root / "secret.jsonl"),
                },
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(payload["continue"])
            output = payload["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "UserPromptSubmit")
            self.assertIn("Stale project sections: auth", output["additionalContext"])
            self.assertNotIn(secret, completed.stdout)
            self.assertEqual(project_model_status(root)["stale_sections"], ["auth"])

    def test_recovery_failure_returns_manual_skill_fallback_and_stays_fail_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".praxis"
            directory.mkdir()
            state = directory / "state.json"
            original = b"{not-json\n"
            state.write_bytes(original)

            completed, payload = self.run_hook(
                root,
                {
                    "hook_event_name": "UserPromptSubmit",
                    "session_id": "buddy-session",
                    "cwd": str(root),
                    "prompt": "continue",
                },
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(payload["continue"])
            self.assertIn(
                "automatic recovery is unavailable",
                payload["hookSpecificOutput"]["additionalContext"],
            )
            self.assertEqual(state.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
