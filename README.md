# Praxis

**Build with AI. Keep the judgment.**

Praxis is an AI tutor for building software with coding agents. It lets AI handle execution while keeping the human involved in consequential decisions, tradeoffs, and feedback that build engineering judgment.

## Architecture direction

Praxis uses a Python 3.10+ standard-library neutral core, a shared English Tutor Skill, and thin host adapters.

```text
host adapter ──→ shared Praxis Tutor Skill
                       |
                       v
                neutral Python core
                       |
                       v
              project-local `.praxis/`
```

Harness-specific APIs must not enter the neutral Python core.

## Current status

Features 01–04 are implemented: the AI-native repository foundation, Praxis State Core, Verified Project Model, and host-neutral Tutor Decision Loop.

Feature-02 provides project-boundary discovery, symlink-safe project state paths, format-versioned `.praxis/state.json`, bounded write locking, atomic replacement, compare-and-swap revisions, durable multi-task records, pause/resume state, and a JSON CLI contract for host adapters.

Feature-03 adds machine-owned source fingerprints, section-level compare-and-swap for the verified project model, incremental stale detection, and deterministic `.praxis/code.md` recovery. `state.json.project_model` is authoritative; `code.md` is a rebuildable human/model-readable projection rather than a second source of truth.

Feature-04 adds durable decision provenance and decision-level compare-and-swap. Engineering/architectural decisions are linked to tasks and keep user proposal, verified constraints, Praxis challenge, selected decision, user reasoning, implementation result, and verification separate. The lifecycle is:

```text
open -> selected -> implemented -> verified
```

`superseded` and `abandoned` are explicit terminal alternatives. An AI recommendation, restart, recovery, or silence cannot turn an open choice into a selected one.

Authoritative decision records live in `state.json.decisions`. `.praxis/decisions.md` is a deterministic rebuildable projection, just like `.praxis/code.md`; neither Markdown file is parsed back into machine state. Different decisions use decision-level revisions so unrelated work can progress despite global state revision changes.

The shared Praxis Tutor Skill under `skills/praxis/` encodes the host-neutral behavior loop: inspect verified facts, surface consequential choices, teach or challenge when needed, record explicit agreement, implement, verify, and connect the observed result back to the decision. Mechanical work proceeds without unnecessary confirmation, and an unresolved choice blocks only its declared dependent scopes.

Installing Praxis still does not enable a project. Explicit `praxis enable --cwd <path>` creates project-local state. Read-only status commands do not create state in an uninitialized project.

Feature-05 and Feature-06 are still pending. Automatic host lifecycle activation, startup/compaction recovery injection, and native adapter integration are not yet implemented; Feature-05 will provide the Codex integration and Feature-06 the native DSH integration. Feature-04 establishes the neutral state and Tutor policy those adapters will consume.

## State CLI

```bash
python -m praxis status --cwd .
python -m praxis enable --cwd .
python -m praxis pause --cwd . --expected-revision 0
python -m praxis task-create --cwd . --expected-revision 0 --host codex --title "Auth design"
```

State commands emit JSON for adapter consumption. Mutations require the caller's expected revision where applicable so stale writers cannot overwrite newer state.

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

Project-model writes use section-level revisions. Source fingerprints and stale reasons are produced by the neutral core rather than supplied by the model.

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

Decision mutations use decision-level revisions for targeted concurrency. `decision-implemented` and `decision-verify` deliberately remain separate so implementation cannot masquerade as verification.

## Repository navigation

Start with `Code.md`, then `State.md`, then the relevant document under `Docs/Architecture/` or `Docs/Specs/`, then source and tests.

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall -q praxis tests
pnpm install --no-frozen-lockfile
pnpm typecheck
pnpm test:dsh
```

Until a real reviewed `pnpm-lock.yaml` is generated by pnpm and committed, the repository intentionally uses `--no-frozen-lockfile`.
