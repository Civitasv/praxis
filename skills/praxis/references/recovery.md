# Recovery

Recovery reconstructs the current judgment boundary from durable task and decision state. It does not replay a full transcript and does not infer consent from missing conversation context.

Recovery is not approval.

## Rules

- An `open` decision remains open after restart, compaction, or another session.
- A prior Praxis recommendation does not become selected during recovery.
- Missing user reasoning stays missing; never manufacture it from the selected option or from AI-authored rationale.
- `selected` is not `implemented`.
- `implemented` is not `verified`.
- If one pending task/decision clearly matches the user's request, resume it without changing its lifecycle state.
- If several pending tasks or decisions are plausible, ask which work to continue rather than silently taking over another task.
- If none is relevant, start or continue work without mutating unrelated durable decisions.

Recovery summaries should be small: identify the task, the unresolved consequential choice, verified constraints needed now, and declared blocked scopes. Load detailed history only when needed.
