import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CodexDistributionTests(unittest.TestCase):
    def test_manifest_references_resolve_to_single_shared_surfaces(self) -> None:
        portable = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        compatibility = json.loads(
            (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        hook_path = portable["extensions"]["com.openai"]["hooks"].removeprefix("./")
        self.assertTrue((ROOT / hook_path).is_file())
        self.assertEqual(compatibility["hooks"].removeprefix("./"), hook_path)
        self.assertTrue((ROOT / compatibility["skills"].removeprefix("./") / "praxis" / "SKILL.md").is_file())
        self.assertFalse((ROOT / "plugins" / "codex" / "skills").exists())
        self.assertFalse((ROOT / "plugins" / "codex" / "praxis").exists())

    def test_adapter_does_not_read_transcript_or_parse_prompt_semantics(self) -> None:
        source = (ROOT / "plugins" / "codex" / "hooks" / "praxis_context.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("transcript_path", source)
        self.assertNotIn('.get("prompt")', source)
        self.assertNotIn("open(event", source)

    def test_neutral_core_has_no_codex_adapter_dependency(self) -> None:
        for path in sorted((ROOT / "praxis").glob("*.py")):
            source = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("plugins.codex", source, path.name)
            self.assertNotIn("from codex", source, path.name)
            self.assertNotIn("import codex", source, path.name)

    def test_ci_has_dedicated_codex_package_job(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("\n  codex:\n", workflow)
        self.assertIn("name: Codex package", workflow)
        self.assertIn("tests.test_codex_distribution", workflow)
        self.assertIn("python -m compileall -q plugins/codex praxis", workflow)

    def test_validation_document_names_codex_package_checks(self) -> None:
        text = (ROOT / "Docs" / "Development" / "Validation.md").read_text(encoding="utf-8")
        self.assertIn("Codex package", text)
        self.assertIn("tests.test_codex_context", text)
        self.assertIn("tests.test_codex_recovery", text)


if __name__ == "__main__":
    unittest.main()
