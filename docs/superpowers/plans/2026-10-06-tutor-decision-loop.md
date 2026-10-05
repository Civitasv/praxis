# Tutor Decision Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Feature-04 so Praxis can persist consequential engineering decisions with honest provenance, decision-level concurrency, deterministic recovery, and a Harness-neutral Tutor behavior contract.

**Architecture:** Keep `state.json` as the sole machine-readable authority and store an optional `decisions` aggregate beside tasks and `project_model`. Reuse Feature-02 locking/atomic writes via `mutate_latest_state`, use per-decision revision CAS so unrelated decisions can progress concurrently, and render `.praxis/decisions.md` as a deterministic projection that is never parsed back into state. Add a shared English Skill that defines Tutor behavior without Codex/DSH lifecycle APIs.

**Tech Stack:** Python 3.10+ standard library only for the neutral core; unittest; Markdown Skill/reference files; existing GitHub Actions Python 3.10/3.13 + Node 22/pnpm 11 DSH seam validation.

**Spec:** `Docs/Specs/Feature-04 Tutor Decision Loop.md` and `docs/superpowers/specs/2026-10-06-tutor-decision-loop-design.md`

## Global Constraints

- Python neutral core remains standard-library only and must not import Codex, DeepSeek Harness, Cordis, or adapter APIs.
- `state.json` remains format version `1`; Feature-04 adds optional validated `decisions` metadata rather than a format migration.
- `state.json.decisions` is authoritative; `.praxis/decisions.md` is a rebuildable deterministic projection and is never parsed back into state.
- Decision ids, aggregate revision, per-decision revisions, lifecycle status, task-link validation, and projection markers are core-owned machine metadata.
- Mechanical choices are not persisted by default; durable records are for consequential engineering/architectural judgment.
- AI recommendation, user proposal, selected decision, user reasoning, implementation result, verification, and later evidence remain distinct provenance slots.
- Recovery, silence, restart, compaction, or an AI recommendation never advances an open decision to selected.
- Only affected implementation is blocked by an open decision's semantic `blocked_scopes`; the neutral core stores labels but does not infer source dependency graphs.
- `selected`, `implemented`, and `verified` remain separate honest lifecycle states.
- Host lifecycle injection remains Feature-05/06; Feature-04 proves neutral state/CLI behavior and encodes Tutor policy, not real-host model compliance.
- No transcript storage, quizzes, understanding scores, external model calls, backend, telemetry, or vector storage.

## Review Focus

- Persisted state containing malformed/partially-present decision records must fail validation without rewriting the original state; covered in Task 1.
- A stale same-decision writer must conflict even when global state changed for unrelated work, while unrelated decision updates still succeed; covered in Task 2.
- Terminal decisions must not be silently reopened or advanced, and `implemented` must never become `verified` without explicit verification payload; covered in Task 2.
- Unsafe/symlinked `decisions.md` and render failures must preserve authoritative state and existing projection bytes; covered in Task 4.
- Tutor policy must explicitly prevent recovery/AI recommendations from becoming approval and must avoid deadlock when the user says “I don't know”; covered in Tasks 6–7.

---

### Task 1: Decision Schema and Provenance Invariants

**Files:**
- Create: `praxis/decisions.py`
- Modify: `praxis/state.py`
- Test: `tests/test_decisions.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Consumes: `praxis.state.load_state(project_root)`, `praxis.state.mutate_latest_state(project_root, mutator)`.
- Produces: `DecisionError`, `InvalidDecisionError`, `DecisionConflictError`, `UnknownDecisionError`, `InvalidDecisionTransitionError`; `get_decisions(state) -> dict[str, Any]`; `get_decision(state, decision_id) -> dict[str, Any]`; `create_decision(project_root, task_id, decision_class, title, context, *, user_proposal=None, verified_constraints=None, praxis_challenge=None, alternatives=None, blocked_scopes=None) -> tuple[str, dict[str, Any]]`.

- [ ] **Step 1: Write failing schema/provenance tests**

Pin these behaviors in `tests/test_decisions.py` and `tests/test_state.py`:
- first decision creates `decisions={"revision": 0, "records": {...}}` and record revision `0`;
- decision ids are core-generated `decision_<hex>` values;
- unknown `task_id` is rejected without a write;
- `decision_class` accepts only `engineering` or `architectural` for durable creation; `mechanical` is rejected from the durable core API;
- required machine/semantic fields are validated;
- optional scalar provenance fields are `None` when not recorded, not synthesized;
- list fields (`verified_constraints`, `alternatives`, `accepted_tradeoffs`, `blocked_scopes`, `later_evidence`) contain non-empty strings only;
- persisted malformed `decisions` aggregates or records cause `InvalidStateError`/`InvalidDecisionError` and preserve original bytes;
- creation preserves tasks, project model, and unknown top-level metadata.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python -m unittest tests.test_decisions tests.test_state -v`
Expected: FAIL because `praxis.decisions` and decision-state validation do not exist.

- [ ] **Step 3: Implement the minimal schema and creation API**

Add the exact interfaces above in `praxis/decisions.py`. Extend `praxis/state.py` validation so an optional `decisions` aggregate is validated during every state load/write, while absent `decisions` remains valid Feature-02/03 state.

Serialized record fields:

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

New records start `status="open"`, `selected_decision=None`, `user_reasoning=None`, `accepted_tradeoffs=[]`, `implementation_result=None`, `verification=None`, `later_evidence=[]`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `python -m unittest tests.test_decisions tests.test_state -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add praxis/decisions.py praxis/state.py tests/test_decisions.py tests/test_state.py
git commit -m "feat: add durable decision schema"
```

---

### Task 2: Decision-Level CAS and Lifecycle Transitions

**Files:**
- Modify: `praxis/decisions.py`
- Test: `tests/test_decision_lifecycle.py`

**Interfaces:**
- Consumes: Task 1 decision aggregate and `mutate_latest_state`.
- Produces:
  - `select_decision(project_root, decision_id, expected_decision_revision, selected_decision, *, user_reasoning=None, accepted_tradeoffs=None) -> dict[str, Any]`
  - `record_implementation(project_root, decision_id, expected_decision_revision, implementation_result) -> dict[str, Any]`
  - `record_verification(project_root, decision_id, expected_decision_revision, verification) -> dict[str, Any]`
  - `supersede_decision(project_root, decision_id, expected_decision_revision, superseding_decision_id) -> dict[str, Any]`
  - `abandon_decision(project_root, decision_id, expected_decision_revision) -> dict[str, Any]`
  - `add_later_evidence(project_root, decision_id, expected_decision_revision, evidence) -> dict[str, Any]`

- [ ] **Step 1: Write failing lifecycle/CAS tests**

Cover:
- exact lifecycle `open -> selected -> implemented -> verified`;
- `open -> superseded|abandoned`, `selected -> superseded|abandoned`, `implemented -> superseded|abandoned` are allowed; terminal records cannot advance further;
- `verified` is terminal;
- `record_implementation` requires `selected` and non-empty result;
- `record_verification` requires `implemented` and non-empty result;
- selection requires explicit non-empty `selected_decision`; omitted user reasoning remains `None` rather than copying AI rationale;
- selection clears only the lifecycle blocker implied by status; it does not rewrite `praxis_challenge` or `user_proposal`;
- successful mutation increments targeted decision revision and aggregate `decisions.revision` exactly once, while global state revision advances once;
- stale expected decision revision raises `DecisionConflictError` without write;
- two different decisions can update after global revision movement;
- no-op later-evidence duplicate is rejected or treated as a semantic no-op consistently (choose one: reject duplicates in validation and do not write).

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_decision_lifecycle -v`
Expected: FAIL because transition APIs do not exist.

- [ ] **Step 3: Implement explicit transition table and decision CAS**

Use per-record `revision` as the only caller concurrency token. Under `mutate_latest_state`, load the latest aggregate, compare the targeted decision revision, apply one legal transition, increment that decision revision once and aggregate revision once, and rely on state layer for the global revision/write.

- [ ] **Step 4: Run lifecycle + existing state concurrency tests**

Run: `python -m unittest tests.test_decision_lifecycle tests.test_state_latest tests.test_tasks -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add praxis/decisions.py tests/test_decision_lifecycle.py
git commit -m "feat: add decision lifecycle and CAS"
```

---

### Task 3: Task Linkage and Unresolved Decision Queries

**Files:**
- Modify: `praxis/decisions.py`
- Modify: `praxis/tasks.py`
- Test: `tests/test_decision_queries.py`
- Test: `tests/test_tasks.py`

**Interfaces:**
- Consumes: Task 1 record shape; Feature-02 task records.
- Produces:
  - `list_decisions(state, *, task_id: str | None = None) -> dict[str, Any]`
  - `list_open_decisions(state, *, task_id: str | None = None) -> dict[str, Any]`
  - `decision_blocked_scopes(state, *, task_id: str | None = None) -> list[str]`

- [ ] **Step 1: Write failing query/linkage tests**

Cover:
- open decisions can be listed globally and by task without transcript data;
- selected/implemented/verified/superseded/abandoned records do not appear in `list_open_decisions`;
- query results are deep copies and cannot mutate state;
- `decision_blocked_scopes` returns stable deduplicated sorted labels from open decisions only;
- unrelated task decisions never appear in another task's query;
- completing a task does not mutate its decisions implicitly;
- existing `tasks.pending_choices` remains preserved but changing it does not create/resolve a durable decision.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_decision_queries tests.test_tasks -v`
Expected: FAIL on missing query helpers.

- [ ] **Step 3: Implement read-only query helpers**

Do not add a second authority field to task records. Keep `pending_choices` backward-compatible only.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `python -m unittest tests.test_decision_queries tests.test_tasks -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add praxis/decisions.py praxis/tasks.py tests/test_decision_queries.py tests/test_tasks.py
git commit -m "feat: add decision task queries"
```

---

### Task 4: Deterministic `decisions.md` Projection and Recovery

**Files:**
- Modify: `praxis/decisions.py`
- Test: `tests/test_decision_render.py`

**Interfaces:**
- Consumes: `state_directory(project_root, create=...)`, `load_state`, Task 1 aggregate.
- Produces:
  - `render_decisions(project_root: Path) -> Path`
  - `decisions_status(project_root: Path) -> dict[str, Any]`

- [ ] **Step 1: Write failing renderer/recovery tests**

Cover:
- stable decision-id ordering and marker `<!-- praxis:decisions revision="N" -->`;
- per-record marker includes id, revision, status, class, task;
- every provenance heading renders from the corresponding field only;
- missing scalar/list content renders `Not recorded` rather than inferred prose;
- deleting `decisions.md` and re-rendering yields identical bytes;
- unrelated task/project-model/global state changes do not require render when `decisions.revision` is unchanged;
- decision aggregate changes make `render_required=True`;
- `decision-status` equivalent read path does not create `.praxis/` when state/decisions are absent;
- symlink/non-regular projection target raises `DecisionRenderError`;
- `os.replace`/write failure preserves authoritative state and any previous projection bytes.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_decision_render -v`
Expected: FAIL because projection/status APIs do not exist.

- [ ] **Step 3: Implement deterministic atomic renderer**

Mirror Feature-03's temp-file -> flush/fsync -> `os.replace` -> directory fsync pattern. Projection sync is keyed only to `decisions.revision`.

- [ ] **Step 4: Run renderer + Feature-03 renderer regression**

Run: `python -m unittest tests.test_decision_render tests.test_project_map_render -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add praxis/decisions.py tests/test_decision_render.py
git commit -m "feat: render decision trail"
```

---

### Task 5: Adapter-Ready Decision JSON CLI

**Files:**
- Modify: `praxis/cli.py`
- Test: `tests/test_decision_cli.py`

**Interfaces:**
- Consumes: Tasks 1–4 neutral decision functions.
- Produces commands:
  - `decision-status --cwd PATH [--task-id TASK]`
  - `decision-create --cwd PATH --task-id TASK --class engineering|architectural --title TITLE --context CONTEXT [provenance/list flags]`
  - `decision-select --cwd PATH --decision-id ID --expected-decision-revision N --selected-decision TEXT [--user-reasoning TEXT] [--accepted-tradeoff ...]`
  - `decision-implemented --cwd PATH --decision-id ID --expected-decision-revision N --result TEXT`
  - `decision-verify --cwd PATH --decision-id ID --expected-decision-revision N --result TEXT`
  - `decision-supersede --cwd PATH --decision-id ID --expected-decision-revision N --superseding-decision-id ID`
  - `decision-abandon --cwd PATH --decision-id ID --expected-decision-revision N`
  - `decision-evidence --cwd PATH --decision-id ID --expected-decision-revision N --evidence TEXT`
  - `decision-render --cwd PATH`

Stable error mappings:
`unknown_task`, `unknown_decision`, `decision_conflict`, `invalid_decision`, `invalid_transition`, `decision_render_failed`.

- [ ] **Step 1: Write failing CLI contract tests**

Cover one success round-trip through create -> select -> implemented -> verify, stable JSON for every decision-specific error class, read-only status with no state, and projection repair.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_decision_cli -v`
Expected: FAIL because decision subcommands/error mappings are absent.

- [ ] **Step 3: Add parser wiring, `_error_code` mappings, and `_run_command` branches**

Keep stdout to one sorted JSON object and preserve existing CLI behavior.

- [ ] **Step 4: Run CLI regression suite**

Run: `python -m unittest tests.test_decision_cli tests.test_cli tests.test_project_map_cli -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add praxis/cli.py tests/test_decision_cli.py
git commit -m "feat: expose decision JSON CLI"
```

---

### Task 6: Shared Praxis Skill and Tutor Policy References

**Files:**
- Create: `skills/praxis/SKILL.md`
- Create: `skills/praxis/references/tutor-behavior.md`
- Create: `skills/praxis/references/decision-policy.md`
- Create: `skills/praxis/references/repository-understanding.md`
- Create: `skills/praxis/references/recovery.md`
- Create: `skills/praxis/references/state-format.md`
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: neutral CLI semantics from Task 5 and verified project-model semantics from Feature-03.
- Produces: Harness-neutral behavioral instructions for future Codex/DSH adapters.

- [ ] **Step 1: Write failing Skill contract tests**

Assert the Skill/reference files exist and encode these exact behavioral invariants:
- installation does not enable a project;
- start from verified project facts and explicitly respect stale/unknown facts;
- distinguish mechanical vs engineering/architectural decisions;
- viable user proposal is respected/refined;
- material false assumption is challenged before dependent implementation;
- AI recommendation is not approval;
- open decision blocks only declared affected scope;
- “I don't know” triggers just-enough explanation + a concrete meaningful tradeoff, not repeated Socratic questioning;
- recovery never approves/implements/verifies a decision;
- reflection connects decision -> implementation -> verification evidence and permits contradictory results;
- no mastery/understanding score;
- no Codex/DSH/Cordis API names in the shared Skill package.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_skill_contract -v`
Expected: FAIL because the shared Skill package is absent.

- [ ] **Step 3: Author compact progressive-loading Skill and references**

Keep `SKILL.md` short: activation/status, Tutor loop, when to load each reference, and neutral CLI intent. Put detailed policy in references.

- [ ] **Step 4: Run contract + harness-import boundary regression**

Run: `python -m unittest tests.test_skill_contract tests.test_cli -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/praxis tests/test_skill_contract.py
git commit -m "feat: add shared Praxis Tutor skill"
```

---

### Task 7: Tutor Scenario and Recovery Behavior Contracts

**Files:**
- Create: `tests/test_tutor_scenarios.py`
- Modify: `skills/praxis/references/tutor-behavior.md`
- Modify: `skills/praxis/references/decision-policy.md`
- Modify: `skills/praxis/references/recovery.md`

**Interfaces:**
- Consumes: Skill/reference text from Task 6 and lifecycle vocabulary from Tasks 1–5.
- Produces: executable repository contracts proving that the policy text contains explicit instructions for high-risk scenarios. This task does not claim end-to-end model compliance in a real host.

- [ ] **Step 1: Add scenario-policy tests for the acceptance cases**

Tests must pin explicit policy for:
- viable user design: keep it unless a verified/material issue exists;
- risky false assumption: explain fact + impact + options, keep dependent scope blocked;
- AI proposal cannot self-select;
- recovery/compaction cannot select an open decision;
- selected is not implemented; implemented is not verified;
- AI rationale cannot be attributed to user reasoning;
- mechanical details proceed without durable decision by default;
- `I don't know`: explain minimum context, give a default when useful, ask one meaningful tradeoff;
- verification may contradict the selected decision's expectation and must be recorded honestly;
- reflection summarizes observed consequence, not a generic lesson or mastery claim.

- [ ] **Step 2: Run scenario tests and verify any missing policy is RED**

Run: `python -m unittest tests.test_tutor_scenarios -v`
Expected: any missing explicit instruction fails with the missing invariant.

- [ ] **Step 3: Tighten references only where tests expose an ambiguity**

Do not add host lifecycle instructions or transcript parsing.

- [ ] **Step 4: Run full Skill/scenario contracts**

Run: `python -m unittest tests.test_skill_contract tests.test_tutor_scenarios -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/praxis/references tests/test_tutor_scenarios.py
git commit -m "test: lock Tutor behavior scenarios"
```

---

### Task 8: Repository Closure and Final Validation

**Files:**
- Modify: `Code.md`
- Modify: `State.md`
- Modify: `README.md`
- Modify: `tests/test_repository_contract.py`

**Interfaces:**
- Consumes: completed Feature-04 runtime/Skill behavior.
- Produces: durable engineering context that reports only capabilities actually implemented and keeps Feature-05/06 pending.

- [ ] **Step 1: Update repository closure tests first**

Require:
- `Code.md` maps `praxis/decisions.py` and `skills/praxis/` to Feature-04;
- `State.md` says `Feature-04: Implemented` and names decision provenance, lifecycle/CAS, deterministic `decisions.md`, JSON CLI, and shared Tutor Skill;
- `State.md` keeps Feature-05/06 pending and explicitly says real host lifecycle/compliance is not implemented;
- README describes the decision loop without claiming Codex/DSH automatic recovery yet.

- [ ] **Step 2: Run repository contract tests and verify RED**

Run: `python -m unittest tests.test_repository_contract -v`
Expected: FAIL only on Feature-04 closure documentation.

- [ ] **Step 3: Update `Code.md`, `State.md`, and README to match verified implementation**

Do not claim real-host Tutor compliance, Codex hooks, or DSH lifecycle integration.

- [ ] **Step 4: Run the full Python suite and syntax validation**

Run:

```bash
python -m unittest discover -s tests -v
python -m compileall -q praxis tests
```

Expected: PASS with zero failures.

- [ ] **Step 5: Run existing TypeScript/DSH seam validation**

Run:

```bash
pnpm typecheck
pnpm test:dsh
```

Expected: PASS where pnpm is available; GitHub Actions remains authoritative for the declared Node/pnpm environment.

- [ ] **Step 6: Open/update the Feature-04 PR and require final GitHub Actions Green**

Final CI evidence must include Python 3.10, Python 3.13, TypeScript typecheck, and DSH seam tests on the final head. Do not mark Ready for review before those jobs pass.

- [ ] **Step 7: Whole-branch self-review**

Review provenance boundaries, terminal transitions, same-decision CAS, projection recovery, JSON error mapping, and Tutor policy scope. Any Critical/Important finding gets a failing regression test before the fix.

- [ ] **Step 8: Commit closure**

```bash
git add Code.md State.md README.md tests/test_repository_contract.py
git commit -m "docs: close Feature-04 Tutor decision loop"
```

## Self-Review Result

- **Spec coverage:** All Feature-04 spec areas map to Tasks 1–8. Codex/DSH lifecycle integration remains explicitly out of scope.
- **Step scan:** Every task has one TDD cycle, exact files/interfaces, focused verification, and a commit boundary. No implementation body is prewritten beyond serialized field names and required command/interface signatures.
- **Type consistency:** Decision mutations consistently take `expected_decision_revision`; aggregate reads use state dictionaries; projection/status use project roots; CLI maps exactly to the core APIs.
- **Review Focus:** Malformed persisted state, same-decision concurrency, terminal lifecycle honesty, projection safety, and Tutor recovery/uncertainty behavior each have owning tests.
- **Proportion:** The plan fixes interfaces and evidence without duplicating the implementation algorithm already established by Features 02–03.
