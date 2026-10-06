import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOKS_PATH = ROOT / "plugins" / "codex" / "hooks" / "hooks.json"


class CodexHooksManifestTests(unittest.TestCase):
    def load_hooks(self) -> dict:
        self.assertTrue(HOOKS_PATH.is_file(), "missing Codex hooks manifest")
        value = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
        self.assertIsInstance(value, dict)
        return value

    def test_only_feature_05_lifecycle_events_are_declared(self) -> None:
        value = self.load_hooks()
        hooks = value["hooks"]
        self.assertEqual(set(hooks), {"SessionStart", "UserPromptSubmit"})

    def test_session_start_matches_all_supported_recovery_sources(self) -> None:
        value = self.load_hooks()
        groups = value["hooks"]["SessionStart"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["matcher"], "^(startup|resume|clear|compact)$")

    def test_user_prompt_submit_has_no_prompt_matcher(self) -> None:
        value = self.load_hooks()
        groups = value["hooks"]["UserPromptSubmit"]
        self.assertEqual(len(groups), 1)
        self.assertNotIn("matcher", groups[0])

    def test_handlers_use_static_plugin_root_command_and_bounded_context(self) -> None:
        value = self.load_hooks()
        handlers = [
            value["hooks"]["SessionStart"][0]["hooks"][0],
            value["hooks"]["UserPromptSubmit"][0]["hooks"][0],
        ]
        for handler in handlers:
            self.assertEqual(handler["type"], "command")
            self.assertEqual(
                handler["command"],
                'python3 "${PLUGIN_ROOT}/plugins/codex/hooks/praxis_context.py"',
            )
            self.assertEqual(
                handler["commandWindows"],
                'py -3 "%PLUGIN_ROOT%\\plugins\\codex\\hooks\\praxis_context.py"',
            )
            self.assertIsInstance(handler["additionalContextLimit"], int)
            self.assertGreater(handler["additionalContextLimit"], 0)
            self.assertLessEqual(handler["additionalContextLimit"], 2500)
            serialized = json.dumps(handler, sort_keys=True)
            for forbidden in ("prompt", "session_id", "transcript_path", "{cwd}", "${cwd}"):
                self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
