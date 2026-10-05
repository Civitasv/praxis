# Praxis Repository Foundation Design

Date: 2026-10-05
Status: Proposed for implementation

## 1. Product intent

Praxis is an AI tutor for building software with coding agents. It lets AI handle execution while keeping the human involved in the consequential decisions, tradeoffs, and feedback that build engineering judgment.

Praxis is not a coding restriction layer and not a fixed teaching workflow. It should reduce mechanical work, surface important decisions, challenge risky assumptions, explain concepts at the point of need, implement agreed work, verify the result, and connect the implementation outcome back to the decisions that produced it.

The desired loop is:

```text
Human + AI Tutor
      ↓
Understand the problem
      ↓
Inspect the real project
      ↓
Surface consequential decisions
      ↓
Discuss / teach / challenge
      ↓
Agree
      ↓
AI implements
      ↓
Verify real behavior
      ↓
Reflect on decision → outcome
      ↓
Product + stronger judgment
```

## 2. V1 scope

V1 supports:

- Codex;
- DeepSeek Harness (DSH);
- project-local persistent Praxis state;
- cross-session and post-compaction recovery;
- a shared English Praxis Skill and behavior references;
- a Python 3.10+ standard-library neutral core;
- thin host adapters;
- verified project understanding with source fingerprints and stale-section detection;
- durable task and decision state;
- concurrency protection for multiple chats/hosts;
- CI, tests, distribution checks, and AI-native repository guidance.

V1 does not include a backend service, vector database, telemetry, external model calls, a custom UI, quizzes, understanding scores, marketplace publication, or migration from VibeWise.

## 3. Core product principles

### 3.1 Consequential decisions stay visible

Praxis should not silently consume decisions that materially affect system behavior, ownership, security, data lifecycle, public interfaces, major dependencies, or future maintainability.

### 3.2 Mechanical work stays automated

Routine implementation details such as imports, naming, formatting, ordinary refactors, standard test organization, and lint fixes do not require repeated confirmation once the surrounding design is settled.

### 3.3 The user may already have a design

When the user proposes an approach, Praxis first understands and evaluates it. A viable approach is not replaced merely because the model prefers another pattern.

If the proposal has a concrete error, risk, or false assumption, Praxis explains the issue and its impact immediately. Implementation that depends on the unresolved issue waits until the user and Praxis explicitly agree on a revision or accepted tradeoff.

### 3.4 The user may not know the answer

Praxis is a tutor, not an examiner. If the user does not know, Praxis explains enough context to make the next meaningful decision possible. It may recommend a concrete starting point and explain why.

### 3.5 Implementation is feedback

After implementation, Praxis reconnects the observed result to the design assumptions and tradeoffs. Writing code is not the learning goal; experiencing judgment → consequence → correction is.

## 4. Decision categories

Praxis distinguishes three broad classes:

| Class | Examples | Default behavior |
| --- | --- | --- |
| Mechanical | imports, local naming, ordinary helper extraction, lint | AI proceeds |
| Engineering | data model, state ownership, concurrency, failure behavior, module boundary | Human + AI discuss |
| Architectural / product | permissions, data lifecycle, public contracts, core dependency or technology choices | Human + AI discuss |

The practical rule is: if repeatedly experiencing this decision would improve future engineering judgment, Praxis should consider surfacing it.

## 5. Tutor loop

For meaningful work Praxis follows a dynamic loop rather than fixed checkpoints:

```text
Understand
  → Inspect
  → Surface consequential decisions
  → Discuss
  → Agree
  → Implement
  → Verify
  → Reflect
```

Requirements are not treated as architecture. Suggestions are not treated as user decisions. A selected decision is not treated as implemented until implementation exists and has been checked.

Praxis must keep these sources distinct:

- verified repository fact;
- user proposal;
- Praxis proposal;
- selected decision;
- implemented result;
- later inference.

Recovery, session restart, compaction, silence, or a new request never implies approval of a pending decision.

## 6. Runtime project state

A Praxis-enabled project stores local state under:

```text
.praxis/
├── state.json
├── code.md
└── decisions.md
```

On first enablement Praxis explains this location and recommends ignoring the directory in Git. It does not modify `.gitignore` automatically.

Praxis never stores full transcripts, credentials, secrets, or large source-code copies in its state.

Shared state format version starts at `1`.

## 7. `state.json`: machine-owned state

`state.json` is the authoritative machine-readable state for:

- enabled / paused state;
- format version;
- global revision;
- active tasks;
- host / conversation association when available;
- task stages;
- pending consequential choices;
- section revisions and other machine metadata needed for conflict detection.

Illustrative shape:

```json
{
  "format_version": 1,
  "revision": 18,
  "enabled": true,
  "tasks": {
    "task_abc123": {
      "host": "codex",
      "conversation_id": "...",
      "stage": "design",
      "status": "active",
      "pending_choices": ["message-storage"]
    }
  }
}
```

Machine metadata such as revision numbers, fingerprints, and lock data is produced by the Python core rather than invented by the model.

Suggested task stages:

- `understanding`;
- `design`;
- `awaiting_decision`;
- `implementation`;
- `verification`;
- `complete`;
- `blocked`.

## 8. Multi-chat task behavior

Tasks are durable and independently identified.

```text
Chat A → task_auth
Chat B → task_notifications
Chat C → task_database
```

A new session behaves as follows:

- no relevant pending task → start a new task;
- one clearly relevant task → recover it;
- several plausible pending tasks → ask the user which one to continue;
- never silently take over an unrelated task.

Different tasks must not overwrite each other's pending decisions.

## 9. `code.md`: verified project model

`code.md` represents current project facts, not decision history.

Stable semantic sections should include:

```text
System Overview
Runtime Entry Points
Modules
Main Data Flows
State Ownership
Data and Trust Boundaries
External Systems
Public Interfaces
Build and Deployment
Known Unknowns
Stale Sections
```

Unknown relationships remain explicitly unknown. Praxis must not complete an architecture map by guessing.

## 10. Repository Understanding Protocol

For an existing repository, Praxis establishes a small, useful, evidence-backed model in this order:

```text
repository boundary
  → project guidance
  → build manifests
  → runtime entry points
  → top-level modules
  → important call/data paths
  → state ownership
  → persistence
  → external boundaries
  → public interfaces
  → build/deployment
  → known unknowns
```

The goal is not a complete repository scan. The first map should be compact, useful, evidence-backed, and explicitly incomplete where evidence is missing.

## 11. Evidence, fingerprints, and stale detection

Important `code.md` sections are associated with source evidence such as files and normalized content fingerprints.

The Python core owns the fingerprint metadata. A changed source fingerprint marks only the dependent project-model section(s) stale.

Example:

```text
src/auth/service.ts changed
  → Auth section stale
  → Session lifecycle stale
  → unrelated Billing section remains verified
```

Praxis re-reads stale sections when the current task touches them, rather than rebuilding the entire map.

## 12. Section-level concurrency

The project model should support section-level revisions so independent work does not create unnecessary conflicts.

```text
Auth revision: 12
Billing revision: 7
```

Two chats may advance different sections concurrently. If two writers both update the same section from the same old revision, the second write receives a conflict and must re-read instead of overwriting.

## 13. `decisions.md`: durable judgment trail

`decisions.md` records why the system became what it is and what decision process the human actually participated in.

Recommended entry structure:

```text
Decision id / title
Status
Context
User's initial proposal
Verified constraints
Issue surfaced by Praxis
Alternatives discussed
Selected decision
User reasoning
Accepted tradeoffs
Implementation result
Verification
Later evidence
```

Praxis distinguishes user reasoning from AI suggestions and later inference. It must not attribute a model-generated reason to the user.

Praxis does not produce numeric understanding scores or claim mastery because a concept was explained once.

## 14. Neutral Python core

The durable state model is implemented in Python 3.10+ using only the standard library.

Initial module layout:

```text
praxis/
├── __init__.py
├── cli.py
├── project.py
├── state.py
├── tasks.py
├── locking.py
├── fingerprints.py
├── project_map.py
└── decisions.py
```

The core owns:

- project-root discovery;
- state format validation;
- atomic writes;
- write locking;
- compare-and-swap revisions;
- task identity and lifecycle;
- fingerprint computation;
- stale-section detection;
- machine metadata;
- consistent JSON result contracts for host adapters.

Harness adapters do not duplicate this logic.

## 15. State safety

State writes use version checks, a write lock, and atomic replacement.

Required behavior:

- callers submit an expected revision where appropriate;
- revision mismatch returns a conflict instead of overwriting;
- malformed state is preserved and reported;
- unsupported format versions are preserved and reported;
- failed writes are never reported as successful;
- state reset or destructive operations re-check the target before committing changes.

Where practical, atomic replacement follows a temporary-file → flush/fsync → replace pattern.

## 16. Project boundaries and symlink safety

Starting from the working directory, Praxis selects the nearest Git repository root. A `.git` directory and a worktree `.git` file both define a boundary. Without Git, the current working directory is the project boundary.

Praxis does not:

- cross into a parent repository;
- borrow state from another worktree;
- follow a symlinked `.praxis` directory;
- follow symlinked state files;
- treat the installed plugin directory as project state.

## 17. Shared Praxis Skill

The shared Skill and its behavior references are written in English.

Planned structure:

```text
skills/praxis/
├── SKILL.md
└── references/
    ├── tutor-behavior.md
    ├── decision-policy.md
    ├── repository-understanding.md
    ├── recovery.md
    └── state-format.md
```

The top-level Skill stays short and progressively loads detail.

It supports enable, resume, pause, status, and architecture inspection through natural language and/or host-supported invocation surfaces.

Installation alone never enables Praxis for a project.

## 18. Codex integration

Codex distribution contains the shared Skill, Python core, and lifecycle hooks.

Canonical distribution uses a portable root `plugin.json`; a compatibility manifest may also be included where required by the host.

`SessionStart` restores Praxis after startup/resume/clear/compaction by injecting only a small bootstrap instruction. It does not inject all project state into context.

`UserPromptSubmit` synchronizes current project/task state and stale markers needed for the turn.

Hooks do not:

- parse full transcripts;
- auto-approve pending decisions;
- create architecture explanations themselves;
- bypass host permissions.

When hooks are disabled/untrusted or Python is unavailable, manual Skill invocation remains supported and Praxis accurately reports that automatic recovery is unavailable.

## 19. DeepSeek Harness integration

DSH ships:

1. a native Praxis plugin for the complete experience;
2. a standalone Praxis Skill for manual use/recovery.

The native adapter uses the host's Skill provider and lifecycle facilities, calls Python through direct subprocess argument APIs rather than shell string concatenation, and converts host events/messages into the neutral JSON contract.

The adapter owns only host lifecycle and translation. It does not own Praxis task/state semantics.

Plugin unload removes listeners and Skill registration while preserving project `.praxis/` data.

Other plugin messages, denials, permissions, and host policy remain intact.

## 20. AI-native repository structure

Praxis follows the useful repository discipline established in Orven without copying Orven's Change Graph runtime.

Planned repository navigation:

```text
AGENTS.md
Code.md
State.md
README.md
Docs/
  Architecture/
  Specs/
  Development/
praxis/
skills/
plugins/
tests/
.github/
```

Responsibilities:

- `AGENTS.md` — durable collaboration invariants for coding agents;
- `Code.md` — stable code/architecture navigation map;
- `State.md` — current implemented project facts and remaining work;
- `Docs/Architecture` — architectural contracts and boundaries;
- `Docs/Specs` — feature contracts and acceptance criteria;
- `Docs/Development` — validation/distribution procedures.

Repository documentation is durable engineering context for disposable AI workers; it does not replace tests or runtime state.

## 21. Agent collaboration invariants

Initial `AGENTS.md` should establish at least:

1. Start at `Code.md`, then the relevant Architecture/Spec, then source/tests.
2. Tutor judgment loop is the product center.
3. Project facts require evidence; unknown remains unknown.
4. User proposal, Praxis proposal, selected decision, and implementation are distinct.
5. Restoration is never approval.
6. Mechanical work does not require repeated confirmation.
7. Consequential unresolved risks block only affected implementation.
8. Python Core owns durable state semantics.
9. Harness adapters are translation layers, not domain owners.
10. Host-specific APIs never enter the neutral Core.
11. Never claim state was saved when a write failed.
12. Never claim Green without executing applicable validation.

## 22. Repository package model

The selected architecture is:

```text
Python neutral core
      ↑
shared Praxis Skill
      ↑
+-----+----------------+
|                      |
Codex file/plugin      TypeScript DSH adapter
                       (thin native host layer)
```

The DSH TypeScript package may depend on DSH/Cordis APIs. The Python core and shared Skill must not.

## 23. CI baseline

GitHub Actions is the CI source of truth.

CI runs for pull requests and pushes to `master`, with concurrency cancellation for obsolete runs.

Baseline checks:

### Python

- Python 3.10 minimum-version tests;
- a current Python version test run;
- `compileall` / syntax validation;
- unit and behavior tests for project boundary, state, locking, CAS, tasks, fingerprints, and stale detection.

### DSH adapter

- Node 22;
- pnpm 11;
- TypeScript typecheck;
- lint;
- adapter tests;
- package build.

### Distribution

- Codex package/manifests validation where host tooling is available;
- DSH package/bundle validation;
- clean package-boundary/install checks where feasible.

A check is Green only when the applicable command or CI job actually passed.

Until a real pnpm-generated lockfile is committed, CI may use `pnpm install --no-frozen-lockfile`. A lockfile must never be fabricated manually. Once committed, CI switches to frozen-lockfile installs.

## 24. Pull-request discipline

The PR template includes:

- Summary;
- Evidence / behavior tests;
- Validation actually run;
- Architecture impact;
- explicit marking of validation that could not run.

No agent should report a change complete while required checks are known to be failing or merely assumed.

## 25. Implementation sequence

### Feature 01 — Repository Foundation

Create the AI-native documentation/navigation model, Python/TypeScript workspace seams, baseline tests, CI, and distribution skeleton.

### Feature 02 — Praxis State Core

Implement project discovery, state initialization, locking, CAS revisions, task identity/lifecycle, pause/resume, corruption handling, and concurrency behavior.

### Feature 03 — Verified Project Model

Implement evidence fingerprints, section metadata, stale detection, and incremental project-model updates.

### Feature 04 — Tutor Decision Loop

Implement the shared Skill behavior, decision provenance, recovery rules, and implementation/reflection protocol.

### Feature 05 — Codex Integration

Package the Skill/core, add lifecycle hooks, test explicit activation/recovery/pause/manual fallback, and validate distribution.

### Feature 06 — DeepSeek Harness Integration

Implement Skill provider, pre-step recovery, subprocess bridge, native bundle, standalone Skill distribution, lifecycle cleanup, and coexistence behavior.

## 26. V1 acceptance scenarios

Praxis must demonstrate:

- a viable user design is respected and refined rather than replaced;
- a risky or false design assumption is surfaced before dependent implementation;
- accepted risk/revision is recorded faithfully;
- a user who does not know receives enough teaching and a concrete starting point to participate;
- ordinary implementation details proceed without repeated approvals;
- a new implementation-time risk pauses only the affected scope;
- restart/compaction restores stage but never invents approval;
- external code changes invalidate only affected project-model sections;
- Codex and DSH share the same project records without reinitialization;
- multiple chats do not overwrite each other's tasks;
- same-section concurrent writes conflict safely;
- missing Python, disabled hooks, unreadable state, or unwritable state produce accurate limitations and manual recovery paths.

## 27. Architectural comparison to Orven

Praxis adopts Orven's repository discipline — durable agent guidance, navigable architecture/spec/state documents, host-neutral core boundaries, thin adapters, and evidence-based CI completion — but does not copy Orven's Change Graph, event sourcing, execution-gate runtime, or release graph.

Praxis's durable product center is:

```text
Verified project facts
        |
        v
Project model
        |
   +----+-----+
   |          |
Decisions   Active tasks
   |          |
   +----+-----+
        v
    Tutor loop
        |
   Human <-> AI
        |
        v
Implementation + verification
```

## 28. Success definition

The repository foundation is successful when a new coding-agent session can enter the repository, discover the product intent and architectural boundaries without relying on prior chat history, identify the relevant spec/state/source/tests for a change, execute the real validation commands, and extend Praxis without leaking host-specific logic into the neutral core or weakening the Tutor decision model.
