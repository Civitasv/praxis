# Codex Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Feature-05 so Codex can inject bounded Praxis recovery/synchronization context across supported lifecycle events while preserving neutral-core authority, explicit activation, honest decision/task recovery, and manual fallback.

**Architecture:** Keep all durable semantics in the existing neutral Python core and shared Skill. Add a root portable Codex plugin package plus a thin stdin/stdout Python hook adapter under `plugins/codex/`; the adapter reads host lifecycle metadata, reuses neutral state/project-map/decision functions, and emits bounded `hookSpecificOutput.additionalContext` without transcript or prompt semantic parsing.

**Tech Stack:** Python 3.10+ standard library; JSON plugin/hook manifests; unittest; GitHub Actions; existing pnpm/TypeScript DSH seam remains unchanged.

**Spec:** `Docs/Specs/Feature-05 Codex Integration.md` and `docs/superpowers/specs/2026-10-06-codex-integration-design.md`

## Global Constraints

- `praxis/` remains Codex-independent and standard-library only.
- `state.json` remains format version 1 and the sole machine-readable authority.
- Existing `skills/praxis/` is referenced in place; no Codex-local Skill copy.
- Installation does not initialize or enable a project.
- Uninitialized hooks are silent and filesystem-read-only.
- Paused state remains paused and is never auto-resumed.
- Recovery, restart, compact, clear, prompt submission, or prior AI recommendation never imply approval.
- Hook code never reads `transcript_path` and never interprets prompt text as approval.
- SessionStart sources are exactly `startup|resume|clear|compact`.
- Automatic injected context is deterministic and <= 3000 characters.
- Hook commands are static apart from `${PLUGIN_ROOT}`; event/user data enters through stdin JSON only.
- Automatic hook failure degrades to truthful manual-Skill fallback; never reset/delete/enable state.
- Feature-05 does not create/adopt/rebind tasks automatically.
- Feature-06 DSH/Cordis lifecycle integration remains out of scope.

## Review Focus

- Malformed/non-object hook JSON or missing/invalid `cwd` must fail safely without mutating project state; covered in Task 3.
- Multiple Codex tasks with the same session identity must not be silently resolved as one exact task; covered in Task 4.
- Refreshing stale project evidence may legitimately mutate freshness metadata, but recovery must not mutate task/decision lifecycle; covered in Task 4.
- Extremely large task/decision/project-model state must produce deterministic <=3000-character context without cutting JSON output validity; covered in Task 6.
- Manifest/hook paths containing stale or duplicated Skill/core surfaces must fail repository validation before distribution; covered in Tasks 1–2 and 7.

---

### Task 1: Portable Codex Plugin Manifest Contract

**Files:**
- Create: `plugin.json`
- Create: `.codex-plugin/plugin.json`
- Create: `tests/test_codex_plugin_manifest.py`

**Interfaces:**
- Consumes: existing `skills/praxis/SKILL.md`, planned `plugins/codex/hooks/hooks.json`.
- Produces: canonical root portable plugin manifest and compatibility fallback manifest referencing the same Skill/hook package.

- [ ] **Step 1: Write failing manifest tests**

Assert:
- both manifest files exist and parse as JSON;
- canonical package identity is Praxis;
- canonical `extensions.com.openai` references the shared `skills/praxis` and `plugins/codex/hooks/hooks.json`;
- compatibility manifest references the same repository surfaces;
- no manifest points to a copied Skill/core under `plugins/codex/`;
- every declared repository-relative path exists once Task 2 is complete.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_codex_plugin_manifest -v`
Expected: FAIL because manifests do not exist.

- [ ] **Step 3: Add the minimum canonical and compatibility manifests**

Use repository-relative paths only. Do not add user configuration, marketplace metadata, or host trust bypass.

- [ ] **Step 4: Run manifest tests**

Run: `python -m unittest tests.test_codex_plugin_manifest -v`
Expected: PASS for manifest shape; hook-path existence assertion may remain deferred until Task 2 only if the test explicitly distinguishes that dependency.

- [ ] **Step 5: Commit**

```bash
git add plugin.json .codex-plugin/plugin.json tests/test_codex_plugin_manifest.py
git commit -m "feat: add Codex plugin manifests"
```

---

### Task 2: Codex Hook Declaration Contract

**Files:**
- Create: `plugins/codex/hooks/hooks.json`
- Modify: `tests/test_codex_plugin_manifest.py`
- Create: `tests/test_codex_hooks_manifest.py`

**Interfaces:**
- Consumes: Task 1 package paths.
- Produces: hook declaration for `SessionStart` and `UserPromptSubmit`, both invoking `${PLUGIN_ROOT}/plugins/codex/hooks/praxis_context.py`.

- [ ] **Step 1: Write failing hook declaration tests**

Assert:
- only `SessionStart` and `UserPromptSubmit` are declared;
- SessionStart matcher covers exactly `startup|resume|clear|compact`;
- UserPromptSubmit has no prompt-content matcher;
- command is static apart from `${PLUGIN_ROOT}` and contains no template for cwd/session/prompt/transcript data;
- a Windows command override is present if required by the manifest schema selected in the spec;
- `additionalContextLimit` is a positive bounded value;
- referenced adapter path exists once Task 3 lands.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_codex_hooks_manifest -v`
Expected: FAIL because hook declaration is absent.

- [ ] **Step 3: Add `hooks.json` with the exact lifecycle contract**

Keep host command construction static and feed all lifecycle data over stdin.

- [ ] **Step 4: Run package/hook tests**

Run: `python -m unittest tests.test_codex_plugin_manifest tests.test_codex_hooks_manifest -v`
Expected: PASS except adapter-existence checks explicitly staged for Task 3.

- [ ] **Step 5: Commit**

```bash
git add plugins/codex/hooks/hooks.json tests/test_codex_plugin_manifest.py tests/test_codex_hooks_manifest.py
git commit -m "feat: declare Codex lifecycle hooks"
```

---

### Task 3: Hook Adapter I/O and Activation Semantics

**Files:**
- Create: `plugins/codex/hooks/praxis_context.py`
- Create: `tests/test_codex_context.py`

**Interfaces:**
- Consumes: `praxis.project.discover_project_root`, `praxis.state.load_state`.
- Produces:
  - `MAX_CONTEXT_CHARS = 3000`
  - `build_context(event: dict[str, Any]) -> str | None`
  - `build_response(event_name: str, context: str) -> dict[str, Any]`
  - `main() -> int`

- [ ] **Step 1: Write failing stdin/stdout and activation tests**

Cover:
- invalid JSON/non-object payload returns nonzero or safe empty/fallback output without filesystem mutation;
- missing/empty/invalid cwd is handled safely;
- uninitialized project returns no additional context and does not create `.praxis/`;
- paused project returns a concise paused context and does not change state bytes;
- response shape uses `hookSpecificOutput.hookEventName` and `additionalContext`;
- `transcript_path` and `prompt` values do not appear in generated context and are not opened/read;
- unsupported hook event name is rejected/ignored without state mutation.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_codex_context -v`
Expected: FAIL because the adapter module is absent.

- [ ] **Step 3: Implement minimal adapter parsing, activation checks, response serialization**

Do not perform enabled-project task/decision recovery yet beyond a basic enabled notice; that belongs to Tasks 4–5.

- [ ] **Step 4: Run adapter + package tests**

Run: `python -m unittest tests.test_codex_context tests.test_codex_plugin_manifest tests.test_codex_hooks_manifest -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/codex/hooks/praxis_context.py tests/test_codex_context.py tests/test_codex_plugin_manifest.py tests/test_codex_hooks_manifest.py
git commit -m "feat: add Codex hook adapter"
```

---

### Task 4: Enabled-Project Freshness and Exact Session Recovery

**Files:**
- Modify: `plugins/codex/hooks/praxis_context.py`
- Modify: `tests/test_codex_context.py`
- Create: `tests/test_codex_recovery.py`

**Interfaces:**
- Consumes: `praxis.project_map.refresh_staleness(project_root)`, `project_model_status(project_root)`, Feature-02 task records.
- Produces: deterministic exact-session recovery summary without task/decision lifecycle mutation.

- [ ] **Step 1: Write failing freshness/exact recovery tests**

Cover:
- enabled startup/resume/clear/compact each produce context;
- UserPromptSubmit produces synchronization context independent of prompt wording;
- changed source evidence becomes stale before context is rendered;
- already-stale section never auto-clears;
- exact task requires `host=="codex"`, matching `conversation_id==session_id`, and non-complete status;
- zero exact matches does not create/rebind a task;
- multiple exact matches are treated as ambiguous rather than choosing one;
- state diff after recovery contains only legitimate freshness metadata changes, never task/decision lifecycle changes.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_codex_recovery -v`
Expected: FAIL on missing freshness/exact recovery behavior.

- [ ] **Step 3: Implement freshness refresh and exact-task selection**

Reuse neutral functions directly; do not duplicate fingerprint/stale logic.

- [ ] **Step 4: Run recovery + Feature-03 regressions**

Run: `python -m unittest tests.test_codex_recovery tests.test_project_map tests.test_project_map_render -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/codex/hooks/praxis_context.py tests/test_codex_context.py tests/test_codex_recovery.py
git commit -m "feat: recover Codex project context"
```

---

### Task 5: Candidate Tasks, Decisions, and Blocked Scope Summaries

**Files:**
- Modify: `plugins/codex/hooks/praxis_context.py`
- Modify: `tests/test_codex_recovery.py`

**Interfaces:**
- Consumes: `praxis.tasks.pending_tasks(state)`, `praxis.decisions.list_open_decisions(state, task_id=...)`, `decision_blocked_scopes(state, task_id=...)`.
- Produces: exact/candidate/ambiguous task summaries plus honest open-decision and blocked-scope context.

- [ ] **Step 1: Write failing recovery-selection tests**

Cover:
- one unmatched pending task is labeled candidate and not rebound;
- several pending tasks are sorted/bounded candidates and instruct user choice;
- decisions for unrelated tasks do not appear;
- open decisions are summarized as unresolved;
- selected/implemented/verified records are never mislabeled open;
- selected is never described as implemented; implemented is never described as verified;
- blocked scopes come only from open decisions;
- missing user reasoning is not invented.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_codex_recovery -v`
Expected: FAIL on missing candidate/decision summaries.

- [ ] **Step 3: Implement read-only candidate and decision summarization**

Do not mutate task association or decision lifecycle.

- [ ] **Step 4: Run recovery + decision regressions**

Run: `python -m unittest tests.test_codex_recovery tests.test_decision_queries tests.test_decision_lifecycle -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/codex/hooks/praxis_context.py tests/test_codex_recovery.py
git commit -m "feat: summarize Codex Tutor recovery"
```

---

### Task 6: Deterministic Context Bound and Truthful Failure Fallback

**Files:**
- Modify: `plugins/codex/hooks/praxis_context.py`
- Modify: `tests/test_codex_context.py`
- Modify: `tests/test_codex_recovery.py`

**Interfaces:**
- Consumes: Task 5 summary model.
- Produces: deterministic truncation to `MAX_CONTEXT_CHARS=3000` and safe fallback context for recoverable Praxis failures.

- [ ] **Step 1: Write failing bound/fallback tests**

Cover:
- huge task/decision/section sets remain <=3000 characters;
- repeated runs with identical state yield byte-identical context;
- truncation preserves core activation/recovery-is-not-approval/manual-Skill guidance;
- corrupt JSON state, unsupported version, read failure, lock timeout, or project refresh error never fabricates recovered facts;
- fallback names automatic recovery as unavailable and points to manual Praxis Skill;
- failures do not delete/reset/enable project state;
- output remains valid hook JSON even when context is truncated.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_codex_context tests.test_codex_recovery -v`
Expected: FAIL on bound/fallback behavior.

- [ ] **Step 3: Implement deterministic prioritized rendering and fallback**

Priority order: activation/fallback invariant -> exact/candidate task -> open decisions/blocked scopes -> stale/unknown sections -> recovery/manual-Skill reminder. Truncate lower-priority repeated entries before final hard clipping.

- [ ] **Step 4: Run adapter/recovery full suite**

Run: `python -m unittest tests.test_codex_context tests.test_codex_recovery -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/codex/hooks/praxis_context.py tests/test_codex_context.py tests/test_codex_recovery.py
git commit -m "feat: bound Codex recovery context"
```

---

### Task 7: Codex Distribution and CI Validation

**Files:**
- Create: `tests/test_codex_distribution.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `Docs/Development/Validation.md`

**Interfaces:**
- Consumes: Tasks 1–6 package.
- Produces: repository validation proving package consistency without a live Codex account.

- [ ] **Step 1: Write failing distribution/boundary tests**

Assert:
- all manifest-referenced files exist;
- no duplicate `plugins/codex/skills` or `plugins/codex/praxis` source tree exists;
- hook source contains no transcript-file reads and no prompt semantic matching;
- no files under `praxis/` import/reference Codex hook/plugin modules;
- adapter compiles under the Python baseline;
- canonical/compatibility manifests stay consistent on package identity/surfaces.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_codex_distribution -v`
Expected: FAIL on missing CI/documented validation contract before closure.

- [ ] **Step 3: Add a dedicated Codex package CI job**

Use Python 3.10 and run targeted Codex manifest/distribution/adapter/recovery tests plus `python -m compileall -q plugins/codex praxis`. Do not require live Codex tooling unless actually available.

- [ ] **Step 4: Run local repository tests available in the environment**

Run:
```bash
python -m unittest tests.test_codex_plugin_manifest tests.test_codex_hooks_manifest tests.test_codex_context tests.test_codex_recovery tests.test_codex_distribution -v
python -m compileall -q plugins/codex praxis tests
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_codex_distribution.py .github/workflows/ci.yml Docs/Development/Validation.md
git commit -m "ci: validate Codex plugin package"
```

---

### Task 8: Repository Closure, Whole-Branch Review, and Final Merge Gate

**Files:**
- Modify: `Code.md`
- Modify: `State.md`
- Modify: `README.md`
- Modify: `Docs/Architecture/Harness Integration.md`
- Modify: `tests/test_repository_contract.py`

**Interfaces:**
- Consumes: complete Feature-05 implementation.
- Produces: durable repository truth marking Feature-05 implemented while keeping Feature-06 pending.

- [ ] **Step 1: Update repository closure tests first**

Require:
- `Code.md` maps root/compatibility manifests and `plugins/codex/hooks/` to Feature-05;
- `State.md` marks Feature-05 Implemented and names activation, SessionStart/UserPromptSubmit recovery, freshness sync, bounded context, and fallback;
- `State.md` keeps Feature-06 pending;
- README documents installation != enable, trusted hooks vs manual Skill fallback, and does not claim marketplace/live-host validation that was not run;
- Harness architecture states Codex adapter is translation-only and transcript-independent.

- [ ] **Step 2: Run and verify closure RED**

Run: `python -m unittest tests.test_repository_contract -v`
Expected: FAIL only on Feature-05 durable documentation.

- [ ] **Step 3: Update durable repository docs**

Report only behavior proven by tests/CI. If live Codex validation is unavailable, state that repository package validation is Green while live-host validation remains unclaimed.

- [ ] **Step 4: Run full validation**

Run:
```bash
python -m unittest discover -s tests -v
python -m compileall -q praxis plugins/codex tests
pnpm typecheck
pnpm test:dsh
```
Expected: PASS where tools are available; GitHub Actions is authoritative for Python 3.10/3.13, Codex package job, and DSH seam.

- [ ] **Step 5: Open/update PR and require final GitHub Actions Green**

Required final head jobs:
- Python 3.10 — tests + compile PASS;
- Python 3.13 — tests + compile PASS;
- Codex package — targeted contract/adapter/recovery/distribution + compile PASS;
- TypeScript / DSH seam — typecheck + seam tests PASS.

- [ ] **Step 6: Whole-branch review**

Review host/neutral boundary, manifest schema assumptions, no-state/paused behavior, refresh-only mutation allowance, exact/candidate ambiguity, lifecycle honesty, deterministic truncation, transcript/prompt independence, and fallback truthfulness. Any Critical/Important finding gets a regression RED before its fix.

- [ ] **Step 7: Commit closure**

```bash
git add Code.md State.md README.md "Docs/Architecture/Harness Integration.md" tests/test_repository_contract.py
git commit -m "docs: close Feature-05 Codex integration"
```

- [ ] **Step 8: Merge only after final head is verified**

When PR is open, non-draft/ready, mergeable, and every required final-head CI job is completed/success, squash merge using an expected-head SHA lease.

## Self-Review Result

- **Spec coverage:** Tasks 1–8 cover manifest/package, hook declaration, activation, supported lifecycle events, freshness, exact/candidate task recovery, decision honesty, bounded context, fallback, distribution CI, and repository closure. Feature-06 remains isolated.
- **Step scan:** Every production change has a preceding failing contract; host manifest and adapter behavior are independently rejectable.
- **Type consistency:** The adapter entry points remain `build_context(event) -> str | None`, `build_response(event_name, context) -> dict`, and `main() -> int`; later tasks extend internal summarization without changing the external hook contract.
- **Review Focus:** malformed hook input, duplicate exact session matches, freshness-only mutation, huge durable state, and stale/duplicated distribution paths all have explicit owning tests.
- **Proportion:** The plan pins external contracts and failure semantics without duplicating implementation bodies.
