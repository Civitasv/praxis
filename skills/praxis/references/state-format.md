# State and Neutral CLI Boundary

Praxis project state is machine-owned. The shared Tutor policy consumes neutral state/CLI results and does not invent ids, revisions, fingerprints, lifecycle status, or approval.

## Durable authority

- `state.json` owns enabled/paused state, tasks, verified project-model metadata, and decision records.
- `code.md` and `decisions.md` are deterministic projections. They are readable context, not writable authority and are never parsed back into state.
- Decision records are authoritative for unresolved consequential choices. `status == open` means unresolved.

## Decision lifecycle data

Keep these provenance slots distinct: user proposal, verified constraints, Praxis challenge, alternatives, selected decision, user reasoning, accepted tradeoffs, implementation result, verification result, and later evidence.

The lifecycle is `open -> selected -> implemented -> verified`, with `superseded` and `abandoned` as terminal alternatives.

## Neutral command intent

Use neutral commands to read status, create/select decisions, record implementation and verification, supersede/abandon decisions, add later evidence, and rebuild projections. Respect decision revision conflicts by re-reading instead of overwriting.

A successful command result is evidence that state was saved. Never claim persistence after an error or failed write.

## Activation

Installation does not enable a project. Explicit project state controls activation. A paused project remains paused until explicitly resumed.
