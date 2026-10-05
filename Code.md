# Praxis Code Map

| Area | Location | Responsibility |
| --- | --- | --- |
| Neutral Python core | `praxis/` | Shared durable state and host-neutral semantics |
| Shared Praxis Skill | `skills/praxis/` | Tutor behavior, decision policy, recovery, repository-understanding instructions |
| Codex adapter | `plugins/codex/` | Codex packaging, hooks, lifecycle translation |
| DSH adapter | `plugins/dsh/` | DeepSeek Harness/Cordis lifecycle translation and distribution |
| Architecture | `Docs/Architecture/` | Stable system boundaries and reasoning |
| Feature specs | `Docs/Specs/` | Acceptance contracts for incremental implementation |
| Development | `Docs/Development/` | Validation and distribution procedures |
| Tests | `tests/`, `plugins/dsh/test/` | Executable repository and behavior contracts |

## Dependency direction

```text
shared Skill / host adapters
          |
          v
      Praxis semantics
          |
          v
       praxis/
```

Harness SDK dependencies terminate in their adapter. The neutral Python core must not import Codex, DeepSeek Harness, or Cordis APIs.
