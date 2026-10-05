# Praxis Code Map

| Area | Contract | Implementation |
| --- | --- | --- |
| Neutral Python CLI | Feature-01/02/03 | `praxis/__init__.py`, `praxis/cli.py`, `praxis/__main__.py` |
| Project boundary and state-path safety | Feature-02 | `praxis/project.py` |
| Versioned state, atomic writes, CAS, latest-state maintenance | Feature-02/03 | `praxis/state.py` |
| Cross-process write lock | Feature-02 | `praxis/locking.py` |
| Durable task lifecycle | Feature-02 | `praxis/tasks.py` |
| Source evidence fingerprints | Feature-03 | `praxis/fingerprints.py` |
| Verified project model, section CAS, stale detection, `code.md` projection | Feature-03 | `praxis/project_map.py` |
| Shared Praxis Skill | Feature-04 | `skills/praxis/` — pending |
| Codex adapter | Feature-05 | `plugins/codex/` — pending |
| DSH adapter seam | Feature-01 | `plugins/dsh/` |
| DSH runtime integration | Feature-06 | `plugins/dsh/` — pending beyond seam |
| CI | Feature-01 | `.github/workflows/ci.yml` |
| Repository contracts | Feature-01/02/03 | `AGENTS.md`, `State.md`, `Docs/` |
| Python tests | Feature-01/02/03 | `tests/` |
| DSH boundary tests | Feature-01 | `plugins/dsh/test/` |

## Dependency direction

```text
shared Skill / host adapters
          |
          v
   neutral JSON/CLI contract
          |
          v
       praxis/
       /     \
      v       v
state.json   source evidence
      |
      v
project_model (authoritative)
      |
      v
.praxis/code.md (rebuildable projection)
```

Harness SDK dependencies terminate in their adapter. The neutral Python core must not import Codex, DeepSeek Harness, Cordis, or adapter package APIs.

Feature-02 centralizes durable state writes through `praxis/state.py`. Feature-03 adds `mutate_latest_state` for machine maintenance that must operate on the latest state without false global-revision conflicts; section-level concurrency remains owned by `praxis/project_map.py`.

`state.json.project_model` is authoritative. `.praxis/code.md` is deterministic output and is never parsed back into state. `praxis/fingerprints.py` owns normalized project-relative evidence paths and SHA-256 values so the model cannot invent machine metadata.

## Where to start

Read `State.md` for current implementation truth. Then read the relevant document under `Docs/Specs/` before changing source or tests. Feature-03 behavior is specified in `Docs/Specs/Feature-03 Verified Project Model.md`.
