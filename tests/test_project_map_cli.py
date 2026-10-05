import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProjectMapCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [sys.executable, "-m", "praxis", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        return result, json.loads(result.stdout)

    def enable(self, project: Path) -> dict:
        result, payload = self.run_cli("enable", "--cwd", str(project))
        self.assertEqual(result.returncode, 0, result.stderr)
        return payload

    def test_map_status_without_state_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result, payload = self.run_cli("map-status", "--cwd", tmp)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(payload["project_model"]["exists"])
            self.assertFalse((root / ".praxis").exists())

    def test_map_upsert_update_and_section_conflict_use_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            source = root / "auth.py"
            source.write_text("v1", encoding="utf-8")

            result, created = self.run_cli(
                "map-upsert", "--cwd", tmp,
                "--section-id", "auth",
                "--title", "Auth",
                "--content", "Auth model 1.",
                "--evidence", "auth.py",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(created["state"]["project_model"]["sections"]["auth"]["revision"], 0)

            source.write_text("v2", encoding="utf-8")
            result, updated = self.run_cli(
                "map-upsert", "--cwd", tmp,
                "--section-id", "auth",
                "--title", "Auth",
                "--content", "Auth model 2.",
                "--evidence", "auth.py",
                "--expected-section-revision", "0",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(updated["state"]["project_model"]["sections"]["auth"]["revision"], 1)

            result, conflict = self.run_cli(
                "map-upsert", "--cwd", tmp,
                "--section-id", "auth",
                "--title", "Auth",
                "--content", "stale writer",
                "--evidence", "auth.py",
                "--expected-section-revision", "0",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(conflict["error"]["code"], "section_conflict")

    def test_map_remove_unknown_section_uses_stable_error_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)

            result, payload = self.run_cli(
                "map-remove", "--cwd", tmp,
                "--section-id", "missing",
                "--expected-section-revision", "0",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(payload["error"]["code"], "unknown_section")

    def test_map_upsert_invalid_evidence_uses_stable_error_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)

            result, payload = self.run_cli(
                "map-upsert", "--cwd", tmp,
                "--section-id", "missing",
                "--title", "Missing",
                "--content", "model",
                "--evidence", "does-not-exist.py",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(payload["error"]["code"], "invalid_evidence")

    def test_map_check_marks_stale_then_repeated_scan_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            source = root / "a.py"
            source.write_text("v1", encoding="utf-8")
            self.run_cli(
                "map-upsert", "--cwd", tmp,
                "--section-id", "a", "--title", "A", "--content", "A model.",
                "--evidence", "a.py",
            )
            source.write_text("v2", encoding="utf-8")

            result, first = self.run_cli("map-check", "--cwd", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(first["project_model"]["stale_sections"], ["a"])
            first_revision = first["state"]["revision"]

            result, second = self.run_cli("map-check", "--cwd", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(second["state"]["revision"], first_revision)

    def test_map_render_repairs_missing_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            (root / "a.py").write_text("a", encoding="utf-8")
            self.run_cli(
                "map-upsert", "--cwd", tmp,
                "--section-id", "a", "--title", "A", "--content", "A model.",
                "--evidence", "a.py",
            )

            _, before = self.run_cli("map-status", "--cwd", tmp)
            self.assertTrue(before["project_model"]["render_required"])
            result, rendered = self.run_cli("map-render", "--cwd", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(rendered["project_model"]["render_required"])
            code_path = root / ".praxis" / "code.md"
            self.assertTrue(code_path.is_file())
            code_path.unlink()
            _, missing = self.run_cli("map-status", "--cwd", tmp)
            self.assertTrue(missing["project_model"]["render_required"])

    def test_invalid_persisted_project_model_uses_stable_error_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            state_path = root / ".praxis" / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["project_model"] = {"revision": -1, "sections": {}}
            state_path.write_text(json.dumps(state), encoding="utf-8")

            result, payload = self.run_cli("map-status", "--cwd", tmp)

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(payload["error"]["code"], "invalid_project_model")

    def test_unsafe_code_projection_path_uses_render_failure_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            (root / "a.py").write_text("a", encoding="utf-8")
            self.run_cli(
                "map-upsert", "--cwd", tmp,
                "--section-id", "a", "--title", "A", "--content", "A model.",
                "--evidence", "a.py",
            )
            (root / ".praxis" / "code.md").mkdir()

            result, payload = self.run_cli("map-render", "--cwd", tmp)

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(payload["error"]["code"], "project_model_render_failed")


if __name__ == "__main__":
    unittest.main()
