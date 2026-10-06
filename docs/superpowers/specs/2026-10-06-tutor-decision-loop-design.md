# Praxis Tutor Decision Loop Design

Date: 2026-10-06
Status: Proposed for Feature-04 implementation

## 1. Intent

Feature-04 is the point where Praxis becomes a Tutor rather than only a reliable project-state system.

The product goal is not to force users to write code or to turn every implementation detail into a question. Praxis should let AI carry execution while keeping the human inside consequential engineering judgment: identifying an important choice, understanding the relevant constraints, challenging risky assumptions, selecting a trade-off, observing implementation consequences, and reflecting on the result.

The desired loop is:

```text
Understand
  -> inspect verified project facts
  -> surface a consequential decision
  -> discuss / explain / challenge
  -> user selects or explicitly accepts a trade-off
  -> AI implements
  -> verify real behavior
  -> connect result back to the decision
```

## 2. Scope

Feature-04 owns:

- durable decision state and provenance;
- decision-level revisions and compare-and-swap;
- decision lifecycle transitions;
- task-to-decision linkage and unresolved-decision queries;
- deterministic `.praxis/decisions.md` projection;
- adapter-ready JSON CLI commands for decision state;
- the shared Praxis Skill and Tutor behavior references;
- behavior contracts for consequential decision handling, recovery, challenge, implementation, verification, and reflection.

Feature-04 does not implement Codex lifecycle hooks, DSH/Cordis lifecycle integration, transcript parsing, external model calls, quizzes, understanding scores, or automatic inference that the user approved a choice.

## 3. Authority model

Feature-04 follows the same authority pattern established by Feature-03.

```text
.praxis/state.json
  `- decisions (authoritative machine state)
          |
          v
.praxis/decisions.md (deterministic projection)
```

`decisions.md` is never parsed back into machine state. It may be deleted and rebuilt. Machine-owned metadata such as ids, revisions, lifecycle status, task linkage, and projection markers is generated and validated by the Python core.

This avoids creating a second persistence/locking/version subsystem and keeps all durable Praxis state under the existing Feature-02 write lock and atomic state writer.

## 4. Decision classes

Praxis distinguishes:

- `mechanical`: imports, local naming, formatting, ordinary helpers, routine lint/test organization;
- `engineering`: data ownership, state boundaries, concurrency, failure behavior, module boundaries, storage semantics;
- `architectural`: permissions, data lifecycle, public contracts, major dependencies, core technology direction, product-level system boundaries.

Mechanical choices are not durable decisions by default. Engineering and architectural choices are eligible for durable decision records when they are consequential to the current task.

A practical criterion is:

> If repeatedly experiencing this judgment would materially improve how the user handles similar future problems, it is worth surfacing.

## 5. Decision record

Authoritative records live under optional top-level `decisions` state:

```json
{
  "decisions": {
    "revision": 7,
    "records": {
      "decision_ab12": {
        "revision": 2,
        "task_id": "task_deadbeef",
        "class": "architectural",
        "status": "selected",
        "title": "Message persistence",
        "context": "Messages must survive realtime infrastructure restarts.",
        "user_proposal": "Store messages only in Redis.",
        "verified_constraints": [
          "Message history must survive Redis restart."
        ],
        "praxis_challenge": "Redis-only storage couples durable product data to Redis durability configuration.",
        "alternatives": [
          "Database as source of truth, Redis for fanout",
          "Redis-only persistence with explicit durability assumptions"
        ],
        "selected_decision": "Database is source of truth; Redis handles realtime fanout.",
        "user_reasoning": "History cannot be lost if Redis is restarted.",
        "accepted_tradeoffs": [
          "Additional database dependency"
        ],
        "blocked_scopes": [
          "message-persistence-implementation"
        ],
        "implementation_result": null,
        "verification": null,
        "later_evidence": []
      }
    }
  }
}
```

The exact serialized fields may be refined during implementation, but the provenance boundaries below are invariant.

## 6. Provenance invariants

Praxis must distinguish:

- verified repository constraint;
- user proposal;
- Praxis challenge / recommendation;
- selected decision;
- user reasoning;
- accepted trade-off;
- implementation result;
- verification result;
- later evidence / inference.

The core and Skill must never silently convert one source into another.

In particular:

- AI-generated rationale is never stored as `user_reasoning` unless the user actually adopts that rationale;
- an AI recommendation is not a selected decision;
- silence, restart, compaction, task recovery, or a later unrelated request is not approval;
- implemented code is not verification;
- a verification result may contradict the original expectation and must be recorded honestly.

## 7. Lifecycle

Decision status is intentionally small:

```text
open
  -> selected
  -> implemented
  -> verified
```

Terminal alternatives:

```text
superseded
abandoned
```

Semantics:

- `open`: a consequential choice is unresolved;
- `selected`: the user has selected an approach or explicitly accepted the risk/trade-off;
- `implemented`: affected implementation has been completed according to the selected decision;
- `verified`: relevant verification evidence/results have been recorded;
- `superseded`: a later decision replaced this record;
- `abandoned`: the task no longer requires the decision.

Allowed transitions are explicit. Recovery never advances a status. `implemented` never implies `verified`.

A stale writer updating the same decision conflicts. Updates to unrelated decisions may proceed after global state revision movement by using decision-level revision checks under the shared project write lock.

## 8. Decisions revision

The top-level `decisions.revision` is independent from global `state.revision` and individual decision revisions.

It advances exactly once for a semantic decision-state change, such as:

- creating a decision;
- lifecycle transition;
- adding implementation/verification data;
- superseding or abandoning a decision;
- adding later evidence.

A no-op operation does not advance decision or global state revisions.

## 9. Task linkage

Every durable decision belongs to an existing task.

```text
task_auth
  |- decision_session-storage
  `- decision_token-transport
```

The neutral core provides unresolved-decision queries by task. `status == open` is authoritative for unresolved decisions.

Feature-02 `pending_choices` remains compatible state but is no longer the source of truth for unresolved Tutor decisions. Host adapters may use it as presentation metadata during migration, but Feature-04 decision records determine whether a consequential choice is actually pending.

## 10. Blocking semantics

Praxis does not freeze the entire task whenever a decision is open.

A decision may declare one or more semantic `blocked_scopes`. While the decision is open, only implementation that depends on those scopes is considered blocked by Tutor policy.

Unrelated mechanical work may continue.

Example:

```text
Open decision:
  durable message storage boundary

Blocked:
  message persistence implementation

Still allowed:
  unrelated tests
  API typing unrelated to storage choice
  lint / formatting
  independent UI copy
```

The neutral core stores the relationship; the shared Skill applies the behavioral rule. Feature-04 does not attempt to automatically infer source-code ranges from a free-form blocked scope.

## 11. Core interfaces

Feature-04 introduces `praxis/decisions.py` with neutral operations conceptually equivalent to:

```text
create_decision(...)
get_decision(...)
list_decisions(...)
list_open_decisions(task_id=...)
select_decision(...)
record_implementation(...)
record_verification(...)
supersede_decision(...)
abandon_decision(...)
add_later_evidence(...)
decisions_status(...)
render_decisions(...)
```

Decision ids and revisions are core-owned. Mutations use the existing Feature-02 lock/atomic writer and latest-state pattern, with decision-level CAS for the targeted record.

The module must preserve unknown top-level state fields, Feature-02 tasks, and Feature-03 project-model state.

## 12. Deterministic `decisions.md`

The projection has a machine marker tied to `decisions.revision` and renders records in stable id order.

Illustrative output:

```markdown
# Praxis Decision Trail

<!-- praxis:decisions revision="7" -->

## Message persistence
<!-- praxis:decision id="decision_ab12" revision="2" status="selected" class="architectural" task="task_deadbeef" -->

### Context
...

### User proposal
...

### Verified constraints
- ...

### Praxis challenge
...

### Selected decision
...

### User reasoning
...

### Accepted tradeoffs
- ...

### Implementation result
Not recorded

### Verification
Not recorded
```

Missing fields are rendered explicitly as `Not recorded` rather than inferred.

Projection writes are atomic. Unsafe/symlinked `decisions.md` paths are rejected. A missing or out-of-sync projection is detectable and rebuildable from state.

## 13. Shared Tutor Skill

Feature-04 creates the shared English Skill:

```text
skills/praxis/
|- SKILL.md
`- references/
   |- tutor-behavior.md
   |- decision-policy.md
   |- repository-understanding.md
   |- recovery.md
   `- state-format.md
```

`SKILL.md` stays short and loads references progressively.

The Skill assumes neutral core/CLI availability but contains no Codex- or DSH-specific APIs.

## 14. Tutor behavior

For a meaningful task, Tutor behavior is dynamic rather than a fixed questionnaire:

```text
Understand
  -> Inspect
  -> Surface consequential decision
  -> Discuss / teach / challenge
  -> Agree
  -> Implement
  -> Verify
  -> Reflect
```

Praxis should not interrupt for mechanical decisions already covered by an agreed design.

When the user has a viable proposal, Praxis respects it and helps expose relevant trade-offs instead of replacing it because the model prefers another pattern.

When the user proposal contains a concrete false assumption or material risk, Praxis immediately explains the issue, impact, and realistic alternatives. Only dependent implementation waits for resolution.

When the user says they do not know, Praxis explains the minimum background necessary to make the next meaningful trade-off, may recommend a concrete default, and then gives the user a real decision they can understand. It must not deadlock into repeated Socratic questioning.

## 15. Reflection behavior

After implementation and verification, Praxis reconnects outcome to judgment rather than delivering a generic lesson summary.

The useful form is:

```text
initial assumption / decision
  -> implementation boundary
  -> observed verification result
  -> consequence of the accepted trade-off
```

The goal is to turn implementation into feedback. Praxis does not claim that one successful discussion means the user mastered the concept.

## 16. Recovery behavior

Recovery reads durable task and decision state.

For an open decision, recovery may summarize what remains unresolved, but must not:

- auto-select the prior Praxis recommendation;
- infer approval from previous implementation intent;
- infer approval from session restart or compaction;
- manufacture missing user reasoning.

If multiple tasks or decisions are plausible, the later host integration asks the user which work to continue rather than silently hijacking another task.

Feature-04 specifies this behavior in the shared Skill; actual host lifecycle injection is Feature-05/06.

## 17. CLI contract

The neutral CLI adds adapter-facing operations equivalent to:

```text
praxis decision-status
praxis decision-create
praxis decision-select
praxis decision-implemented
praxis decision-verify
praxis decision-supersede
praxis decision-abandon
praxis decision-render
```

Additional query or later-evidence commands may be added if they make adapter behavior simpler without expanding scope.

All commands emit one JSON object to stdout. Stable error codes include:

- `unknown_task`;
- `unknown_decision`;
- `decision_conflict`;
- `invalid_decision`;
- `invalid_transition`;
- `decision_render_failed`.

Host adapters translate lifecycle/events and do not duplicate decision semantics.

## 18. Behavior acceptance scenarios

Feature-04 must cover at least:

1. A viable user design is preserved and refined instead of replaced.
2. A risky/false assumption remains open and blocks only dependent implementation.
3. An AI proposal cannot become `selected` without explicit user selection/risk acceptance.
4. Recovery cannot turn `open` into `selected`.
5. `implemented` remains distinct from `verified`.
6. AI rationale cannot be attributed to the user.
7. Two unrelated decisions can update despite global revision movement.
8. Two stale writers to the same decision conflict.
9. Mechanical choices do not require durable decision records by default.
10. `I don't know` results in just-enough teaching and a meaningful trade-off rather than a deadlock.
11. Verification may record a result that contradicts the expected outcome.
12. `decisions.md` can be deleted and rebuilt to identical bytes from authoritative state.

## 19. Implementation sequence

Feature-04 implementation should proceed in this order:

1. Decision schema and provenance invariants.
2. Decision-level CAS and lifecycle transitions.
3. Task linkage and unresolved-decision queries.
4. Deterministic `decisions.md` projection and recovery.
5. Decision JSON CLI.
6. Shared Praxis Skill and behavior references.
7. Tutor scenario/behavior contract tests.
8. `Code.md`, `State.md`, README closure and final CI.

## 20. Non-goals

Feature-04 does not include:

- Codex hooks or plugin lifecycle;
- DSH/Cordis plugin lifecycle;
- automatic transcript parsing;
- automatic semantic extraction of a user's approval;
- code-range dependency inference from blocked scopes;
- quizzes, learning scores, or mastery claims;
- backend services, external model calls, vector databases, or telemetry;
- changes to Feature-03 authority: project facts remain in `project_model`, not decisions.

## 21. Selected approach

The selected architecture is **decisions-in-state + deterministic Markdown projection**.

Rejected alternatives:

- `decisions.md` as authority: simpler initially but weak for provenance validation, concurrency, lifecycle constraints, and recovery.
- separate `decisions.json`: cleaner physical separation but duplicates locking, atomic writes, corruption handling, and version coordination already solved by `state.json`.

The selected approach maximizes consistency with Features 02–03 and keeps host adapters disposable.