from pathlib import Path
import ast
import json
import subprocess
import sys
import tempfile
import unittest

from praxis.cli import _error_code
import praxis.state as state_module


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_IMPORT_FRAGMENTS = ("deepseek", "cordis", "codex", "plugins.dsh", "plugins.codex")


class CliBaselineTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "praxis", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_json(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = self.run_cli(*args)
        return result, json.loads(result.stdout)

    def test_version_command_succeeds(self) -> None:
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout.strip(), r"^Praxis 0\.1\.0a0$")

    def test_unknown_argument_is_rejected(self) -> None:
        result = self.run_cli("--definitely-unknown")
        self.assertNotEqual(result.returncode, 0)

    def test_generated_project_state_is_ignored(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".praxis/", ignore.splitlines())

    def test_neutral_python_core_has_no_harness_imports(self) -> None:
        package = ROOT / "praxis"
        self.assertTrue(package.is_dir())
        for path in package.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.append(node.module)
            for module in imported:
                with self.subTest(path=str(path), module=module):
                    self.assertFalse(
                        any(fragment in module.lower() for fragment in FORBIDDEN_IMPORT_FRAGMENTS),
                        f"Harness-specific import leaked into neutral core: {module}",
                    )


class CliStateTests(CliBaselineTests):
    def test_state_read_failure_has_distinct_error_code(self) -> None:
        error = state_module.StateReadError("denied")
        self.assertEqual(_error_code(error), "state_read_failed")

    def test_status_without_state_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, payload = self.run_json("status", "--cwd", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(payload["ok"])
            self.assertFalse(payload["active"])
            self.assertIsNone(payload["state"])
            self.assertFalse((Path(tmp) / ".praxis").exists())

    def test_enable_and_pause_use_json_and_revision_cas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, enabled = self.run_json("enable", "--cwd", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(enabled["state"]["revision"], 0)
            self.assertTrue(enabled["active"])

            result, conflict = self.run_json(
                "pause", "--cwd", tmp, "--expected-revision", "9"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(conflict["ok"])
            self.assertEqual(conflict["error"]["code"], "revision_conflict")

            result, paused = self.run_json(
                "pause", "--cwd", tmp, "--expected-revision", "0"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(paused["active"])
            self.assertEqual(paused["state"]["revision"], 1)

    def test_task_create_and_update_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.run_json("enable", "--cwd", tmp)
            result, created = self.run_json(
                "task-create",
                "--cwd",
                tmp,
                "--expected-revision",
                "0",
                "--host",
                "codex",
                "--conversation-id",
                "c1",
                "--title",
                "Auth",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            task_id = created["task_id"]
            self.assertEqual(created["state"]["revision"], 1)

            result, updated = self.run_json(
                "task-update",
                "--cwd",
                tmp,
                "--expected-revision",
                "1",
                "--task-id",
                task_id,
                "--stage",
                "awaiting_decision",
                "--pending-choice",
                "storage",
                "permissions",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                updated["state"]["tasks"][task_id]["pending_choices"],
                ["storage", "permissions"],
            )

    def test_missing_required_state_argument_returns_json_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, payload = self.run_json("pause", "--cwd", tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "invalid_request")

    def test_corrupt_state_returns_stable_error_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / ".praxis"
            directory.mkdir()
            state_path = directory / "state.json"
            state_path.write_text("{bad", encoding="utf-8")
            result, payload = self.run_json("status", "--cwd", tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(payload["error"]["code"], "malformed_state")
            self.assertEqual(state_path.read_text(encoding="utf-8"), "{bad")


if __name__ == "__main__":
    unittest.main()
