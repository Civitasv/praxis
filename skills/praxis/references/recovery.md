# Recovery

Recovery reconstructs the current judgment boundary from durable task and decision state. It does not replay a full transcript and does not infer consent from missing conversation context.

Recovery is not approval. Never treat silence, restart, compaction, or recovery as approval.

## Rules

- An `open` decision remains open after restart, compaction, or another session.
- A prior Praxis recommendation does not become selected during recovery.
- Missing user reasoning stays missing; never manufacture it from the selected option or from AI-authored rationale.
- A selected decision is not implemented.
- An implemented decision is not verified.
- If one pending task/decision clearly matches the user's request, resume it without changing its lifecycle state.
- If several pending tasks or decisions are plausible, ask which work to continue rather than silently taking over another task.
- If none is relevant, start or continue work without mutating unrelated durable decisions.

Recovery summaries should be small: identify the task, the unresolved consequential choice, verified constraints needed now, and declared blocked scopes. Load detailed history only when needed.

## Resume the actual next contribution

Host recovery summaries may expose only open decisions. Once the relevant task is identified, call `decision-status --cwd . --task-id TASK` and read its complete relevant records from the returned `state`, including selected and implemented decisions. Inspect `user_proposal`, `selected_decision`, `user_reasoning`, `implementation_result`, `verification`, and all relevant `later_evidence`; an initial excerpt is not proof that delegation or a wait is absent.

Determine the next contribution from the recorded evidence:

- `open`: recover the current proposal and constraint, then resume the unresolved reasoning or selection. Read revisions in later evidence rather than overwriting the original proposal. Missing reasoning is unknown, not proof of inability.
- `selected`: look for explicit implementation delegation and its scope. If absent, summarize the selected design and request delegation before coding. If present, resume only that scope; do not demand reasoning or approval already provided.
- `implemented`: compare observed results with the chosen reason. Unrun checks remain Pending; observed failures remain Fail, with the failure evidence preserved. Keep the decision implemented until the required consequence is verified or the design is explicitly superseded/abandoned. Continue verification or discuss revision. Do not implement the same change again merely because verification is missing.
- `verified`: use evidence as context for a comparable new choice, but invite a fresh judgment; old delegation does not authorize the new work.

Chronological evidence can resolve earlier wait notes. Neither a wait label nor a task stage is a second machine state or consent source. Evidence of an explained concept, an explicit choice, and user reasoning are different things. Missing detail stays unknown; report unreadable records rather than filling gaps from AI rationale or lost conversation context.
