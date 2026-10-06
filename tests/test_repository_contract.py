from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        path = ROOT / relative
        self.assertTrue(path.is_file(), f"missing repository contract file: {relative}")
        return path.read_text(encoding="utf-8")

    def test_repository_contract_files_exist(self) -> None:
        required = [
            "AGENTS.md",
            "Code.md",
            "State.md",
            "README.md",
            "README.zh-CN.md",
            "LICENSE",
            "Docs/Architecture/Overview.md",
            "Docs/Architecture/Tutor Model.md",
            "Docs/Architecture/Harness Integration.md",
            "Docs/Development/Validation.md",
            "Docs/Specs/Feature-01 Repository Foundation.md",
            "Docs/Specs/Feature-02 Praxis State Core.md",
            "Docs/Specs/Feature-03 Verified Project Model.md",
            "Docs/Specs/Feature-04 Tutor Decision Loop.md",
            "Docs/Specs/Feature-05 Codex Integration.md",
            "Docs/Specs/Feature-06 DSH Integration.md",
            "Docs/Specs/Feature-07 Cursor and CodeBuddy Integration.md",
            ".github/pull_request_template.md",
        ]
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_repository_uses_single_canonical_docs_tree(self) -> None:
        self.assertTrue((ROOT / "Docs").is_dir())
        # Inspect actual names: case-insensitive filesystems resolve docs to Docs.
        names = [path.name for path in ROOT.iterdir() if path.name.casefold() == "docs"]
        self.assertEqual(names, ["Docs"])

    def test_agents_contract_names_core_invariants(self) -> None:
        text = self.read("AGENTS.md")
        for expected in (
            "Tutor taste loop is the product center",
            "Teach the distinction between credible alternatives",
            "Verification should test the consequence",
            "Restoration is never approval",
            "Harness-specific APIs must not enter the neutral Python core",
            "Never claim Green without executing the applicable checks",
            "Start at `Code.md`",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_code_map_names_implemented_neutral_core_boundaries(self) -> None:
        text = self.read("Code.md")
        for expected in (
            "praxis/",
            "skills/praxis/",
            "plugins/codex/",
            "plugins/dsh/",
            "praxis/project.py",
            "praxis/state.py",
            "praxis/locking.py",
            "praxis/tasks.py",
            "praxis/fingerprints.py",
            "praxis/project_map.py",
            "praxis/decisions.py",
            ".praxis/decisions.md",
            "plugin.json",
            ".codex-plugin/plugin.json",
            "plugins/codex/hooks/",
            "praxis/recovery.py",
            "plugins/dsh/src/lifecycle.ts",
            "plugins/dsh/src/praxis-cli.ts",
            "plugins/dsh/src/context.ts",
            "plugins/dsh/src/skill.ts",
            ".cursor-plugin/plugin.json",
            "plugins/cursor/hooks/",
            ".codebuddy-plugin/plugin.json",
            "plugins/codebuddy/hooks/",
            "plugins/shared/recovery_hook.py",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_state_records_features_one_through_seven_implemented(self) -> None:
        text = self.read("State.md")
        for feature in range(1, 8):
            self.assertIn(f"Feature-{feature:02d}: Implemented", text)
        for capability in (
            "Durable decision provenance",
            "Decision-level CAS and lifecycle",
            "Deterministic decisions.md projection",
            "Decision JSON CLI",
            "Shared Praxis Tutor Skill",
            "Portable Codex plugin package",
            "SessionStart and UserPromptSubmit recovery",
            "Bounded Codex recovery context",
            "Manual Skill fallback",
            "Neutral recovery snapshot",
            "Native DSH Cordis plugin",
            "DSH shared Skill registration",
            "DSH agent lifecycle recovery",
            "DSH direct-argv Python bridge",
            "Bounded DSH recovery context",
            "Native Cursor plugin",
            "Native CodeBuddy plugin",
            "Shared host recovery CLI bridge",
        ):
            self.assertIn(f"{capability}: Implemented", text)
        self.assertNotIn("Feature-06: Pending", text)
        self.assertNotIn("Feature-07: Pending", text)

    def test_state_lists_current_validation_commands(self) -> None:
        text = self.read("State.md")
        for command in (
            "python -m unittest discover -s tests -v",
            "python -m compileall -q praxis tests",
            "pnpm typecheck",
            "pnpm test:dsh",
        ):
            self.assertIn(command, text)

    def test_readme_is_product_facing_and_routes_internals_to_docs(self) -> None:
        text = self.read("README.md")
        for expected in (
            "Build with AI. Develop taste.",
            "## Philosophy",
            "## What using Praxis feels like",
            "## Install",
            "/praxis enable",
            "/praxis:enable",
            "$praxis:praxis-enable",
            "Codex",
            "DeepSeek Harness / Cordis",
            "Cursor",
            "CodeBuddy",
            "## What Praxis helps you build",
            "Docs/Architecture/Overview.md",
            "Docs/Architecture/Harness%20Integration.md",
            "Docs/Specs/",
            "Docs/Development/Validation.md",
            "AGPL-3.0-only",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

        for implementation_detail in (
            "Features 01–06 are implemented",
            "compare-and-swap",
            "source fingerprints",
            "agent/pre-step",
            "SessionStart",
            "UserPromptSubmit",
        ):
            with self.subTest(implementation_detail=implementation_detail):
                self.assertNotIn(implementation_detail, text)

    def test_tutor_skill_encodes_taste_first_behavior(self) -> None:
        skill = self.read("skills/praxis/SKILL.md")
        behavior = self.read("skills/praxis/references/tutor-behavior.md")
        policy = self.read("skills/praxis/references/decision-policy.md")
        model = self.read("Docs/Architecture/Tutor Model.md")

        for expected in (
            "develop engineering taste",
            "User proposes an approach",
            "User revises the approach",
            "User selects the design and user delegates implementation",
            "Teach what makes one choice better than another here",
            "Tests passing is not proof that a design was good",
            "Prefer X when Y because Z.",
        ):
            with self.subTest(source="skill", expected=expected):
                self.assertIn(expected, skill)

        for expected in (
            "teaches the distinction, not just the answer",
            "what it optimizes for",
            "boundary condition",
            "Do not equate \"tests passed\" with \"the design was good\"",
            "reusable distinction",
        ):
            with self.subTest(source="behavior", expected=expected):
                self.assertIn(expected, behavior)

        for expected in (
            "taste-bearing decision",
            "locally easiest option differs from the structurally cleaner option",
            "The distinction between them should be worth learning",
        ):
            with self.subTest(source="policy", expected=expected):
                self.assertIn(expected, policy)

        for expected in (
            "The Tutor teaches distinctions, not just answers.",
            "Passing tests alone does not prove that a design was good.",
            "The product outcome is not merely a correct implementation.",
        ):
            with self.subTest(source="model", expected=expected):
                self.assertIn(expected, model)

    def test_harness_architecture_records_codex_translation_boundary(self) -> None:
        text = self.read("Docs/Architecture/Harness Integration.md")
        for expected in (
            "translation-only",
            "SessionStart",
            "UserPromptSubmit",
            "transcript-independent",
            "manual",
        ):
            self.assertIn(expected, text)

    def test_harness_architecture_records_dsh_translation_boundary(self) -> None:
        text = self.read("Docs/Architecture/Harness Integration.md")
        for expected in (
            "DSH — Feature-06",
            "agent/created",
            "agent/pre-step",
            "translation-only",
            "direct argv",
            "praxis-dsh",
        ):
            self.assertIn(expected, text)

    def test_harness_architecture_records_cursor_and_codebuddy_boundaries(self) -> None:
        text = self.read("Docs/Architecture/Harness Integration.md")
        for expected in (
            "Cursor — Feature-07",
            "CodeBuddy — Feature-07",
            "beforeSubmitPrompt",
            "UserPromptSubmit",
            "does not support per-prompt context injection",
            "recovery-status",
            "No MCP",
        ):
            self.assertIn(expected, text)

    def test_validation_requires_python_310_and_github_actions(self) -> None:
        text = self.read("Docs/Development/Validation.md")
        self.assertIn("Python 3.10", text)
        self.assertIn("GitHub Actions", text)
        self.assertIn("cannot be reported Green", text)

    def test_pr_template_requires_pending_for_unrun_checks(self) -> None:
        text = self.read(".github/pull_request_template.md")
        self.assertIn("unrun", text.lower())
        self.assertIn("pending", text.lower())


if __name__ == "__main__":
    unittest.main()
