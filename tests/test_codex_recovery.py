from pathlib import Path
import tempfile
import unittest

from plugins.codex.hooks.praxis_context import build_context
from praxis.project_map import project_model_status, upsert_section
from praxis.state import enable_state, load_state
from praxis.tasks import create_task


class CodexRecoveryTests(unittest.TestCase):
    def event(self, root: Path, *, source: str = "startup", session_id: str = "session-1") -> dict[str, object]:
        return {
            "hook_event_name": "SessionStart",
            "cwd": str(root),
            "session_id": session_id,
            "source": source,
        }

    def test_all_session_start_sources_produce_enabled_context(self) -> None:
        for source in ("startup", "resume", "clear", "compact"):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                enable_state(root)
                context = build_context(self.event(root, source=source))
                self.assertIn("Praxis is enabled", context)

    def test_exact_codex_session_task_is_recovered_without_task_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, state = create_task(
                root,
                0,
                host="codex",
                conversation_id="session-1",
                title="Authentication",
            )
            before_tasks = load_state(root)["tasks"]
            context = build_context(self.event(root))
            self.assertIn("Recovered task", context)
            self.assertIn(task_id, context)
            self.assertIn("Authentication", context)
            self.assertEqual(load_state(root)["tasks"], before_tasks)
            self.assertEqual(load_state(root)["revision"], state["revision"])

    def test_multiple_exact_session_tasks_are_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            first, state = create_task(root, 0, host="codex", conversation_id="session-1", title="First")
            second, _ = create_task(
                root,
                state["revision"],
                host="codex",
                conversation_id="session-1",
                title="Second",
            )
            context = build_context(self.event(root))
            self.assertIn("Multiple matching Codex tasks", context)
            self.assertIn(first, context)
            self.assertIn(second, context)
            self.assertNotIn("Recovered task:", context)

    def test_changed_project_evidence_is_marked_stale_before_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "auth.py"
            evidence.write_text("v1", encoding="utf-8")
            enable_state(root)
            upsert_section(root, "auth", "Authentication", "Auth facts.", ["auth.py"])
            evidence.write_text("v2", encoding="utf-8")
            context = build_context(self.event(root))
            status = project_model_status(root)
            self.assertEqual(status["stale_sections"], ["auth"])
            self.assertIn("Stale project sections: auth", context)

    def test_recovery_does_not_auto_clear_existing_stale_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "auth.py"
            evidence.write_text("v1", encoding="utf-8")
            enable_state(root)
            upsert_section(root, "auth", "Authentication", "Auth facts.", ["auth.py"])
            evidence.write_text("v2", encoding="utf-8")
            build_context(self.event(root))
            self.assertEqual(project_model_status(root)["stale_sections"], ["auth"])
            evidence.write_text("v1", encoding="utf-8")
            build_context(self.event(root))
            self.assertEqual(project_model_status(root)["stale_sections"], ["auth"])


if __name__ == "__main__":
    unittest.main()
