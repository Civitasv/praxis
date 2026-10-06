# Praxis Codex Integration Design

Date: 2026-10-06
Status: Proposed for Feature-05 implementation

## 1. Intent

Feature-05 connects the already-stable Praxis neutral core and shared Tutor Skill to Codex without moving any durable domain semantics into the host adapter.

The goal is automatic, bounded recovery and prompt-time synchronization when Codex lifecycle hooks are available and trusted, while preserving a truthful manual fallback when hooks are unavailable.

Feature-05 must not reinterpret approval, duplicate task/decision state, or make Codex-specific APIs part of the neutral Python core.

## 2. Existing authority

Feature-05 consumes, but does not redefine:

- `.praxis/state.json` as the sole machine-readable authority;
- durable tasks from Feature-02;
- verified project-model freshness and stale detection from Feature-03;
- durable decisions and Tutor lifecycle from Feature-04;
- the shared host-neutral Praxis Tutor Skill under `skills/praxis/`.

Host integration is translation only.

## 3. Selected Codex integration shape

The repository root is the portable plugin package root.

```text
praxis/
├── plugin.json
├── .codex-plugin/
│   └── plugin.json
├── skills/
│   └── praxis/
├── praxis/
└── plugins/
    └── codex/
        └── hooks/
            ├── hooks.json
            └── praxis_context.py
```

The root `plugin.json` is the canonical portable manifest. `.codex-plugin/plugin.json` is a compatibility fallback.

The shared Skill and neutral Python package remain single-source files in their existing locations; Feature-05 does not duplicate them under `plugins/codex/`.

## 4. Lifecycle events

Feature-05 uses two Codex lifecycle surfaces:

- `SessionStart`;
- `UserPromptSubmit`.

`SessionStart` is configured for startup/resume/clear/compact recovery.

Both lifecycle hooks invoke the same thin Python adapter:

```text
plugins/codex/hooks/praxis_context.py
```

The adapter reads the host event payload, invokes neutral Praxis state/CLI logic, and emits only bounded context for Codex.

It does not parse transcript history.

## 5. Host input

The adapter may consume host lifecycle metadata such as:

- hook event name;
- current working directory;
- Codex session identity;
- SessionStart source.

A prompt field may exist in `UserPromptSubmit`, but Feature-05 does not use prompt text to infer approval, intent, selection, implementation, or verification.

## 6. Activation semantics

Plugin installation is not project activation.

Three states are distinct:

### Uninitialized project

No valid `.praxis/state.json` exists.

The hook returns no Tutor context and creates no project state.

### Paused project

Praxis state exists with `enabled=false`.

The hook emits a small paused notice stating that Tutor behavior remains inactive until explicit resume.

It does not mutate state.

### Enabled project

The hook may refresh machine-owned project freshness metadata and emits bounded recovery/synchronization context.

## 7. Freshness synchronization

For an enabled project, lifecycle synchronization performs the equivalent of the neutral project-model freshness check before preparing context.

This may mark verified project-model sections stale when their evidence changed, disappeared, became unsafe, or unreadable.

It must not:

- rewrite semantic section content;
- clear an existing stale section back to verified;
- invent source evidence;
- change decision lifecycle.

Feature-03 remains authoritative for freshness behavior.

## 8. Session-aware task recovery

When a Codex session id is available, the adapter first searches for an active/non-complete task with:

```text
task.host == "codex"
task.conversation_id == current Codex session id
```

If exactly one exact task matches, the recovery context identifies that task.

If no exact task matches:

- zero plausible pending tasks: do not create a task automatically;
- one plausible pending task: describe it as a recoverable candidate, but do not adopt/bind it automatically;
- multiple plausible pending tasks: describe a bounded candidate list and instruct the Tutor to ask the user which task to continue.

Recovery never mutates task lifecycle merely because a task was found.

## 9. Decision recovery

Recovery may summarize durable open decisions relevant to the recovered/candidate task.

It preserves Feature-04 lifecycle truth:

- open stays open;
- selected is not implemented;
- implemented is not verified;
- recovery is not approval;
- prior Praxis recommendation is not user selection;
- missing user reasoning remains missing.

The hook never invokes a selection or lifecycle-advancing decision command automatically.

## 10. Recovery context shape

Injected context is intentionally small and operational.

It may include:

- Praxis enabled/paused state;
- exact task or bounded candidate tasks;
- open consequential decision titles/ids;
- declared blocked scopes;
- stale/unknown project-model section ids;
- a short reminder to load/use the shared Praxis Skill;
- the invariant that recovery is not approval.

It does not include:

- full task history;
- full decision history;
- full `code.md` or `decisions.md`;
- source-code copies;
- transcript text.

Detailed state remains available through the shared Skill and neutral CLI on demand.

## 11. Hard context bound

The adapter applies a deterministic hard maximum to injected context.

Target V1 bound:

```text
MAX_CONTEXT_CHARS = 3000
```

Ordering/truncation must be deterministic. Context growth in durable state must not cause unbounded prompt injection.

The hook declaration should also use the Codex host-side additional-context limit when supported.

## 12. Failure behavior

Codex integration must degrade safely.

Examples:

- Python unavailable;
- malformed hook input;
- unreadable/corrupt/unsupported Praxis state;
- project-model refresh failure;
- state lock timeout;
- hook script unavailable or not trusted by host policy.

Feature-05 must not convert these into false recovery claims.

Where the hook executes but automatic recovery fails, it emits a concise fallback notice indicating that automatic recovery was unavailable and that the shared Praxis Skill can be used manually.

The hook must not:

- reset state;
- delete state;
- auto-enable Praxis;
- fabricate recovered facts;
- auto-approve decisions.

## 13. Hook trust and manual fallback

Codex host policy/trust remains authoritative for whether hooks execute.

Praxis does not bypass trust controls and does not modify user Codex configuration to force hook execution.

When hooks are unavailable, disabled, untrusted, or not installed in the execution environment, the shared Praxis Skill remains usable manually.

Praxis documentation must distinguish:

```text
plugin/Skill available
!=
automatic lifecycle hooks active
```

## 14. Manifest contract

Feature-05 adds a canonical root portable plugin manifest and compatibility manifest.

The canonical manifest points Codex to:

- the shared Praxis Skill;
- the Codex hook declaration under `plugins/codex/hooks/hooks.json`.

The compatibility manifest describes the same package surfaces and must not introduce a second Skill copy or separate state model.

Manifest tests validate path existence and package consistency without requiring network access.

## 15. Hook declaration contract

`plugins/codex/hooks/hooks.json` configures:

- `SessionStart` for startup/resume/clear/compact;
- `UserPromptSubmit`;
- direct invocation of `praxis_context.py`;
- bounded additional context;
- no shell-interpolated user input.

The hook adapter must be executable through an argument-safe host command declaration.

## 16. Neutral-core boundary

No Codex import, SDK type, hook event type, or manifest concern may enter `praxis/`.

The Codex adapter may call or import neutral Python modules, but all durable mutations and validation remain owned by existing neutral modules.

Feature-05 should add no new durable state format merely to support Codex.

## 17. Distribution and validation

Feature-05 extends CI with Codex-package validation that can run without a live Codex account.

CI should verify:

- canonical and compatibility manifests parse;
- referenced Skill/hook paths exist;
- hook declaration contains only intended lifecycle events/sources;
- hook adapter compiles under Python 3.10+;
- adapter tests exercise real stdin/stdout contracts;
- neutral-core import boundary remains clean;
- existing Python and DSH checks remain green.

If an official local Codex plugin validation command is available in the CI environment, it may be added. Its absence must not be reported as Green.

## 18. Acceptance scenarios

Feature-05 must demonstrate:

1. installing package files alone does not initialize or enable a project;
2. an uninitialized project produces no Tutor recovery context and no filesystem mutation;
3. a paused project remains paused and receives only a paused notice;
4. SessionStart startup/resume/clear/compact each produce bounded recovery context for an enabled project;
5. UserPromptSubmit refreshes state context without parsing prompt text as approval;
6. an exact Codex session-linked task can be identified without lifecycle mutation;
7. one unmatched pending task is a candidate rather than auto-adopted;
8. several plausible tasks require user choice;
9. an open decision remains open after recovery;
10. selected and implemented decisions are described with honest lifecycle;
11. changed repository evidence can mark project-model sections stale before context is emitted;
12. malformed/unreadable Praxis state produces a truthful fallback rather than fabricated recovery;
13. injected context remains under the configured hard bound with deterministic truncation;
14. hook code does not parse transcript files;
15. shared Skill/manual use remains the documented fallback when automatic hooks are unavailable;
16. neutral Python core remains free of Codex-specific dependencies.

## 19. Non-goals

Feature-05 does not implement:

- DSH/Cordis runtime integration;
- transcript parsing;
- semantic approval extraction from prompt text;
- automatic task creation on SessionStart;
- automatic task adoption or session rebinding;
- automatic decision selection;
- user Codex configuration mutation;
- hook trust bypass;
- MCP server/runtime;
- marketplace publication;
- backend services or telemetry.

## 20. Selected approach

Selected: root portable Codex plugin + shared Praxis Skill + thin command hook adapter.

Rejected alternatives:

- Skill-only: manual use works but does not satisfy automatic lifecycle recovery.
- duplicate Codex-local Skill/core: creates drift and multiple sources of truth.
- MCP server: unnecessary for a project-local, dependency-free V1 state system.
- hook-owned state semantics: violates the Harness-neutral architecture and would fork Features 02–04.
