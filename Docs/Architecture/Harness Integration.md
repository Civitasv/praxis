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
- invoke the Python core through stable JSON/CLI interfaces;
- inject concise recovery guidance;
- register host-native packaging or Skill surfaces.

Host adapters may not:
- own project-state transitions;
- infer approval from resume/compaction;
- fork the durable state model;
- place Harness SDK imports in `praxis/`.

Codex and DSH share the same project-local `.praxis/` records. Cross-host recovery restores persisted facts only; it does not fabricate missing chat context.
