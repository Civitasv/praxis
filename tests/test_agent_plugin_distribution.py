from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentPluginDistributionTests(unittest.TestCase):
    def test_cursor_and_codebuddy_reuse_single_shared_skill_and_neutral_core(self) -> None:
        for host in ("cursor", "codebuddy"):
            self.assertFalse((ROOT / "plugins" / host / "skills").exists())
            self.assertFalse((ROOT / "plugins" / host / "praxis").exists())
        self.assertTrue((ROOT / "skills" / "praxis" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "praxis" / "recovery.py").is_file())

    def test_shared_hook_bridge_uses_cli_direct_argv_without_mcp(self) -> None:
        source = (ROOT / "plugins" / "shared" / "recovery_hook.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"recovery-status"', source)
        self.assertIn("subprocess.run(", source)
        self.assertIn("shell=False", source)
        self.assertNotIn("shell=True", source)

        for relative in (
            "plugins/cursor/.mcp.json",
            "plugins/codebuddy/.mcp.json",
            ".cursor-plugin/mcp.json",
            ".codebuddy-plugin/mcp.json",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_host_wrappers_do_not_parse_prompt_or_transcript_semantics(self) -> None:
        for relative in (
            "plugins/cursor/hooks/praxis_context.py",
            "plugins/codebuddy/hooks/praxis_context.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn('.get("prompt")', source, relative)
            self.assertNotIn('.get("transcript_path")', source, relative)
            self.assertNotIn("decision-select", source, relative)

    def test_ci_has_cursor_codebuddy_package_job(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("\n  agent_plugins:\n", workflow)
        self.assertIn("name: Cursor / CodeBuddy plugins", workflow)
        self.assertIn("tests.test_cursor_integration", workflow)
        self.assertIn("tests.test_codebuddy_integration", workflow)
        self.assertIn("tests.test_shared_recovery_hook", workflow)
        self.assertIn("tests.test_command_surfaces", workflow)
        self.assertIn(
            "python -m compileall -q plugins/shared plugins/cursor plugins/codebuddy",
            workflow,
        )

    def test_validation_document_names_both_host_packages_and_cursor_limitation(self) -> None:
        text = (ROOT / "Docs" / "Development" / "Validation.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Cursor / CodeBuddy plugins", text)
        self.assertIn("beforeSubmitPrompt", text)
        self.assertIn("does not inject", text)
        self.assertIn("UserPromptSubmit", text)


if __name__ == "__main__":
    unittest.main()
