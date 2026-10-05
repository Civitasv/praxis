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
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_state_records_features_one_through_three_implemented(self) -> None:
        text = self.read("State.md")
        self.assertIn("Feature-01: Implemented", text)
        self.assertIn("Feature-02: Implemented", text)
        self.assertIn("Feature-03: Implemented", text)
        for capability in (
            "Source evidence fingerprints",
            "Section-level project-model CAS",
            "Incremental stale detection",
            "Deterministic code.md projection",
            "Project-model JSON CLI",
        ):
            self.assertIn(f"{capability}: Implemented", text)
        for feature in range(4, 7):
            self.assertIn(f"Feature-{feature:02d}: Pending", text)
        self.assertNotIn("Feature-03: Pending", text)

    def test_state_lists_current_validation_commands(self) -> None:
        text = self.read("State.md")
        for command in (
            "python -m unittest discover -s tests -v",
            "python -m compileall -q praxis tests",
            "pnpm typecheck",
            "pnpm test:dsh",
        ):
            self.assertIn(command, text)

    def test_readme_describes_verified_model_without_claiming_tutor_or_host_runtime(self) -> None:
        text = self.read("README.md")
        for expected in (
            "state.json",
            "compare-and-swap",
            "source fingerprints",
            "section-level",
            "stale",
            "code.md",
        ):
            self.assertIn(expected, text)
        self.assertIn("Features 04–06", text)

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
