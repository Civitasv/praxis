# Feature-06 DSH Integration Implementation Plan

**Goal:** Replace the DSH placeholder seam with a native Cordis plugin that registers the shared Praxis Skill and injects bounded, truthful durable recovery context through current DSH lifecycle events.

**Authority:** `Docs/Specs/Feature-06 DSH Integration.md` and `docs/superpowers/specs/2026-10-06-dsh-integration-design.md`.

## Global constraints

- DSH/Cordis imports remain under `plugins/dsh/`; never under `praxis/`.
- `.praxis/state.json` remains authoritative.
- Recovery never creates/adopts/rebinds tasks or advances decisions.
- No prompt/transcript semantic approval parsing.
- Direct argv subprocess only; never `shell: true`.
- Automatic context <=3000 chars and deterministic.
- DSH failures never abort Agent creation.
- Shared Skill stays single-source at `skills/praxis/`.
- Target current pinned preview: dsh-agent/dsh-llm/dsh-skill 0.2.1-alpha.1, Cordis 4.0.5-alpha.1.

### Task 1 — Neutral recovery snapshot

Files:
- Create `praxis/recovery.py`
- Modify `praxis/cli.py`
- Create `tests/test_recovery.py`
- Modify `tests/test_cli.py`

TDD:
1. RED tests for uninitialized, paused, exact/ambiguous/candidate tasks, open decisions, blocked scopes, stale+unknown sections, and no lifecycle mutation.
2. Add `recovery_status(...)`.
3. Add `praxis recovery-status --cwd --host [--conversation-id]`.
4. GREEN full Python suite.

### Task 2 — DSH package/type baseline

Files:
- Modify root `package.json`
- Modify `plugins/dsh/package.json`
- Modify `plugins/dsh/src/index.ts`
- Modify `plugins/dsh/test/boundary.test.ts`
- Add focused package/type tests as needed.

TDD:
1. RED for native exports `name`, `inject`, `apply` and exact preview peer pins.
2. Add official DSH development dependencies and peer dependencies.
3. Minimal native plugin shell typechecks against current APIs.
4. GREEN `pnpm typecheck` and existing DSH tests.

### Task 3 — Shared Skill registration

Files:
- Modify `plugins/dsh/src/index.ts`
- Create `plugins/dsh/src/skill.ts`
- Create `plugins/dsh/test/skill.test.ts`

TDD:
1. RED for one runtime `praxis` skill, shared content, resource base, invocation policy, and Cordis-owned disposer.
2. Implement repository-root/shared-skill resolution and registration.
3. GREEN DSH tests/typecheck.

### Task 4 — Neutral CLI subprocess + bounded renderer

Files:
- Create `plugins/dsh/src/praxis-cli.ts`
- Create `plugins/dsh/src/context.ts`
- Create `plugins/dsh/test/praxis-cli.test.ts`
- Create `plugins/dsh/test/context.test.ts`

TDD:
1. RED for argv execution, no shell, cwd/session as separate args, PYTHONPATH prefix, JSON parsing/failure classes.
2. RED for enabled/paused/fallback rendering, stable ordering, single-line free-text sanitization, <=3000 char bound.
3. Implement direct `execFile` runner and renderer.
4. Add a real TypeScript -> Python `recovery-status` integration test.
5. GREEN.

### Task 5 — Agent lifecycle integration

Files:
- Modify `plugins/dsh/src/index.ts`
- Create `plugins/dsh/test/lifecycle.test.ts`

TDD:
1. RED: `agent/created` injects startup/resume recovery, stays silent for uninitialized, never throws on neutral failure.
2. RED: `agent/pre-step` skips empty-message continuations, always delegates, adds changed snapshot only to downstream `enter`, never rejects.
3. RED: unchanged digest does not duplicate context.
4. Implement producer-owned `praxis-dsh` source with `createUserMessage`.
5. GREEN.

### Task 6 — Distribution/CI/closure

Files:
- Modify `.github/workflows/ci.yml`
- Modify `Docs/Development/Validation.md`
- Modify `Code.md`
- Modify `State.md`
- Modify `README.md`
- Modify `Docs/Architecture/Harness Integration.md`
- Modify `tests/test_repository_contract.py`
- Create/modify DSH distribution tests.

TDD:
1. RED repository closure/distribution tests.
2. Extend DSH CI with Python 3.10 available for real adapter integration.
3. Document current DSH preview pin, `agent/created`, Skill registration, pre-step sync, and repository-local installation boundary.
4. Run full Python + TypeScript/DSH validation.
5. Whole-branch self-review focused on host-version drift, subprocess trust boundary, lifecycle failure containment, context injection, and cleanup.
6. Any Important/Critical finding gets regression RED→GREEN.
7. Ready PR and squash merge only after final-head CI is fully Green.
