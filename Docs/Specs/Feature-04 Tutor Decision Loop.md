# Feature-04 Tutor Decision Loop

## Objective

Turn Praxis from a reliable project-state system into a persistent AI Tutor that helps the human develop engineering taste while AI handles most implementation work.

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

The first materialized `decisions` collection starts at aggregate revision `0`. A newly created decision starts at decision revision `0`. Subsequent semantic changes increment the affected decision revision and aggregate decisions revision exactly once. Global `state.revision` still advances once for each durable state write. True no-ops advance none of these revisions.

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

`verified_constraints` is semantic content supplied by the caller, not something the decision core independently proves. The shared Tutor policy may populate it only from already verified project facts/evidence or an explicitly identified external fact source; unknown assumptions remain unknown rather than being promoted to verified constraints.

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

Allowed transitions are:

```text
open        -> selected | superseded | abandoned
selected    -> implemented | superseded | abandoned
implemented -> verified | superseded | abandoned
verified    -> superseded
superseded  -> (none)
abandoned   -> (none)
```

Rules:

- `open` means a consequential choice remains unresolved;
- only explicit user selection or explicit risk/tradeoff acceptance advances to `selected`;
- implementation completion advances `selected` to `implemented` only when the recorded selected decision was actually implemented;
- verification is recorded separately and is required for `verified`;
- a later decision may supersede an earlier decision after any non-abandoned stage, but superseding must reference the replacement decision id;
- abandoned decisions are terminal and cannot later become selected;
- lifecycle never moves backward;
- recovery never changes lifecycle status;
- invalid transitions fail without mutating state.

## Decision-level concurrency

Existing decisions use exact decision revision CAS.

Two unrelated decisions may advance despite global state revision movement. Two writers using the same stale revision for the same decision conflict and must re-read.

All writes reuse Feature-02 locking, atomic state replacement, and no-op detection semantics.

## Task linkage

Every durable decision references an existing task id.

The neutral core must support listing open decisions globally and by task.

`decisions.records[*].status == open` is authoritative for unresolved Tutor choices. Feature-02 `pending_choices` remains compatible presentation metadata but is not authoritative after Feature-04. Feature-04 does not maintain two synchronized pending-decision stores; decision queries are the source of truth.

## Blocking semantics

An open decision may record semantic blocked scopes. Tutor behavior blocks only dependent implementation while allowing unrelated/mechanical work to continue.

The neutral core validates and stores blocked scope labels but does not infer source-code dependency graphs from them.

## Decision record schema

Every persisted decision has required machine/identity fields:

```text
revision
task_id
class
status
title
```

The schema also reserves provenance slots:

```text
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
superseding_decision_id
```

Semantic slots may be `null` or empty when genuinely not recorded, subject to lifecycle validation. For example, `selected_decision` must be present before status can become `selected`, `implementation_result` must be present before `implemented`, and `verification` must be present before `verified`. Missing historical content is never synthesized during rendering or recovery.

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
-> Inspect verified project facts together
-> User proposes product behavior, technology choices, and architecture
-> Examine assumptions and possible problems together
-> User revises with Praxis guidance
-> Repeat review and revision until the affected scope is ready
-> User selects and delegates implementation
-> AI implements the agreed scope
-> Verify consequences
-> Distill
```

Behavior requirements:

- invite the user's approach and wait before offering a project-specific design; use an existing user proposal without asking again;
- distinguish requirements from implementation choices; desired behavior does not imply architecture selection;
- explicitly distinguish product design (user behavior and interaction) from technical design (responsibilities, state/data flow, interfaces, dependencies, technology and operational tradeoffs) within Designing; a product selection does not settle consequential technical choices; topics make the distinction visible without mandatory separate phases;
- examine the user's reasoning and explain concrete problems using evidence or uncertainty, consequences, and suggestions, then return revision to the user;
- repeat review and revision until behavior, responsibilities, relevant technology/architecture choices, constraints, and verification expectations are clear for the affected scope, with material issues resolved or tradeoffs explicitly accepted;
- readiness does not require perfect whole-system design or an AI understanding score; a viable design cannot be vetoed by AI preference;
- implementation requires explicit delegation of the agreed scope, separate from design selection; one reply may provide both and existing delegation must not trigger repeated confirmation;
- return new consequential choices discovered during implementation or later feedback to the user, preserving prior provenance and continuing independent work;
- small code changes may carry consequential product decisions;
- viable user designs are respected and refined, not replaced because the AI prefers another pattern;
- a surfaced choice must contain a distinction worth learning, not merely multiple possible implementations;
- for meaningful alternatives, Praxis explains what each optimizes for, what it costs, why the recommendation fits the verified context, and when another option would be better;
- concrete false assumptions/material risks are surfaced before dependent implementation;
- unresolved risk blocks only affected work;
- mechanical details proceed without repeated confirmation once the surrounding design is settled;
- when the user does not know, Praxis teaches the smallest useful mental model and invites the user to form or revise an approach; it offers examples, options, or recommendations when the user requests help or remains stuck, without deadlocking into repeated questioning or forced paraphrasing;
- verification targets the consequence the selected decision was intended to create when practical; green tests alone are not treated as proof of good design;
- distillation connects alternatives -> reason -> implementation -> observed consequence -> reusable heuristic when evidence supports one;
- Praxis does not claim mastery or understanding scores.

### Node presentation

Substantive Tutor replies use a bold `<ASCII face> <node>` heading, a blank line, and `<topic>: <body>` in normal Markdown. Node names, topics, and bodies follow the current conversation language and explicit user language preference; mixed-language exchanges use their main language. ASCII faces remain fixed. English/Chinese mappings are `(o.o) Understanding / 理解`, `(o-o) Designing / 设计`, `(o_^) Reviewing / 检查`, `(^_~) Revising / 修正`, and `(^_^) Implementing / 实现`. Other languages use equivalent activity names. Localization changes presentation only, not node semantics or durable lifecycle state.

Nodes describe the current activity and may repeat or switch freely. Reviewing includes scoped readiness review; Revising includes requirements revision. Prefer one main node per reply without empty template sections. User proposals, AI suggestions, and selected decisions remain distinct. Headings do not advance durable lifecycle state or provide consent; Implementing requires existing scope delegation and honest execution/verification reporting.

The node-specific teaching, adaptive assistance, and cross-task practice design is recorded in [Tutor Guidance Design](Tutor%20Guidance%20Design.md). Guidance uses the user's demonstrated reasoning in the current topic, explains why viable proposals work, and links expectations to observed outcomes. Earlier decisions inform fresh judgment without choosing or authorizing a new design.

## Recovery contract

Durable task/decision state is sufficient to recover the current decision boundary without full transcript storage.

Recovery may summarize open decisions but cannot:

- auto-select the prior AI recommendation;
- infer approval from restart/compaction;
- invent user reasoning;
- treat selected as implemented;
- treat implemented as verified.

Host-specific lifecycle injection remains Feature-05/06.

## Testing boundary

Feature-04 can prove the neutral state machine, provenance schema, rendering, JSON contracts, and that the shared Skill/reference files encode the required Tutor policy.

Feature-04 cannot prove that a language model inside a real Codex or DSH lifecycle will always follow those instructions. Static Skill/fixture tests must therefore be described as policy/contract tests, not as proof of human understanding or Tutor compliance.

Real host acceptance for recovery, compaction, prompt injection, and observed Tutor behavior belongs to Feature-05/06.

## Acceptance criteria

### AC-001 — provenance remains distinct

User proposal/reasoning, AI challenge/recommendation, verified facts, selected decision, implementation, and verification cannot silently overwrite each other's provenance.

### AC-002 — explicit selection is required

An AI proposal, recovery, silence, or compaction cannot move an open decision to selected.

### AC-003 — lifecycle states remain honest

Selected, implemented, and verified are separate durable states with validated forward-only transitions.

### AC-004 — same-decision conflicts are detected

A stale same-decision writer conflicts; unrelated decisions may proceed after global state revision movement.

### AC-005 — task linkage is durable

Open decisions can be queried by task without transcript parsing, and unknown task ids are rejected.

### AC-006 — only affected implementation is blocked

The encoded Tutor policy allows unrelated/mechanical work to continue while an open decision blocks its declared dependent scopes.

### AC-007 — deterministic decision history recovery

`decisions.md` can be deleted/outdated and rebuilt deterministically from authoritative state.

### AC-008 — adapter-ready JSON

Decision operations expose stable JSON success/error contracts with no Harness-specific dependency in the Python core.

### AC-009 — Tutor policy handles uncertainty

Skill/behavior contract tests cover `I don't know` and require just-enough teaching followed by an invitation to form or revise an approach. Examples, options, and recommendations support requested help or continued uncertainty rather than replacing user reasoning. Real host/model compliance is deferred to Feature-05/06 acceptance.

### AC-010 — implementation becomes feedback

The encoded Tutor policy connects the selected decision to implementation and real verification results, including cases where verification contradicts the original expectation.

### AC-011 — Tutor policy develops taste

Skill/behavior contract tests require comparison of credible alternatives, explicit recommendation boundaries, verification of intended consequences where practical, and evidence-backed distillation into reusable heuristics.

### AC-012 — user leads design before delegation

Skill/behavior contract tests require user-first proposals, evidence-backed challenge, iterative user revision, scoped readiness, and explicit implementation delegation. The same boundary applies to consequential product behavior and small changes. A selected design alone is not delegation, and an AI preference cannot veto a viable user design. These are policy tests, not proof of model compliance.

## Implementation order

1. Decision schema and provenance validation.
2. Decision-level CAS and lifecycle transitions.
3. Task linkage and unresolved-decision queries.
4. Deterministic `decisions.md` projection.
5. Decision JSON CLI.
6. Shared Praxis Skill and behavior references.
7. Tutor policy/scenario contract tests.
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
