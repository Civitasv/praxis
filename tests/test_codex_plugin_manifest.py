import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CodexPluginManifestTests(unittest.TestCase):
    def load_manifest(self, relative: str) -> dict:
        path = ROOT / relative
        self.assertTrue(path.is_file(), f"missing manifest: {relative}")
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(value, dict)
        return value

    def test_portable_and_compatibility_manifests_describe_praxis(self) -> None:
        portable = self.load_manifest("plugin.json")
        compatibility = self.load_manifest(".codex-plugin/plugin.json")
        self.assertEqual(portable["name"], "praxis")
        self.assertEqual(compatibility["name"], "praxis")
        self.assertEqual(portable["version"], compatibility["version"])
        self.assertEqual(portable["description"], compatibility["description"])

    def test_portable_manifest_uses_agent_plugins_schema_and_openai_hooks_overlay(self) -> None:
        portable = self.load_manifest("plugin.json")
        self.assertEqual(
            portable["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        openai = portable["extensions"]["com.openai"]
        self.assertEqual(openai["hooks"], "./plugins/codex/hooks/hooks.json")
        self.assertFalse("skills" in openai)

    def test_compatibility_manifest_references_shared_skill_and_hook_surfaces(self) -> None:
        compatibility = self.load_manifest(".codex-plugin/plugin.json")
        self.assertEqual(compatibility["skills"], "./skills/")
        self.assertEqual(compatibility["hooks"], "./plugins/codex/hooks/hooks.json")
        serialized = json.dumps(compatibility, sort_keys=True)
        self.assertNotIn("plugins/codex/skills", serialized)
        self.assertNotIn("plugins/codex/praxis", serialized)

    def test_declared_shared_skill_exists(self) -> None:
        self.assertTrue((ROOT / "skills" / "praxis" / "SKILL.md").is_file())

    def test_direct_control_skills_route_to_existing_cli(self) -> None:
        for action in ("enable", "disable", "status"):
            with self.subTest(action=action):
                source = (ROOT / "skills" / f"praxis-{action}" / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn(f"name: praxis-{action}\n", source)
                self.assertIn(f"`praxis {action} --cwd .`", source)


if __name__ == "__main__":
    unittest.main()
