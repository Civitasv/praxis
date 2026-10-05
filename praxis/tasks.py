"""Durable Praxis task lifecycle."""

from __future__ import annotations

import copy
from pathlib import Path
import secrets
from typing import Any

from .state import InvalidStateError, TASK_STAGES, TASK_STATUSES, mutate_state


ALLOWED_STAGES = TASK_STAGES
ALLOWED_STATUSES = TASK_STATUSES


class InvalidTaskError(InvalidStateError):
    pass


def _validate_host(host: str) -> None:
    if not isinstance(host, str) or not host.strip():
        raise InvalidTaskError("host must be a non-empty string")


def _validate_optional_string(name: str, value: str | None) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise InvalidTaskError(f"{name} must be a non-empty string when provided")


def _validate_pending_choices(values: list[str]) -> None:
    if not isinstance(values, list) or any(
        not isinstance(value, str) or not value for value in values
    ):
        raise InvalidTaskError("pending_choices must be a list of non-empty strings")


def create_task(
    project_root: Path,
    expected_revision: int,
    host: str,
    conversation_id: str | None = None,
    title: str | None = None,
) -> tuple[str, dict[str, Any]]:
    _validate_host(host)
    _validate_optional_string("conversation_id", conversation_id)
    _validate_optional_string("title", title)
    task_id = f"task_{secrets.token_hex(8)}"

    def add_task(state: dict[str, Any]) -> None:
        if task_id in state["tasks"]:
            raise InvalidTaskError(f"task id collision: {task_id}")
        task: dict[str, Any] = {
            "host": host,
            "stage": "understanding",
            "status": "active",
            "pending_choices": [],
        }
        if conversation_id is not None:
            task["conversation_id"] = conversation_id
        if title is not None:
            task["title"] = title
        state["tasks"][task_id] = task
        return None

    state = mutate_state(project_root, expected_revision, add_task)
    return task_id, state


def update_task(
    project_root: Path,
    expected_revision: int,
    task_id: str,
    *,
    stage: str | None = None,
    status: str | None = None,
    pending_choices: list[str] | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    if stage is not None and stage not in ALLOWED_STAGES:
        raise InvalidTaskError(f"unsupported task stage: {stage}")
    if status is not None and status not in ALLOWED_STATUSES:
        raise InvalidTaskError(f"unsupported task status: {status}")
    if pending_choices is not None:
        _validate_pending_choices(pending_choices)
    if title is not None:
        _validate_optional_string("title", title)

    def edit_task(state: dict[str, Any]) -> None:
        task = state["tasks"].get(task_id)
        if not isinstance(task, dict):
            raise InvalidTaskError(f"unknown task id: {task_id}")
        if stage is not None:
            task["stage"] = stage
        if status is not None:
            task["status"] = status
        if pending_choices is not None:
            task["pending_choices"] = list(pending_choices)
        if title is not None:
            task["title"] = title
        return None

    return mutate_state(project_root, expected_revision, edit_task)


def pending_tasks(state: dict[str, Any]) -> dict[str, Any]:
    tasks = state.get("tasks")
    if not isinstance(tasks, dict):
        raise InvalidTaskError("state tasks must be an object")
    return {
        task_id: copy.deepcopy(task)
        for task_id, task in tasks.items()
        if isinstance(task, dict) and task.get("status") != "complete"
    }
