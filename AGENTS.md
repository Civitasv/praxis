# Praxis Agent Collaboration Contract

## Purpose

Praxis is a Harness-neutral AI tutor for building software with coding agents. AI may carry execution, while Praxis helps humans develop engineering taste by comparing consequential choices and connecting decisions to verified outcomes.

## Working rules

1. Start at `Code.md`, then read the relevant Architecture/Spec, then source/tests.
2. Tutor taste loop is the product center.
3. Slow down taste-bearing decisions; automate mechanical work.
4. Teach the distinction between credible alternatives, not just the recommended answer.
5. User proposal, Praxis proposal, verified fact, selected decision, and implemented result are distinct states.
6. Restoration is never approval.
7. A resumed, compacted, or cross-host session must not invent consent, rationale, or implementation status.
8. Harness-specific APIs must not enter the neutral Python core.
9. Codex and DSH adapters translate host lifecycle/events into shared Praxis semantics; they do not own durable domain rules.
10. Project facts need evidence. Unknown relationships remain unknown until verified.
11. Verification should test the consequence a decision was meant to create when practical; green tests alone do not prove good design.
12. Runtime project state belongs under `.praxis/` and is never repository source.
13. Failed writes, unsupported state versions, or unreadable state must be reported accurately; never claim persistence succeeded when it did not.
14. Never claim Green without executing the applicable checks.
15. Unrun validation is Pending, not Green.
16. Keep the neutral Python runtime dependency-free beyond the Python 3.10+ standard library in V1.

## Completion baseline

For a foundation change, run the relevant Python unit tests and compile checks plus TypeScript checks once the DSH workspace exists. GitHub Actions is the CI source of truth after the workflow is present.
