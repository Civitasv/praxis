# Praxis State Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Harness-neutral `.praxis/state.json` engine with safe project boundaries, validated persistence, CAS revisions, locking, durable tasks, and an adapter-ready JSON CLI.

**Architecture:** Feature-02 remains entirely in the Python 3.10+ standard-library core. `project.py` owns repository/state-path boundaries, `locking.py` owns cross-process write exclusion, `state.py` owns schema/atomic persistence/CAS, and `tasks.py` composes state mutations for durable task lifecycle. The CLI translates neutral exceptions into stable JSON without introducing Codex/DSH dependencies.

**Tech Stack:** Python 3.10+ standard library, `unittest`, GitHub Actions inherited from Feature-01.

**Spec:** `Docs/Specs/Feature-02 Praxis State Core.md`

## Global Constraints

- Python 3.10+ only; no third-party runtime dependency.
- Harness-specific APIs must not enter `praxis/`.
- Format version is exactly `1` in Feature-02.
- Machine-owned revisions start at `0` and increment exactly once per successful existing-state mutation.
- Corrupt, invalid, unsupported, symlinked, or unwritable state must never be silently replaced.
- Installing Praxis does not enable a project; only explicit `enable` may initialize state.
- Lock acquisition is bounded and never steals an existing lock.
- Feature-02 does not implement project fingerprints, `code.md`, `decisions.md`, Tutor behavior, or host lifecycle code.

## Review Focus

1. Nested repo/worktree isolation — nearest `.git` marker must stop parent-state borrowing.
2. Symlink/state-file attacks — `.praxis` and `state.json` symlinks must be rejected before reads/writes.
3. Lost updates — stale expected revision must fail while preserving the newer bytes exactly.
4. Partial write failures — a failing `os.replace` must leave the previous valid state readable.
5. Task cross-talk — updating one task must leave unrelated task fields unchanged.

---

### Task 1: Project boundary and state-path safety

**Files:**
- Create: `praxis/project.py`
- Create: `tests/test_project.py`

**Interfaces:**
- Produces: `discover_project_root(cwd: str | Path) -> Path`, `state_directory(project_root: Path, *, create: bool = False) -> Path`, and `state_file(project_root: Path) -> Path`.

- [ ] Write failing tests for nearest Git root, `.git` file worktree, nested repo isolation, no-Git cwd behavior, and rejection of symlinked `.praxis` / `state.json`.
- [ ] Run `python -m unittest tests.test_project -v`; verify failures are due to missing APIs.
- [ ] Implement the minimum project/path-safety APIs without reading `.git` targets.
- [ ] Run focused tests and `python -m unittest discover -s tests -v`; require PASS.
- [ ] Commit `feat: add praxis project boundary discovery`.

### Task 2: State schema and safe reads/initialization

**Files:**
- Create: `praxis/state.py`
- Create: `tests/test_state.py`

**Interfaces:**
- Produces: `FORMAT_VERSION = 1`, typed neutral state exceptions, `load_state(project_root) -> dict | None`, and `enable_state(project_root, expected_revision: int | None = None) -> dict`.

- [ ] Write failing tests for absent state, explicit first enable shape/revision, malformed JSON preservation, invalid schema, unsupported format preservation, and repeated enable requiring CAS when it changes paused state.
- [ ] Run `python -m unittest tests.test_state -v`; verify RED.
- [ ] Implement schema validation and first initialization; preserve unknown compatible top-level fields.
- [ ] Run focused + full Python tests; require PASS.
- [ ] Commit `feat: add versioned praxis state schema`.

### Task 3: Write lock, atomic replacement, and CAS

**Files:**
- Create: `praxis/locking.py`
- Modify: `praxis/state.py`
- Modify: `tests/test_state.py`
- Create: `tests/test_locking.py`

**Interfaces:**
- Produces: `StateLock(project_root, timeout=..., poll_interval=...)`, `mutate_state(project_root, expected_revision, mutator) -> dict`, and `pause_state(project_root, expected_revision) -> dict`.

- [ ] Write failing tests for lock contention timeout, stale revision conflict, exactly-one revision increment, pause preserving all tasks/unknown fields, and simulated `os.replace` failure preserving old state.
- [ ] Run focused tests; verify RED.
- [ ] Implement lock-directory acquisition/release plus temporary-file → flush/fsync → replace persistence under lock.
- [ ] Run focused + full Python tests and `compileall`; require PASS.
- [ ] Commit `feat: add atomic cas state mutations`.

### Task 4: Durable multi-task lifecycle

**Files:**
- Create: `praxis/tasks.py`
- Create: `tests/test_tasks.py`

**Interfaces:**
- Produces: `create_task(...) -> tuple[str, dict]`, `update_task(...) -> dict`, `pending_tasks(state) -> dict`, allowed stages/statuses.

- [ ] Write failing tests for core-generated ids, host/conversation association, validation of stages/statuses, pending choices, two independent tasks, completion isolation, and stale-revision conflict.
- [ ] Run `python -m unittest tests.test_tasks -v`; verify RED.
- [ ] Implement task creation/update exclusively through `mutate_state`.
- [ ] Run focused + full Python tests; require PASS.
- [ ] Commit `feat: add durable praxis task lifecycle`.

### Task 5: Adapter-ready JSON CLI

**Files:**
- Modify: `praxis/cli.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Produces CLI commands `status`, `enable`, `pause`, `task-create`, `task-update` with one JSON object on stdout and stable error codes on failure.

- [ ] Write failing subprocess tests for no-state status without side effects, explicit enable, pause CAS conflict, task create/update, corrupt-state error JSON, and non-zero exits.
- [ ] Run `python -m unittest tests.test_cli -v`; verify RED.
- [ ] Implement argparse subcommands and neutral-exception → JSON translation; preserve existing `--version` behavior.
- [ ] Run focused + full Python tests and `compileall`; require PASS.
- [ ] Commit `feat: expose praxis state json cli`.

### Task 6: Feature-02 closure and CI evidence

**Files:**
- Modify: `Code.md`
- Modify: `State.md`
- Modify: `README.md`
- Modify: `tests/test_repository_contract.py`

**Interfaces:**
- Consumes all Feature-02 APIs and records only verified implementation facts.

- [ ] Extend repository-contract tests so Feature-02 must be Implemented while Features 03–06 remain Pending, and code-map paths name `project.py`, `state.py`, `locking.py`, and `tasks.py`.
- [ ] Run repository-contract test and verify RED before docs are updated.
- [ ] Update docs with actual API/state semantics and validation commands; do not claim fingerprints/Tutor/host integration.
- [ ] Run `python -m unittest discover -s tests -v`, `python -m compileall -q praxis tests`, `pnpm typecheck`, and `pnpm test:dsh` where locally available; open a draft PR and require GitHub Actions Python 3.10/current + TypeScript job Green.
- [ ] Commit `docs: record praxis state core implementation`.

## Self-review result

- Feature-02 is isolated from Feature-03 project understanding and Feature-04 Tutor provenance.
- Every state-changing interface goes through one CAS/lock/atomic-write path.
- Review-focus failure modes are assigned to explicit tests.
- Host adapters receive JSON/error contracts but no host-specific semantics are added.
