# Harness Integration

## Boundary

Praxis supports multiple coding-agent hosts without making any host the product runtime.

```text
praxis/                 # neutral Python semantics
skills/praxis/          # shared behavior
plugins/codex/          # Codex-only lifecycle/package code
plugins/dsh/            # DSH/Cordis-only lifecycle/package code
```

Host adapters may:
- resolve host session identity;
- translate lifecycle events;
- invoke/reuse the neutral Python core;
- inject concise recovery guidance;
- register host-native packaging or Skill surfaces.

Host adapters may not:
- own project-state transitions;
- infer approval from resume/compaction/prompt text;
- fork the durable state model;
- place Harness SDK imports in `praxis/`;
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

Codex and DSH share the same project-local `.praxis/` records. Cross-host recovery restores persisted facts only; it does not fabricate missing chat context or mutate lifecycle merely because a host session resumed.

## Distribution boundary

Repository CI validates both adapters without claiming external deployment. Feature-06 does not install `@praxis/plugin-dsh` into a DSH profile, mutate profile configuration, or claim npm publication. Host/package installation remains a separate user/deployment action.
