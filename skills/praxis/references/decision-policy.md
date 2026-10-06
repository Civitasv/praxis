# Decision Policy

## Classes

- `mechanical`: local implementation details that do not materially change ownership, failure semantics, contracts, or future system shape. Do not persist these by default.
- `engineering`: data ownership, state boundaries, concurrency, failure behavior, module boundaries, and storage semantics. Surface when consequential.
- `architectural`: permissions, data lifecycle, public contracts, major dependencies, technology direction, and product-level system boundaries. Surface when consequential.

A useful rule: surface a decision when repeated experience with that choice would materially improve the user's engineering taste in similar future problems.

The user proposes and revises consequential product and engineering choices with Praxis guidance. Desired outcomes are requirements, not selected architecture. Small implementation size does not make a decision mechanical when it changes product behavior or another consequential property.

A taste-bearing decision usually has at least one of these properties:

- several credible options can work, but they optimize for different futures;
- the choice changes ownership, coupling, failure behavior, contracts, reversibility, or future change cost;
- the locally easiest option differs from the structurally cleaner option;
- verification can reveal whether the reason for choosing actually held.

Do not surface a choice only because alternatives exist. The distinction between them should be worth learning.

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

AI recommendation is not approval. Never attribute Praxis-authored rationale to user reasoning. If the user does not state or adopt a reason, leave user reasoning unrecorded.

## Lifecycle

```text
open -> selected -> implemented -> verified
```

`superseded` and `abandoned` are terminal alternatives.

- `open` means the consequential choice remains unresolved.
- `selected` requires explicit user selection or explicit acceptance of a risk/tradeoff.
- Selecting the design alone does not delegate implementation. The user must also explicitly delegate the affected scope; one reply may do both, and existing delegation does not need repeated confirmation. This is a Tutor interaction boundary, not an additional durable lifecycle state.
- `implemented` requires the affected implementation to exist according to the selected decision.
- `verified` requires relevant verification evidence to be recorded.

Recovery, silence, session changes, or AI preference do not advance lifecycle status.

## Blocking

Open decisions may declare blocked scopes. Only the affected declared scope waits. Unrelated mechanical work may continue. Independent work outside the declared blocked scopes may continue when safe.

The durable decision records are authoritative for unresolved choices. Legacy task presentation hints are not approval and are not the source of truth.
