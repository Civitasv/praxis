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

    def test_code_map_names_foundation_and_state_core_boundaries(self) -> None:
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
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_state_records_feature_one_and_two_implemented(self) -> None:
        text = self.read("State.md")
        self.assertIn("Feature-01: Implemented", text)
        self.assertIn("Feature-02: Implemented", text)
        for capability in (
            "Project boundary discovery",
            "Versioned state schema",
            "Atomic CAS state writes",
            "Durable multi-task lifecycle",
            "JSON CLI state contract",
        ):
            self.assertIn(f"{capability}: Implemented", text)
        for feature in range(3, 7):
            self.assertIn(f"Feature-{feature:02d}: Pending", text)

    def test_state_lists_current_validation_commands(self) -> None:
        text = self.read("State.md")
        for command in (
            "python -m unittest discover -s tests -v",
            "python -m compileall -q praxis tests",
            "pnpm typecheck",
            "pnpm test:dsh",
        ):
            self.assertIn(command, text)

    def test_readme_does_not_claim_later_runtime_features(self) -> None:
        text = self.read("README.md")
        self.assertIn("state.json", text)
        self.assertIn("compare-and-swap", text)
        self.assertIn("Features 03–06", text)

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
