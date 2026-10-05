import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DecisionCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [sys.executable, "-m", "praxis", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        return result, json.loads(result.stdout)

    def make_task(self, root: Path) -> str:
        result, enabled = self.run_cli("enable", "--cwd", str(root))
        self.assertEqual(result.returncode, 0, result.stderr)
        result, task = self.run_cli(
            "task-create", "--cwd", str(root),
            "--expected-revision", str(enabled["state"]["revision"]),
            "--host", "codex", "--title", "Tutor",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return task["task_id"]

    def test_decision_status_without_state_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result, payload = self.run_cli("decision-status", "--cwd", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(payload["decisions"]["exists"])
            self.assertFalse((root / ".praxis").exists())

    def test_create_select_implement_verify_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            result, created = self.run_cli(
                "decision-create", "--cwd", tmp,
                "--task-id", task_id,
                "--class", "engineering",
                "--title", "Storage",
                "--context", "Choose storage",
                "--user-proposal", "Use Redis",
                "--verified-constraint", "History is durable",
                "--praxis-challenge", "Redis durability needs explicit configuration",
                "--alternative", "Database source of truth",
                "--blocked-scope", "storage-implementation",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            decision_id = created["decision_id"]
            self.assertIn(decision_id, created["decisions"]["open_decisions"])

            result, selected = self.run_cli(
                "decision-select", "--cwd", tmp,
                "--decision-id", decision_id,
                "--expected-decision-revision", "0",
                "--selected-decision", "Database source of truth",
                "--user-reasoning", "History cannot be lost",
                "--accepted-tradeoff", "Extra dependency",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(selected["state"]["decisions"]["records"][decision_id]["status"], "selected")

            result, implemented = self.run_cli(
                "decision-implemented", "--cwd", tmp,
                "--decision-id", decision_id,
                "--expected-decision-revision", "1",
                "--result", "Postgres stores messages",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(implemented["state"]["decisions"]["records"][decision_id]["status"], "implemented")

            result, verified = self.run_cli(
                "decision-verify", "--cwd", tmp,
                "--decision-id", decision_id,
                "--expected-decision-revision", "2",
                "--result", "Redis restart preserved history",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(verified["state"]["decisions"]["records"][decision_id]["status"], "verified")

    def test_unknown_task_conflict_and_invalid_transition_have_stable_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            result, unknown = self.run_cli(
                "decision-create", "--cwd", tmp,
                "--task-id", "task_deadbeef",
                "--class", "engineering", "--title", "X", "--context", "Y",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(unknown["error"]["code"], "unknown_task")

            _, created = self.run_cli(
                "decision-create", "--cwd", tmp,
                "--task-id", task_id,
                "--class", "engineering", "--title", "Storage", "--context", "ctx",
            )
            decision_id = created["decision_id"]
            result, invalid = self.run_cli(
                "decision-implemented", "--cwd", tmp,
                "--decision-id", decision_id,
                "--expected-decision-revision", "0", "--result", "too early",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(invalid["error"]["code"], "invalid_transition")

            self.run_cli(
                "decision-select", "--cwd", tmp,
                "--decision-id", decision_id,
                "--expected-decision-revision", "0", "--selected-decision", "A",
            )
            result, conflict = self.run_cli(
                "decision-select", "--cwd", tmp,
                "--decision-id", decision_id,
                "--expected-decision-revision", "0", "--selected-decision", "B",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(conflict["error"]["code"], "decision_conflict")

    def test_unknown_decision_and_invalid_decision_have_stable_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_task(root)
            result, unknown = self.run_cli(
                "decision-abandon", "--cwd", tmp,
                "--decision-id", "decision_deadbeef",
                "--expected-decision-revision", "0",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(unknown["error"]["code"], "unknown_decision")

            result, invalid = self.run_cli(
                "decision-create", "--cwd", tmp,
                "--task-id", next(iter(json.loads((root / ".praxis" / "state.json").read_text())["tasks"])),
                "--class", "mechanical", "--title", "Name", "--context", "ctx",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(invalid["error"]["code"], "invalid_decision")

    def test_render_repairs_projection_and_render_errors_are_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            _, created = self.run_cli(
                "decision-create", "--cwd", tmp,
                "--task-id", task_id, "--class", "engineering",
                "--title", "Storage", "--context", "ctx",
            )
            self.assertTrue(created["decisions"]["render_required"])
            result, rendered = self.run_cli("decision-render", "--cwd", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(rendered["decisions"]["render_required"])
            path = root / ".praxis" / "decisions.md"
            path.unlink()
            path.mkdir()
            result, failed = self.run_cli("decision-render", "--cwd", tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(failed["error"]["code"], "decision_render_failed")


if __name__ == "__main__":
    unittest.main()
