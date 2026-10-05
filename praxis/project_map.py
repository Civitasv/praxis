"""Verified, section-concurrent project model state for Praxis."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Iterable

from .fingerprints import EvidenceError, capture_evidence, fingerprint_file
from .state import mutate_latest_state


_SECTION_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_ALLOWED_STATUSES = {"verified", "stale", "unknown"}
_ALLOWED_STALE_REASONS = {"changed", "missing", "unsafe", "unreadable"}


class ProjectModelError(RuntimeError):
    """Base class for neutral verified-project-model errors."""


class InvalidProjectModelError(ProjectModelError):
    pass


class SectionConflictError(ProjectModelError):
    def __init__(self, section_id: str, expected: int | None, actual: int | None) -> None:
        self.section_id = section_id
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"project-model section conflict for {section_id}: expected {expected}, actual {actual}"
        )


class UnknownSectionError(ProjectModelError):
    pass


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_section_id(section_id: object) -> str:
    if not isinstance(section_id, str) or _SECTION_ID.fullmatch(section_id) is None:
        raise InvalidProjectModelError(f"invalid project-model section id: {section_id!r}")
    return section_id


def _validate_nonempty(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidProjectModelError(f"{name} must be a non-empty string")
    return value


def _validate_evidence(evidence: object) -> None:
    if not isinstance(evidence, list):
        raise InvalidProjectModelError("section evidence must be a list")
    seen: set[str] = set()
    previous: str | None = None
    for item in evidence:
        if not isinstance(item, dict):
            raise InvalidProjectModelError("evidence entries must be objects")
        path = item.get("path")
        digest = item.get("sha256")
        if not isinstance(path, str) or not path or path in seen:
            raise InvalidProjectModelError("evidence paths must be unique non-empty strings")
        if previous is not None and path < previous:
            raise InvalidProjectModelError("evidence paths must be sorted")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            raise InvalidProjectModelError(f"invalid evidence sha256 for {path}")
        seen.add(path)
        previous = path


def _validate_stale_reasons(reasons: object) -> None:
    if not isinstance(reasons, list):
        raise InvalidProjectModelError("stale_reasons must be a list")
    previous: tuple[str, str] | None = None
    for reason in reasons:
        if not isinstance(reason, dict):
            raise InvalidProjectModelError("stale reasons must be objects")
        path = reason.get("path")
        kind = reason.get("reason")
        if not isinstance(path, str) or not path or kind not in _ALLOWED_STALE_REASONS:
            raise InvalidProjectModelError("invalid stale reason")
        key = (path, kind)
        if previous is not None and key < previous:
            raise InvalidProjectModelError("stale reasons must be sorted")
        previous = key


def _validate_section(section_id: object, section: object) -> None:
    _validate_section_id(section_id)
    if not isinstance(section, dict):
        raise InvalidProjectModelError(f"section {section_id} must be an object")
    _validate_nonempty(f"section {section_id} title", section.get("title"))
    _validate_nonempty(f"section {section_id} content", section.get("content"))
    revision = section.get("revision")
    if not _is_int(revision) or revision < 0:
        raise InvalidProjectModelError(f"section {section_id} revision must be non-negative")
    status = section.get("status")
    if status not in _ALLOWED_STATUSES:
        raise InvalidProjectModelError(f"section {section_id} has invalid status")
    _validate_evidence(section.get("evidence"))
    _validate_stale_reasons(section.get("stale_reasons"))
    if status == "verified" and not section["evidence"]:
        raise InvalidProjectModelError(f"section {section_id} cannot be verified without evidence")
    if status == "unknown" and section["evidence"]:
        raise InvalidProjectModelError(f"section {section_id} cannot be unknown with evidence")
    if status != "stale" and section["stale_reasons"]:
        raise InvalidProjectModelError(f"section {section_id} has stale reasons while not stale")


def _validate_model(model: object) -> dict[str, Any]:
    if not isinstance(model, dict):
        raise InvalidProjectModelError("project_model must be an object")
    revision = model.get("revision")
    if not _is_int(revision) or revision < 0:
        raise InvalidProjectModelError("project_model revision must be non-negative")
    sections = model.get("sections")
    if not isinstance(sections, dict):
        raise InvalidProjectModelError("project_model sections must be an object")
    for section_id, section in sections.items():
        _validate_section(section_id, section)
    return model


def get_project_model(state: dict[str, Any]) -> dict[str, Any]:
    """Return a validated copy of the authoritative model or an empty virtual model."""

    if "project_model" not in state:
        return {"revision": 0, "sections": {}}
    return copy.deepcopy(_validate_model(state["project_model"]))


def _model_for_mutation(state: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    existing = state.get("project_model")
    if existing is None:
        return {"revision": 0, "sections": {}}, False
    return copy.deepcopy(_validate_model(existing)), True


def upsert_section(
    project_root: Path,
    section_id: str,
    title: str,
    content: str,
    evidence_paths: Iterable[str | Path],
    expected_section_revision: int | None = None,
) -> dict[str, Any]:
    """Create or update one project-model section with section-level CAS."""

    section_id = _validate_section_id(section_id)
    title = _validate_nonempty("section title", title)
    content = _validate_nonempty("section content", content)
    evidence = capture_evidence(project_root, evidence_paths)

    def mutate(state: dict[str, Any]) -> None:
        model, existed = _model_for_mutation(state)
        current = model["sections"].get(section_id)
        if current is None:
            if expected_section_revision is not None:
                raise SectionConflictError(section_id, expected_section_revision, None)
            section_revision = 0
        else:
            actual = current["revision"]
            if expected_section_revision != actual:
                raise SectionConflictError(section_id, expected_section_revision, actual)
            section_revision = actual + 1

        model["sections"][section_id] = {
            "title": title,
            "revision": section_revision,
            "status": "verified" if evidence else "unknown",
            "content": content,
            "evidence": evidence,
            "stale_reasons": [],
        }
        if existed:
            model["revision"] += 1
        _validate_model(model)
        state["project_model"] = model
        return None

    return mutate_latest_state(project_root, mutate)


def remove_section(
    project_root: Path,
    section_id: str,
    expected_section_revision: int,
) -> dict[str, Any]:
    """Remove one project-model section with exact section-revision CAS."""

    section_id = _validate_section_id(section_id)
    if not _is_int(expected_section_revision) or expected_section_revision < 0:
        raise InvalidProjectModelError("expected_section_revision must be a non-negative integer")

    def mutate(state: dict[str, Any]) -> None:
        if "project_model" not in state:
            raise UnknownSectionError(f"unknown project-model section: {section_id}")
        model, _ = _model_for_mutation(state)
        current = model["sections"].get(section_id)
        if current is None:
            raise UnknownSectionError(f"unknown project-model section: {section_id}")
        actual = current["revision"]
        if expected_section_revision != actual:
            raise SectionConflictError(section_id, expected_section_revision, actual)
        del model["sections"][section_id]
        model["revision"] += 1
        _validate_model(model)
        state["project_model"] = model
        return None

    return mutate_latest_state(project_root, mutate)


def refresh_staleness(project_root: Path) -> dict[str, Any]:
    """Recompute source fingerprints and mark only affected sections stale."""

    root = Path(project_root).resolve()

    def mutate(state: dict[str, Any]) -> None:
        if "project_model" not in state:
            return None
        model, _ = _model_for_mutation(state)
        changed = False

        for section_id in sorted(model["sections"]):
            section = model["sections"][section_id]
            evidence = section["evidence"]
            if not evidence:
                continue

            reasons: list[dict[str, str]] = []
            for stored in evidence:
                path = stored["path"]
                try:
                    current = fingerprint_file(root, path)
                except EvidenceError as error:
                    reason = error.reason if error.reason in _ALLOWED_STALE_REASONS else "unreadable"
                    reasons.append({"path": path, "reason": reason})
                    continue
                if current["sha256"] != stored["sha256"]:
                    reasons.append({"path": path, "reason": "changed"})

            reasons.sort(key=lambda item: (item["path"], item["reason"]))
            status = "stale" if reasons else "verified"
            if section["status"] != status or section["stale_reasons"] != reasons:
                section["status"] = status
                section["stale_reasons"] = reasons
                changed = True

        if changed:
            model["revision"] += 1
            _validate_model(model)
            state["project_model"] = model
        return None

    return mutate_latest_state(root, mutate)
