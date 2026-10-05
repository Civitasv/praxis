# Decision Policy

## Classes

- `mechanical`: local implementation details that do not materially change ownership, failure semantics, contracts, or future system shape. Do not persist these by default.
- `engineering`: data ownership, state boundaries, concurrency, failure behavior, module boundaries, and storage semantics. Surface when consequential.
- `architectural`: permissions, data lifecycle, public contracts, major dependencies, technology direction, and product-level system boundaries. Surface when consequential.

A useful rule: surface a decision when repeated experience with that judgment would materially improve how the user handles similar future problems.

## Provenance

Never collapse these fields:

- verified constraints;
- user proposal;
- Praxis challenge or recommendation;
- selected decision;
- user reasoning;
- accepted tradeoffs;
- implementation result;
- verification result;
- later evidence or inference.

AI recommendation is not approval. AI-authored rationale must not be stored as user reasoning unless the user actually adopts it.

## Lifecycle

```text
open -> selected -> implemented -> verified
```

`superseded` and `abandoned` are terminal alternatives.

- `open` means the consequential choice remains unresolved.
- `selected` requires explicit user selection or explicit acceptance of a risk/tradeoff.
- `implemented` requires the affected implementation to exist according to the selected decision.
- `verified` requires relevant verification evidence to be recorded.

Recovery, silence, session changes, or AI preference do not advance lifecycle status.

## Blocking

Open decisions may declare blocked scopes. Only those dependent scopes are blocked. The rest of the task may continue when independent and safe.

The durable decision records are authoritative for unresolved choices. Legacy task presentation hints are not approval and are not the source of truth.
