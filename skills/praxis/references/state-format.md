# State and Neutral CLI Boundary

Praxis project state is machine-owned. The shared Tutor policy consumes neutral state/CLI results and does not invent ids, revisions, fingerprints, lifecycle status, or approval.

## Durable authority

- `state.json` owns enabled/paused state, tasks, verified project-model metadata, and decision records.
- `code.md` and `decisions.md` are deterministic projections. They are readable context, not writable authority and are never parsed back into state.
- Decision records are authoritative for unresolved consequential choices. `status == open` means unresolved.

## Decision lifecycle data

Keep these provenance slots distinct: user proposal, verified constraints, Praxis challenge, alternatives, selected decision, user reasoning, accepted tradeoffs, implementation result, verification result, and later evidence.

The lifecycle is `open -> selected -> implemented -> verified`, with `superseded` and `abandoned` as terminal alternatives.

## Neutral command intent

Use neutral commands to read status, create/select decisions, record implementation and verification, supersede/abandon decisions, add later evidence, and rebuild projections. Respect decision revision conflicts by re-reading instead of overwriting.

A successful command result is evidence that state was saved. Never claim persistence after an error or failed write.

## Recording recipe

Use the neutral CLI available for the active installation. Confirm supported arguments with `--help`; if a stale launcher lacks a command, use the installation's documented module launcher and report the mismatch. Never edit state.json directly or create a parallel learning-notes authority. Runtime records stay under `.praxis/`, not repository source.

Read this recipe before the first consequential decision in sustained development. Record at meaningful events, not every message or tool call. Pure explanation and mechanical edits do not need a new task or decision.

1. Read `praxis status --cwd .`. Use a clearly relevant existing task without rebinding it; several plausible candidates require user choice. Otherwise create a task with `task-create --cwd . --expected-revision REV --host HOST --title TITLE`. Supply `--conversation-id` only when the host provides a verified identity; never invent one. `REV` is the returned state revision, and `HOST` is the actual host name.
2. At the first important unresolved choice, use `decision-create --cwd . --task-id TASK --class engineering --title TITLE --context CONTEXT`. Use `architectural` for a system-level boundary. Optional `--user-proposal`, repeated `--verified-constraint`, `--praxis-challenge`, repeated `--alternative`, and repeated `--blocked-scope` contain only already established content. Save before waiting on user reasoning so the choice survives an interruption.
3. Use `decision-evidence --cwd . --decision-id DECISION --expected-decision-revision DREV --evidence TEXT` for subsequent user reasoning, revisions, predictions, explicit skips, user delegation, and later observations. Read the relevant record before appending. Label source and scope in ordinary text, for example `User revision: ...`, `User delegation: implement ...`, or `Observed result: ...`. Preserve the original proposal. AI explanations are not evidence that the user demonstrated understanding. Evidence does not itself advance lifecycle.
4. Explicit selection permits `decision-select --cwd . --decision-id DECISION --expected-decision-revision DREV --selected-decision DESIGN`. Supply `--user-reasoning` only for a reason the user actually stated or adopted; use repeated `--accepted-tradeoff` only for explicit acceptance. If selection and implementation delegation occur together, save both from the same reply without asking again. Selection alone leaves implementation unauthorized.
5. Save user delegation with `decision-evidence` before dependent implementation. It must identify the agreed coding scope. Missing evidence during recovery remains missing even if the decision is selected. Explicit direct implementation may settle and delegate the bounded proposal presented; it does not settle undisclosed independent choices.
6. Once the selected change actually exists, use `decision-implemented --cwd . --decision-id DECISION --expected-decision-revision DREV --result RESULT`. Explain the implemented mechanism and relevant location, not merely an intended outcome.
7. Save observed checks with `decision-evidence` while required consequence checks are still Pending. Partial passing results or a failed check do not justify `verified`. After applicable checks of the chosen property's consequence succeed, use `decision-verify --cwd . --decision-id DECISION --expected-decision-revision DREV --result RESULT`. Include the actual checks, outcome, what the evidence supports, and limits. A recorded result is caller-supplied evidence, not independent proof by the CLI. If evidence contradicts the choice, discuss revision and preserve the failed observation; do not mark the rejected reason verified.
8. Keep task presentation current using `task-update --cwd . --task-id TASK --expected-revision REV --stage STAGE --status STATUS`. Stages are `understanding`, `design`, `awaiting_decision`, `implementation`, `verification`, `complete`, or `blocked`; statuses are `active`, `blocked`, or `complete`. These are existing lifecycle values, not the localized reply headings. Only mark a task complete after relevant decisions and agreed checks are resolved, verified, superseded, or explicitly abandoned. Pending cross-application acceptance keeps the task active at verification. Mechanical work outside blocked scopes continues.

Replace uppercase placeholders with actual values as separate CLI arguments. Global writes require the returned state revision; decision writes require the returned decision revision from `state.decisions.records[DECISION].revision`. IDs come from successful create results. Read `decision-status --cwd . --task-id TASK` for summaries and the corresponding full records in its returned `state`; never infer that a summary contains all evidence.

Before each dependent write, use the latest returned revision. On conflict, re-read, reconcile the actual change, and retry only the still-valid action. Do not blindly retry creation and duplicate a task or decision. A failed write prevents a persistence claim; report it and continue independent safe work. Never pretend recovery will contain unsaved evidence.

An evidence note may say what response is awaited: reasoning about ownership, selection between proposals, implementation delegation, or an unrun check. This is not a machine-readable stage, a new authorization field, or a second pending-decision store. Preserve the chronology; a resolved note is historical evidence. Later explicit replies may resolve an earlier wait, so inspect the complete relevant record.

Use `decision-render --cwd .` when a readable projection is useful or reported out of date. Rendering does not select a design or advance any lifecycle.

## Activation

Installation does not enable a project. Explicit project state controls activation. A paused project remains paused until explicitly resumed.
