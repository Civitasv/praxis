# Repository Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish Praxis as an AI-native, Harness-neutral repository with executable Python/TypeScript baselines, explicit architecture boundaries, and CI that verifies the foundation on every pull request and push to `master`.

**Architecture:** Praxis keeps durable product semantics in a Python 3.10+ standard-library neutral core. Codex and DeepSeek Harness integrations live outside that core; the DSH side uses a minimal TypeScript package so Cordis/DSH-native lifecycle code can evolve without leaking into Python. Repository guidance follows the Orven pattern: `AGENTS.md` defines invariants, `Code.md` is the navigation map, `State.md` records current implementation truth, and `Docs/` contains architecture/spec/validation material.

**Tech Stack:** Python 3.10+ standard library and `unittest`; TypeScript 6 / Node 22 / pnpm 11 for the DSH package; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-05-praxis-repository-foundation-design.md`

## Global Constraints

- Shared Praxis Skill and companion instructions are written in English.
- User-facing conversation, architecture explanations, and decision records follow the user's language by default.
- Python baseline is 3.10+ and the neutral core has no third-party runtime dependencies.
- Harness-specific APIs must not enter the neutral Python core.
- Codex and DSH adapters must remain thin translations over shared semantics.
- Project-local runtime state will live under `.praxis/`; this repository must not commit generated runtime state.
- Installing Praxis must not implicitly enable project mode.
- GitHub Actions is the CI source of truth for this repository foundation.
- A check is not Green unless it was actually executed successfully.
- V1 does not add a backend, database, telemetry, external model calls, vector storage, custom UI, quizzes, or understanding scores.

## Review Focus

1. **Python 3.10 compatibility** — syntax and standard-library APIs must work on the minimum supported version; CI must exercise Python 3.10 explicitly.
2. **Harness leakage** — a neutral-core import scan must fail if Codex/DSH package names appear in `praxis/` Python imports.
3. **Missing Node dependencies / lockfile bootstrap** — CI may use `pnpm install --no-frozen-lockfile` until a real pnpm lockfile is generated and committed; no hand-written lockfile.
4. **Generated Praxis state** — `.praxis/` must be ignored and tests must assert the shipped repository never treats it as source.
5. **False Green claims** — the validation docs and PR template must require unrun checks to be marked pending rather than assumed successful.

---

### Task 1: AI-native repository guidance and architecture map

**Files:**
- Create: `AGENTS.md`
- Create: `Code.md`
- Create: `State.md`
- Create: `README.md`
- Create: `Docs/Architecture/Overview.md`
- Create: `Docs/Architecture/Tutor Model.md`
- Create: `Docs/Architecture/Harness Integration.md`
- Create: `Docs/Development/Validation.md`
- Create: `Docs/Specs/Feature-01 Repository Foundation.md`
- Create: `.github/pull_request_template.md`
- Test: `tests/test_repository_contract.py`

**Interfaces:**
- Consumes: repository-foundation design spec.
- Produces: stable navigation and invariants future agents must read before implementation.

- [ ] **Step 1: Write the failing repository-contract tests**

Create `tests/test_repository_contract.py` with tests that assert:
- `AGENTS.md`, `Code.md`, `State.md`, `README.md`, Feature-01, architecture overview, validation guide, and PR template exist;
- `AGENTS.md` states that Tutor judgment is the product center, restoration is not approval, neutral Python code cannot depend on Harness SDKs, and Green requires executed checks;
- `Code.md` names the Python neutral core, shared Skill, Codex adapter, and DSH adapter locations;
- `State.md` initially labels only the repository foundation as implemented and later features as pending;
- validation guidance explicitly requires Python 3.10 and GitHub Actions.

- [ ] **Step 2: Run the tests and verify RED**

Run: `python -m unittest tests.test_repository_contract -v`

Expected: FAIL because the repository contract files do not exist yet.

- [ ] **Step 3: Create the repository guidance files**

Write the files above with concise contracts derived from the design spec. `AGENTS.md` must direct agents to read `Code.md`, then the relevant Architecture/Spec, then source/tests. `State.md` records implementation truth only, not aspirations.

- [ ] **Step 4: Run the repository-contract tests and verify GREEN**

Run: `python -m unittest tests.test_repository_contract -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `docs: establish praxis repository contracts`

---

### Task 2: Python neutral-core executable baseline

**Files:**
- Create: `praxis/__init__.py`
- Create: `praxis/__main__.py`
- Create: `praxis/cli.py`
- Create: `tests/test_cli.py`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.editorconfig`

**Interfaces:**
- Consumes: repository invariants from Task 1.
- Produces: `praxis.cli.main(argv: Sequence[str] | None = None) -> int` and `python -m praxis --version` as the first executable neutral-core contract.

- [ ] **Step 1: Write failing CLI tests**

Create tests asserting:
- `python -m praxis --version` exits 0 and prints a Praxis version string;
- invoking the CLI with an unknown argument returns a non-zero exit code;
- `.gitignore` contains `.praxis/`;
- Python files under `praxis/` do not import modules containing `deepseek`, `cordis`, `codex`, or Harness adapter package paths.

- [ ] **Step 2: Run the tests and verify RED**

Run: `python -m unittest tests.test_cli -v`

Expected: FAIL because the package/CLI does not exist.

- [ ] **Step 3: Implement the minimal neutral-core baseline**

Implement `praxis.cli.main(argv: Sequence[str] | None = None) -> int` using only the Python standard library and expose it from `praxis.__main__`. Set the package version to an initial pre-release value suitable for an unreleased repository foundation.

- [ ] **Step 4: Run CLI tests and the full Python suite**

Run:
- `python -m unittest tests.test_cli -v`
- `python -m unittest discover -s tests -v`
- `python -m compileall -q praxis tests`

Expected: all PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: add neutral praxis python baseline`

---

### Task 3: DSH adapter boundary baseline

**Files:**
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `tsconfig.json`
- Create: `plugins/dsh/package.json`
- Create: `plugins/dsh/tsconfig.json`
- Create: `plugins/dsh/src/index.ts`
- Create: `plugins/dsh/test/boundary.test.ts`

**Interfaces:**
- Consumes: no Python internals; establishes only the package seam.
- Produces: an importable TypeScript package boundary named for the Praxis DSH adapter, with no Tutor/state implementation yet.

- [ ] **Step 1: Write the failing DSH boundary test**

Create a test that imports the adapter entry point and asserts it exports stable metadata identifying itself as the DSH adapter and that no neutral Python-source path or future private implementation path is imported by the TypeScript package.

- [ ] **Step 2: Run the test and verify RED**

Run: `pnpm test:dsh`

Expected: FAIL because the workspace and adapter do not exist.

- [ ] **Step 3: Implement the minimal TypeScript workspace and adapter seam**

Use TypeScript 6, Node `^22.19.0 || >=24.0.0`, pnpm 11, ESM/NodeNext. Keep Cordis/DSH runtime dependencies out until Feature-06; Task 3 only establishes an independently typecheckable adapter package boundary.

- [ ] **Step 4: Verify TypeScript baseline**

Run:
- `pnpm typecheck`
- `pnpm test:dsh`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: establish dsh adapter boundary`

---

### Task 4: GitHub Actions CI and validation contract

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `Docs/Development/Validation.md`
- Modify: `.github/pull_request_template.md`
- Test: `tests/test_ci_contract.py`

**Interfaces:**
- Consumes: Python and TypeScript validation commands from Tasks 2–3.
- Produces: the repository's authoritative CI definition for pushes to `master` and all pull requests.

- [ ] **Step 1: Write failing CI-contract tests**

Create tests that parse the workflow text and assert:
- triggers include pull requests and pushes to `master`;
- Python 3.10 is tested explicitly;
- Python unit tests and `compileall` are run;
- Node 22 and pnpm 11 are configured;
- TypeScript typecheck and DSH tests are run;
- workflow concurrency cancels superseded runs;
- install uses `--no-frozen-lockfile` while no reviewed `pnpm-lock.yaml` exists;
- validation docs say a failed or unrun check cannot be reported Green.

- [ ] **Step 2: Run the CI-contract tests and verify RED**

Run: `python -m unittest tests.test_ci_contract -v`

Expected: FAIL because `.github/workflows/ci.yml` does not exist.

- [ ] **Step 3: Add GitHub Actions workflow and validation wording**

Use separate Python and TypeScript jobs or a clearly separated matrix. Keep permissions read-only unless a later feature requires more. Set concurrency to cancel superseded runs.

- [ ] **Step 4: Run all local validation available without GitHub Actions**

Run:
- `python -m unittest discover -s tests -v`
- `python -m compileall -q praxis tests`
- `pnpm typecheck`
- `pnpm test:dsh`

Expected: all PASS.

- [ ] **Step 5: Commit**

Commit message: `ci: validate praxis foundation`

---

### Task 5: Foundation state closure

**Files:**
- Modify: `Code.md`
- Modify: `State.md`
- Modify: `README.md`
- Test: `tests/test_repository_contract.py`

**Interfaces:**
- Consumes: verified repository structure from Tasks 1–4.
- Produces: an accurate current-state snapshot that future Praxis agents can resume from without reading chat history.

- [ ] **Step 1: Extend repository-contract tests for completed foundation state**

Assert that `State.md` records only actually implemented Feature-01 capabilities and points to the exact validation commands, while Features 02–06 remain pending.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_repository_contract -v`

Expected: FAIL until documentation reflects the implemented foundation.

- [ ] **Step 3: Update the code map, current state, and README**

Document the actual source/test locations and make clear that Tutor/state/project-model/Codex/DSH runtime behavior is not implemented yet.

- [ ] **Step 4: Run the full foundation validation**

Run:
- `python -m unittest discover -s tests -v`
- `python -m compileall -q praxis tests`
- `pnpm typecheck`
- `pnpm test:dsh`

Expected: all PASS locally. GitHub Actions remains pending until the branch is pushed and its checks finish.

- [ ] **Step 5: Commit**

Commit message: `docs: record repository foundation state`

## Self-review result

- Spec coverage: Feature-01 foundation, AI-native guidance, neutral-core boundary, DSH package seam, validation discipline, `.praxis/` ignore rule, and CI are covered. Features 02–06 are intentionally deferred to separate plans.
- Type consistency: the only Python public contract introduced here is `praxis.cli.main(argv) -> int`; later state APIs are not invented prematurely.
- Review Focus: all five listed failure modes have explicit tests or CI assertions in the owning task.
- Proportion: this plan defines interfaces/tests/commands without pre-writing later state or Tutor implementation.
