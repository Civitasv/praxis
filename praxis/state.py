"""Versioned Praxis project state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .project import state_directory, state_file


FORMAT_VERSION = 1


class PraxisStateError(RuntimeError):
    """Base class for neutral Praxis state errors."""


class MalformedStateError(PraxisStateError):
    pass


class InvalidStateError(PraxisStateError):
    pass


class UnsupportedFormatError(PraxisStateError):
    pass


class RevisionConflictError(PraxisStateError):
    def __init__(self, expected: int | None, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"state revision conflict: expected {expected}, actual {actual}")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


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
    return value


def load_state(project_root: Path) -> dict[str, Any] | None:
    path = state_file(project_root)
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
        value = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MalformedStateError(f"unable to read valid Praxis state: {path}") from error
    return _validate_state(value)


def _write_state_unlocked(project_root: Path, state: dict[str, Any]) -> None:
    directory = state_directory(project_root, create=True)
    path = directory / "state.json"
    path.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def enable_state(project_root: Path, expected_revision: int | None = None) -> dict[str, Any]:
    current = load_state(project_root)
    if current is None:
        state: dict[str, Any] = {
            "format_version": FORMAT_VERSION,
            "revision": 0,
            "enabled": True,
            "tasks": {},
        }
        _write_state_unlocked(project_root, state)
        return state

    if current["enabled"] is True:
        return current
    if expected_revision != current["revision"]:
        raise RevisionConflictError(expected_revision, current["revision"])

    updated = dict(current)
    updated["enabled"] = True
    updated["revision"] = current["revision"] + 1
    _write_state_unlocked(project_root, updated)
    return updated
