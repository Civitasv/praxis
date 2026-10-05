# Feature-01 Repository Foundation

## Objective

Establish the repository, execution baselines, host boundaries, validation discipline, and AI-native navigation that later Praxis features depend on.

## Scope

1. Repository contracts: `AGENTS.md`, `Code.md`, `State.md`, Architecture/Spec/Development docs.
2. Python 3.10+ neutral-core executable baseline.
3. TypeScript DSH adapter package seam without DSH runtime behavior.
4. GitHub Actions validation for Python and TypeScript baselines.
5. Accurate foundation-state closure.

## Acceptance criteria

### AC-001 — AI-native navigation
Agents can start from `Code.md`, find the relevant contract, and distinguish current implementation truth from future design.

### AC-002 — neutral Python boundary
`praxis/` imports no Codex, DeepSeek Harness, Cordis, or adapter-specific SDK.

### AC-003 — Python baseline
`python -m praxis --version` works on Python 3.10+ and the package uses no third-party runtime dependency.

### AC-004 — DSH seam
A minimal TypeScript workspace exposes the DSH adapter boundary without implementing Tutor/state semantics.

### AC-005 — CI
Pull requests and pushes to `master` execute Python tests/compile validation plus TypeScript typecheck/tests. Python 3.10 is exercised explicitly.

### AC-006 — generated state boundary
Generated project-local `.praxis/` state is ignored and never treated as repository source.

## Non-goals

Feature-01 does not implement the durable state engine, verified project model, Tutor decision loop, Codex hooks, DSH runtime integration, backend services, telemetry, model calls, or UI.
