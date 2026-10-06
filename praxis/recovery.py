"""Host-neutral durable recovery snapshot for Praxis adapters."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .decisions import decision_blocked_scopes, list_open_decisions
from .project_map import get_project_model, refresh_staleness
from .state import load_state
from .tasks import pending_tasks


def _task_summary(task_id: str, task: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "id": task_id,
        "host": task["host"],
        "stage": task["stage"],
        "status": task["status"],
    }
    for field in ("conversation_id", "title"):
        value = task.get(field)
        if isinstance(value, str):
            summary[field] = value
    return summary


def _project_model_summary(state: dict[str, Any]) -> dict[str, list[str]]:
    model = get_project_model(state)
    stale: list[str] = []
    unknown: list[str] = []
    for section_id in sorted(model["sections"]):
        status = model["sections"][section_id]["status"]
        if status == "stale":
            stale.append(section_id)
        elif status == "unknown":
            unknown.append(section_id)
    return {
        "stale_sections": stale,
        "unknown_sections": unknown,
    }


def _empty_resolution() -> dict[str, Any]:
    return {"kind": "none", "task": None, "candidates": []}


def _base_snapshot(
    *,
    initialized: bool,
    enabled: bool,
    revision: int | None,
    project_model: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    return {
        "initialized": initialized,
        "enabled": enabled,
        "revision": revision,
        "task_resolution": _empty_resolution(),
        "open_decisions": [],
        "blocked_scopes": [],
        "project_model": project_model
        if project_model is not None
        else {"stale_sections": [], "unknown_sections": []},
    }


def recovery_status(
    project_root: Path,
    *,
    host: str,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Return a compact durable recovery snapshot without advancing lifecycle.

    Enabled projects refresh machine-owned project-model freshness first.
    Uninitialized and paused projects remain read-only.
    """

    if not isinstance(host, str) or not host.strip():
        raise ValueError("host must be a non-empty string")
    if conversation_id is not None and (
        not isinstance(conversation_id, str) or not conversation_id.strip()
    ):
        raise ValueError("conversation_id must be a non-empty string when provided")

    root = Path(project_root).resolve()
    state = load_state(root)
    if state is None:
        return _base_snapshot(initialized=False, enabled=False, revision=None)

    if not state["enabled"]:
        return _base_snapshot(
            initialized=True,
            enabled=False,
            revision=state["revision"],
            project_model=_project_model_summary(state),
        )

    state = refresh_staleness(root)
    snapshot = _base_snapshot(
        initialized=True,
        enabled=True,
        revision=state["revision"],
        project_model=_project_model_summary(state),
    )

    exact: list[tuple[str, dict[str, Any]]] = []
    if conversation_id is not None:
        for task_id, task in sorted(state["tasks"].items()):
            if (
                task.get("status") != "complete"
                and task.get("host") == host
                and task.get("conversation_id") == conversation_id
            ):
                exact.append((task_id, task))

    context_task_id: str | None = None
    if len(exact) == 1:
        task_id, task = exact[0]
        context_task_id = task_id
        snapshot["task_resolution"] = {
            "kind": "exact",
            "task": _task_summary(task_id, task),
            "candidates": [],
        }
    elif len(exact) > 1:
        snapshot["task_resolution"] = {
            "kind": "exact_ambiguous",
            "task": None,
            "candidates": [
                _task_summary(task_id, task) for task_id, task in exact
            ],
        }
    else:
        candidates = sorted(pending_tasks(state).items())
        if len(candidates) == 1:
            task_id, task = candidates[0]
            context_task_id = task_id
            snapshot["task_resolution"] = {
                "kind": "candidate",
                "task": _task_summary(task_id, task),
                "candidates": [],
            }
        elif len(candidates) > 1:
            snapshot["task_resolution"] = {
                "kind": "candidate_ambiguous",
                "task": None,
                "candidates": [
                    _task_summary(task_id, task) for task_id, task in candidates
                ],
            }

    if context_task_id is not None:
        open_records = list_open_decisions(state, task_id=context_task_id)
        snapshot["open_decisions"] = [
            {
                "id": decision_id,
                "task_id": record["task_id"],
                "class": record["class"],
                "status": record["status"],
                "title": record["title"],
                "revision": record["revision"],
            }
            for decision_id, record in sorted(open_records.items())
        ]
        snapshot["blocked_scopes"] = decision_blocked_scopes(
            state, task_id=context_task_id
        )

    return copy.deepcopy(snapshot)
