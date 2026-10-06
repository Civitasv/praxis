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

Feature-05: Implemented
- Portable Codex plugin package: Implemented
- SessionStart and UserPromptSubmit recovery: Implemented
- Project freshness synchronization: Implemented
- Bounded Codex recovery context: Implemented
- Manual Skill fallback: Implemented
- Codex package CI validation: Implemented

Feature-06: Pending — DSH integration

## Implemented state, project model, and Tutor decision core

- `praxis/project.py` resolves the nearest Git/worktree boundary and rejects symlinked `.praxis` directories or state files.
- `.praxis/state.json` remains format version `1` and is the sole machine-readable authority for enabled/paused state, tasks, optional verified `project_model`, and optional durable decision records.
- writes use a bounded lock directory plus temporary-file flush/fsync and atomic replacement.
- state, section, and decision concurrency semantics remain owned by the neutral Python core.
- `praxis/fingerprints.py` owns normalized source fingerprints and `praxis/project_map.py` owns stale detection.
- stale semantic project sections require explicit semantic refresh and are never auto-cleared merely because source bytes later match again.
- `.praxis/code.md` and `.praxis/decisions.md` are deterministic projections and are never parsed back into authoritative state.
- `praxis/decisions.py` owns durable engineering/architectural decision provenance, lifecycle, task linkage, open-decision queries, and blocked scopes.
- decision lifecycle is `open -> selected -> implemented -> verified`; `superseded` and `abandoned` are explicit terminal alternatives.
- recovery, silence, restart, compaction, or an AI recommendation never advances decision lifecycle.
- `skills/praxis/` provides the shared English, host-neutral Tutor policy.

## Implemented Codex integration

- the repository root `plugin.json` is the canonical portable Agent Plugins manifest; `.codex-plugin/plugin.json` is the Codex compatibility fallback.
- both package surfaces reference the existing shared `skills/praxis/` tree and `plugins/codex/hooks/hooks.json`; Feature-05 does not duplicate the Skill or neutral core.
- `plugins/codex/hooks/hooks.json` declares `SessionStart` for `startup|resume|clear|compact` and `UserPromptSubmit`.
- `plugins/codex/hooks/praxis_context.py` is a thin translation adapter. Event/user data arrives over stdin JSON rather than being interpolated into hook commands.
- plugin installation does not enable Praxis. An uninitialized project is silent and creates no `.praxis/` state. A paused project remains paused.
- enabled-project lifecycle events reuse Feature-03 freshness checks before recovery context is built.
- exact Codex session linkage can recover an existing non-complete task without mutating task lifecycle; absent exact linkage yields zero, one candidate, or multiple user-choice candidates without auto-adoption/rebinding.
- open decisions and their declared blocked scopes are summarized only for the selected recovery context; selected/implemented/verified states are not rewritten or mislabeled.
- automatic context is deterministic and hard-bounded to 3000 characters.
- the adapter deliberately ignores prompt semantics and transcript paths for approval/recovery decisions.
- malformed/unsupported/unreadable state and refresh/lock failures degrade to a truthful manual Praxis Skill fallback rather than fabricated recovery.
- Codex host trust remains authoritative. Repository validation proves package/adapter contracts but does not prove that a particular user's environment has deployed or trusted the hook scripts.

## Validation contract

Current repository validation commands are:

```bash
python -m unittest discover -s tests -v
python -m compileall -q praxis tests
python -m unittest tests.test_codex_plugin_manifest tests.test_codex_hooks_manifest tests.test_codex_context tests.test_codex_recovery tests.test_codex_distribution -v
python -m compileall -q plugins/codex praxis
pnpm typecheck
pnpm test:dsh
```

GitHub Actions is authoritative for Python 3.10, Python 3.13, the dedicated Codex package job, and the TypeScript/DSH seam. A check is Green only when it actually runs successfully.

## Not implemented yet

Feature-06 remains responsible for native DSH/Cordis lifecycle integration. Praxis does not yet claim automatic DSH lifecycle recovery. Feature-05 also does not claim marketplace publication, user-level hook trust, or live-host deployment validation.
