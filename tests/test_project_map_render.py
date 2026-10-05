from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from praxis.project_map import (
    ProjectModelRenderError,
    project_model_status,
    refresh_staleness,
    render_project_model,
    upsert_section,
)
from praxis.state import enable_state, load_state, mutate_state


class ProjectMapRenderTests(unittest.TestCase):
    def make_source(self, root: Path, relative: str, content: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_render_is_stable_and_orders_sections_by_id_with_machine_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            self.make_source(root, "b.py", "b")
            self.make_source(root, "a.py", "a")
            upsert_section(root, "b", "Billing", "Billing model.", ["b.py"])
            state = upsert_section(root, "a", "Authentication", "Auth model.", ["a.py"])

            path = render_project_model(root)
            text = path.read_text(encoding="utf-8")

            self.assertIn(f'<!-- praxis:project-model revision="{state["project_model"]["revision"]}" -->', text)
            self.assertLess(text.index("## Authentication"), text.index("## Billing"))
            self.assertIn('<!-- praxis:section id="a" revision="0" status="verified" -->', text)
            self.assertIn("`a.py` — `sha256:", text)

    def test_unknown_section_explicitly_renders_no_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            upsert_section(root, "unknowns", "Known Unknowns", "Deployment remains unknown.", [])

            text = render_project_model(root).read_text(encoding="utf-8")

            self.assertIn('status="unknown"', text)
            self.assertIn("Evidence: none (unknown)", text)

    def test_stale_section_renders_machine_stale_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            source = self.make_source(root, "a.py", "v1")
            upsert_section(root, "a", "A", "A model.", ["a.py"])
            source.write_text("v2", encoding="utf-8")
            refresh_staleness(root)

            text = render_project_model(root).read_text(encoding="utf-8")

            self.assertIn('status="stale"', text)
            self.assertIn("Stale reasons:", text)
            self.assertIn("`a.py` — `changed`", text)

    def test_missing_code_map_is_render_required_and_render_repairs_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            self.make_source(root, "a.py", "a")
            upsert_section(root, "a", "A", "A model.", ["a.py"])

            before = project_model_status(root)
            self.assertTrue(before["render_required"])
            render_project_model(root)
            after = project_model_status(root)

            self.assertFalse(after["render_required"])
            self.assertEqual(after["revision"], before["revision"])

    def test_global_task_style_state_change_does_not_invalidate_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            self.make_source(root, "a.py", "a")
            state = upsert_section(root, "a", "A", "A model.", ["a.py"])
            render_project_model(root)

            mutate_state(root, state["revision"], lambda value: {**value, "future_metadata": True})

            self.assertFalse(project_model_status(root)["render_required"])

    def test_model_revision_change_marks_existing_projection_out_of_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            source = self.make_source(root, "a.py", "v1")
            upsert_section(root, "a", "A", "A model 1.", ["a.py"])
            render_project_model(root)
            source.write_text("v2", encoding="utf-8")

            upsert_section(root, "a", "A", "A model 2.", ["a.py"], expected_section_revision=0)

            self.assertTrue(project_model_status(root)["render_required"])

    def test_deleted_projection_rebuilds_to_identical_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            self.make_source(root, "a.py", "a")
            upsert_section(root, "a", "A", "A model.", ["a.py"])
            path = render_project_model(root)
            first = path.read_bytes()
            path.unlink()

            rebuilt = render_project_model(root)

            self.assertEqual(rebuilt.read_bytes(), first)
            self.assertFalse(project_model_status(root)["render_required"])

    def test_render_failure_is_reported_without_changing_authoritative_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            self.make_source(root, "a.py", "a")
            upsert_section(root, "a", "A", "A model.", ["a.py"])
            before = (root / ".praxis" / "state.json").read_bytes()

            with patch("praxis.project_map.os.replace", side_effect=OSError("boom")):
                with self.assertRaises(ProjectModelRenderError):
                    render_project_model(root)

            self.assertEqual((root / ".praxis" / "state.json").read_bytes(), before)
            self.assertTrue(project_model_status(root)["render_required"])


if __name__ == "__main__":
    unittest.main()
