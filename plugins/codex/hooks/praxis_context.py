"""Thin Codex lifecycle adapter for Praxis.

Host event data arrives only through stdin JSON. Durable state and Tutor
semantics remain owned by the neutral Praxis package.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from praxis.decisions import decision_blocked_scopes, list_open_decisions  # noqa: E402
from praxis.project import discover_project_root  # noqa: E402
from praxis.project_map import project_model_status, refresh_staleness  # noqa: E402
from praxis.state import load_state  # noqa: E402
from praxis.tasks import pending_tasks  # noqa: E402


MAX_CONTEXT_CHARS = 3000
_ALLOWED_EVENTS = {"SessionStart", "UserPromptSubmit"}
_SESSION_SOURCES = {"startup", "resume", "clear", "compact"}


def _valid_event(event: object) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
    event_name = event.get("hook_event_name")
    if event_name not in _ALLOWED_EVENTS:
        return None
    if event_name == "SessionStart" and event.get("source") not in _SESSION_SOURCES:
        return None
    cwd = event.get("cwd")
    if not isinstance(cwd, str) or not cwd.strip():
        return None
    return event


def _task_line(task_id: str, task: dict[str, Any]) -> str:
    title = task.get("title") or "(untitled)"
    return (
        f"{task_id} — {title} "
        f"[stage={task.get('stage', 'unknown')}, status={task.get('status', 'unknown')}]"
    )


def _exact_codex_tasks(state: dict[str, Any], session_id: object) -> list[tuple[str, dict[str, Any]]]:
    if not isinstance(session_id, str) or not session_id:
        return []
    matches: list[tuple[str, dict[str, Any]]] = []
    for task_id, task in sorted(state.get("tasks", {}).items()):
        if (
            isinstance(task, dict)
            and task.get("host") == "codex"
            and task.get("conversation_id") == session_id
            and task.get("status") != "complete"
        ):
            matches.append((task_id, task))
    return matches


def build_context(event: dict[str, Any]) -> str | None:
    """Build bounded Tutor context without interpreting prompt/transcript data."""

    value = _valid_event(event)
    if value is None:
        return None

    try:
        project_root = discover_project_root(value["cwd"])
    except (OSError, ValueError):
        return None

    state = load_state(project_root)
    if state is None:
        return None
    if not state["enabled"]:
        return (
            "Praxis is paused for this project. "
            "Do not activate Tutor behavior until the user explicitly resumes it."
        )

    state = refresh_staleness(project_root)
    lines = [
        "Praxis is enabled for this project.",
        "Load and follow the shared Praxis Tutor Skill.",
    ]

    exact = _exact_codex_tasks(state, value.get("session_id"))
    context_task_id: str | None = None
    if len(exact) == 1:
        task_id, task = exact[0]
        context_task_id = task_id
        lines.append(f"Recovered task: {_task_line(task_id, task)}")
    elif len(exact) > 1:
        lines.append("Multiple matching Codex tasks; ask the user which task to continue:")
        for task_id, task in exact:
            lines.append(f"- {_task_line(task_id, task)}")
    else:
        candidates = sorted(pending_tasks(state).items())
        if len(candidates) == 1:
            task_id, task = candidates[0]
            context_task_id = task_id
            lines.append(f"Recoverable task candidate: {_task_line(task_id, task)}")
            lines.append("This task is a candidate only; do not adopt or rebind it without the user's choice.")
        elif len(candidates) > 1:
            lines.append("Multiple pending task candidates; ask the user which task to continue:")
            for task_id, task in candidates:
                lines.append(f"- {_task_line(task_id, task)}")

    if context_task_id is not None:
        for decision_id, record in sorted(
            list_open_decisions(state, task_id=context_task_id).items()
        ):
            lines.append(
                f"Open decision: {decision_id} — {record['title']} "
                f"[class={record['class']}]"
            )
        blocked = decision_blocked_scopes(state, task_id=context_task_id)
        if blocked:
            lines.append("Blocked scopes: " + ", ".join(blocked))

    model = project_model_status(project_root)
    stale = model.get("stale_sections", [])
    if stale:
        lines.append("Stale project sections: " + ", ".join(stale))

    lines.append("Recovery is not approval.")
    return "\n".join(lines)


def build_response(event_name: str, context: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context[:MAX_CONTEXT_CHARS],
        }
    }


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeError):
        return 0
    if not isinstance(event, dict):
        return 0
    context = build_context(event)
    if context is None:
        return 0
    event_name = event.get("hook_event_name")
    if not isinstance(event_name, str):
        return 0
    print(json.dumps(build_response(event_name, context), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
