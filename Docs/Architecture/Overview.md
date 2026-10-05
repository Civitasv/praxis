# Praxis Architecture Overview

## Goal

Praxis is a Harness-neutral AI Tutor layer. Its product center is the judgment loop: understand the real project, expose consequential choices, discuss or teach where necessary, implement agreed work, verify behavior, and connect outcome back to decision.

## Layers

```text
+---------------------------------------------+
| Shared Praxis Skill / Tutor behavior        |
+---------------------------------------------+
| Thin host adapters: Codex / DSH             |
+---------------------------------------------+
| Neutral Python core                         |
| project boundary / state / tasks / map      |
| decisions / locking / fingerprints          |
+---------------------------------------------+
| Project-local .praxis/ records              |
+---------------------------------------------+
```

## Invariants

1. Durable state semantics live in the Python core.
2. Harness-specific APIs stay outside the neutral core.
3. Restoration never creates consent.
4. Project understanding is evidence-backed and explicitly stale when evidence changes.
5. Mechanical implementation does not require repeated user confirmation.
6. Consequential unresolved risk blocks only affected work.
