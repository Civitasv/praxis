# Praxis Current State

## Feature status

Feature-01: Implemented
- Repository contracts: Implemented
- Python neutral-core executable baseline: Implemented
- DSH TypeScript boundary: Implemented
- GitHub Actions CI: Implemented

Feature-02: Pending — Praxis state core
Feature-03: Pending — Verified project model
Feature-04: Pending — Tutor decision loop
Feature-05: Pending — Codex integration
Feature-06: Pending — DSH integration

## Implemented foundation

- `AGENTS.md`, `Code.md`, `State.md`, Architecture/Spec/Development docs define the AI-native repository contract.
- `praxis/` exposes the standard-library Python baseline and `python -m praxis --version`.
- generated project-local `.praxis/` state is ignored by the repository.
- `plugins/dsh/` exposes only a TypeScript adapter seam; DSH runtime behavior is not implemented yet.
- `.github/workflows/ci.yml` validates Python 3.10/3.13 and the TypeScript/DSH seam on pull requests and pushes to `master`.

## Validation contract

Feature-01 validation commands are:

```bash
python -m unittest discover -s tests -v
python -m compileall -q praxis tests
pnpm typecheck
pnpm test:dsh
```

A check is Green only when it actually runs successfully. GitHub Actions is authoritative for the minimum Python 3.10 and pnpm/TypeScript environment.

## Not implemented yet

Praxis does not yet provide durable `.praxis/state.json` semantics, task concurrency/CAS, verified project fingerprints, Tutor decision behavior, Codex lifecycle hooks, or native DSH/Cordis runtime integration. Those remain Features 02–06.
