from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CiContractTests(unittest.TestCase):
    def workflow(self) -> str:
        path = ROOT / ".github" / "workflows" / "ci.yml"
        self.assertTrue(path.is_file(), "missing GitHub Actions workflow")
        return path.read_text(encoding="utf-8")

    def test_runs_for_pull_requests_and_master_pushes(self) -> None:
        text = self.workflow()
        self.assertIn("pull_request:", text)
        self.assertIn("push:", text)
        self.assertIn("- master", text)

    def test_python_310_unit_and_compile_checks_are_explicit(self) -> None:
        text = self.workflow()
        self.assertIn("3.10", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python -m compileall -q praxis tests", text)

    def test_node_pnpm_typecheck_and_dsh_tests_are_explicit(self) -> None:
        text = self.workflow()
        self.assertIn("pnpm/action-setup@v4", text)
        self.assertIn("version: 11.7.0", text)
        self.assertIn("node-version: 22.20.0", text)
        self.assertIn("pnpm typecheck", text)
        self.assertIn("pnpm test:dsh", text)

    def test_superseded_runs_are_cancelled(self) -> None:
        text = self.workflow()
        self.assertIn("concurrency:", text)
        self.assertIn("cancel-in-progress: true", text)

    def test_lockfile_bootstrap_is_not_frozen(self) -> None:
        text = self.workflow()
        self.assertIn("pnpm install --no-frozen-lockfile", text)

    def test_validation_docs_forbid_false_green(self) -> None:
        text = (ROOT / "Docs" / "Development" / "Validation.md").read_text(encoding="utf-8")
        self.assertIn("cannot be reported Green", text)


if __name__ == "__main__":
    unittest.main()
