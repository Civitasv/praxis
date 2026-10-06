"""Shared recovery CLI bridge and bounded renderer for host adapters."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


MAX_CONTEXT_CHARS = 3000
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
_RECOVERY_FOOTER = (
    "Recovery is not approval. Use the shared Praxis Tutor Skill for details."
)
_FALLBACK_CONTEXT = (
    "Praxis automatic recovery is unavailable. "
    "Use the shared Praxis Tutor Skill manually. "
    "Do not assume durable state was restored. "
    "Recovery is not approval."
)


class RecoveryHookError(RuntimeError):
    """Raised when the neutral Praxis recovery CLI cannot be consumed safely."""


def build_invocation(
    *,
    cwd: str,
    host: str,
    conversation_id: str | None,
    python_executable: str | None = None,
) -> dict[str, Any]:
    if not isinstance(cwd, str) or not cwd.strip():
        raise RecoveryHookError("cwd must be a non-empty string")
    if not isinstance(host, str) or not host.strip():
        raise RecoveryHookError("host must be a non-empty string")
    if conversation_id is not None and (
        not isinstance(conversation_id, str) or not conversation_id.strip()
    ):
        raise RecoveryHookError(
            "conversation_id must be a non-empty string when provided"
        )

    args = [
        "-m",
        "praxis",
        "recovery-status",
        "--cwd",
        cwd,
        "--host",
        host,
    ]
    if conversation_id is not None:
        args.extend(["--conversation-id", conversation_id])

    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    root = str(PLUGIN_ROOT)
    env["PYTHONPATH"] = (
        root if not existing else root + os.pathsep + existing
    )

    return {
        "command": python_executable or sys.executable,
        "args": args,
        "cwd": cwd,
        "env": env,
        "shell": False,
    }


def run_recovery_status(
    *,
    cwd: str,
    host: str,
    conversation_id: str | None,
    python_executable: str | None = None,
) -> dict[str, Any]:
    invocation = build_invocation(
        cwd=cwd,
        host=host,
        conversation_id=conversation_id,
        python_executable=python_executable,
    )
    try:
        completed = subprocess.run(
            [invocation["command"], *invocation["args"]],
            cwd=invocation["cwd"],
            env=invocation["env"],
            shell=False,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RecoveryHookError(f"unable to run Praxis recovery CLI: {error}") from error

    if completed.returncode != 0:
        raise RecoveryHookError(
            "Praxis recovery CLI failed"
            + (f": {completed.stderr.strip()}" if completed.stderr.strip() else "")
        )

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RecoveryHookError("Praxis recovery CLI returned malformed JSON") from error

    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise RecoveryHookError("Praxis recovery CLI returned an unsuccessful response")
    snapshot = payload.get("recovery")
    if not isinstance(snapshot, dict):
        raise RecoveryHookError("Praxis recovery response is missing a snapshot")
    return snapshot


def _inline_text(value: object) -> str:
    return " ".join(str(value).split())


def _task_line(task: dict[str, Any]) -> str:
    task_id = _inline_text(task.get("id", "unknown-task"))
    title = _inline_text(task.get("title") or "(untitled)")
    stage = _inline_text(task.get("stage", "unknown"))
    status = _inline_text(task.get("status", "unknown"))
    return f"{task_id} — {title} [stage={stage}, status={status}]"


def _decision_line(decision: dict[str, Any]) -> str:
    decision_id = _inline_text(decision.get("id", "unknown-decision"))
    title = _inline_text(decision.get("title", "(untitled)"))
    decision_class = _inline_text(decision.get("class", "unknown"))
    return (
        f"Open decision: {decision_id} — {title} "
        f"[class={decision_class}]"
    )


def _bounded_context(lines: list[str]) -> str:
    kept: list[str] = []
    used = 0
    budget = MAX_CONTEXT_CHARS - len(_RECOVERY_FOOTER) - 1

    for raw in lines:
        line = _inline_text(raw)
        separator = 1 if kept else 0
        available = budget - used - separator
        if available <= 0:
            break
        if len(line) <= available:
            kept.append(line)
            used += separator + len(line)
            continue
        if available > 1:
            kept.append(line[: available - 1] + "…")
        break

    if not kept:
        return _RECOVERY_FOOTER[:MAX_CONTEXT_CHARS]
    return "\n".join(kept) + "\n" + _RECOVERY_FOOTER


def render_recovery_context(snapshot: dict[str, Any]) -> str | None:
    if snapshot.get("initialized") is not True:
        return None
    if snapshot.get("enabled") is not True:
        return (
            "Praxis is paused for this project. "
            "Do not activate Tutor behavior until the user explicitly resumes it."
        )

    lines = [
        "Praxis is enabled for this project.",
        "Load and follow the shared Praxis Tutor Skill.",
    ]

    resolution = snapshot.get("task_resolution")
    if isinstance(resolution, dict):
        kind = resolution.get("kind")
        task = resolution.get("task")
        candidates = resolution.get("candidates")
        if kind == "exact" and isinstance(task, dict):
            lines.append(f"Recovered task: {_task_line(task)}")
        elif kind == "exact_ambiguous" and isinstance(candidates, list):
            lines.append(
                "Multiple matching host tasks; ask the user which task to continue:"
            )
            for candidate in candidates:
                if isinstance(candidate, dict):
                    lines.append(f"- {_task_line(candidate)}")
        elif kind == "candidate" and isinstance(task, dict):
            lines.append(f"Recoverable task candidate: {_task_line(task)}")
            lines.append(
                "This task is a candidate only; do not adopt or rebind it "
                "without the user's choice."
            )
        elif kind == "candidate_ambiguous" and isinstance(candidates, list):
            lines.append(
                "Multiple pending task candidates; ask the user which task to continue:"
            )
            for candidate in candidates:
                if isinstance(candidate, dict):
                    lines.append(f"- {_task_line(candidate)}")

    decisions = snapshot.get("open_decisions")
    if isinstance(decisions, list):
        for decision in decisions:
            if isinstance(decision, dict):
                lines.append(_decision_line(decision))

    blocked = snapshot.get("blocked_scopes")
    if isinstance(blocked, list) and blocked:
        lines.append(
            "Blocked scopes: "
            + ", ".join(_inline_text(value) for value in blocked)
        )

    model = snapshot.get("project_model")
    if isinstance(model, dict):
        stale = model.get("stale_sections")
        if isinstance(stale, list) and stale:
            lines.append(
                "Stale project sections: "
                + ", ".join(_inline_text(value) for value in stale)
            )
        unknown = model.get("unknown_sections")
        if isinstance(unknown, list) and unknown:
            lines.append(
                "Unknown project sections: "
                + ", ".join(_inline_text(value) for value in unknown)
            )

    return _bounded_context(lines)


def render_recovery_fallback() -> str:
    return _FALLBACK_CONTEXT[:MAX_CONTEXT_CHARS]
