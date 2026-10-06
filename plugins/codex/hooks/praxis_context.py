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

from praxis.project import discover_project_root  # noqa: E402
from praxis.state import load_state  # noqa: E402


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

    return (
        "Praxis is enabled for this project. "
        "Load and follow the shared Praxis Tutor Skill. "
        "Recovery is not approval."
    )


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
