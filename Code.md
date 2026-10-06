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
| Portable Codex plugin package | Feature-05 | `plugin.json`, `.codex-plugin/plugin.json` |
| Codex lifecycle adapter | Feature-05 | `plugins/codex/hooks/hooks.json`, `plugins/codex/hooks/praxis_context.py` |
| DSH adapter seam | Feature-01 | `plugins/dsh/` |
| DSH runtime integration | Feature-06 | `plugins/dsh/` — pending beyond seam |
| CI | Feature-01/05 | `.github/workflows/ci.yml` |
| Repository contracts | Feature-01/02/03/04/05 | `AGENTS.md`, `State.md`, `Docs/` |
| Python tests | Feature-01/02/03/04/05 | `tests/` |
| DSH boundary tests | Feature-01 | `plugins/dsh/test/` |

## Dependency direction

```text
Codex SessionStart / UserPromptSubmit       future DSH lifecycle
                  |                                  |
                  v                                  v
       plugins/codex/hooks/                    plugins/dsh/
                  \                              /
                   \                            /
                    v                          v
                     shared Praxis Tutor Skill
                              |
                              v
                       neutral Python core
                              |
                 +------------+------------+
                 |            |            |
                 v            v            v
              tasks      decisions    project_model
                 |            |            |
                 +------------+------------+
                              |
                              v
                     .praxis/state.json
```

Harness-specific dependencies terminate in their adapter. The neutral Python core must not import Codex, DeepSeek Harness, Cordis, or adapter package APIs.

Feature-02 centralizes durable state writes through `praxis/state.py`. Feature-03 adds latest-state machine maintenance and section-level project-model concurrency. Feature-04 adds decision-level CAS and durable Tutor provenance. Feature-05 consumes those neutral semantics through a translation-only Codex lifecycle adapter.

`state.json.project_model` remains authoritative for verified repository facts and `.praxis/code.md` is rebuildable. `state.json.decisions` remains authoritative for consequential decision lifecycle/provenance and `.praxis/decisions.md` is rebuildable. Codex hooks do not create a parallel host-owned state model.

The root `plugin.json` is the portable package manifest. `.codex-plugin/plugin.json` is the compatibility fallback. Both point to the single shared Skill and `plugins/codex/hooks/` package.

## Where to start

Read `State.md` for current implementation truth. Then read the relevant document under `Docs/Specs/` before changing source or tests. Feature-03 behavior is specified in `Docs/Specs/Feature-03 Verified Project Model.md`; Feature-04 Tutor semantics in `Docs/Specs/Feature-04 Tutor Decision Loop.md`; Feature-05 Codex behavior in `Docs/Specs/Feature-05 Codex Integration.md`.
