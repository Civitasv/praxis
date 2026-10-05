# Feature-03 Verified Project Model

## Objective

Implement the Harness-neutral verified project model used by later Praxis Tutor and host adapters to reason about the current codebase without trusting stale prose.

Feature-03 owns source evidence fingerprints, machine-owned project-model metadata, section-level compare-and-swap, stale detection, incremental refresh, deterministic `.praxis/code.md` rendering, and a JSON CLI contract for those operations.

Feature-03 does **not** implement Tutor decision provenance, `decisions.md`, Codex lifecycle hooks, or native DSH/Cordis integration.

## Runtime layout

A Praxis-enabled project may contain:

```text
<project>/.praxis/
├── state.json
├── code.md
└── .write-lock/   # transient while a writer holds the state lock
```

`state.json` remains the machine-readable authority. `.praxis/code.md` is a deterministic human/model-readable projection of the project-model state and can be rebuilt from `state.json`.

## Authority and recovery

Project-model semantic content and machine metadata are stored under the optional `project_model` field in `state.json`.

Illustrative shape:

```json
{
  "project_model": {
    "revision": 3,
    "sections": {
      "auth": {
        "title": "Authentication",
        "revision": 1,
        "status": "verified",
        "content": "Authentication and session lifecycle.",
        "evidence": [
          {
            "path": "src/auth/service.py",
            "sha256": "..."
          }
        ],
        "stale_reasons": []
      }
    }
  }
}
```

The Python core, not the model, computes:

- `project_model.revision`;
- section revisions;
- evidence paths after normalization;
- SHA-256 fingerprints;
- stale status and stale reasons;
- the machine markers rendered into `code.md`.

If `code.md` is missing or out of sync, it is rebuilt from the authoritative state. A render failure is reported as failure and is never claimed as saved output.

## Project-model revision

`project_model.revision` is independent from the global state revision.

It increments exactly once when project-model state changes, including:

- adding a section;
- updating or removing a section;
- a stale scan changing one or more section statuses/reasons.

A no-op stale scan does not increment either project-model or global state revision.

Task-only mutations from Feature-02 do not change `project_model.revision`, so they do not make `code.md` appear stale.

## Section records

Section ids are stable machine keys matching:

```text
[a-z0-9][a-z0-9-]*
```

Each section contains:

- `title`: non-empty string;
- `revision`: non-negative integer;
- `status`: `verified`, `stale`, or `unknown`;
- `content`: non-empty Markdown/plain-text semantic content supplied by the caller;
- `evidence`: normalized project-relative source file paths and SHA-256 fingerprints;
- `stale_reasons`: machine-generated reasons, empty unless stale.

A section with at least one evidence file becomes `verified` after an upsert. A section with no evidence becomes `unknown`; it is never represented as verified without evidence.

## Evidence safety

Evidence paths are always interpreted relative to the discovered project root.

The core rejects evidence that:

- escapes the project root after path resolution;
- points to a directory or non-file entry;
- points inside `.praxis/`;
- points inside `.git/`;
- is missing at capture time.

An in-project symlink may be fingerprinted only when its resolved target remains inside the same project root and is a regular file. A symlink that resolves outside the project is rejected.

Fingerprints use SHA-256 over the exact file bytes. The stored path is normalized to POSIX-style project-relative form.

## Section-level compare-and-swap

Project-model writes do not use the caller's global state revision as their concurrency gate.

For an existing section, callers submit `expected_section_revision`. Under the project write lock Praxis loads the latest state and compares only that section revision.

This permits independent concurrent work:

```text
Auth revision 4 -> 5
Billing revision 7 -> 8
```

Both updates may succeed even if the first write advanced the global state revision.

Two writers updating the same section from the same old section revision conflict; the second must re-read.

For a new section, `expected_section_revision` must be omitted. If the section already exists, creation conflicts instead of overwriting.

Removal likewise requires the exact current section revision.

## Stale detection

A stale scan recomputes current fingerprints for every evidence path associated with every section.

A section becomes `stale` if any evidence file:

- changed content;
- disappeared;
- became unsafe/outside the project;
- can no longer be read.

Machine-generated `stale_reasons` identify affected evidence paths and the reason (`changed`, `missing`, `unsafe`, or `unreadable`).

Unrelated sections remain unchanged.

A section already stale with the same reasons remains unchanged on a repeated scan.

An `unknown` section with no evidence remains `unknown`.

To return a stale section to `verified`, a caller explicitly upserts that section after re-reading the relevant source. Praxis captures fresh fingerprints and increments only that section revision.

## Incremental model semantics

Feature-03 never automatically rewrites semantic section content after source changes.

Its responsibility is:

```text
source changed
  -> evidence fingerprint mismatch
  -> affected section(s) stale
  -> later Tutor/host re-reads only those sections' evidence
  -> caller upserts refreshed semantic content
  -> section verified again
```

This keeps source interpretation in the AI/Tutor layer while making freshness machine-verifiable.

## Deterministic `code.md`

`.praxis/code.md` is rendered in stable section-id order with a machine header:

```markdown
# Praxis Verified Project Model

<!-- praxis:project-model revision="3" -->

## Authentication
<!-- praxis:section id="auth" revision="1" status="verified" -->

Authentication and session lifecycle.

Evidence:
- `src/auth/service.py` — `sha256:...`
```

Stale sections include a `Stale reasons:` block. Unknown sections explicitly say `Evidence: none (unknown)`.

The renderer does not parse semantic content back from Markdown. State remains authoritative.

`code.md` is considered synchronized when its project-model marker revision equals the current `project_model.revision`. Missing/mismatched output is reported as `render_required` and can be repaired by rendering from state.

## Core interfaces

Feature-03 introduces neutral Python interfaces:

```text
praxis.fingerprints.capture_evidence(project_root, paths) -> list[dict]
praxis.fingerprints.fingerprint_file(project_root, path) -> dict

praxis.project_map.get_project_model(state) -> dict
praxis.project_map.upsert_section(project_root, section_id, title, content, evidence_paths, expected_section_revision=None) -> dict
praxis.project_map.remove_section(project_root, section_id, expected_section_revision) -> dict
praxis.project_map.refresh_staleness(project_root) -> dict
praxis.project_map.render_project_model(project_root) -> Path
praxis.project_map.project_model_status(project_root) -> dict
```

Section mutations use the latest state under the Feature-02 write lock and perform section-level CAS internally. They increment global state revision once per successful state change.

## State mutation support

Feature-03 may add a neutral Feature-02-compatible helper for machine-owned latest-state maintenance:

```text
praxis.state.mutate_latest_state(project_root, mutator) -> dict
```

It acquires the existing write lock, loads the latest valid state, deep-copies it, applies the mutator, and only writes/increments the global revision when the semantic state actually changed.

This helper is used for machine-maintenance operations such as stale detection where global expected-revision CAS would create false conflicts.

## CLI JSON contract

The neutral CLI adds:

```text
praxis map-status --cwd PATH
praxis map-upsert --cwd PATH --section-id ID --title TITLE --content CONTENT [--evidence PATH ...] [--expected-section-revision N]
praxis map-remove --cwd PATH --section-id ID --expected-section-revision N
praxis map-check --cwd PATH
praxis map-render --cwd PATH
```

Commands emit one JSON object to stdout.

Stable project-model error codes include:

- `invalid_evidence`;
- `section_conflict`;
- `unknown_section`;
- `invalid_project_model`;
- `project_model_render_failed`.

`map-status` is read-only. It reports whether a model exists, project-model revision, section summaries, stale section ids, and whether `code.md` requires rendering.

`map-check` may mutate state only if freshness status/reasons actually change.

## Acceptance criteria

### AC-001 — fingerprints are core-owned

The core captures normalized project-relative evidence paths and SHA-256 values; callers cannot supply fingerprints.

### AC-002 — evidence cannot escape the project

Missing, unsafe, `.praxis`, `.git`, directory, and outside-project evidence is rejected.

### AC-003 — independent section concurrency

Unrelated section updates can both succeed despite global revision movement; stale writes to the same section conflict.

### AC-004 — incremental stale detection

Changing one evidence file marks only dependent sections stale; unchanged sections retain status/revision/content.

### AC-005 — no-op scans are no-op writes

Repeated stale scans with identical results do not advance global or project-model revisions.

### AC-006 — deterministic recovery

`code.md` can be deleted or become out of sync and then be regenerated deterministically from authoritative state.

### AC-007 — adapter-ready JSON

Project-model CLI operations use stable JSON success/error contracts and no Harness-specific dependencies.

## Non-goals

- automatic semantic interpretation of changed source;
- repository-wide scanning heuristics that decide which sections to create;
- `decisions.md` or Tutor decision provenance;
- learning/understanding scores;
- Codex lifecycle hooks;
- native DSH/Cordis lifecycle integration;
- backend services, external model calls, vector storage, or telemetry.
