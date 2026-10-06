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

Feature-07: Implemented
- Native Cursor plugin: Implemented
- Native CodeBuddy plugin: Implemented
- Shared host recovery CLI bridge: Implemented
- Cursor session recovery and prompt freshness synchronization: Implemented
- CodeBuddy session and prompt recovery: Implemented
- Cursor / CodeBuddy package CI validation: Implemented

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
- `skills/praxis/` provides the shared English, host-neutral Tutor policy for explicitly enabled projects. Separate control skills handle enable/disable/status.
- Tutor policy now invites user proposals before project-specific AI solutions, guides problem review and iterative user revision, and requires scoped implementation delegation after design selection. Policy tests check the encoded contract; real model compliance remains unverified by those tests.
- Fixed node output now routes by the unresolved gap and includes adaptive teaching, expectation/result comparison, and evidence-based transfer to later tasks. The bounded simulation results and validation limits are recorded in `Docs/Specs/Tutor Guidance Design.md`.
- `praxis/recovery.py` produces the compact host-neutral recovery snapshot used by DSH, Cursor, and CodeBuddy adapters. It refreshes only machine-owned project freshness for enabled state and never creates/adopts tasks or advances decisions.

## Implemented Codex integration

- the repository root `plugin.json` is the canonical portable Agent Plugins manifest; `.codex-plugin/plugin.json` is the Codex compatibility fallback.
- both package surfaces reference the existing shared `skills/praxis/` tree and `plugins/codex/hooks/hooks.json`; Feature-05 does not duplicate the Skill or neutral core.
- `skills/praxis-enable/`, `skills/praxis-disable/`, and `skills/praxis-status/` expose direct control entries in the Codex skill picker, using the existing neutral CLI.
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
- `plugins/dsh/src/praxis-cli.ts` executes the neutral `praxis recovery-status` module with direct argv and `shell: false`; the default launcher is `python3` on POSIX and `py -3` on Windows, `PRAXIS_PYTHON` can override the executable path, and project cwd/session id remain separate arguments with the Praxis repository root prepended to `PYTHONPATH`.
- `plugins/dsh/src/context.ts` renders deterministic recovery/fallback context capped at 3000 characters and flattens free-form task/decision/scope labels before injection.
- `plugins/dsh/src/lifecycle.ts` declares the `praxis-dsh` instructions message source.
- `plugins/dsh/src/command.ts` registers the direct human `/praxis enable|disable|status` command through the DSH command registry; it runs outside model history and calls the neutral CLI bridge.
- `agent/created` synchronizes startup/resume lifecycle context through `agent.inject()`; uninitialized projects are silent and recovery failures are contained so Praxis cannot reject Agent creation.
- user-driven `agent/pre-step` delegates first, preserves downstream reject decisions, skips empty continuation steps, and appends changed Praxis context only to downstream `enter` messages.
- a per-agent digest suppresses duplicate unchanged automatic context. A visible recovery change makes the next user-driven step eligible for reinjection.
- Cordis fiber disposal removes the plugin listeners and runtime Skill registration. Unload never deletes or edits `.praxis`.
- repository validation uses real current DSH/Cordis types and real AgentRegistry event dispatch plus a TypeScript-to-Python subprocess integration test.
- the repository root now declares a DSH bundle layer at `plugins/dsh/cordis.patch.yml`, so `dsh plugin --profile <name> add github:Civitasv/praxis` can install the Git checkout into a profile. The package is still not claimed as npm-published.

## Implemented Cursor and CodeBuddy integration

- `.cursor-plugin/plugin.json` and `.codebuddy-plugin/plugin.json` both reference the existing root `skills/praxis/` tree and host-specific hook files; neither duplicates the Skill or neutral Python core.
- `plugins/shared/recovery_hook.py` invokes `praxis recovery-status` through direct argv with `shell: false`, validates the JSON response, renders deterministic context capped at 3000 characters, and provides a truthful manual-Skill fallback.
- Cursor `sessionStart` injects recovery context using the current project/session identity.
- Cursor `beforeSubmitPrompt` refreshes durable/project freshness and fails open, but does not claim unsupported per-prompt context injection.
- Cursor exposes `/praxis enable|disable|status` through its plugin command surface.
- CodeBuddy `SessionStart` and `UserPromptSubmit` both refresh and inject recovery context through the documented `additionalContext` envelope.
- CodeBuddy exposes `/praxis:enable`, `/praxis:disable`, and `/praxis:status` through plugin-namespaced commands.
- prompt and transcript text are never interpreted as decision approval.
- installing either host plugin does not enable Praxis; uninitialized projects remain silent and paused projects remain paused.
- Feature-07 adds no MCP server or MCP configuration.
- `.agents/plugins/marketplace.json` exposes the root plugin as a Codex marketplace source; `.codebuddy-plugin/marketplace.json` exposes the repository to CodeBuddy's plugin marketplace CLI.
- `pyproject.toml` now has an explicit setuptools build backend, so the neutral `praxis` CLI can be installed directly from the Git repository.

## Validation contract

Current repository validation commands are:

```bash
python -m unittest discover -s tests -v
python -m compileall -q praxis tests
python -m pip wheel --no-deps . -w /tmp/praxis-wheel
python -m unittest tests.test_codex_plugin_manifest tests.test_codex_hooks_manifest tests.test_codex_context tests.test_codex_recovery tests.test_codex_distribution -v
python -m compileall -q plugins/codex praxis
pnpm typecheck
pnpm test:dsh
```

GitHub Actions is authoritative for Python 3.10, Python 3.13, the dedicated Codex package job, the Cursor / CodeBuddy plugins job, and the TypeScript/DSH integration job with Python 3.10. A check is Green only when it actually runs successfully.

## External distribution status

Praxis does not yet claim publication in the public Codex, Cursor, or CodeBuddy marketplaces, nor npm publication for DSH. The repository does ship source-installable Codex and CodeBuddy marketplace catalogs plus a Git-installable DSH bundle. Cursor remains a local-plugin checkout until Marketplace publication. Host enablement and trust remain controlled by their environments.
