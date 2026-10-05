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

Feature-04: Implemented
- Durable decision provenance: Implemented
- Decision-level CAS and lifecycle: Implemented
- Deterministic decisions.md projection: Implemented
- Decision JSON CLI: Implemented
- Shared Praxis Tutor Skill: Implemented

Feature-05: Pending — Codex integration
Feature-06: Pending — DSH integration

## Implemented state, project model, and Tutor decision core

- `praxis/project.py` resolves the nearest Git/worktree boundary and rejects symlinked `.praxis` directories or state files.
- `.praxis/state.json` remains format version `1` and is the sole machine-readable authority for enabled/paused state, tasks, optional verified `project_model`, and optional durable decision records.
- writes use a bounded lock directory plus temporary-file flush/fsync and atomic replacement.
- Feature-02 state mutations use compare-and-swap expected revisions; stale writers receive a conflict instead of overwriting newer state.
- `mutate_latest_state` supports latest-state machine maintenance and performs no write/revision increment when the semantic state is unchanged.
- `praxis/tasks.py` owns core task ids and task lifecycle through the shared state mutation path.
- `praxis/fingerprints.py` normalizes project-relative evidence paths, prevents evidence from escaping the project or entering `.praxis` / `.git`, and computes SHA-256 from exact source bytes.
- `praxis/project_map.py` stores caller-supplied semantic sections while the core owns project-model revisions, section revisions, evidence fingerprints, freshness status, and stale reasons.
- section-level CAS permits unrelated project-model sections to progress despite global state revision movement while stale same-section writers conflict.
- stale scans mark only sections whose source evidence changed, disappeared, became unsafe, or became unreadable; stale semantic sections require explicit refresh rather than silently becoming verified again.
- `.praxis/code.md` is a deterministic, atomically written projection of authoritative `state.json.project_model`; missing or out-of-sync output can be detected and rebuilt.
- `praxis/decisions.py` owns durable engineering/architectural decision ids, provenance fields, aggregate/record revisions, lifecycle transitions, task linkage, open-decision queries, and blocked-scope summaries.
- decision lifecycle is `open -> selected -> implemented -> verified`; `superseded` and `abandoned` are explicit terminal alternatives. Recovery, silence, or AI recommendation never advances lifecycle state.
- decision-level CAS permits unrelated decisions to progress despite global state revision movement while stale same-decision writers conflict.
- `tasks.pending_choices` remains compatibility/presentation metadata; durable decision records with `status == open` are authoritative for unresolved consequential choices.
- `.praxis/decisions.md` is a deterministic, atomically written projection of authoritative `state.json.decisions`; it is never parsed back into state and can be deleted/rebuilt.
- `praxis decision-status|decision-create|decision-select|decision-implemented|decision-verify|decision-supersede|decision-abandon|decision-evidence|decision-render` expose stable JSON behavior for future host adapters.
- `skills/praxis/` provides the shared English, host-neutral Tutor policy for consequential decisions, just-enough teaching, recovery, blocked scopes, verification, and reflection.

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

Feature-04 defines and tests host-neutral Tutor semantics and durable decision state, but automatic host lifecycle injection is not yet implemented. Feature-05 remains responsible for Codex activation/recovery hooks and distribution; Feature-06 remains responsible for native DSH/Cordis lifecycle integration. Praxis does not yet claim automatic cross-session host recovery through either adapter.
