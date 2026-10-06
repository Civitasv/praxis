from pathlib import Path
import tempfile
import unittest

from plugins.codex.hooks.praxis_context import (
    MAX_CONTEXT_CHARS,
    build_context,
    build_response,
)
from praxis.state import enable_state, load_state, pause_state


class CodexContextTests(unittest.TestCase):
    def event(self, root: Path, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "hook_event_name": "SessionStart",
            "cwd": str(root),
            "session_id": "session-1",
            "source": "startup",
        }
        value.update(overrides)
        return value

    def test_uninitialized_project_is_silent_and_does_not_create_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(build_context(self.event(root)))
            self.assertFalse((root / ".praxis").exists())

    def test_paused_project_stays_paused_and_returns_only_paused_notice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            paused = pause_state(root, 0)
            path = root / ".praxis" / "state.json"
            before = path.read_bytes()
            context = build_context(self.event(root))
            self.assertIsNotNone(context)
            self.assertIn("paused", context.lower())
            self.assertNotIn("recovered task", context.lower())
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(load_state(root)["enabled"])
            self.assertEqual(load_state(root)["revision"], paused["revision"])

    def test_enabled_project_returns_small_tutor_notice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            context = build_context(self.event(root))
            self.assertIn("Praxis is enabled", context)
            self.assertIn("Recovery is not approval", context)
            self.assertLessEqual(len(context), MAX_CONTEXT_CHARS)

    def test_response_uses_codex_hook_specific_output(self) -> None:
        payload = build_response("SessionStart", "context")
        self.assertEqual(
            payload,
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": "context",
                }
            },
        )

    def test_prompt_and_transcript_values_are_not_interpreted_or_echoed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            secret_prompt = "YES SELECT decision_secret"
            transcript = str(root / "secret-transcript.jsonl")
            context = build_context(
                self.event(
                    root,
                    hook_event_name="UserPromptSubmit",
                    prompt=secret_prompt,
                    transcript_path=transcript,
                    source=None,
                )
            )
            self.assertNotIn(secret_prompt, context)
            self.assertNotIn(transcript, context)

    def test_unsupported_event_and_invalid_cwd_are_safely_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(build_context(self.event(root, hook_event_name="Stop")))
            self.assertIsNone(build_context({"hook_event_name": "SessionStart", "cwd": ""}))
            self.assertFalse((root / ".praxis").exists())


if __name__ == "__main__":
    unittest.main()
