from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "skills" / "praxis" / "references"


class TutorScenarioPolicyTests(unittest.TestCase):
    def text(self, name: str) -> str:
        return (REFS / name).read_text(encoding="utf-8").lower()

    def test_uncertainty_teaches_then_returns_the_design_to_the_user(self) -> None:
        text = self.text("tutor-behavior.md")
        self.assertIn("i don't know", text)
        self.assertIn("minimum context", text)
        self.assertIn("invite the user to form or revise their approach", text)
        self.assertIn("when the user asks for help or remains stuck", text)

    def test_user_leads_design_and_revises_before_delegating_implementation(self) -> None:
        # Policy contract only: this does not execute or evaluate a model conversation.
        text = self.text("tutor-behavior.md")
        for required in (
            "ask for the user's approach and wait before offering a project-specific solution",
            "product behavior, technology choices, and architecture",
            "explain the evidence or uncertainty, the consequence, and a concrete suggestion",
            "personal preference is not a veto",
            "repeat review and revision",
            "no material unresolved issue in the affected scope",
            "explicitly delegates implementation",
            "implementation reveals a new consequential choice",
            "small code changes can carry consequential product decisions",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)
        skill = (REFS.parent / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("user proposes an approach", skill)
        self.assertIn("user revises the approach", skill)
        self.assertIn("user delegates implementation", skill)

    def test_recovery_cannot_promote_lifecycle(self) -> None:
        text = self.text("recovery.md")
        self.assertIn("never treat silence, restart, compaction, or recovery as approval", text)
        self.assertIn("a selected decision is not implemented", text)
        self.assertIn("an implemented decision is not verified", text)

    def test_node_output_uses_fixed_ascii_faces_and_topic_body_format(self) -> None:
        for name in (REFS.parent / "SKILL.md", REFS / "tutor-behavior.md"):
            text = name.read_text(encoding="utf-8")
            for heading in (
                "(o.o) Understanding",
                "(o-o) Designing",
                "(o_^) Reviewing",
                "(^_~) Revising",
                "(^_^) Implementing",
            ):
                with self.subTest(file=name.name, heading=heading):
                    self.assertIn(heading, text)
            self.assertIn("<topic>: <body>", text)
        behavior = self.text("tutor-behavior.md")
        self.assertIn("nodes can repeat or switch freely", behavior)
        self.assertIn("a node heading is not approval", behavior)

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

    def test_guidance_routes_by_gap_and_adapts_without_replacing_user_judgment(self) -> None:
        text = self.text("tutor-behavior.md")
        for required in (
            "choose the node from the unresolved gap",
            "including viable proposals",
            "one useful distinction and one next contribution",
            "demonstrated reasoning in this topic",
            "do not repeat the same unanswered design question",
            "invite a prediction of the consequence",
            "identify what changed before inviting a fresh judgment",
            "a past decision does not select the new design",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_build_requests_and_short_answers_preserve_reasoning_opportunities(self) -> None:
        behavior = self.text("tutor-behavior.md")
        for required in (
            "ordinary build requests retain the learning loop",
            "a brief answer or hesitation is not evidence that the user is stuck",
            "ask one concrete reasoning question",
            "missing reasoning does not revoke an explicit selection or delegation",
            "leave the project's design question open",
        ):
            with self.subTest(required=required):
                self.assertIn(required, behavior)

    def test_implementation_feedback_explains_the_mechanism_and_evidence(self) -> None:
        behavior = self.text("tutor-behavior.md")
        for required in (
            "the key code mechanism",
            "what the observed result supports or contradicts",
            "pending",
            "state ownership example",
            "clipboard restoration example",
            "testing boundary example",
        ):
            with self.subTest(required=required):
                self.assertIn(required, behavior)

    def test_recording_recipe_uses_existing_cli_and_separates_delegation(self) -> None:
        recipe = self.text("state-format.md")
        for command in (
            "task-create", "decision-create", "decision-evidence", "decision-select",
            "decision-implemented", "decision-verify", "task-update",
        ):
            with self.subTest(command=command):
                self.assertIn(command, recipe)
        for required in (
            "user delegation", "returned revision", "partial", "pending",
            "never edit state.json directly", "not a machine-readable stage",
        ):
            with self.subTest(required=required):
                self.assertIn(required, recipe)

    def test_recovery_loads_selected_and_implemented_records_and_evidence(self) -> None:
        recovery = self.text("recovery.md")
        for required in (
            "decision-status", "selected and implemented", "later_evidence",
            "missing reasoning", "implementation delegation", "pending",
        ):
            with self.subTest(required=required):
                self.assertIn(required, recovery)

    def test_recovery_does_not_relabel_observed_failure_as_pending(self) -> None:
        recovery = self.text("recovery.md")
        self.assertIn("unrun checks remain pending; observed failures remain fail", recovery)
        self.assertNotIn("unrun or failed, leave it pending", recovery)


if __name__ == "__main__":
    unittest.main()
