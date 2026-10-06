import json
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallationContractTests(unittest.TestCase):
    def test_python_package_is_git_pip_installable(self) -> None:
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(data["build-system"]["build-backend"], "setuptools.build_meta")
        self.assertIn("setuptools", " ".join(data["build-system"]["requires"]))
        self.assertEqual(data["tool"]["setuptools"]["packages"]["find"]["include"], ["praxis*"])
        self.assertEqual(data["project"]["scripts"]["praxis"], "praxis.cli:main")

    def test_codex_marketplace_exposes_root_praxis_plugin(self) -> None:
        path = ROOT / ".agents" / "plugins" / "marketplace.json"
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "praxis")
        self.assertEqual(len(data["plugins"]), 1)
        plugin = data["plugins"][0]
        self.assertEqual(plugin["name"], "praxis")
        self.assertEqual(plugin["source"]["source"], "url")
        self.assertEqual(plugin["source"]["url"], "https://github.com/Civitasv/praxis.git")
        self.assertEqual(plugin["source"]["ref"], "master")
        self.assertEqual(plugin["policy"]["installation"], "AVAILABLE")

    def test_codebuddy_marketplace_exposes_repository_plugin(self) -> None:
        path = ROOT / ".codebuddy-plugin" / "marketplace.json"
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "praxis")
        self.assertEqual(len(data["plugins"]), 1)
        plugin = data["plugins"][0]
        self.assertEqual(plugin["name"], "praxis")
        self.assertEqual(
            plugin["source"],
            {"source": "github", "repo": "Civitasv/praxis"},
        )

    def test_repository_root_is_an_installable_dsh_bundle(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["exports"]["."], "./plugins/dsh/src/index.ts")
        self.assertEqual(
            package["dsh"]["bundle"]["patch"],
            "./plugins/dsh/cordis.patch.yml",
        )
        for dependency in (
            "@deepseek-ai/cordis",
            "@deepseek-ai/dsh-agent",
            "@deepseek-ai/dsh-llm",
            "@deepseek-ai/dsh-skill",
        ):
            self.assertIn(dependency, package["peerDependencies"])

        patch = (ROOT / "plugins" / "dsh" / "cordis.patch.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("id: praxis-dsh", patch)
        self.assertIn("name: praxis", patch)

    def test_readme_has_shortest_supported_install_paths(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for expected in (
            "## Install",
            "python3 -m pip install --user 'git+https://github.com/Civitasv/praxis.git'",
            "codex plugin marketplace add Civitasv/praxis",
            "/plugins",
            "git clone --depth 1 https://github.com/Civitasv/praxis.git ~/.cursor/plugins/local/praxis",
            "dsh plugin --profile web add github:Civitasv/praxis",
            "codebuddy plugin marketplace add Civitasv/praxis --name praxis && codebuddy plugin install praxis@praxis",
            "python3 -m praxis enable --cwd .",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

        self.assertIn("Codex", text)
        self.assertIn("Cursor", text)
        self.assertIn("DeepSeek Harness", text)
        self.assertIn("CodeBuddy", text)
        self.assertIn("does not currently expose a non-interactive plugin install command", text)
        self.assertIn("does not currently expose a plugin-install subcommand", text)


if __name__ == "__main__":
    unittest.main()
