from pathlib import Path
import tempfile
import unittest

from praxis.project_map import (
    ProjectModelError,
    SectionConflictError,
    UnknownSectionError,
    get_project_model,
    remove_section,
    upsert_section,
)
from praxis.state import enable_state, load_state, mutate_state


class ProjectMapSectionTests(unittest.TestCase):
    def make_source(self, root: Path, relative: str, content: str = "source") -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_new_evidence_backed_section_starts_verified_at_revision_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            self.make_source(root, "src/auth.py")

            state = upsert_section(
                root,
                "auth",
                "Authentication",
                "Owns authentication and session lifecycle.",
                ["src/auth.py"],
            )

            model = get_project_model(state)
            self.assertEqual(model["revision"], 0)
            section = model["sections"]["auth"]
            self.assertEqual(section["revision"], 0)
            self.assertEqual(section["status"], "verified")
            self.assertEqual(section["stale_reasons"], [])
            self.assertEqual(section["evidence"][0]["path"], "src/auth.py")

    def test_evidence_free_section_is_explicitly_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)

            state = upsert_section(root, "unknowns", "Known Unknowns", "Deployment is not yet verified.", [])

            section = get_project_model(state)["sections"]["unknowns"]
            self.assertEqual(section["status"], "unknown")
            self.assertEqual(section["evidence"], [])

    def test_existing_section_requires_exact_section_revision_and_increments_only_that_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            source = self.make_source(root, "src/auth.py", "v1")
            first = upsert_section(root, "auth", "Auth", "v1 model", ["src/auth.py"])
            self.assertEqual(get_project_model(first)["sections"]["auth"]["revision"], 0)

            source.write_text("v2", encoding="utf-8")
            updated = upsert_section(
                root,
                "auth",
                "Auth",
                "v2 model",
                ["src/auth.py"],
                expected_section_revision=0,
            )

            section = get_project_model(updated)["sections"]["auth"]
            self.assertEqual(section["revision"], 1)
            self.assertEqual(section["content"], "v2 model")
            with self.assertRaises(SectionConflictError):
                upsert_section(
                    root,
                    "auth",
                    "Auth",
                    "stale writer",
                    ["src/auth.py"],
                    expected_section_revision=0,
                )

    def test_new_section_conflicts_when_same_id_already_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            self.make_source(root, "src/a.py")
            upsert_section(root, "auth", "Auth", "first", ["src/a.py"])

            with self.assertRaises(SectionConflictError):
                upsert_section(root, "auth", "Auth", "overwrite", ["src/a.py"])

    def test_unrelated_sections_can_update_after_global_revision_moves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            auth = self.make_source(root, "src/auth.py", "a1")
            billing = self.make_source(root, "src/billing.py", "b1")
            upsert_section(root, "auth", "Auth", "auth 1", ["src/auth.py"])
            state = upsert_section(root, "billing", "Billing", "billing 1", ["src/billing.py"])
            global_revision = state["revision"]

            auth.write_text("a2", encoding="utf-8")
            state = upsert_section(root, "auth", "Auth", "auth 2", ["src/auth.py"], expected_section_revision=0)
            state = mutate_state(root, state["revision"], lambda value: {**value, "future_metadata": {"keep": True}})
            self.assertGreater(state["revision"], global_revision)

            billing.write_text("b2", encoding="utf-8")
            final = upsert_section(
                root,
                "billing",
                "Billing",
                "billing 2",
                ["src/billing.py"],
                expected_section_revision=0,
            )

            model = get_project_model(final)
            self.assertEqual(model["sections"]["auth"]["revision"], 1)
            self.assertEqual(model["sections"]["billing"]["revision"], 1)
            self.assertEqual(final["future_metadata"], {"keep": True})

    def test_removal_requires_exact_section_revision_and_preserves_other_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            self.make_source(root, "a.py")
            self.make_source(root, "b.py")
            upsert_section(root, "a", "A", "section a", ["a.py"])
            upsert_section(root, "b", "B", "section b", ["b.py"])

            with self.assertRaises(SectionConflictError):
                remove_section(root, "a", expected_section_revision=4)
            state = remove_section(root, "a", expected_section_revision=0)

            model = get_project_model(state)
            self.assertNotIn("a", model["sections"])
            self.assertIn("b", model["sections"])
            with self.assertRaises(UnknownSectionError):
                remove_section(root, "a", expected_section_revision=0)

    def test_section_mutation_preserves_tasks_and_unknown_top_level_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            seeded = mutate_state(
                root,
                0,
                lambda state: {
                    **state,
                    "tasks": {
                        "task_deadbeef": {
                            "host": "codex",
                            "stage": "design",
                            "status": "active",
                            "pending_choices": ["storage"],
                        }
                    },
                    "future_metadata": {"keep": True},
                },
            )
            self.make_source(root, "src/a.py")

            state = upsert_section(root, "a", "A", "A model", ["src/a.py"])

            self.assertEqual(state["tasks"], seeded["tasks"])
            self.assertEqual(state["future_metadata"], {"keep": True})

    def test_invalid_section_id_title_and_content_are_rejected_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initial = enable_state(root)
            self.make_source(root, "a.py")

            invalid_calls = (
                lambda: upsert_section(root, "Auth Space", "Auth", "content", ["a.py"]),
                lambda: upsert_section(root, "auth", "", "content", ["a.py"]),
                lambda: upsert_section(root, "auth", "Auth", "   ", ["a.py"]),
            )
            for call in invalid_calls:
                with self.subTest(call=call):
                    with self.assertRaises(ProjectModelError):
                        call()
            self.assertEqual(load_state(root), initial)


if __name__ == "__main__":
    unittest.main()
