from pathlib import Path
import ast
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_IMPORT_FRAGMENTS = ("deepseek", "cordis", "codex", "plugins.dsh", "plugins.codex")


class CliBaselineTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "praxis", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_version_command_succeeds(self) -> None:
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout.strip(), r"^Praxis 0\.1\.0a0$")

    def test_unknown_argument_is_rejected(self) -> None:
        result = self.run_cli("--definitely-unknown")
        self.assertNotEqual(result.returncode, 0)

    def test_generated_project_state_is_ignored(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".praxis/", ignore.splitlines())

    def test_neutral_python_core_has_no_harness_imports(self) -> None:
        package = ROOT / "praxis"
        self.assertTrue(package.is_dir())
        for path in package.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.append(node.module)
            for module in imported:
                with self.subTest(path=str(path), module=module):
                    self.assertFalse(
                        any(fragment in module.lower() for fragment in FORBIDDEN_IMPORT_FRAGMENTS),
                        f"Harness-specific import leaked into neutral core: {module}",
                    )


if __name__ == "__main__":
    unittest.main()
