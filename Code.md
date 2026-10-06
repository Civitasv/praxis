# Praxis Code Map

| Area | Contract | Implementation |
| --- | --- | --- |
| Neutral Python CLI | Feature-01/02/03/04 | `praxis/__init__.py`, `praxis/cli.py`, `praxis/__main__.py` |
| Project boundary and state-path safety | Feature-02 | `praxis/project.py` |
| Versioned state, atomic writes, CAS, latest-state maintenance | Feature-02/03/04 | `praxis/state.py` |
| Cross-process write lock | Feature-02 | `praxis/locking.py` |
| Durable task lifecycle | Feature-02 | `praxis/tasks.py` |
| Source evidence fingerprints | Feature-03 | `praxis/fingerprints.py` |
| Verified project model, section CAS, stale detection, `code.md` projection | Feature-03 | `praxis/project_map.py` |
| Durable decision provenance, lifecycle, decision CAS, `decisions.md` projection | Feature-04 | `praxis/decisions.py` |
| Shared Praxis Tutor Skill | Feature-04 | `skills/praxis/` |
| Codex adapter | Feature-05 | `plugins/codex/` — pending |
| DSH adapter seam | Feature-01 | `plugins/dsh/` |
| DSH runtime integration | Feature-06 | `plugins/dsh/` — pending beyond seam |
| CI | Feature-01 | `.github/workflows/ci.yml` |
| Repository contracts | Feature-01/02/03/04 | `AGENTS.md`, `State.md`, `Docs/` |
| Python tests | Feature-01/02/03/04 | `tests/` |
| DSH boundary tests | Feature-01 | `plugins/dsh/test/` |

## Dependency direction

```text
shared Praxis Tutor Skill / host adapters
                |
                v
         neutral JSON/CLI contract
                |
                v
             praxis/
          /      |       \
         v       v        v
   state.json  decisions  source evidence
      |          |             |
      |          |             v
      |          |       project_model
      |          |             |
      |          v             v
      |   .praxis/decisions.md .praxis/code.md
      |       (projection)       (projection)
      v
machine-owned tasks / revisions / lifecycle metadata
```

Harness SDK dependencies terminate in their adapter. The neutral Python core must not import Codex, DeepSeek Harness, Cordis, or adapter package APIs.

Feature-02 centralizes durable state writes through `praxis/state.py`. Feature-03 adds `mutate_latest_state` for machine maintenance and section-level project-model concurrency. Feature-04 reuses the same write/lock path for decision-level CAS and durable Tutor provenance.

`state.json.project_model` is authoritative for verified repository facts and `.praxis/code.md` is a rebuildable projection. `state.json.decisions` is authoritative for consequential decision lifecycle/provenance and `.praxis/decisions.md` is likewise a deterministic projection. Neither Markdown projection is parsed back into state.

`praxis/fingerprints.py` owns normalized project-relative evidence paths and SHA-256 values. `praxis/decisions.py` owns decision ids, decision revisions, aggregate decision revision, lifecycle transitions, unresolved-decision queries, blocked scopes, and the decision-trail renderer.

## Where to start

Read `State.md` for current implementation truth. Then read the relevant document under `Docs/Specs/` before changing source or tests. Feature-03 behavior is specified in `Docs/Specs/Feature-03 Verified Project Model.md`; Feature-04 Tutor semantics are specified in `Docs/Specs/Feature-04 Tutor Decision Loop.md`.
