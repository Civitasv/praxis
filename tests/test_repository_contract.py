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
            "Docs/Architecture/Overview.md",
            "Docs/Architecture/Tutor Model.md",
            "Docs/Architecture/Harness Integration.md",
            "Docs/Development/Validation.md",
            "Docs/Specs/Feature-01 Repository Foundation.md",
            "Docs/Specs/Feature-02 Praxis State Core.md",
            "Docs/Specs/Feature-03 Verified Project Model.md",
            "Docs/Specs/Feature-04 Tutor Decision Loop.md",
            "Docs/Specs/Feature-05 Codex Integration.md",
            ".github/pull_request_template.md",
        ]
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_agents_contract_names_core_invariants(self) -> None:
        text = self.read("AGENTS.md")
        for expected in (
            "Tutor judgment loop is the product center",
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
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_state_records_features_one_through_five_implemented(self) -> None:
        text = self.read("State.md")
        for feature in range(1, 6):
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
        ):
            self.assertIn(f"{capability}: Implemented", text)
        self.assertIn("Feature-06: Pending", text)
        self.assertNotIn("Feature-05: Pending", text)

    def test_state_lists_current_validation_commands(self) -> None:
        text = self.read("State.md")
        for command in (
            "python -m unittest discover -s tests -v",
            "python -m compileall -q praxis tests",
            "pnpm typecheck",
            "pnpm test:dsh",
        ):
            self.assertIn(command, text)

    def test_readme_describes_codex_integration_without_claiming_live_host_trust(self) -> None:
        text = self.read("README.md")
        for expected in (
            "Features 01–05 are implemented",
            "state.json",
            "source fingerprints",
            "decision-level",
            "decisions.md",
            "open -> selected -> implemented -> verified",
            "shared Praxis Tutor Skill",
            "SessionStart",
            "UserPromptSubmit",
            "3000",
            "manual",
            "Feature-06",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)
        self.assertIn("trust", text.lower())
        self.assertIn("installation", text.lower())
        self.assertIn("does not enable", text.lower())

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
