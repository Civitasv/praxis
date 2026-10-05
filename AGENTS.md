# Praxis Agent Collaboration Contract

## Purpose

Praxis is a Harness-neutral AI tutor for building software with coding agents. AI may carry execution, but Praxis keeps humans inside consequential engineering decisions and connects those decisions to verified outcomes.

## Working rules

1. Start at `Code.md`, then read the relevant Architecture/Spec, then source/tests.
2. Tutor judgment loop is the product center.
3. Preserve consequential decisions; automate mechanical work.
4. User proposal, Praxis proposal, verified fact, selected decision, and implemented result are distinct states.
5. Restoration is never approval.
6. A resumed, compacted, or cross-host session must not invent consent, rationale, or implementation status.
7. Harness-specific APIs must not enter the neutral Python core.
8. Codex and DSH adapters translate host lifecycle/events into shared Praxis semantics; they do not own durable domain rules.
9. Project facts need evidence. Unknown relationships remain unknown until verified.
10. Runtime project state belongs under `.praxis/` and is never repository source.
11. Failed writes, unsupported state versions, or unreadable state must be reported accurately; never claim persistence succeeded when it did not.
12. Never claim Green without executing the applicable checks.
13. Unrun validation is Pending, not Green.
14. Keep the neutral Python runtime dependency-free beyond the Python 3.10+ standard library in V1.

## Completion baseline

For a foundation change, run the relevant Python unit tests and compile checks plus TypeScript checks once the DSH workspace exists. GitHub Actions is the CI source of truth after the workflow is present.
