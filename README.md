# Praxis

**Build with AI. Keep the judgment.**

Praxis is an AI tutor for building software with coding agents. It lets AI handle execution while keeping the human involved in consequential decisions, tradeoffs, and feedback that build engineering judgment.

## Architecture direction

Praxis uses a Python 3.10+ standard-library neutral core, a shared English Tutor Skill, and thin host adapters.

```text
host lifecycle ──→ thin adapter ──→ shared Praxis Tutor Skill
                                        |
                                        v
                                 neutral Python core
                                        |
                                        v
                               project-local .praxis/
```

Harness-specific APIs must not enter the neutral Python core.

## Current status

Features 01–06 are implemented: the AI-native repository foundation, Praxis State Core, Verified Project Model, host-neutral Tutor Decision Loop, Codex Integration, and native DeepSeek Harness/Cordis Integration.

Feature-02 provides project-boundary discovery, symlink-safe project state paths, format-versioned `.praxis/state.json`, bounded write locking, atomic replacement, compare-and-swap revisions, durable multi-task records, pause/resume state, and a JSON CLI contract.

Feature-03 adds machine-owned source fingerprints, section-level compare-and-swap, incremental stale detection, and deterministic `.praxis/code.md` recovery. `state.json.project_model` remains authoritative.

Feature-04 adds durable decision provenance and decision-level compare-and-swap. Engineering/architectural decisions keep user proposal, verified constraints, Praxis challenge, selected decision, user reasoning, implementation result, and verification separate:

```text
open -> selected -> implemented -> verified
```

`superseded` and `abandoned` are explicit terminal alternatives. An AI recommendation, restart, recovery, or silence cannot turn an open choice into a selected one. Authoritative decision records live in `state.json.decisions`; `.praxis/decisions.md` is a deterministic rebuildable projection.

The shared Praxis Tutor Skill under `skills/praxis/` encodes the host-neutral loop: inspect verified facts, surface consequential choices, teach or challenge when needed, record explicit agreement, implement, verify, and connect observed results back to the decision.

### Codex integration

Feature-05 packages Praxis as a portable Codex plugin using root `plugin.json`, a `.codex-plugin/plugin.json` compatibility fallback, and thin lifecycle hooks under `plugins/codex/hooks/`.

The adapter handles Codex `SessionStart` events for startup, resume, clear, and compact, plus `UserPromptSubmit`. For an enabled project it refreshes machine-owned project freshness, identifies exact or candidate durable tasks, summarizes relevant open decisions and blocked scopes, and injects no more than **3000 characters** of deterministic recovery context.

Plugin installation does not enable a project. Explicit `praxis enable --cwd <path>` remains the activation boundary. An uninitialized project is silent, and a paused project stays paused.

Automatic recovery does not parse prompt text as approval and does not read transcript history. Recovery never selects a decision, marks implementation complete, or marks verification complete.

Codex hook execution is subject to host installation, execution-environment availability, and hook **trust**. Repository CI validates package files and adapter behavior, but it does not claim that hooks are active in a particular user's Codex environment. If automatic hooks are unavailable, the shared Praxis Tutor Skill remains the **manual** fallback.

### DeepSeek Harness / Cordis integration

Feature-06 replaces the original DSH seam with a native Cordis plugin under `plugins/dsh/`. It is tested against the current DSH preview family `0.2.1-alpha.1` and Cordis `4.0.5-alpha.1`.

The plugin registers the same shared Praxis Skill and listens to DSH `agent/created` plus `agent/pre-step`. Session creation/resume can inject durable recovery context through `agent.inject()`; later user-driven steps synchronize only when the rendered recovery snapshot changes. Empty continuation steps are ignored, and downstream reject decisions are preserved.

DSH does not interpret the user's prompt as approval. Exact/candidate tasks, open decisions, blocked scopes, and stale/unknown project sections come from:

```bash
python -m praxis recovery-status --cwd . --host dsh --conversation-id <session-id>
```

The TypeScript adapter invokes this through direct argv execution with `shell: false` and caps injected context at **3000 characters**. Its model-facing message source is `praxis-dsh`.

Installing or checking out this repository does not enable Praxis, and Feature-06 **does not install** the private `@praxis/plugin-dsh` package into any DSH **profile**. Repository CI proves package/API/lifecycle behavior; profile composition and external package publication remain deployment concerns.

## State CLI

```bash
python -m praxis status --cwd .
python -m praxis enable --cwd .
python -m praxis pause --cwd . --expected-revision 0
python -m praxis task-create --cwd . --expected-revision 0 --host codex --title "Auth design"
python -m praxis recovery-status --cwd . --host dsh --conversation-id session-id
```

State and recovery commands emit JSON for adapter consumption. Mutations require expected revisions where applicable so stale writers cannot overwrite newer state.

## Verified project model CLI

```bash
python -m praxis map-status --cwd .
python -m praxis map-upsert --cwd . \
  --section-id auth \
  --title "Authentication" \
  --content "Owns authentication and session lifecycle." \
  --evidence src/auth.py
python -m praxis map-check --cwd .
python -m praxis map-render --cwd .
```

## Tutor decision CLI

```bash
python -m praxis decision-status --cwd .
python -m praxis decision-create --cwd . \
  --task-id task_... \
  --class engineering \
  --title "Message persistence" \
  --context "Choose the durable source of truth"
python -m praxis decision-select --cwd . \
  --decision-id decision_... \
  --expected-decision-revision 0 \
  --selected-decision "Database source of truth"
python -m praxis decision-render --cwd .
```

`decision-implemented` and `decision-verify` remain separate so implementation cannot masquerade as verification.

## Repository navigation

Start with `Code.md`, then `State.md`, then the relevant document under `Docs/Architecture/` or `Docs/Specs/`, then source and tests.

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall -q praxis tests
python -m unittest tests.test_codex_plugin_manifest tests.test_codex_hooks_manifest tests.test_codex_context tests.test_codex_recovery tests.test_codex_distribution -v
python -m compileall -q plugins/codex praxis
pnpm install --no-frozen-lockfile
pnpm typecheck
pnpm test:dsh
```

Until a real reviewed `pnpm-lock.yaml` is generated by pnpm and committed, the repository intentionally uses `--no-frozen-lockfile`.
