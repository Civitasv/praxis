"""Machine-owned source evidence fingerprints for Praxis."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable


class EvidenceError(ValueError):
    """Raised when a project-model evidence path cannot be safely fingerprinted."""


def _normalized_relative_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        raise EvidenceError(f"evidence path must be project-relative: {path}")
    normalized = Path(os.path.normpath(str(candidate)))
    if normalized == Path(".") or ".." in normalized.parts:
        raise EvidenceError(f"evidence path escapes project: {path}")
    if normalized.parts and normalized.parts[0] in {".praxis", ".git"}:
        raise EvidenceError(f"evidence path targets Praxis/Git internals: {path}")
    return normalized


def fingerprint_file(project_root: Path, path: str | Path) -> dict[str, str]:
    """Fingerprint one safe project-relative regular file with SHA-256."""

    root = Path(project_root).resolve()
    relative = _normalized_relative_path(path)
    lexical = root / relative

    try:
        resolved = lexical.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise EvidenceError(f"evidence file does not exist or cannot be resolved: {relative.as_posix()}") from error

    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise EvidenceError(f"evidence path resolves outside project: {relative.as_posix()}") from error

    if not resolved.is_file():
        raise EvidenceError(f"evidence path must resolve to a regular file: {relative.as_posix()}")

    try:
        payload = resolved.read_bytes()
    except OSError as error:
        raise EvidenceError(f"unable to read evidence file: {relative.as_posix()}") from error

    return {
        "path": relative.as_posix(),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def capture_evidence(project_root: Path, paths: Iterable[str | Path]) -> list[dict[str, str]]:
    """Capture unique evidence records sorted by normalized project-relative path."""

    records: dict[str, dict[str, str]] = {}
    for path in paths:
        evidence = fingerprint_file(project_root, path)
        records[evidence["path"]] = evidence
    return [records[path] for path in sorted(records)]
