# Praxis

**Build with AI. Keep the judgment.**

Praxis is an AI tutor for building software with coding agents. It lets AI handle execution while keeping the human involved in consequential decisions, tradeoffs, and feedback that build engineering judgment.

## V1 architecture

Praxis uses a Python 3.10+ standard-library neutral core, a shared English Skill, and thin Codex and DeepSeek Harness adapters.

```text
Codex adapter ─┐
               ├─ shared Praxis semantics ─→ project-local `.praxis/` state
DSH adapter ───┘
```

The neutral core must remain independent of Harness SDKs.

## Repository navigation

Start with `Code.md`, then the relevant document under `Docs/Architecture/` or `Docs/Specs/`, then source and tests. `State.md` records what is actually implemented.

## Development status

Feature-01 repository foundation is in progress. Runtime state, verified project understanding, Tutor behavior, and host integrations are intentionally not implemented yet.
