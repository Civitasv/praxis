# Feature-04 Tutor Decision Loop

## Objective

Turn Praxis from a reliable project-state system into a persistent AI Tutor that keeps the human inside consequential engineering judgment while AI handles most implementation work.

Feature-04 establishes durable decision provenance, task-linked decision lifecycle state, decision-level concurrency, deterministic decision history projection, adapter-ready JSON commands, and the shared Tutor Skill/behavior contract.

The detailed design rationale is recorded in `docs/superpowers/specs/2026-10-06-tutor-decision-loop-design.md`.

## Authority

`state.json` remains the sole machine-readable authority.

Decision state lives under optional top-level `decisions` metadata. `.praxis/decisions.md` is a deterministic, rebuildable projection and is never parsed back into state.

Machine-owned values include:

- decision ids;
- decision revisions;
- decisions aggregate revision;
- lifecycle status;
- task linkage validation;
- projection markers.

The model supplies semantic content but cannot manufacture machine revision metadata.

## Decision classes

Praxis recognizes:

- `mechanical`;
- `engineering`;
- `architectural`.

Mechanical choices are not persisted by default. Engineering and architectural decisions are persisted when consequential to the task.

## Provenance contract

Decision state must distinguish:

- verified constraints;
- user proposal;
- Praxis challenge/recommendation;
- selected decision;
- user reasoning;
- accepted tradeoffs;
- implementation result;
- verification result;
- later evidence/inference.

Praxis must not rewrite provenance. AI-generated reasoning is not stored as user reasoning unless the user actually adopts it. An AI recommendation is not a selected decision. Restart/recovery/compaction/silence is not approval.

## Lifecycle

Primary lifecycle:

```text
open -> selected -> implemented -> verified
```

Terminal alternatives:

```text
superseded
abandoned
```

Rules:

- `open` means a consequential choice remains unresolved;
- only explicit user selection or explicit risk/tradeoff acceptance advances to `selected`;
- implementation completion advances `selected` to `implemented` only when the recorded selected decision was actually implemented;
- verification is recorded separately and is required for `verified`;
- recovery never changes lifecycle status;
- invalid transitions fail without mutating state.

## Decision-level concurrency

Existing decisions use exact decision revision CAS.

Two unrelated decisions may advance despite global state revision movement. Two writers using the same stale revision for the same decision conflict and must re-read.

All writes reuse Feature-02 locking, atomic state replacement, and no-op detection semantics.

## Task linkage

Every durable decision references an existing task id.

The neutral core must support listing open decisions globally and by task.

`decisions[*].status == open` is authoritative for unresolved Tutor choices. Feature-02 `pending_choices` remains compatible metadata but is not authoritative after Feature-04.

## Blocking semantics

An open decision may record semantic blocked scopes. Tutor behavior blocks only dependent implementation while allowing unrelated/mechanical work to continue.

The neutral core validates and stores blocked scope labels but does not infer source-code dependency graphs from them.

## Decision record minimum fields

Each decision includes at least:

```text
revision
task_id
class
status
title
context
user_proposal
verified_constraints
praxis_challenge
alternatives
selected_decision
user_reasoning
accepted_tradeoffs
blocked_scopes
implementation_result
verification
later_evidence
```

Optional semantic fields may be absent/null when genuinely not recorded. Missing historical content is never synthesized during rendering or recovery.

## Neutral Python core

Feature-04 adds `praxis/decisions.py`.

Required neutral capabilities:

```text
create decision
read/list decisions
list open decisions by task
select decision
record implementation result
record verification result
supersede decision
abandon decision
add later evidence
read decision/projection status
render decisions projection
```

All operations preserve task state, project-model state, and unknown top-level metadata.

## `decisions.md` projection

The renderer emits stable decision-id ordering and a machine marker keyed to the aggregate decisions revision.

Missing semantic fields render as `Not recorded` rather than inferred prose.

Projection creation/replacement is atomic. Symlinked or otherwise unsafe projection targets are rejected. Missing/out-of-sync output is reported as render-required and can be deterministically rebuilt from state.

## CLI JSON contract

Feature-04 adds adapter-facing commands for:

```text
decision-status
decision-create
decision-select
decision-implemented
decision-verify
decision-supersede
decision-abandon
decision-render
```

Additional read/later-evidence commands are allowed when needed for a clean adapter contract.

Commands emit exactly one JSON object. Stable decision error codes include:

```text
unknown_task
unknown_decision
decision_conflict
invalid_decision
invalid_transition
decision_render_failed
```

## Shared Praxis Skill

Feature-04 creates:

```text
skills/praxis/
├── SKILL.md
└── references/
    ├── tutor-behavior.md
    ├── decision-policy.md
    ├── repository-understanding.md
    ├── recovery.md
    └── state-format.md
```

The Skill is English, Harness-neutral, and progressively loads detailed references.

Installation alone does not enable Praxis.

## Tutor behavior contract

Praxis follows a dynamic loop:

```text
Understand
-> Inspect verified project facts
-> Surface consequential decisions
-> Discuss / teach / challenge
-> Agree
-> Implement
-> Verify
-> Reflect
```

Behavior requirements:

- viable user designs are respected and refined, not replaced because the AI prefers another pattern;
- concrete false assumptions/material risks are surfaced before dependent implementation;
- unresolved risk blocks only affected work;
- mechanical details proceed without repeated confirmation once the surrounding design is settled;
- when the user does not know, Praxis explains only enough background to enable the next meaningful tradeoff, may give a default recommendation, and does not deadlock into repeated questioning;
- reflection connects decision -> implementation -> observed verification result rather than producing a generic lesson;
- Praxis does not claim mastery or understanding scores.

## Recovery contract

Durable task/decision state is sufficient to recover the current judgment boundary without full transcript storage.

Recovery may summarize open decisions but cannot:

- auto-select the prior AI recommendation;
- infer approval from restart/compaction;
- invent user reasoning;
- treat selected as implemented;
- treat implemented as verified.

Host-specific lifecycle injection remains Feature-05/06.

## Acceptance criteria

### AC-001 — provenance remains distinct

User proposal/reasoning, AI challenge/recommendation, verified facts, selected decision, implementation, and verification cannot silently overwrite each other's provenance.

### AC-002 — explicit selection is required

An AI proposal, recovery, silence, or compaction cannot move an open decision to selected.

### AC-003 — lifecycle states remain honest

Selected, implemented, and verified are separate durable states with validated transitions.

### AC-004 — same-decision conflicts are detected

A stale same-decision writer conflicts; unrelated decisions may proceed after global state revision movement.

### AC-005 — task linkage is durable

Open decisions can be queried by task without transcript parsing, and unknown task ids are rejected.

### AC-006 — only affected implementation is blocked

The Tutor policy allows unrelated/mechanical work to continue while an open decision blocks its declared dependent scopes.

### AC-007 — deterministic decision history recovery

`decisions.md` can be deleted/outdated and rebuilt deterministically from authoritative state.

### AC-008 — adapter-ready JSON

Decision operations expose stable JSON success/error contracts with no Harness-specific dependency in the Python core.

### AC-009 — Tutor does not deadlock on uncertainty

Behavior tests cover `I don't know` and require just-enough teaching plus a meaningful tradeoff rather than repeated Socratic prompts.

### AC-010 — implementation becomes feedback

Behavior contracts connect the selected decision to implementation and real verification results, including cases where verification contradicts the original expectation.

## Implementation order

1. Decision schema and provenance validation.
2. Decision-level CAS and lifecycle transitions.
3. Task linkage and unresolved decision queries.
4. Deterministic `decisions.md` projection.
5. Decision JSON CLI.
6. Shared Praxis Skill and behavior references.
7. Tutor behavior/scenario contract tests.
8. Repository closure (`Code.md`, `State.md`, README) and final CI.

## Non-goals

Feature-04 does not implement:

- Codex SessionStart/UserPromptSubmit hooks;
- native DSH/Cordis lifecycle integration;
- transcript parsing;
- automatic semantic approval detection;
- code-range dependency inference from blocked scopes;
- quizzes or learning/understanding scores;
- external model calls;
- backend services, vector stores, or telemetry.