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
DECISION_CLASSES = {"engineering", "architectural"}
DECISION_STATUSES = {"open", "selected", "implemented", "verified", "superseded", "abandoned"}
DECISION_LIST_FIELDS = {
    "verified_constraints",
    "alternatives",
    "accepted_tradeoffs",
    "blocked_scopes",
    "later_evidence",
}
DECISION_OPTIONAL_TEXT_FIELDS = {
    "user_proposal",
    "praxis_challenge",
    "selected_decision",
    "user_reasoning",
    "implementation_result",
    "verification",
    "superseding_decision_id",
}


class PraxisStateError(RuntimeError):
    """Base class for neutral Praxis state errors."""


class MalformedStateError(PraxisStateError):
    pass


class StateReadError(PraxisStateError):
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


def _validate_decision_id(decision_id: object) -> bool:
    if not isinstance(decision_id, str) or not decision_id.startswith("decision_"):
        return False
    suffix = decision_id[9:]
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


def _validate_string_list(name: str, value: object) -> None:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise InvalidStateError(f"{name} must be a list of non-empty strings")


def _validate_decision_provenance_order(decision_id: object, record: dict[str, Any]) -> None:
    selected = record.get("selected_decision")
    implementation = record.get("implementation_result")
    verification = record.get("verification")
    user_reasoning = record.get("user_reasoning")
    accepted_tradeoffs = record.get("accepted_tradeoffs")

    if selected is None:
        if user_reasoning is not None or accepted_tradeoffs:
            raise InvalidStateError(
                f"decision {decision_id} cannot record user selection reasoning before selection"
            )
        if implementation is not None or verification is not None:
            raise InvalidStateError(
                f"decision {decision_id} cannot record implementation or verification before selection"
            )
    if implementation is None and verification is not None:
        raise InvalidStateError(
            f"decision {decision_id} cannot record verification before implementation"
        )


def _validate_decision_lifecycle(decision_id: object, record: dict[str, Any]) -> None:
    status = record["status"]
    selected = record.get("selected_decision")
    implementation = record.get("implementation_result")
    verification = record.get("verification")
    superseding = record.get("superseding_decision_id")

    _validate_decision_provenance_order(decision_id, record)

    if status == "open":
        if selected is not None or implementation is not None or verification is not None:
            raise InvalidStateError(f"decision {decision_id} open state contains later lifecycle data")
    elif status == "selected":
        if selected is None or implementation is not None or verification is not None:
            raise InvalidStateError(f"decision {decision_id} selected state is inconsistent")
    elif status == "implemented":
        if selected is None or implementation is None or verification is not None:
            raise InvalidStateError(f"decision {decision_id} implemented state is inconsistent")
    elif status == "verified":
        if selected is None or implementation is None or verification is None:
            raise InvalidStateError(f"decision {decision_id} verified state is inconsistent")

    if status == "superseded":
        if not _validate_decision_id(superseding) or superseding == decision_id:
            raise InvalidStateError(f"decision {decision_id} has invalid superseding decision id")
    elif superseding is not None:
        raise InvalidStateError(
            f"decision {decision_id} records a superseding decision while status is {status}"
        )


def _validate_decision_record(decision_id: object, record: object, tasks: dict[str, Any]) -> None:
    if not _validate_decision_id(decision_id):
        raise InvalidStateError(f"invalid decision id: {decision_id!r}")
    if not isinstance(record, dict):
        raise InvalidStateError(f"decision {decision_id} must be an object")
    revision = record.get("revision")
    if not _is_int(revision) or revision < 0:
        raise InvalidStateError(f"decision {decision_id} revision must be non-negative")
    task_id = record.get("task_id")
    if not isinstance(task_id, str) or task_id not in tasks:
        raise InvalidStateError(f"decision {decision_id} references unknown task")
    if record.get("class") not in DECISION_CLASSES:
        raise InvalidStateError(f"decision {decision_id} has invalid class")
    if record.get("status") not in DECISION_STATUSES:
        raise InvalidStateError(f"decision {decision_id} has invalid status")
    for field in ("title", "context"):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            raise InvalidStateError(f"decision {decision_id} {field} must be non-empty")
    for field in DECISION_LIST_FIELDS:
        _validate_string_list(f"decision {decision_id} {field}", record.get(field))
    for field in DECISION_OPTIONAL_TEXT_FIELDS:
        if field not in record:
            if field == "superseding_decision_id":
                continue
            raise InvalidStateError(f"decision {decision_id} missing {field}")
        value = record.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise InvalidStateError(f"decision {decision_id} {field} must be non-empty when recorded")
    _validate_decision_lifecycle(decision_id, record)


def _validate_decisions(value: object, tasks: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise InvalidStateError("decisions must be an object")
    revision = value.get("revision")
    if not _is_int(revision) or revision < 0:
        raise InvalidStateError("decisions revision must be non-negative")
    records = value.get("records")
    if not isinstance(records, dict):
        raise InvalidStateError("decisions records must be an object")
    for decision_id, record in records.items():
        _validate_decision_record(decision_id, record, tasks)
    for decision_id, record in records.items():
        if record.get("status") == "superseded":
            replacement = record.get("superseding_decision_id")
            if replacement not in records:
                raise InvalidStateError(
                    f"decision {decision_id} references unknown superseding decision"
                )


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
    if "decisions" in value:
        _validate_decisions(value["decisions"], value["tasks"])
    return value


def load_state(project_root: Path) -> dict[str, Any] | None:
    path = state_file(project_root)
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise StateReadError(f"unable to read Praxis state: {path}") from error
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise MalformedStateError(f"unable to parse Praxis state: {path}") from error
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


def _apply_mutator(
    current: dict[str, Any],
    mutator: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> dict[str, Any]:
    working = copy.deepcopy(current)
    candidate = mutator(working)
    updated = working if candidate is None else candidate
    if not isinstance(updated, dict):
        raise InvalidStateError("state mutator must return an object or None")
    return updated


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

    updated = _apply_mutator(current, mutator)
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


def mutate_latest_state(
    project_root: Path,
    mutator: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> dict[str, Any]:
    """Mutate the latest state under lock and avoid writing semantic no-ops."""

    with StateLock(project_root):
        current = load_state(project_root)
        if current is None:
            raise StateNotInitializedError("Praxis state is not initialized")

        updated = _apply_mutator(current, mutator)
        updated["revision"] = current["revision"]
        _validate_state(updated)
        if updated == current:
            return current

        updated["revision"] = current["revision"] + 1
        _validate_state(updated)
        _atomic_write_state(project_root, updated)
        return updated


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
