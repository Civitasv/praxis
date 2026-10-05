# Praxis Code Map

| Area | Contract | Implementation |
| --- | --- | --- |
| Neutral Python baseline | Feature-01 | `praxis/__init__.py`, `praxis/cli.py`, `praxis/__main__.py` |
| Shared Praxis Skill | Feature-04 | `skills/praxis/` — pending |
| Codex adapter | Feature-05 | `plugins/codex/` — pending |
| DSH adapter seam | Feature-01 | `plugins/dsh/` |
| DSH runtime integration | Feature-06 | `plugins/dsh/` — pending beyond seam |
| CI | Feature-01 | `.github/workflows/ci.yml` |
| Repository contracts | Feature-01 | `AGENTS.md`, `State.md`, `Docs/` |
| Python tests | Feature-01 | `tests/` |
| DSH boundary tests | Feature-01 | `plugins/dsh/test/` |

## Dependency direction

```text
shared Skill / host adapters
          |
          v
     shared semantics
          |
          v
       praxis/
```

Harness SDK dependencies terminate in their adapter. The neutral Python core must not import Codex, DeepSeek Harness, Cordis, or adapter package APIs.

## Where to start

Read `State.md` for current implementation truth. Then read the relevant `Docs/Architecture/` document and Feature spec before changing source or tests.
