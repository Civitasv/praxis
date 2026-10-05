# Praxis Current State

## Feature status

Feature-01: Implemented
- Repository contracts: Implemented
- Python neutral-core executable baseline: Implemented
- DSH TypeScript boundary: Implemented
- GitHub Actions CI: Implemented

Feature-02: Implemented
- Project boundary discovery: Implemented
- Versioned state schema: Implemented
- Atomic CAS state writes: Implemented
- Durable multi-task lifecycle: Implemented
- JSON CLI state contract: Implemented

Feature-03: Implemented
- Source evidence fingerprints: Implemented
- Section-level project-model CAS: Implemented
- Incremental stale detection: Implemented
- Deterministic code.md projection: Implemented
- Project-model JSON CLI: Implemented

Feature-04: Pending — Tutor decision loop
Feature-05: Pending — Codex integration
Feature-06: Pending — DSH integration

## Implemented state and project model

- `praxis/project.py` resolves the nearest Git/worktree boundary and rejects symlinked `.praxis` directories or `state.json` files.
- `.praxis/state.json` uses format version `1`, machine-owned global revisions, an `enabled` flag, durable task records, and optional authoritative `project_model` metadata/content.
- writes use a bounded lock directory plus temporary-file flush/fsync and atomic replacement.
- Feature-02 state mutations use compare-and-swap expected revisions; stale writers receive a conflict instead of overwriting newer state.
- `mutate_latest_state` supports machine maintenance against the latest state and performs no write/revision increment when the semantic state is unchanged.
- `praxis/tasks.py` creates core-owned task ids and updates tasks through the shared state mutation path.
- `praxis/fingerprints.py` normalizes project-relative evidence paths, prevents evidence from escaping the project or entering `.praxis` / `.git`, and computes SHA-256 from exact source bytes.
- `praxis/project_map.py` stores caller-supplied semantic sections while the core owns project-model revisions, section revisions, evidence fingerprints, freshness status, and stale reasons.
- section-level CAS permits unrelated sections to progress despite global state revision movement while stale same-section writers conflict.
- stale scans mark only sections whose source evidence changed, disappeared, became unsafe, or became unreadable; section semantic revisions do not change during freshness scans.
- repeated stale scans with identical results are true no-ops for state and project-model revisions.
- `.praxis/code.md` is a deterministic, atomically written projection of authoritative `state.json.project_model`; missing or out-of-sync output can be detected and rebuilt.
- ordinary task/global state mutations do not invalidate `code.md` because projection freshness is keyed to `project_model.revision`.
- `praxis map-status|map-upsert|map-remove|map-check|map-render` expose stable JSON behavior for future host adapters.

## Validation contract

Current repository validation commands are:

```bash
python -m unittest discover -s tests -v
python -m compileall -q praxis tests
pnpm typecheck
pnpm test:dsh
```

A check is Green only when it actually runs successfully. GitHub Actions is authoritative for the minimum Python 3.10 and pnpm/TypeScript environment.

## Not implemented yet

Praxis does not yet provide durable decision provenance / Tutor behavior, Codex lifecycle hooks, or native DSH/Cordis runtime integration. Those remain Features 04–06.
