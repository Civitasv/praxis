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

Feature-06: Implemented
- Neutral recovery snapshot: Implemented
- Native DSH Cordis plugin: Implemented
- DSH shared Skill registration: Implemented
- DSH agent lifecycle recovery: Implemented
- DSH direct-argv Python bridge: Implemented
- Bounded DSH recovery context: Implemented
- DSH integration CI validation: Implemented

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
- `praxis/recovery.py` produces the compact host-neutral recovery snapshot used by the DSH adapter. It refreshes only machine-owned project freshness for enabled state and never creates/adopts tasks or advances decisions.

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

## Implemented DeepSeek Harness integration

- `plugins/dsh/` is a native Cordis plugin targeting the pinned DSH preview family `0.2.1-alpha.1` with Cordis `4.0.5-alpha.1`.
- `plugins/dsh/src/skill.ts` registers the single shared `skills/praxis/SKILL.md` as model- and user-invocable; no Skill copy lives under `plugins/dsh/`.
- `plugins/dsh/src/praxis-cli.ts` executes `python3 -m praxis recovery-status` with direct argv, `shell: false`, project cwd, session id as a separate argument, and the Praxis repository root prepended to `PYTHONPATH`.
- `plugins/dsh/src/context.ts` renders deterministic recovery/fallback context capped at 3000 characters and flattens free-form task/decision/scope labels before injection.
- `plugins/dsh/src/lifecycle.ts` declares the `praxis-dsh` instructions message source.
- `agent/created` synchronizes startup/resume lifecycle context through `agent.inject()`; uninitialized projects are silent and recovery failures are contained so Praxis cannot reject Agent creation.
- user-driven `agent/pre-step` delegates first, preserves downstream reject decisions, skips empty continuation steps, and appends changed Praxis context only to downstream `enter` messages.
- a per-agent digest suppresses duplicate unchanged automatic context. A visible recovery change makes the next user-driven step eligible for reinjection.
- Cordis fiber disposal removes the plugin listeners and runtime Skill registration. Unload never deletes or edits `.praxis`.
- repository validation uses real current DSH/Cordis types and real AgentRegistry event dispatch plus a TypeScript-to-Python subprocess integration test.
- the repository package remains private and is not claimed as npm-published or automatically installed into a user's DSH profile.

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

GitHub Actions is authoritative for Python 3.10, Python 3.13, the dedicated Codex package job, and the TypeScript/DSH integration job with Python 3.10. A check is Green only when it actually runs successfully.

## External distribution status

Praxis does not yet claim marketplace publication. The DSH package is repository-local/private and Feature-06 does not mutate DSH profiles or install itself into a host deployment. Codex hook trust/deployment likewise remains controlled by the host environment.
