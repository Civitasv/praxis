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

Codex and DSH share the same project-local `.praxis/` records. Cross-host recovery restores persisted facts only; it does not fabricate missing chat context or mutate lifecycle merely because a host session resumed.

## DSH — Feature-06 boundary

The existing TypeScript DSH seam remains a boundary placeholder. Native DSH/Cordis lifecycle registration and cleanup remain Feature-06.
