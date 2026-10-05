"""Versioned Praxis project state."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable

from .locking import StateLock
from .project import state_directory, state_file


FORMAT_VERSION = 1
TASK_STAGES = {
    "understanding",
    "design",
    "awaiting_decision",
    "implementation",
    "verification",
    "complete",
    "blocked",
}
TASK_STATUSES = {"active", "blocked", "complete"}


class PraxisStateError(RuntimeError):
    """Base class for neutral Praxis state errors."""


class MalformedStateError(PraxisStateError):
    pass


class InvalidStateError(PraxisStateError):
    pass


class UnsupportedFormatError(PraxisStateError):
    pass


class StateNotInitializedError(PraxisStateError):
    pass


class StateWriteError(PraxisStateError):
    pass


class RevisionConflictError(PraxisStateError):
    def __init__(self, expected: int | None, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"state revision conflict: expected {expected}, actual {actual}")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_task_id(task_id: object) -> bool:
    if not isinstance(task_id, str) or not task_id.startswith("task_"):
        return False
    suffix = task_id[5:]
    return bool(suffix) and all(char in "0123456789abcdef" for char in suffix)


def _validate_task_record(task_id: object, task: object) -> None:
    if not _validate_task_id(task_id):
        raise InvalidStateError(f"invalid task id: {task_id!r}")
    if not isinstance(task, dict):
        raise InvalidStateError(f"task {task_id} must be an object")

    host = task.get("host")
    if not isinstance(host, str) or not host.strip():
        raise InvalidStateError(f"task {task_id} host must be a non-empty string")
    if task.get("stage") not in TASK_STAGES:
        raise InvalidStateError(f"task {task_id} has invalid stage")
    if task.get("status") not in TASK_STATUSES:
        raise InvalidStateError(f"task {task_id} has invalid status")

    choices = task.get("pending_choices")
    if not isinstance(choices, list) or any(
        not isinstance(choice, str) or not choice for choice in choices
    ):
        raise InvalidStateError(f"task {task_id} pending_choices must be strings")

    for field in ("conversation_id", "title"):
        if field in task and (
            not isinstance(task[field], str) or not task[field].strip()
        ):
            raise InvalidStateError(f"task {task_id} {field} must be a non-empty string")


def _validate_state(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InvalidStateError("state must be a JSON object")

    version = value.get("format_version")
    if not _is_int(version):
        raise InvalidStateError("format_version must be an integer")
    if version != FORMAT_VERSION:
        raise UnsupportedFormatError(f"unsupported state format version: {version}")

    revision = value.get("revision")
    if not _is_int(revision) or revision < 0:
        raise InvalidStateError("revision must be a non-negative integer")
    if not isinstance(value.get("enabled"), bool):
        raise InvalidStateError("enabled must be a boolean")
    if not isinstance(value.get("tasks"), dict):
        raise InvalidStateError("tasks must be an object")
    for task_id, task in value["tasks"].items():
        _validate_task_record(task_id, task)
    return value


def load_state(project_root: Path) -> dict[str, Any] | None:
    path = state_file(project_root)
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise MalformedStateError(f"unable to parse Praxis state: {path}") from error
    except (OSError, UnicodeError) as error:
        raise MalformedStateError(f"unable to read Praxis state: {path}") from error
    return _validate_state(value)


def _fsync_directory(directory: Path) -> None:
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _atomic_write_state(project_root: Path, state: dict[str, Any]) -> None:
    _validate_state(state)
    directory = state_directory(project_root, create=True)
    path = state_file(project_root)
    try:
        payload = json.dumps(state, ensure_ascii=False, sort_keys=True) + "\n"
    except (TypeError, ValueError) as error:
        raise StateWriteError("Praxis state is not JSON serializable") from error

    descriptor: int | None = None
    temporary_path: Path | None = None
    try:
        descriptor, raw_path = tempfile.mkstemp(prefix=".state-", dir=directory)
        temporary_path = Path(raw_path)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = None
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
        _fsync_directory(directory)
    except (OSError, UnicodeError) as error:
        raise StateWriteError(f"failed to persist Praxis state: {path}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _mutate_locked(
    project_root: Path,
    expected_revision: int,
    mutator: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> dict[str, Any]:
    current = load_state(project_root)
    if current is None:
        raise StateNotInitializedError("Praxis state is not initialized")
    if expected_revision != current["revision"]:
        raise RevisionConflictError(expected_revision, current["revision"])

    working = copy.deepcopy(current)
    candidate = mutator(working)
    updated = working if candidate is None else candidate
    if not isinstance(updated, dict):
        raise InvalidStateError("state mutator must return an object or None")
    updated["revision"] = current["revision"] + 1
    _validate_state(updated)
    _atomic_write_state(project_root, updated)
    return updated


def mutate_state(
    project_root: Path,
    expected_revision: int,
    mutator: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> dict[str, Any]:
    with StateLock(project_root):
        return _mutate_locked(project_root, expected_revision, mutator)


def enable_state(project_root: Path, expected_revision: int | None = None) -> dict[str, Any]:
    with StateLock(project_root):
        current = load_state(project_root)
        if current is None:
            state: dict[str, Any] = {
                "format_version": FORMAT_VERSION,
                "revision": 0,
                "enabled": True,
                "tasks": {},
            }
            _atomic_write_state(project_root, state)
            return state

        if current["enabled"] is True:
            return current
        if expected_revision != current["revision"]:
            raise RevisionConflictError(expected_revision, current["revision"])
        return _mutate_locked(
            project_root,
            current["revision"],
            lambda state: {**state, "enabled": True},
        )


def pause_state(project_root: Path, expected_revision: int) -> dict[str, Any]:
    return mutate_state(
        project_root,
        expected_revision,
        lambda state: {**state, "enabled": False},
    )
