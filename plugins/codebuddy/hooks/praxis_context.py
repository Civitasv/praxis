"""CodeBuddy lifecycle adapter for Praxis."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from plugins.shared.recovery_hook import (  # noqa: E402
    RecoveryHookError,
    render_recovery_context,
    render_recovery_fallback,
    run_recovery_status,
)


def _project_dir(event: dict[str, Any]) -> str | None:
    cwd = event.get("cwd")
    if isinstance(cwd, str) and cwd.strip():
        return cwd
    env_cwd = os.environ.get("CODEBUDDY_PROJECT_DIR")
    if isinstance(env_cwd, str) and env_cwd.strip():
        return env_cwd
    return None


def _conversation_id(event: dict[str, Any]) -> str | None:
    value = event.get("session_id")
    if isinstance(value, str) and value.strip():
        return value
    return None


def _recover(event: dict[str, Any]) -> str | None:
    cwd = _project_dir(event)
    if cwd is None:
        return None
    snapshot = run_recovery_status(
        cwd=cwd,
        host="codebuddy",
        conversation_id=_conversation_id(event),
    )
    return render_recovery_context(snapshot)


def _response(event_name: str, context: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if event_name == "UserPromptSubmit":
        payload["continue"] = True
    if context is not None:
        payload["hookSpecificOutput"] = {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    return payload


def handle_event(event: dict[str, Any]) -> dict[str, Any]:
    event_name = event.get("hook_event_name")
    if event_name not in {"SessionStart", "UserPromptSubmit"}:
        return {}

    try:
        context = _recover(event)
    except RecoveryHookError:
        context = render_recovery_fallback()
    return _response(event_name, context)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeError):
        print("{}")
        return 0
    if not isinstance(event, dict):
        print("{}")
        return 0
    print(json.dumps(handle_event(event), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
