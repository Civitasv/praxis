"""Thin Codex lifecycle adapter for Praxis.

Host event data arrives only through stdin JSON. Durable state and Tutor
semantics remain owned by the neutral Praxis package.
"""

from __future__ import annotations

import json
import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from praxis.decisions import decision_blocked_scopes, list_open_decisions  # noqa: E402
from praxis.diagnostics import record_hook  # noqa: E402
from praxis.fingerprints import EvidenceError  # noqa: E402
from praxis.locking import LockTimeoutError  # noqa: E402
from praxis.project import UnsafeStatePathError, discover_project_root  # noqa: E402
from praxis.project_map import ProjectModelError, project_model_status, refresh_staleness  # noqa: E402
from praxis.state import PraxisStateError, load_state  # noqa: E402
from praxis.tasks import pending_tasks  # noqa: E402


MAX_CONTEXT_CHARS = 3000
_ALLOWED_EVENTS = {"SessionStart", "UserPromptSubmit"}
_SESSION_SOURCES = {"startup", "resume", "clear", "compact"}
_RECOVERABLE_ERRORS = (
    PraxisStateError,
    ProjectModelError,
    EvidenceError,
    UnsafeStatePathError,
    LockTimeoutError,
    OSError,
    UnicodeError,
)
_RECOVERY_FOOTER = "Recovery is not approval. Use the shared Praxis Tutor Skill for details."
_FALLBACK_CONTEXT = (
    "Praxis automatic recovery is unavailable. "
    "Use the shared Praxis Tutor Skill manually. "
    "Do not assume durable state was restored. "
    "Recovery is not approval."
)
_ACTIVE_CONTEXT = [
    "Praxis is enabled for this project.",
    "Praxis active: load and follow the shared Praxis Tutor Skill before proposing a solution or editing.",
    "A preference answer does not select an implementation.",
    "Resolve consequential choices with the user; execute mechanical work within an already delegated scope without repeated confirmation.",
]


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


def _inline_text(value: object) -> str:
    return " ".join(str(value).split())


def _task_line(task_id: str, task: dict[str, Any]) -> str:
    title = _inline_text(task.get("title") or "(untitled)")
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


def _bounded_context(lines: list[str]) -> str:
    """Render deterministic priority-ordered lines within the product hard cap."""

    kept: list[str] = []
    budget = MAX_CONTEXT_CHARS - len(_RECOVERY_FOOTER) - 1
    for line in lines:
        separator = 1 if kept else 0
        remaining = budget - sum(len(item) for item in kept) - max(0, len(kept) - 1)
        if remaining <= separator:
            break
        available = remaining - separator
        if len(line) <= available:
            kept.append(line)
            continue
        if available > 1:
            kept.append(line[: available - 1] + "…")
        break

    if not kept:
        return _RECOVERY_FOOTER[:MAX_CONTEXT_CHARS]
    return "\n".join(kept) + "\n" + _RECOVERY_FOOTER



def build_context(event: dict[str, Any], *, synchronize: bool = True) -> str | None:
    """Build bounded Tutor context without interpreting prompt/transcript data."""

    value = _valid_event(event)
    if value is None:
        return None

    try:
        project_root = discover_project_root(value["cwd"])
    except (OSError, ValueError):
        return None

    try:
        state = load_state(project_root)
    except _RECOVERABLE_ERRORS:
        return _FALLBACK_CONTEXT
    if state is None:
        return None
    if not state["enabled"]:
        return (
            "Praxis is paused for this project. "
            "Do not activate Tutor behavior until the user explicitly resumes it."
        )

    if synchronize:
        try:
            state = refresh_staleness(project_root)
        except _RECOVERABLE_ERRORS:
            return _FALLBACK_CONTEXT
    lines = list(_ACTIVE_CONTEXT)

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
                f"Open decision: {decision_id} — {_inline_text(record['title'])} "
                f"[class={record['class']}]"
            )
        blocked = decision_blocked_scopes(state, task_id=context_task_id)
        if blocked:
            lines.append("Blocked scopes: " + ", ".join(_inline_text(scope) for scope in blocked))

    try:
        model = project_model_status(project_root)
    except _RECOVERABLE_ERRORS:
        return _FALLBACK_CONTEXT
    stale = model.get("stale_sections", [])
    if stale:
        lines.append("Stale project sections: " + ", ".join(stale))
    unknown = [
        item["id"]
        for item in model.get("sections", [])
        if isinstance(item, dict) and item.get("status") == "unknown"
    ]
    if unknown:
        lines.append("Unknown project sections: " + ", ".join(unknown))

    return _bounded_context(lines)


def build_response(event_name: str, context: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context[:MAX_CONTEXT_CHARS],
        }
    }


def _observe(event: dict[str, Any], status: str) -> None:
    if _valid_event(event) is None:
        return
    try:
        record_hook(discover_project_root(event["cwd"]), host="codex",
                    event=event["hook_event_name"],
                    source=event.get("source") if event["hook_event_name"] == "SessionStart" else None,
                    status=status, adapter_root=PLUGIN_ROOT)
    except (RuntimeError, OSError, ValueError, TypeError, UnicodeError) as error:
        print(f"Praxis diagnostic write failed: {type(error).__name__}", file=sys.stderr)


def doctor_report(cwd: str, host_config: str | None) -> dict[str, Any]:
    """Inspect this adapter and probe its output without logging or refreshing state."""
    report: dict[str, Any] = {}
    expected = 'python3 "${PLUGIN_ROOT}/plugins/codex/hooks/praxis_context.py"'
    try:
        portable = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
        extension = portable.get("extensions", {}).get("com.openai")
        overlay = extension if isinstance(extension, dict) else json.loads(
            (PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        relative = overlay.get("hooks")
        if relative != "./plugins/codex/hooks/hooks.json":
            raise ValueError("Manifest does not reference this adapter's hook configuration")
        hooks = json.loads((PLUGIN_ROOT / relative).read_text(encoding="utf-8"))["hooks"]
        for event in sorted(_ALLOWED_EVENTS):
            groups = hooks[event]
            if len(groups) != 1 or len(groups[0]["hooks"]) != 1:
                raise ValueError("Expected one handler per recovery event")
            handler = groups[0]["hooks"][0]
            if handler.get("type") != "command" or handler.get("command") != expected:
                raise ValueError("Hook command does not match the packaged adapter")
            if handler.get("commandWindows") != 'py -3 "%PLUGIN_ROOT%\\plugins\\codex\\hooks\\praxis_context.py"':
                raise ValueError("Windows hook command does not match the packaged adapter")
            limit = handler.get("additionalContextLimit")
            if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
                raise ValueError("Hook context limit must be a positive integer")
            if event == "SessionStart" and groups[0].get("matcher") != "^(startup|resume|clear|compact)$":
                raise ValueError("Recovery sources are incomplete")
            if event == "UserPromptSubmit" and "matcher" in groups[0]:
                raise ValueError("Prompt recovery must not depend on prompt matching")
        report["hook_config"] = {"status": "ok", "path": str(PLUGIN_ROOT / relative)}
    except (OSError, ValueError, KeyError, TypeError) as error:
        report["hook_config"] = {"status": "error", "error_type": type(error).__name__}

    config = Path(host_config) if host_config else Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"
    try:
        import tomllib
        value = tomllib.loads(config.read_text(encoding="utf-8"))
        entries = [v for k, v in value.get("hooks", {}).get("state", {}).items()
                   if k.startswith("praxis@praxis:")]
        report["host_configuration"] = {
            "status": "inspected", "path": str(config),
            "plugin_enabled": value.get("plugins", {}).get("praxis@praxis", {}).get("enabled"),
            "trust": "recorded_current_hash_unverified" if any(v.get("trusted_hash") for v in entries) else "not_recorded",
            "disabled_entries": sum(v.get("enabled") is False or v.get("disabled") is True for v in entries),
            "meaning": "This config file alone does not establish effective host policy or trust of the current definition.",
        }
    except (ImportError, OSError, ValueError, TypeError, AttributeError) as error:
        report["host_configuration"] = {"status": "unknown", "path": str(config), "error_type": type(error).__name__,
                                        "hint": "Inspect Codex hook trust in the host; TOML inspection needs Python 3.11+."}

    event = {"hook_event_name": "SessionStart", "source": "startup", "cwd": cwd}
    launcher = ["py", "-3"] if os.name == "nt" else ["python3"]
    try:
        result = subprocess.run([*launcher, str(Path(__file__).resolve()), "--probe"],
                                input=json.dumps(event), text=True, capture_output=True,
                                timeout=5, shell=False, cwd=cwd)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] if result.stdout else None
        report["script_probe"] = {
            "status": "ok" if result.returncode == 0 and context != _FALLBACK_CONTEXT else "error",
            "returncode": result.returncode, "context_emitted": context is not None,
            "meaning": "Synthetic read-only probe; not a host invocation or model delivery receipt.",
        }
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        report["script_probe"] = {"status": "error", "error_type": type(error).__name__}
    return report


def main() -> int:
    if "--doctor" in sys.argv[1:]:
        parser = argparse.ArgumentParser()
        parser.add_argument("--doctor", action="store_true")
        parser.add_argument("--cwd", required=True)
        parser.add_argument("--host-config")
        args = parser.parse_args()
        print(json.dumps(doctor_report(args.cwd, args.host_config), sort_keys=True))
        return 0
    probe = "--probe" in sys.argv[1:]
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeError):
        return 0
    if not isinstance(event, dict):
        return 0
    if not probe:
        _observe(event, "started")
    context = build_context(event, synchronize=not probe)
    if context is None:
        if not probe:
            _observe(event, "no_context")
        return 0
    event_name = event.get("hook_event_name")
    if not isinstance(event_name, str):
        return 0
    try:
        print(json.dumps(build_response(event_name, context), ensure_ascii=False, sort_keys=True), flush=True)
    except OSError:
        if not probe:
            _observe(event, "output_failed")
        return 0
    if not probe:
        outcome = "recovery_failed" if context == _FALLBACK_CONTEXT else "paused" if context.startswith("Praxis is paused") else "context_emitted"
        _observe(event, outcome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
