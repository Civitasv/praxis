import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from praxis.cli import main
from praxis.diagnostics import doctor_status
from praxis.state import disable_state, enable_state
from contextlib import redirect_stdout
from io import StringIO


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/codex/hooks/praxis_context.py"


class DeliveryTests(unittest.TestCase):
    def command(self, *args: str) -> dict:
        output = StringIO()
        with redirect_stdout(output):
            code = main(args)
        value = json.loads(output.getvalue())
        self.assertEqual(code, 0, value)
        return value

    def test_enable_fallback_is_explicit_preserves_user_text_and_is_removable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agents = root / "AGENTS.md"
            original = "# User rules\nKeep my text.\n"
            agents.write_text(original)
            self.command("enable", "--cwd", tmp)
            self.assertEqual(agents.read_text(), original)
            enabled = self.command("enable", "--cwd", tmp, "--agents-fallback")
            self.assertTrue(enabled["agents_fallback"]["installed"])
            self.assertIn("removable", enabled["agents_fallback"]["notice"])
            text = agents.read_text()
            self.assertIn("praxis status --cwd .", text)
            self.assertIn("paused", text)
            self.command("enable", "--cwd", tmp, "--agents-fallback")
            self.assertEqual(agents.read_text(), text)
            self.command("disable", "--cwd", tmp)
            self.assertEqual(agents.read_text(), text)
            self.command("agents-fallback", "--cwd", tmp, "--remove")
            self.assertEqual(agents.read_text(), original)

    def test_fallback_refuses_symlinks_without_modifying_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "outside.md"
            target.write_text("untouched")
            (root / "AGENTS.md").symlink_to(target)
            output = StringIO()
            with redirect_stdout(output):
                code = main(["enable", "--cwd", tmp, "--agents-fallback"])
            self.assertEqual(code, 2)
            self.assertFalse(json.loads(output.getvalue())["ok"])
            self.assertEqual(target.read_text(), "untouched")

    def test_doctor_distinguishes_probe_from_invocation_and_leaves_project_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            before = (root / ".praxis/state.json").read_bytes()
            config = root / "host.toml"
            config.write_text('[plugins."praxis@praxis"]\nenabled = true\n')
            report = doctor_status(root, plugin_root=ROOT, host_config=config)
            self.assertEqual(report["activation"]["status"], "enabled")
            self.assertEqual(report["adapter"]["hook_config"]["status"], "ok")
            self.assertEqual(report["adapter"]["script_probe"]["status"], "ok")
            self.assertEqual(report["observations"]["status"], "not_observed")
            self.assertEqual(report["model_delivery"], "unknown")
            self.assertEqual((root / ".praxis/state.json").read_bytes(), before)
            self.assertFalse((root / ".praxis/hook-observations.json").exists())

    def test_hook_records_only_fixed_metadata_and_doctor_probe_does_not_replace_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            event = {"hook_event_name": "SessionStart", "source": "startup", "cwd": tmp,
                     "session_id": "PRIVATE_SESSION", "prompt": "PRIVATE_PROMPT",
                     "transcript_path": "PRIVATE_TRANSCRIPT"}
            result = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps(event),
                                    text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("A preference answer does not select an implementation", context)
            path = root / ".praxis/hook-observations.json"
            original = path.read_bytes()
            record = json.loads(original)["hosts"]["codex"]["SessionStart"]
            self.assertEqual(record["status"], "context_emitted")
            self.assertEqual(record["source"], "startup")
            self.assertIn("timestamp", record)
            for secret in ("PRIVATE_SESSION", "PRIVATE_PROMPT", "PRIVATE_TRANSCRIPT"):
                self.assertNotIn(secret, original.decode())
            report = doctor_status(root, plugin_root=ROOT, host_config=root / "missing.toml")
            self.assertEqual(report["observations"]["status"], "observed")
            self.assertEqual(path.read_bytes(), original)
            disable_state(root)
            event["hook_event_name"] = "UserPromptSubmit"
            result = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps(event),
                                    text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(path.read_bytes())["hosts"]["codex"]["UserPromptSubmit"]["status"], "paused")

    def test_doctor_on_uninitialized_project_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self.command("doctor", "--cwd", tmp, "--plugin-root", str(ROOT))
            self.assertEqual(report["doctor"]["activation"]["status"], "uninitialized")
            self.assertFalse((root / ".praxis").exists())

    def test_doctor_keeps_other_checks_when_state_or_observations_are_corrupt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            state_path = root / ".praxis/state.json"
            state_path.write_text("broken-state")
            (root / ".praxis/hook-observations.json").write_text("broken-observations")
            report = doctor_status(root, plugin_root=ROOT)
            self.assertEqual(report["activation"]["status"], "error")
            self.assertEqual(report["observations"]["status"], "error")
            self.assertEqual(report["adapter"]["hook_config"]["status"], "ok")
            self.assertEqual(report["adapter"]["script_probe"]["status"], "error")
            self.assertEqual(state_path.read_text(), "broken-state")

    def test_failed_observation_write_does_not_suppress_context(self) -> None:
        from plugins.codex.hooks.praxis_context import main as hook_main
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            target = root / "untouched.json"
            target.write_text("untouched")
            (root / ".praxis/hook-observations.json").symlink_to(target)
            event = {"hook_event_name": "SessionStart", "source": "compact", "cwd": tmp}
            output, errors = StringIO(), StringIO()
            with patch("sys.argv", [str(SCRIPT)]), patch("sys.stdin", StringIO(json.dumps(event))), \
                 redirect_stdout(output), patch("sys.stderr", errors):
                self.assertEqual(hook_main(), 0)
            self.assertIn("Praxis is enabled", json.loads(output.getvalue())["hookSpecificOutput"]["additionalContext"])
            self.assertIn("diagnostic write failed", errors.getvalue())
            self.assertEqual(target.read_text(), "untouched")

    def test_malformed_fallback_is_preserved_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agents = root / "AGENTS.md"
            text = "# My rules\n<!-- praxis:tutor-fallback:start -->\nunfinished"
            agents.write_text(text)
            output = StringIO()
            with redirect_stdout(output):
                code = main(["agents-fallback", "--cwd", tmp, "--remove"])
            self.assertEqual(code, 2)
            self.assertEqual(agents.read_text(), text)


if __name__ == "__main__":
    unittest.main()
