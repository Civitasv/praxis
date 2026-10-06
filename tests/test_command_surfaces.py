from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PraxisCommandSurfaceTests(unittest.TestCase):
    def test_shared_skill_defines_explicit_control_intents(self) -> None:
        text = (ROOT / "skills" / "praxis" / "SKILL.md").read_text(encoding="utf-8")
        for expected in (
            "`enable`: run `praxis enable --cwd .`",
            "`disable`: run `praxis disable --cwd .`",
            "`status`: run `praxis status --cwd .`",
            "Do not ask the user to run the underlying CLI",
        ):
            self.assertIn(expected, text)

    def test_cursor_exposes_praxis_command(self) -> None:
        manifest = json.loads(
            (ROOT / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["commands"], "./plugins/cursor/commands/")
        text = (
            ROOT / "plugins" / "cursor" / "commands" / "praxis.md"
        ).read_text(encoding="utf-8")
        self.assertIn("name: praxis", text)
        self.assertIn("/praxis enable", text)
        self.assertIn("/praxis disable", text)
        self.assertIn("/praxis status", text)
        self.assertIn("praxis enable --cwd .", text)
        self.assertIn("praxis disable --cwd .", text)

    def test_codebuddy_exposes_namespaced_activation_commands(self) -> None:
        manifest = json.loads(
            (ROOT / ".codebuddy-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["commands"], "./plugins/codebuddy/commands/")
        for command in ("enable", "disable", "status"):
            path = ROOT / "plugins" / "codebuddy" / "commands" / f"{command}.md"
            self.assertTrue(path.is_file(), command)
            text = path.read_text(encoding="utf-8")
            self.assertIn(f"praxis {command} --cwd .", text)

    def test_readme_uses_agent_commands_instead_of_manual_enable_script(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for expected in (
            "/praxis enable",
            "/praxis disable",
            "/praxis status",
            "/praxis:enable",
            "$praxis enable",
        ):
            self.assertIn(expected, text)
        self.assertNotIn("python3 -m praxis enable --cwd .", text)


if __name__ == "__main__":
    unittest.main()
