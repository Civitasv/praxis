# Praxis Code Map

| Area | Contract | Implementation |
| --- | --- | --- |
| Neutral Python CLI and source package | Feature-01/02/03/04/06 | `praxis/__init__.py`, `praxis/cli.py`, `praxis/__main__.py`, `pyproject.toml` |
| Host-neutral recovery snapshot | Feature-06 | `praxis/recovery.py` |
| Project boundary and state-path safety | Feature-02 | `praxis/project.py` |
| Versioned state, atomic writes, CAS, latest-state maintenance | Feature-02/03/04 | `praxis/state.py` |
| Cross-process write lock | Feature-02 | `praxis/locking.py` |
| Durable task lifecycle | Feature-02 | `praxis/tasks.py` |
| Source evidence fingerprints | Feature-03 | `praxis/fingerprints.py` |
| Verified project model, section CAS, stale detection, `code.md` projection | Feature-03 | `praxis/project_map.py` |
| Durable decision provenance, lifecycle, decision CAS, `decisions.md` projection | Feature-04 | `praxis/decisions.py` |
| Shared Praxis Tutor Skill | Feature-04/06/07 | `skills/praxis/` |
| Portable Codex plugin package | Feature-05 | `plugin.json`, `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` |
| Codex lifecycle adapter | Feature-05 | `plugins/codex/hooks/hooks.json`, `plugins/codex/hooks/praxis_context.py` |
| Shared Python host recovery bridge | Feature-07 | `plugins/shared/recovery_hook.py` |
| Cursor plugin package and lifecycle adapter | Feature-07 | `.cursor-plugin/plugin.json`, `plugins/cursor/hooks/` |
| CodeBuddy plugin package and lifecycle adapter | Feature-07 | `.codebuddy-plugin/plugin.json`, `.codebuddy-plugin/marketplace.json`, `plugins/codebuddy/hooks/` |
| Native DSH Cordis plugin / bundle | Feature-06 | `plugins/dsh/src/index.ts`, `plugins/dsh/cordis.patch.yml`, root `package.json` |
| DSH Skill registration | Feature-06 | `plugins/dsh/src/skill.ts` |
| DSH direct-argv neutral-core bridge | Feature-06 | `plugins/dsh/src/praxis-cli.ts` |
| DSH bounded recovery renderer | Feature-06 | `plugins/dsh/src/context.ts` |
| DSH Agent lifecycle adapter | Feature-06 | `plugins/dsh/src/lifecycle.ts` |
| CI | Feature-01/05/06/07 | `.github/workflows/ci.yml` |
| Repository contracts | Feature-01/02/03/04/05/06/07 | `AGENTS.md`, `State.md`, `Docs/` |
| Python tests | Feature-01/02/03/04/05/06/07 | `tests/` |
| DSH integration tests | Feature-01/06 | `plugins/dsh/test/` |

## Dependency direction

```text
Codex SessionStart / UserPromptSubmit       DSH agent/created / agent/pre-step
                  |                                      |
                  v                                      v
       plugins/codex/hooks/                       plugins/dsh/
                  \                                  /
                   \                                /
                    v                              v
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

Feature-02 centralizes durable state writes through `praxis/state.py`. Feature-03 adds latest-state machine maintenance and section-level project-model concurrency. Feature-04 adds decision-level CAS and durable Tutor provenance. Feature-05 consumes those neutral semantics through a translation-only Codex lifecycle adapter. Feature-06 adds `praxis/recovery.py` as a host-neutral snapshot API and consumes it from the native DSH Cordis adapter through direct argv subprocess execution. Feature-07 reuses the same recovery CLI through a shared Python bridge for Cursor and CodeBuddy; neither host introduces a second state model or MCP dependency.

`state.json.project_model` remains authoritative for verified repository facts and `.praxis/code.md` is rebuildable. `state.json.decisions` remains authoritative for consequential decision lifecycle/provenance and `.praxis/decisions.md` is rebuildable. Neither host adapter creates a parallel state model.

The root `plugin.json` is the portable Codex package manifest. `.codex-plugin/plugin.json` is its compatibility fallback and `.agents/plugins/marketplace.json` exposes it as a repository marketplace. DSH uses the TypeScript package under `plugins/dsh/`; the root Node package declares the DSH bundle so Git installation retains the same `skills/praxis/` and Python core instead of copying them. CodeBuddy's repository marketplace is `.codebuddy-plugin/marketplace.json`.

## Where to start

Read `State.md` for current implementation truth. Then read the relevant document under `Docs/Specs/` before changing source or tests. Feature-03 behavior is specified in `Docs/Specs/Feature-03 Verified Project Model.md`; Feature-04 Tutor semantics in `Docs/Specs/Feature-04 Tutor Decision Loop.md`; Feature-05 Codex behavior in `Docs/Specs/Feature-05 Codex Integration.md`; Feature-06 DSH behavior in `Docs/Specs/Feature-06 DSH Integration.md`; Feature-07 Cursor/CodeBuddy behavior in `Docs/Specs/Feature-07 Cursor and CodeBuddy Integration.md`.
