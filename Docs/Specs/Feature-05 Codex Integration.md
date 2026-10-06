# Feature-05 Codex Integration

## Objective

Integrate the existing Praxis neutral core and shared Tutor Skill with Codex lifecycle surfaces so an explicitly enabled project can recover bounded durable task/decision/project context across startup, resume, clear, compact, and prompt submission without transcript parsing or implicit approval.

The detailed design rationale is recorded in `docs/superpowers/specs/2026-10-06-codex-integration-design.md`.

## Authority

Feature-05 is a host adapter only.

- `state.json` remains authoritative for activation, tasks, project-model metadata, and decisions.
- `skills/praxis/` remains the shared Tutor behavior source.
- `praxis/` remains the neutral domain/state implementation.
- Codex adapter files may translate host events and emit context, but may not own durable task/decision/project semantics.

## Package layout

Feature-05 creates:

```text
plugin.json
.codex-plugin/plugin.json
plugins/codex/hooks/hooks.json
plugins/codex/hooks/praxis_context.py
```

The existing `skills/praxis/` and `praxis/` trees are referenced in place and are not copied into `plugins/codex/`.

The shared skills directory also exposes `praxis-enable`, `praxis-disable`, and
`praxis-status` as direct skill-picker entries. Each runs the corresponding
existing neutral CLI command with `--cwd .` and reports its actual result.
The shared Tutor skill provides only Tutor behavior for explicitly enabled projects.

## Lifecycle contract

Codex integration handles:

- `SessionStart` with startup/resume/clear/compact sources;
- `UserPromptSubmit`.

Both lifecycle surfaces route to the same thin adapter.

The adapter does not read transcript history.

## Activation contract

### AC-001 — install is not enable

Plugin/package installation creates no project-local Praxis state.

### AC-002 — uninitialized is silent

If no valid project Praxis state exists, lifecycle hooks emit no Tutor recovery context and do not create `.praxis/`.

### AC-003 — paused remains paused

If `enabled=false`, hooks do not run Tutor recovery behavior or mutate state. A concise paused notice is allowed.

### AC-004 — enabled projects synchronize

Enabled projects may refresh machine-owned project freshness metadata before recovery context is constructed.

## Project freshness

Lifecycle synchronization may invoke the existing Feature-03 stale check.

It must not modify semantic project-model section content or automatically clear a previously stale section to verified.

## Session/task recovery

The adapter prefers an exact active Codex task match using current session identity.

Exact recovery does not advance task stage/status.

If no exact match exists:

- zero plausible pending tasks -> no automatic task creation;
- one plausible task -> candidate only;
- multiple plausible tasks -> bounded candidate list plus instruction to ask the user which task to continue.

Automatic adoption/rebinding is not allowed.

## Decision recovery

Open decisions remain open.

Recovery cannot:

- select a decision;
- infer approval;
- convert selected to implemented;
- convert implemented to verified;
- invent user reasoning.

Open decision titles/ids and blocked scopes may be included in bounded context.

## Context contract

Automatic context is a summary, not a state dump.

It may include:

- activation state;
- recovered/candidate task summary;
- open decision summary;
- blocked scopes;
- stale/unknown project-model sections;
- recovery-is-not-approval reminder.

It must omit:

- full transcripts;
- full source code;
- full `code.md`;
- full `decisions.md`;
- credentials/secrets.

Injected automatic context is deterministically bounded to at most 3000 characters.

## Prompt handling

`UserPromptSubmit` must not parse prompt text to infer semantic approval or mutate decision lifecycle.

The prompt may be ignored by the adapter except as host-provided data that is deliberately not interpreted.

## Failure and fallback

Automatic recovery failures are reported truthfully and must not fabricate successful recovery.

The adapter never resets/deletes project state or bypasses host trust controls.

When automatic hooks cannot run, the shared Praxis Skill remains the documented manual fallback.

## Delivery diagnostics and project fallback

`praxis doctor --cwd .` reports activation, the managed AGENTS.md block, recent hook observations, and adapter diagnostics. `--plugin-root` selects the installed plugin checkout when the CLI's package does not contain adapters; `--host-config` selects a config file for inspection. Host-specific configuration and probe semantics remain in the adapter, reached through direct argv subprocess execution. The neutral core does not import host APIs.

The Codex adapter checks its manifest/hook declarations and executes the configured launcher against its static script with a synthetic read-only probe. The probe does not refresh project state or write invocation observations. Script execution, host configuration clues, observed invocation, and model delivery are distinct results. A user config file is not a complete view of managed/project policy; trust entries do not prove that the current definition hash is trusted. On Python 3.10, TOML inspection is reported unavailable rather than adding a runtime dependency.

Normal valid hooks store the latest observation per event under `.praxis/hook-observations.json`, outside authoritative domain state. Records contain event/source, UTC timestamp, project/plugin paths, and outcome only. They exclude prompts, transcripts, session ids, recovered content, and exception messages. A started record without completion can indicate interruption. Output success means the script emitted context, not that the host delivered it to the model. Manual invocations are not distinguishable from host invocations. Uninitialized projects create no diagnostics directory. Paused hooks may record diagnostics but cannot mutate domain state or resume tutoring. Failed diagnostic writes are reported on stderr without suppressing context output.

`praxis enable --cwd . --agents-fallback` explicitly installs a removable block in project-root AGENTS.md. The enable Skill announces this before executing and reports the actual results; declining the block uses ordinary enable. Existing user instructions are preserved, and unsafe files or malformed/duplicate markers are rejected. A failed fallback write after activation explicitly reports that activation succeeded but fallback persistence failed. Disable/pause leaves the block in place: its live state check keeps tutoring inactive. `praxis agents-fallback --cwd . --remove` removes only the managed region.

The active injection starts with the instruction to load the Tutor Skill before proposing solutions or editing, distinguishes preferences from implementation selection, and permits delegated mechanical work without repeated confirmation. It adds no edit approval interceptor or semantic consent parser.

Repository tests cover these script and persistence contracts. Live-host acceptance is separately documented in `Docs/Development/Validation.md` and remains Pending until observed in the host. Plugin installation does not grant hook trust; no diagnostic or fallback action changes the host's trust settings.

## Manifest contract

The repository root `plugin.json` is canonical.

Its `extensions.com.openai` object contains the complete OpenAI-specific overlay for consumers that support it. It is not merged with the compatibility overlay.

For Codex Desktop 0.160.0, omit the Agent Plugins `$schema` declaration: a local `hooks/list` probe returned zero hooks with the declaration and two untrusted hooks without it, using identical hook files. This host loads the existing compatibility manifest when the declaration is absent. Keep both hook references identical. Restore the schema only after verifying discovery on supported hosts.

`.codex-plugin/plugin.json` is a compatibility manifest describing the same shared Skill and hook package for fallback consumers.

Tests verify:

- both manifests parse;
- referenced repository-relative paths exist;
- package identity/surfaces are consistent;
- the canonical package does not duplicate Skill/core sources.

## Hook declaration contract

`plugins/codex/hooks/hooks.json` declares only the intended Feature-05 lifecycle hooks.

It must:

- match SessionStart `source` exactly across startup/resume/clear/compact;
- cover UserPromptSubmit without relying on prompt matching;
- invoke the thin Python adapter through a static plugin-root-based command;
- never interpolate prompt/cwd/session/event values into the command string;
- declare a positive `additionalContextLimit`;
- provide a Windows command override when required for portable execution.

## Adapter contract

`plugins/codex/hooks/praxis_context.py`:

- accepts Codex lifecycle payload from stdin;
- uses only documented fields needed by Feature-05: `hook_event_name`, `cwd`, `session_id`, and SessionStart `source`;
- deliberately ignores `transcript_path`;
- validates enough input to operate safely;
- discovers the current Praxis project through neutral project rules;
- reads neutral state;
- for enabled state, refreshes project freshness through existing neutral behavior;
- selects exact/candidate task context without mutating recovery lifecycle;
- summarizes open decisions and blocked scopes;
- emits deterministic bounded additional context;
- emits structured Codex hook JSON using `hookSpecificOutput.hookEventName` plus `additionalContext`;
- emits a truthful manual-fallback notice on recoverable automatic-recovery failure.

It must not import a Codex SDK into `praxis/` or add host-specific state fields solely for Codex.

## Distribution/CI

Feature-05 adds repository tests/CI validation for:

- plugin manifests;
- hook declaration;
- Python hook adapter stdin/stdout behavior;
- context bound/truncation;
- activation/recovery/fallback scenarios;
- neutral-core Codex dependency boundary;
- continued Python 3.10/3.13 checks;
- continued DSH TypeScript seam checks.

A live Codex host is not required for repository CI. Any validation requiring unavailable host tooling remains explicitly Pending rather than assumed Green.

## Acceptance criteria

### AC-005 — startup/resume/clear/compact recovery

Each declared SessionStart source can generate bounded enabled-project context without lifecycle mutation.

### AC-006 — prompt synchronization

UserPromptSubmit can synchronize durable context/freshness but cannot interpret prompt text as approval.

### AC-007 — exact session recovery

An exact active Codex task can be identified from host/session linkage without silently changing state.

### AC-008 — ambiguous recovery remains ambiguous

One unmatched task is a candidate; several plausible tasks require a user choice.

### AC-009 — decision lifecycle stays honest

Open/selected/implemented/verified distinctions survive host recovery unchanged.

### AC-010 — stale project facts are surfaced

Changed evidence may mark affected project-model sections stale before they are summarized.

### AC-011 — automatic context is bounded

The adapter output remains deterministic and <= 3000 characters regardless of durable-state size.

### AC-012 — transcript-independent

Feature-05 does not read or parse transcript history.

### AC-013 — truthful fallback

Unreadable/corrupt/unsupported Praxis state or automatic hook failure produces no fabricated recovered facts and points to manual Skill use when possible.

### AC-014 — neutral core remains host-neutral

No Codex-specific imports/APIs are introduced under `praxis/`.

## Non-goals

Feature-05 does not include:

- DSH/Cordis lifecycle integration;
- prompt semantic approval parsing;
- transcript parsing;
- automatic task creation/adoption/rebinding;
- automatic decision selection;
- Codex trust bypass or config mutation;
- MCP/server architecture;
- marketplace publication;
- backend/telemetry.

## Implementation order

1. Codex plugin manifest/package contract.
2. Hook declaration contract.
3. Thin adapter input/output and activation behavior.
4. Enabled-project freshness and exact task recovery.
5. Candidate-task and decision/blocking recovery summaries.
6. Deterministic bounded context and failure fallback.
7. Codex package/distribution CI validation.
8. Repository closure and final CI.
