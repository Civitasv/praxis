# Feature-07 Cursor and CodeBuddy Integration

## Objective

Add first-class Praxis support for Cursor and CodeBuddy without introducing MCP or new durable semantics.

Both hosts reuse:

- the shared `skills/praxis/` Tutor Skill;
- the host-neutral `praxis recovery-status` CLI;
- the existing project-local `.praxis/state.json` authority.

Host adapters translate lifecycle events only.

## Supported hosts

### Cursor

Praxis ships a Cursor Plugin manifest at:

```text
.cursor-plugin/plugin.json
```

The Cursor plugin references:

- `./skills/`
- `./plugins/cursor/hooks/hooks.json`

Lifecycle:

- `sessionStart`: run `praxis recovery-status --host cursor` and inject bounded recovery context through Cursor `additional_context`.
- `beforeSubmitPrompt`: run the same CLI to refresh durable/project freshness, but return only `{"continue": true}`.

Cursor's native `beforeSubmitPrompt` output schema does not provide context injection. Feature-07 must not claim per-prompt automatic recovery context that Cursor cannot deliver. The shared Skill/CLI remains the on-demand path during the session.

Cursor project/workspace location comes from `CURSOR_PROJECT_DIR`, with event workspace/cwd fields only as fallback.

Cursor session identity uses `session_id` when present, otherwise `conversation_id`.

The adapter ignores prompt and transcript contents for approval/recovery semantics.

### CodeBuddy

Praxis ships a CodeBuddy Plugin manifest at:

```text
.codebuddy-plugin/plugin.json
```

The manifest references:

- `./skills/`
- `./plugins/codebuddy/hooks/hooks.json`

Lifecycle:

- `SessionStart`: run `praxis recovery-status --host codebuddy` and return nested `hookSpecificOutput.additionalContext`.
- `UserPromptSubmit`: refresh and inject the current recovery context through the same nested response.

CodeBuddy project location comes from event `cwd` when available, otherwise `CODEBUDDY_PROJECT_DIR`.

Session identity uses `session_id`.

Prompt and transcript text are never interpreted as approval.

## Shared adapter layer

Cursor and CodeBuddy wrappers share:

```text
plugins/shared/recovery_hook.py
```

The shared layer:

- invokes `python -m praxis recovery-status` through direct argv;
- uses the current Python executable by default;
- sets the plugin repository root on `PYTHONPATH`;
- uses `shell=False`;
- parses the JSON protocol;
- renders deterministic context capped at 3000 characters;
- flattens free-form task/decision/scope labels before context injection;
- produces a truthful manual-Skill fallback on recovery errors.

No host-specific event names or response envelopes enter `praxis/`.

## Activation and safety

- Installing a Cursor/CodeBuddy plugin does not enable Praxis.
- Uninitialized projects remain silent.
- Paused projects remain paused.
- Recovery never creates/adopts/rebinds tasks.
- Recovery never advances decisions.
- Host prompt/transcript content is not semantic authority.
- Host adapter failure is fail-open; it must not block ordinary coding work.
- No MCP server or MCP configuration is added.

## Packaging

Cursor:

```text
.cursor-plugin/plugin.json
plugins/cursor/hooks/hooks.json
plugins/cursor/hooks/praxis_context.py
```

CodeBuddy:

```text
.codebuddy-plugin/plugin.json
plugins/codebuddy/hooks/hooks.json
plugins/codebuddy/hooks/praxis_context.py
```

Both point to the existing root `skills/` tree.

## Acceptance criteria

1. Cursor and CodeBuddy manifests parse and reference existing shared Skill/hook paths.
2. No copied `skills` or `praxis` tree exists under either host adapter.
3. Cursor `sessionStart` injects bounded enabled-project context.
4. Cursor `beforeSubmitPrompt` refreshes state but does not claim unsupported context injection.
5. CodeBuddy `SessionStart` injects bounded recovery context.
6. CodeBuddy `UserPromptSubmit` injects refreshed bounded recovery context.
7. Exact task recovery uses host-specific identity (`cursor` or `codebuddy`).
8. Prompt/transcript contents cannot become selected/approved state.
9. Uninitialized projects create no `.praxis/`.
10. Recovery failures fail open and never fabricate success.
11. Context remains <=3000 characters and free-form labels are single-line.
12. No MCP files/configuration are introduced by Feature-07.
13. Repository CI validates both host packages on Python 3.10.
14. README remains product-facing; setup specifics live under `Docs/`.

## Non-goals

- MCP server support;
- Cursor cloud-session parity where `sessionStart` is unavailable;
- marketplace publication;
- automatic plugin installation;
- support for Claude Code, Copilot, Gemini CLI, WorkBuddy, or other hosts.
