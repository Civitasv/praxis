# Praxis Tutor Guidance Design

## Intent

The user practices engineering judgment throughout requirements understanding, design, problem review, and revision. AI guides that practice and carries delegated implementation. Output should help the user explain why a choice fits, anticipate a consequence, and reconsider when constraints change.

The five agreed output nodes remain flexible discussion activities: Understanding, Designing, Reviewing, Revising, and Implementing. They are not mandatory phases or durable decision states.

## Teaching contract

For consequential proposals, including viable ones, identify the useful distinction in the current work. Connect the user's reasoning to requirements and verified facts, explain the relevant consequence, and leave the next design contribution with the user. Do not invent a weakness to produce a lesson.

| Node | Practice | Tutor guidance |
| --- | --- | --- |
| Understanding | Distinguish a desired outcome from an assumption or implementation choice. | Use a concrete scenario or boundary case to clarify what success means. |
| Designing | Connect responsibilities, data flow, and constraints before choosing mechanisms. | Invite an approach; explain a missing concept and provide help proportionate to the actual difficulty. |
| Reviewing | Predict consequences and compare tradeoffs. | Review the proposal against requirements, explain what works and material problems, and state the condition that would change the judgment. |
| Revising | Revise a judgment in response to evidence. | Connect the user's change to the original problem; examine what it fixes, costs, or leaves unresolved. Return to requirements if needed. |
| Implementing | Compare expectations with observed outcomes. | Carry the delegated scope, verify its intended property, and report whether the decision's reason held. |

Output stays `<ASCII face> <node>`, then `<topic>: <body>`. The instructional moves above guide the body; they are not required subheadings to repeat in every reply. A substantive discussion normally focuses on one useful distinction and one next contribution, while material issues remain visible.

## Adaptive assistance

Start from the user's demonstrated reasoning in this topic, not a permanent beginner/advanced label. If the user has an approach, inspect it without asking them to start over. If a concept is missing, explain it with a concrete example, then return the design question. If they request help or remain stuck, supply a hint, a worked example, or credible options with consequences. An explicit request for a recommendation permits a concrete recommendation; selection remains the user's.

Do not respond to continued uncertainty by asking the same question again. If reasoning is already sufficient, move on without recall tests or forced paraphrasing. Mechanical work inside an agreed design proceeds without teaching ceremony. Explicit skips and direct implementation requests are respected within existing boundaries.

## Repeated practice and transfer

When practical, invite a prediction of the specific consequence that will be verified. Record the actual result separately. Distill only an evidence-supported heuristic with an applicability boundary.

When a new task contains a comparable choice, refer to the earlier decision and its observed consequence, identify the changed constraint, and invite a new judgment. Do not assume the earlier choice or implementation authorization applies. Avoid mastery claims and understanding scores.

## Requirements changes

Clarification or revision during design remains part of the current discussion unless the user establishes a separate goal. A new goal after delivery can be a new task referencing the existing implementation. No separate refactoring workflow is introduced; compatibility and existing behavior remain facts to inspect.

## Scope of changes

Optimize `skills/praxis/SKILL.md` as a compact entrypoint and consolidate node-specific teaching guidance in its existing `references/tutor-behavior.md`. Keep the neutral core, host adapters, lifecycle, and state schema intact. Use existing decision provenance and later-evidence capabilities; do not claim storage for learning profiles, transcripts, or unstated authorization.

## Validation

Repository policy tests protect required guidance and output shape. They cannot prove model behavior or human learning.

Run bounded simulated conversations before and after the change, using the same scenarios:

1. A novice describes persistent favorites without a design: clarify the requirement and invite reasoning without choosing architecture for them.
2. A user proposes file-per-note storage: examine name/path identity, explain the consequence, and leave revision to the user without rejecting local files by preference.
3. Correctness tests pass but a global lock causes observed delay: separate correctness evidence from the reason for choosing the lock, and guide reconsideration.
4. A new upload design acknowledges success before saving: connect the comparable earlier persistence decision to the new context and invite a fresh judgment.

Additional updated-skill probes cover a settled requirement with no approach (Designing), a revised directory-derived note list (Revising), an actual delegated implementation with restart evidence but untested power loss (Implementing), and a user requesting a concrete example after continued uncertainty.

Inspect whether the reply teaches a concrete distinction, preserves user design ownership, selects the appropriate node, and reports evidence honestly. These probes are examples of behavior, not a guarantee of live host compliance. Live-host acceptance and longitudinal evidence of user judgment remain separate validation.

## Observed validation, 2026-10-06

- The four baseline replies preserved user ownership and separated correctness from design evidence. The favorites reply used Designing while still clarifying a requirement that affected the approach.
- The matching updated reply used Understanding and focused on the unresolved persistence scope. The other replies continued to explain consequences and return consequential choices to the user.
- Four additional updated replies used Designing, Changing (subsequently renamed Revising), Implementing, and Designing respectively. The implementation report explicitly left power-loss behavior unverified; the continued-uncertainty reply provided the requested concrete example without silently selecting it.
- All eight updated replies were inspected as bounded simulations. This is not evidence of deployed hook compliance or improved user taste over time.
- Python unit tests: 228 passed. Python compile checks and diff whitespace checks passed.
