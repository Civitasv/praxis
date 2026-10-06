# Harness Integration

## Boundary

Praxis supports multiple coding-agent hosts without making any host the product runtime.

```text
praxis/                 # neutral Python semantics
skills/praxis/          # shared behavior
plugins/codex/          # Codex-only lifecycle/package code
plugins/dsh/            # DSH/Cordis-only lifecycle/package code
plugins/cursor/         # Cursor-only hook adapter
plugins/codebuddy/      # CodeBuddy-only hook adapter
plugins/shared/         # host-adapter recovery CLI bridge
```

Host adapters may:
- resolve host session identity;
- translate lifecycle events;
- invoke/reuse the neutral Python core or CLI;
- inject concise recovery guidance;
- register host-native packaging or Skill surfaces.

Host adapters may not:
- own project-state transitions;
- infer approval from resume/compaction/prompt text;
- fork the durable state model;
- place host SDK imports in `praxis/`;
- depend on transcript formats for correctness.

## Codex — Feature-05

The Codex adapter is **translation-only**. It maps Codex lifecycle metadata onto existing neutral Praxis semantics.

`SessionStart` covers startup, resume, clear, and compact. `UserPromptSubmit` refreshes the same bounded durable context without interpreting the submitted prompt as approval.

Codex recovery is **transcript-independent**: `transcript_path` is deliberately ignored. Exact session task linkage, candidate tasks, open decisions, blocked scopes, and project-model freshness all come from authoritative project-local Praxis state.

Automatic context is bounded. Hook failures degrade to a truthful **manual** shared-Skill fallback. Plugin installation or availability never auto-enables a project, and Codex hook trust remains a host policy decision.

## DSH — Feature-06

The DSH adapter is also **translation-only**. DSH/Cordis APIs remain under `plugins/dsh/`; the neutral `praxis/` package has no DeepSeek Harness or Cordis dependency.

Feature-06 targets the current preview API family `@deepseek-ai/dsh-agent@0.2.1-alpha.1`, `@deepseek-ai/dsh-llm@0.2.1-alpha.1`, `@deepseek-ai/dsh-skill@0.2.1-alpha.1`, and `@deepseek-ai/cordis@4.0.5-alpha.1`.

The plugin registers the existing shared Praxis Skill through `ctx.skills.register()`. The Skill body remains single-source at `skills/praxis/SKILL.md`.

`agent/created` is the session lifecycle initialization edge. Praxis calls the host-neutral `recovery-status` CLI, renders bounded context, and uses `agent.inject()` with a producer-owned `praxis-dsh` instructions source. Recovery errors are contained and converted to manual-Skill fallback context rather than rejecting Agent creation.

`agent/pre-step` synchronizes only user-driven steps. It calls the downstream decision first; empty-message continuations are delegated unchanged, downstream rejects remain rejects, and changed Praxis context is appended only to downstream `enter` messages. A per-agent digest suppresses unchanged duplicate context.

The TypeScript subprocess bridge uses **direct argv** execution with `execFile` and `shell: false`. Project cwd and DSH session id are separate arguments, never shell-interpolated input. The neutral Python recovery snapshot remains responsible for exact/candidate task resolution, open decisions, blocked scopes, and stale/unknown project facts.

Cordis owns cleanup. Disposing the plugin removes listeners and the Skill contribution without touching `.praxis`.

## Cursor — Feature-07

Cursor integration is **translation-only** and uses the existing `praxis recovery-status` CLI through `plugins/shared/recovery_hook.py`.

The Cursor package is declared by `.cursor-plugin/plugin.json`, references the root `skills/` directory, and loads `plugins/cursor/hooks/hooks.json`.

`sessionStart` resolves the project from `CURSOR_PROJECT_DIR`, uses Cursor session/conversation identity, and injects bounded recovery context through Cursor's documented `additional_context` response.

Cursor's native `beforeSubmitPrompt` currently does not support per-prompt context injection. Praxis still runs `recovery-status` there so project freshness is synchronized, but returns only `continue: true`; current recovery context remains available through the shared Skill/CLI rather than an invented hook field.

Prompt and transcript contents are ignored for approval semantics. Hook failures fail open. Cursor cloud environments where `sessionStart` is unavailable rely on the shared Skill/CLI path.

**No MCP** server or MCP configuration is part of the Cursor integration.

### Cursor local setup

Praxis is not published to the Cursor Marketplace yet. For local use, place a **copy** of the Praxis repository at:

```text
~/.cursor/plugins/local/praxis
```

and restart Cursor (or run **Developer: Reload Window**), then confirm Praxis appears in Customize with the Cursor-plugin components enabled. Cursor's local-plugin loader does not follow a symlink whose target lives outside `~/.cursor/plugins/local/`, so copying the checkout is the reliable development path.

The repository also contains the portable root `plugin.json` used by Codex/Agent Plugins. Cursor-specific hooks are declared by `.cursor-plugin/plugin.json`; verify the Cursor-plugin form is active when testing Feature-07.

## CodeBuddy — Feature-07

CodeBuddy integration is **translation-only** and uses the same shared Python recovery bridge.

The package is declared by `.codebuddy-plugin/plugin.json`, reuses root `skills/`, and loads `plugins/codebuddy/hooks/hooks.json`.

`SessionStart` and `UserPromptSubmit` both run `praxis recovery-status --host codebuddy`. When Praxis is enabled, the adapter injects bounded context through CodeBuddy's documented `hookSpecificOutput.additionalContext` response. `UserPromptSubmit` also returns `continue: true`, so Praxis never blocks ordinary prompt processing.

Prompt/transcript contents are not parsed as approval. Recovery failures degrade to the manual shared-Skill fallback while remaining fail-open.

**No MCP** server or MCP configuration is part of the CodeBuddy integration.

### CodeBuddy local setup

CodeBuddy can load the Praxis checkout directly for a session:

```bash
codebuddy --plugin-dir /path/to/praxis
```

Use `/reload-plugins` after changing the checkout. Marketplace installation is not claimed by Feature-07.

## Cross-host state

Codex, DSH, Cursor, and CodeBuddy share the same project-local `.praxis/` records. Cross-host recovery restores persisted facts only; it does not fabricate missing chat context or mutate lifecycle merely because a host session resumed.

## Distribution boundary

Repository CI validates host adapters without claiming external deployment or marketplace publication. Host installation, enablement, and trust remain separate user/deployment actions.
