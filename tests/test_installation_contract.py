import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallationContractTests(unittest.TestCase):
    def test_python_package_is_git_pip_installable(self) -> None:
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        for expected in (
            '[build-system]',
            'requires = ["setuptools>=68"]',
            'build-backend = "setuptools.build_meta"',
            '[tool.setuptools.packages.find]',
            'include = ["praxis*"]',
            'praxis = "praxis.cli:main"',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

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
        self.assertEqual(package["exports"]["."], "./plugins/dsh/lib/index.js")
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
            "git clone --depth 1 https://github.com/Civitasv/praxis.git ~/.cursor/plugins/local/praxis",
            "dsh plugin --profile web add github:Civitasv/praxis",
            "codebuddy plugin marketplace add Civitasv/praxis --name praxis && codebuddy plugin install praxis@praxis",
            "/praxis enable",
            "/praxis:enable",
            "$praxis:praxis-enable",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

        self.assertIn("Codex", text)
        self.assertIn("Cursor", text)
        self.assertIn("DeepSeek Harness", text)
        self.assertIn("CodeBuddy", text)
        self.assertIn("codex plugin add praxis@praxis", text)

    def test_readme_documents_plugin_update_paths(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for expected in (
            "## Update Praxis",
            "python3 -m pip install --user --upgrade 'git+https://github.com/Civitasv/praxis.git'",
            "codex plugin marketplace upgrade praxis",
            "git -C ~/.cursor/plugins/local/praxis pull --ff-only",
            "dsh plugin --profile web update praxis",
            "codebuddy plugin marketplace update praxis && codebuddy plugin update praxis@praxis",
            "/reload-plugins",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)



if __name__ == "__main__":
    unittest.main()
