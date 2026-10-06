# Feature-06 DSH Integration

## Objective

Implement a native DeepSeek Harness / Cordis adapter that exposes the shared Praxis Tutor Skill and synchronizes durable Praxis recovery context through current DSH Agent lifecycle events while leaving all durable semantics in the neutral Python core.

Detailed rationale: `docs/superpowers/specs/2026-10-06-dsh-integration-design.md`.

## Host baseline

Feature-06 supports two explicitly bounded API families: DSH `0.2.0-rc.2` with Cordis `4.0.4`, and the following developer-preview family:

- `@deepseek-ai/dsh-agent@0.2.1-alpha.1`
- `@deepseek-ai/dsh-llm@0.2.1-alpha.1`
- `@deepseek-ai/dsh-skill@0.2.1-alpha.1`
- `@deepseek-ai/cordis@4.0.5-alpha.1`

Lifecycle initialization is `agent/created` for both families. Root and adapter peer dependencies allow only these two tested versions; CI typechecks and runs the integration suite against each family.

## Neutral recovery API

Add:

```text
praxis recovery-status --cwd PATH --host HOST [--conversation-id ID]
```

The command is host-neutral, refreshes project-model freshness only for enabled state, and returns compact JSON describing activation, task recovery resolution, open decisions/blocked scopes, and stale/unknown project sections.

It never creates or adopts tasks and never advances decision lifecycle.

## DSH plugin contract

`plugins/dsh/src/index.ts` exports:

- `adapterMetadata` (existing compatibility);
- `name = "praxis-dsh"`;
- `inject = ["agents", "skills"]`;
- `apply(ctx)`.

The plugin registers the shared Praxis Skill and lifecycle listeners.

## Skill contract

The runtime skill:

- name: `praxis`;
- uses the existing `skills/praxis/SKILL.md` content;
- exposes the shared skill directory as resource base;
- is model-invocable and user-invocable;
- is not copied into `plugins/dsh/`.

## Agent lifecycle contract

### `agent/created`

For startup/resume and any future clear/compact source emitted by DSH:

- uninitialized -> silent;
- paused -> paused notice;
- enabled -> recovery context;
- failure -> manual-Skill fallback;
- no Praxis failure may reject Agent creation.

### `agent/pre-step`

Only user-driven steps (`messages.length > 0`) synchronize.

The listener always delegates. It may append one Praxis context message to a downstream `enter` decision when the snapshot changed.

It never rejects or rewrites user messages and does no semantic approval parsing.

## Child-process boundary

The adapter invokes the neutral CLI using direct argv execution with `shell: false`.

Cwd and Agent/session id are never interpolated into a command string.

Repository-local execution prepends the Praxis repository root to `PYTHONPATH`.

## Message contract

Praxis declares a producer-owned `praxis-dsh` message-source kind and creates model-facing context with the official `createUserMessage` helper.

Automatic context is deterministic and <=3000 characters.

Free-form labels are flattened before rendering.

## Recovery truth

Exact task recovery requires `host == "dsh"`, matching conversation id, and non-complete status.

Absent an exact match, one pending task is a candidate only and multiple pending tasks require user choice.

Open decisions and blocked scopes are surfaced only for one exact/candidate task.

Recovery never means approval, implementation, verification, completion, or rebinding.

## Cleanup

Cordis lifecycle ownership removes listeners and skill registration on unload.

No unload path deletes or edits `.praxis`.

## CI

Feature-06 must add/extend tests proving:

- neutral recovery-status Python behavior;
- official DSH type compatibility at pinned versions;
- Skill registration;
- agent-created recovery;
- pre-step delegation + changed-context injection;
- no duplicate unchanged context;
- no work for empty-message continuation steps;
- direct argv subprocess behavior;
- real adapter -> Python CLI integration;
- context bound/sanitization;
- neutral-core dependency boundary.

## Non-goals

No DSH UI, no transcript parsing, no task auto-adoption, no decision auto-selection, no profile mutation, no npm/marketplace publication, no backend/telemetry.
