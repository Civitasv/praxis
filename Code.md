# Praxis Code Map

| Area | Contract | Implementation |
| --- | --- | --- |
| Neutral Python CLI | Feature-01/02 | `praxis/__init__.py`, `praxis/cli.py`, `praxis/__main__.py` |
| Project boundary and state-path safety | Feature-02 | `praxis/project.py` |
| Versioned state, atomic writes, CAS | Feature-02 | `praxis/state.py` |
| Cross-process write lock | Feature-02 | `praxis/locking.py` |
| Durable task lifecycle | Feature-02 | `praxis/tasks.py` |
| Shared Praxis Skill | Feature-04 | `skills/praxis/` — pending |
| Codex adapter | Feature-05 | `plugins/codex/` — pending |
| DSH adapter seam | Feature-01 | `plugins/dsh/` |
| DSH runtime integration | Feature-06 | `plugins/dsh/` — pending beyond seam |
| CI | Feature-01 | `.github/workflows/ci.yml` |
| Repository contracts | Feature-01/02 | `AGENTS.md`, `State.md`, `Docs/` |
| Python tests | Feature-01/02 | `tests/` |
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
          |
          v
 project-local .praxis/state.json
```

Harness SDK dependencies terminate in their adapter. The neutral Python core must not import Codex, DeepSeek Harness, Cordis, or adapter package APIs.

Feature-02 centralizes all durable state mutations through `praxis/state.py`; `praxis/tasks.py` composes that state API rather than creating a second persistence path.

## Where to start

Read `State.md` for current implementation truth. Then read the relevant `Docs/Architecture/` document and Feature spec before changing source or tests.
