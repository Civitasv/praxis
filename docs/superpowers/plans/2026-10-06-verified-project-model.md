# Verified Project Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a machine-verifiable, section-concurrent project model with source fingerprints, incremental stale detection, deterministic `.praxis/code.md`, and adapter-ready JSON commands.

**Architecture:** `state.json` remains authoritative and stores `project_model` semantic sections plus machine metadata. `fingerprints.py` captures safe source evidence, `project_map.py` owns section CAS/staleness/rendering, and `state.py` gains one latest-state no-op-aware mutation primitive for machine maintenance. `.praxis/code.md` is a deterministic projection, never the concurrency/source-of-truth layer.

**Tech Stack:** Python 3.10+ standard library, `unittest`, SHA-256 via `hashlib`, existing Feature-02 lock/atomic state engine, GitHub Actions.

**Spec:** `Docs/Specs/Feature-03 Verified Project Model.md`

## Global Constraints

- Python 3.10+ only; no third-party runtime dependency.
- Harness-specific APIs must not enter `praxis/`.
- `state.json` remains authoritative; `.praxis/code.md` is rebuildable output.
- Fingerprints, normalized evidence paths, section revisions, stale states, and project-model revisions are core-owned.
- Evidence must remain inside the project and outside `.praxis/` / `.git/`.
- Section CAS uses section revision, not global state revision.
- A no-op stale scan must not write or advance revisions.
- Feature-03 does not interpret changed source semantically and does not implement Tutor/decision behavior.

## Review Focus

1. Path escape/symlink escape — evidence resolving outside the project must be rejected.
2. False concurrency conflicts — unrelated section writes must survive global revision movement.
3. Lost section updates — stale same-section writes/removals must conflict.
4. Stale fanout — changing one shared evidence file must stale every dependent section and no unrelated section.
5. Projection drift — missing/outdated `code.md` must be detectable and deterministically repairable.

---

### Task 1: Safe evidence fingerprints

**Files:**
- Create: `praxis/fingerprints.py`
- Create: `tests/test_fingerprints.py`

**Interfaces:**
- Produces: `EvidenceError`, `fingerprint_file(project_root, path) -> dict[str, str]`, `capture_evidence(project_root, paths) -> list[dict[str, str]]`.

- [ ] Write failing tests for exact SHA-256, POSIX relative-path normalization, missing file, directory, `.praxis`, `.git`, `..`/absolute escape, outside-project symlink, and allowed in-project symlink.
- [ ] Run `python -m unittest tests.test_fingerprints -v`; verify RED due to missing module/APIs.
- [ ] Implement safe resolution and SHA-256 over exact bytes; callers provide paths only, never hashes.
- [ ] Run focused + full Python tests; require PASS.
- [ ] Commit `feat: add verified source fingerprints`.

### Task 2: Latest-state no-op-aware mutation

**Files:**
- Modify: `praxis/state.py`
- Modify: `tests/test_state.py`

**Interfaces:**
- Produces: `mutate_latest_state(project_root, mutator) -> dict[str, Any]`.

- [ ] Write failing tests that latest-state mutation uses current state despite prior revision movement, advances global revision once on change, and performs no write/revision increment when the mutator leaves semantic state unchanged.
- [ ] Run focused test; verify RED.
- [ ] Refactor the existing locked mutation path minimally and implement `mutate_latest_state` using the same lock/validation/atomic writer.
- [ ] Run state + full Python tests and `compileall`; require PASS.
- [ ] Commit `feat: add latest state maintenance mutation`.

### Task 3: Section model and section-level CAS

**Files:**
- Create: `praxis/project_map.py`
- Create: `tests/test_project_map.py`

**Interfaces:**
- Produces: `ProjectModelError`, `InvalidProjectModelError`, `SectionConflictError`, `UnknownSectionError`, `get_project_model(state)`, `upsert_section(...)`, `remove_section(...)`.

- [ ] Write failing tests for new section revision 0, evidence-backed `verified`, evidence-free `unknown`, same-section stale CAS conflict, exact-revision update/removal, two unrelated sections updating successfully across global revision changes, invalid ids/content, and preservation of Feature-02 tasks/unknown top-level fields.
- [ ] Run `python -m unittest tests.test_project_map -v`; verify RED.
- [ ] Implement `project_model = {revision, sections}` validation and section mutations through `mutate_latest_state`; increment model revision once per model mutation.
- [ ] Run focused + full Python tests; require PASS.
- [ ] Commit `feat: add section concurrent project model`.

### Task 4: Incremental stale detection

**Files:**
- Modify: `praxis/project_map.py`
- Modify: `tests/test_project_map.py`

**Interfaces:**
- Produces: `refresh_staleness(project_root) -> dict[str, Any]`.

- [ ] Write failing tests for changed/missing/unsafe/unreadable evidence, shared-evidence fanout, unrelated-section preservation, unknown sections remaining unknown, stable machine reason ordering, and repeated identical scan being a no-op for global/model/section revisions.
- [ ] Run focused tests; verify RED.
- [ ] Recompute evidence hashes from stored normalized paths; update only `status` and `stale_reasons`, never semantic content or section revision.
- [ ] Run focused + full Python tests and `compileall`; require PASS.
- [ ] Commit `feat: add incremental project model staleness`.

### Task 5: Deterministic `.praxis/code.md` projection

**Files:**
- Modify: `praxis/project_map.py`
- Modify: `tests/test_project_map.py`

**Interfaces:**
- Produces: `ProjectModelRenderError`, `render_project_model(project_root) -> Path`, `project_model_status(project_root) -> dict[str, Any]`.

- [ ] Write failing tests for stable section ordering/markers, evidence rendering, stale reasons, explicit unknown evidence, missing code file reporting `render_required`, model-revision mismatch reporting `render_required`, deterministic rebuild, and render failure being reported without changing authoritative state.
- [ ] Run focused tests; verify RED.
- [ ] Render atomically from authoritative state and detect synchronization only from the machine model-revision marker.
- [ ] Run focused + full Python tests; require PASS.
- [ ] Commit `feat: render verified project code map`.

### Task 6: JSON CLI and Feature-03 closure

**Files:**
- Modify: `praxis/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_repository_contract.py`
- Modify: `Code.md`
- Modify: `State.md`
- Modify: `README.md`

**Interfaces:**
- Produces CLI commands `map-status`, `map-upsert`, `map-remove`, `map-check`, `map-render` and stable Feature-03 error codes.

- [ ] Add failing CLI tests for read-only map status, upsert/update/remove CAS, map-check stale transition + no-op rescan, map-render recovery, invalid evidence, section conflict, unknown section, invalid model, and render failure/error JSON where injectable.
- [ ] Run CLI tests; verify RED.
- [ ] Implement CLI translation while preserving existing Feature-02 JSON/`--version` behavior.
- [ ] Extend repository-contract tests so Feature-03 must be Implemented while Features 04–06 remain Pending; verify RED before docs update.
- [ ] Update `Code.md`, `State.md`, and `README.md` with only verified Feature-03 capabilities.
- [ ] Run full Python suite + `compileall`; open draft PR and require GitHub Actions Python 3.10/current and DSH TypeScript job Green.
- [ ] Commit `docs: record verified project model implementation`.

## Self-review result

- Project-model semantic interpretation remains outside the core; this feature only verifies freshness and stores caller-supplied model content.
- Machine metadata cannot be supplied through project-map APIs.
- Section CAS avoids false conflicts from task/global revision movement while preserving same-section lost-update protection.
- `code.md` is recoverable output, so projection failure cannot silently become authoritative state.
- Every review-focus failure mode is assigned to explicit tests.
