# Praxis DeepSeek Harness / Cordis Integration Design

Date: 2026-10-06
Status: Feature-06 implementation design

## 1. Intent

Feature-06 turns the existing DSH TypeScript seam into a native DeepSeek Harness Cordis plugin.

The plugin must make the shared Praxis Tutor Skill available to DSH, restore bounded durable Praxis context when an Agent is created or resumed, refresh relevant context before user-driven steps, and cleanly disappear when the plugin unloads.

The DSH adapter remains translation-only. Durable project, task, project-model, and decision semantics stay in the neutral Python core.

## 2. Current DSH API baseline

Feature-06 targets the current DeepSeek Harness developer-preview API family:

- `@deepseek-ai/dsh-agent@0.2.1-alpha.1`
- `@deepseek-ai/dsh-llm@0.2.1-alpha.1`
- `@deepseek-ai/dsh-skill@0.2.1-alpha.1`
- `@deepseek-ai/cordis@4.0.5-alpha.1`

The versions are intentionally pinned in repository development validation because DSH APIs are still evolving.

The current lifecycle contract uses awaited serial `agent/created`, not the older observe-only `agent/session-start`.

## 3. Native plugin shape

`plugins/dsh/src/index.ts` becomes a real Cordis plugin:

- exports `name = "praxis-dsh"`;
- exports `inject = ["agents", "skills"]`;
- exports `apply(ctx)`;
- registers the shared Praxis Skill through `ctx.skills.register()`;
- listens to `agent/created`;
- listens to `agent/pre-step`;
- relies on Cordis registration/effect ownership for unload cleanup.

The neutral Python package never imports DSH/Cordis.

## 4. Shared Skill

Feature-06 does not author a second Tutor policy.

The plugin loads the existing repository source:

```text
skills/praxis/SKILL.md
skills/praxis/references/
```

and registers `praxis` as a DSH runtime skill with both model and user invocation enabled.

The DSH skill registration uses the shared skill directory as its resource base so progressive references resolve from the same source files.

Repository-local/plugin-source deployment is in scope. Marketplace/npm publication of a self-contained artifact is not part of Feature-06.

## 5. Neutral recovery snapshot

Feature-06 adds a host-neutral Python recovery query instead of reimplementing durable semantics in TypeScript.

New neutral API:

```text
praxis recovery-status --cwd PATH --host HOST [--conversation-id ID]
```

It returns a compact structured JSON snapshot and, for enabled projects, refreshes Feature-03 staleness before returning.

The snapshot distinguishes:

- uninitialized;
- paused;
- enabled;
- exact task;
- multiple exact tasks;
- one candidate task;
- multiple candidate tasks;
- open decisions and blocked scopes for one resolved/candidate task;
- stale project-model sections;
- unknown project-model sections.

It never creates, adopts, rebinds, selects, implements, verifies, or completes anything.

## 6. Python invocation boundary

The DSH adapter invokes the neutral CLI with `execFile`/equivalent direct argv execution.

No shell interpolation is allowed.

Host/user values such as cwd and session id are separate argv entries.

The child process runs with the Agent workspace as cwd and receives a `PYTHONPATH` prefix pointing at the Praxis package root for repository-local development.

Default interpreter:

- POSIX: `python3`
- Windows: `py -3`

`PRAXIS_PYTHON` may override the interpreter executable path. It is still passed as an executable, never a shell command.

## 7. Agent-created recovery

`agent/created({ agent, source, signal })` is awaited by current DSH before queued work starts.

Praxis uses it to obtain one neutral recovery snapshot for:

- startup;
- resume;
- reserved clear/compact sources when DSH emits them.

Behavior:

- uninitialized -> no injection;
- paused -> concise paused notice;
- enabled -> bounded recovery snapshot;
- neutral CLI failure -> truthful manual-Skill fallback.

Praxis failures must not throw out of `agent/created`, because that would fail DSH Agent creation.

Recovery never implies approval.

## 8. Pre-step synchronization

`agent/pre-step` is the request-time synchronization point.

Praxis participates only when `messages.length > 0`; tool-only continuation steps pass through without spawning recovery work.

The listener:

1. obtains the neutral recovery snapshot;
2. delegates with `next()`;
3. if downstream returns `enter`, appends a Praxis context message only when the rendered snapshot differs from the last one observed for that Agent.

This keeps current context near the user-driven request without injecting the same durable snapshot on every unchanged step.

Praxis never rejects a step.

## 9. Context source and persistence truth

Praxis uses a producer-owned DSH message-source kind:

```text
praxis-dsh
```

declared through `MessageSourceMap` module augmentation.

Model-facing recovery messages use `createUserMessage()`; Praxis never constructs an incomplete message without id/source metadata.

Free-form durable labels are flattened to one line before model-facing context rendering.

Automatic context is deterministically bounded to 3000 characters.

## 10. Recovery selection

Exact recovery requires all of:

- task status is not complete;
- task.host == "dsh";
- task.conversation_id == current Agent/session id.

If there is no exact match:

- zero pending tasks -> none;
- one pending task -> candidate only;
- multiple pending tasks -> bounded candidate list requiring user choice.

No automatic host/session rebinding occurs.

Open decision and blocked-scope summaries are included only when exactly one task is the recovery context.

## 11. Failure behavior

Recoverable failures include:

- Python executable unavailable;
- child process failure;
- invalid child JSON;
- malformed/unsupported/unreadable Praxis state;
- lock timeout;
- project freshness failure;
- cancellation.

A failure does not reset/delete/enable state and does not abort the Agent.

The model-facing fallback says automatic recovery is unavailable and instructs use of the shared Praxis Skill manually.

Cancellation caused by Agent/plugin teardown may return no new context rather than manufacturing a fallback after disposal.

## 12. Unload behavior

Cordis owns listener and skill-registration teardown.

Feature-06 adds no teardown mutation to `.praxis`.

Plugin unload:

- removes the Praxis DSH skill registration;
- removes Agent lifecycle listeners;
- aborts/ends plugin-owned subprocess work through owning signals where available;
- preserves all project-local Praxis state.

## 13. Validation

Repository CI validates:

- neutral `recovery-status` contract on Python 3.10 and 3.13;
- DSH source typechecks against the pinned official developer-preview packages;
- DSH Skill registration contract;
- `agent/created` recovery behavior;
- `agent/pre-step` delegation/current-step context behavior;
- direct argv subprocess invocation and no shell execution;
- real Python CLI subprocess integration from the TypeScript adapter;
- 3000-character deterministic bound;
- no transcript parsing;
- no DSH/Cordis dependency entering `praxis/`;
- unload/disposal registrations remain Cordis-owned.

A live DSH Web UI is not required for CI. Repository CI must not claim profile installation or a particular desktop/runtime deployment was exercised when it was not.

## 14. Non-goals

Feature-06 does not implement:

- DSH UI panels;
- custom model-facing tools;
- transcript/event-log parsing for approval;
- automatic task creation/adoption/rebinding;
- decision auto-selection;
- DSH profile mutation on the user's behalf;
- npm/marketplace publication;
- backend services or telemetry;
- a second Tutor Skill copy.

## 15. Acceptance scenarios

1. loading the plugin registers exactly one shared Praxis Skill;
2. plugin unload registration does not delete `.praxis`;
3. uninitialized project produces no recovery context and no state directory;
4. paused project remains paused;
5. startup/resume Agent creation receives bounded context before the first turn;
6. a neutral recovery failure does not fail Agent creation;
7. exact DSH session task is identified without lifecycle mutation;
8. one unmatched task is only a candidate;
9. several unmatched tasks require user choice;
10. open decisions/blocked scopes are scoped to one recovery task;
11. stale and unknown project sections are surfaced;
12. user-driven pre-step refresh delegates and adds changed context to an `enter` decision;
13. unchanged pre-step state does not duplicate context;
14. tool-only continuation steps do no recovery subprocess work;
15. context is <=3000 characters and free-form labels cannot create new structural lines;
16. subprocess execution uses argv and `shell: false`;
17. the adapter never reads transcript history or infers approval from prompt text;
18. neutral Python core contains no DSH/Cordis imports.
