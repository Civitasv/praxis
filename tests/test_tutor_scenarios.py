from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "skills" / "praxis" / "references"


class TutorScenarioPolicyTests(unittest.TestCase):
    def text(self, name: str) -> str:
        return (REFS / name).read_text(encoding="utf-8").lower()

    def test_uncertainty_teaches_then_surfaces_one_meaningful_tradeoff(self) -> None:
        text = self.text("tutor-behavior.md")
        self.assertIn("i don't know", text)
        self.assertIn("minimum context", text)
        self.assertIn("one meaningful tradeoff", text)
        self.assertIn("default recommendation", text)

    def test_recovery_cannot_promote_lifecycle(self) -> None:
        text = self.text("recovery.md")
        self.assertIn("never treat silence, restart, compaction, or recovery as approval", text)
        self.assertIn("a selected decision is not implemented", text)
        self.assertIn("an implemented decision is not verified", text)

    def test_user_reasoning_never_backfills_from_praxis_rationale(self) -> None:
        text = self.text("decision-policy.md")
        self.assertIn("never attribute praxis-authored rationale to user reasoning", text)
        self.assertIn("leave user reasoning unrecorded", text)

    def test_verification_can_disprove_expectation_without_rewriting_history(self) -> None:
        text = self.text("tutor-behavior.md")
        self.assertIn(
            "verification may contradict the expected outcome; record the observed result without rewriting history",
            text,
        )
        self.assertIn("decision -> implementation -> verification", text)

    def test_open_risk_blocks_only_affected_scope(self) -> None:
        text = self.text("decision-policy.md")
        self.assertIn("only the affected declared scope waits", text)
        self.assertIn("unrelated mechanical work may continue", text)


if __name__ == "__main__":
    unittest.main()
