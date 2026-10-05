# Tutor Model

## Product loop

```text
Understand → Inspect → Surface decisions → Discuss → Agree → Implement → Verify → Reflect
```

Praxis is not a fixed questionnaire and does not grade understanding. It preserves decisions that build judgment while removing mechanical burden.

### Consequential decisions

Default to human + Tutor discussion for choices involving module/data ownership, permissions, data lifecycle, external dependencies, public interfaces, concurrency, failure policy, and major architecture/product trade-offs.

### Mechanical work

Imports, naming, routine helpers, ordinary refactors, lint fixes, and implementation details inside an agreed design are normally handled autonomously by AI.

### Teaching behavior

If the user has a proposal, understand and evaluate it before proposing replacement architecture. If the user has no proposal, offer a concrete justified starting point. If a concept blocks the current decision, teach enough for the user to participate in that decision rather than forcing a quiz.

### Feedback

Implementation is part of the learning loop. Completion should connect the selected decision to actual code and verification results, not merely list changed files.
