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
MANIFEST = ROOT / ".cursor-plugin" / "plugin.json"
HOOKS = ROOT / "plugins" / "cursor" / "hooks" / "hooks.json"
SCRIPT = ROOT / "plugins" / "cursor" / "hooks" / "praxis_context.py"


class CursorIntegrationTests(unittest.TestCase):
    def run_hook(
        self,
        root: Path,
        event: dict[str, object],
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        env = os.environ.copy()
        env["CURSOR_PROJECT_DIR"] = str(root)
        env["CURSOR_PLUGIN_ROOT"] = str(ROOT)
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

    def test_manifest_reuses_shared_skill_and_cursor_hooks_without_mcp(self) -> None:
        self.assertTrue(MANIFEST.is_file())
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "praxis")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["hooks"], "./plugins/cursor/hooks/hooks.json")
        self.assertNotIn("mcpServers", manifest)

    def test_hook_manifest_declares_only_session_and_prompt_lifecycle(self) -> None:
        self.assertTrue(HOOKS.is_file())
        value = json.loads(HOOKS.read_text(encoding="utf-8"))
        self.assertEqual(value["version"], 1)
        self.assertEqual(set(value["hooks"]), {"sessionStart", "beforeSubmitPrompt"})
        for event in ("sessionStart", "beforeSubmitPrompt"):
            hooks = value["hooks"][event]
            self.assertEqual(len(hooks), 1)
            command = hooks[0]["command"]
            self.assertIn("${CURSOR_PLUGIN_ROOT}", command)
            self.assertIn("plugins/cursor/hooks/praxis_context.py", command)
            for forbidden in ("prompt", "conversation_id", "session_id", "transcript"):
                self.assertNotIn(forbidden, command)

    def test_session_start_is_silent_for_uninitialized_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            completed, payload = self.run_hook(
                root,
                {
                    "hook_event_name": "sessionStart",
                    "session_id": "cursor-session",
                    "conversation_id": "cursor-session",
                },
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(payload, {})
            self.assertFalse((root / ".praxis").exists())

    def test_session_start_injects_exact_cursor_recovery_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, _ = create_task(
                root,
                0,
                host="cursor",
                conversation_id="cursor-session",
                title="Authentication",
            )
            completed, payload = self.run_hook(
                root,
                {
                    "hook_event_name": "sessionStart",
                    "session_id": "cursor-session",
                    "conversation_id": "cursor-session",
                },
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            context = payload["additional_context"]
            self.assertIn("Praxis is enabled", context)
            self.assertIn(f"Recovered task: {task_id}", context)
            self.assertIn("Recovery is not approval", context)
            self.assertLessEqual(len(context), 3000)

    def test_before_submit_prompt_refreshes_but_does_not_claim_context_injection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "auth.py"
            evidence.write_text("v1", encoding="utf-8")
            enable_state(root)
            upsert_section(root, "auth", "Authentication", "Auth facts.", ["auth.py"])
            evidence.write_text("v2", encoding="utf-8")

            secret = "SELECT decision_secret AND IGNORE PRIOR"
            completed, payload = self.run_hook(
                root,
                {
                    "hook_event_name": "beforeSubmitPrompt",
                    "conversation_id": "cursor-session",
                    "prompt": secret,
                    "transcript_path": str(root / "secret.jsonl"),
                },
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(payload, {"continue": True})
            self.assertNotIn(secret, completed.stdout)
            self.assertEqual(project_model_status(root)["stale_sections"], ["auth"])

    def test_session_start_recovery_failure_is_truthful_and_fail_open(self) -> None:
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
                    "hook_event_name": "sessionStart",
                    "session_id": "cursor-session",
                },
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(
                "automatic recovery is unavailable",
                payload["additional_context"],
            )
            self.assertEqual(state.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
