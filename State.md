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

Feature-03: Pending — Verified project model
Feature-04: Pending — Tutor decision loop
Feature-05: Pending — Codex integration
Feature-06: Pending — DSH integration

## Implemented state core

- `praxis/project.py` resolves the nearest Git/worktree boundary and rejects symlinked `.praxis` directories or `state.json` files.
- `.praxis/state.json` uses format version `1`, machine-owned revisions, an `enabled` flag, and durable task records.
- writes use a bounded lock directory plus temporary-file flush/fsync and atomic replacement.
- state mutations use compare-and-swap expected revisions; stale writers receive a conflict instead of overwriting newer state.
- malformed, invalid, unsupported, or unsafe state is reported without silently replacing the original file.
- `praxis/tasks.py` creates core-owned task ids and updates tasks through the same state mutation path so multiple tasks do not overwrite each other.
- pause/resume changes the enabled flag while preserving task state; it does not imply approval or completion.
- `praxis status|enable|pause|task-create|task-update` expose a stable JSON boundary for future host adapters.
- `status` on a project without Praxis state is read-only and does not create `.praxis/`.

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

Praxis does not yet provide verified project fingerprints or `code.md` stale-section semantics, durable decision provenance / Tutor behavior, Codex lifecycle hooks, or native DSH/Cordis runtime integration. Those remain Features 03–06.
