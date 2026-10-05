from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "praxis"
REQUIRED = [
    SKILL_ROOT / "SKILL.md",
    SKILL_ROOT / "references" / "tutor-behavior.md",
    SKILL_ROOT / "references" / "decision-policy.md",
    SKILL_ROOT / "references" / "repository-understanding.md",
    SKILL_ROOT / "references" / "recovery.md",
    SKILL_ROOT / "references" / "state-format.md",
]


class SkillContractTests(unittest.TestCase):
    def test_required_skill_files_exist_and_top_level_skill_is_compact(self) -> None:
        for path in REQUIRED:
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), str(path))
        lines = REQUIRED[0].read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), 160)

    def test_skill_progressively_links_every_reference(self) -> None:
        text = REQUIRED[0].read_text(encoding="utf-8")
        for name in (
            "tutor-behavior.md",
            "decision-policy.md",
            "repository-understanding.md",
            "recovery.md",
            "state-format.md",
        ):
            with self.subTest(name=name):
                self.assertIn(name, text)

    def test_shared_skill_is_host_neutral(self) -> None:
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in REQUIRED)
        for banned in ("Codex", "DeepSeek Harness", "DSH", "Cordis"):
            with self.subTest(banned=banned):
                self.assertNotIn(banned, corpus)

    def test_skill_encodes_activation_decision_and_recovery_boundaries(self) -> None:
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in REQUIRED).lower()
        for required in (
            "installation does not enable",
            "mechanical",
            "consequential",
            "verified project facts",
            "ai recommendation is not approval",
            "recovery is not approval",
            "blocked scopes",
            "no mastery score",
        ):
            with self.subTest(required=required):
                self.assertIn(required, corpus)

    def test_skill_keeps_provenance_and_lifecycle_distinct(self) -> None:
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in REQUIRED).lower()
        for required in (
            "user proposal",
            "praxis challenge",
            "selected decision",
            "user reasoning",
            "implementation result",
            "verification result",
            "open -> selected -> implemented -> verified",
        ):
            with self.subTest(required=required):
                self.assertIn(required, corpus)


if __name__ == "__main__":
    unittest.main()
