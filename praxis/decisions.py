"""Durable, provenance-preserving Tutor decisions for Praxis."""

from __future__ import annotations

import copy
from pathlib import Path
import secrets
from typing import Any, Callable, Iterable

from .state import mutate_latest_state


DURABLE_DECISION_CLASSES = {"engineering", "architectural"}
DECISION_STATUSES = {"open", "selected", "implemented", "verified", "superseded", "abandoned"}
TERMINAL_DECISION_STATUSES = {"verified", "superseded", "abandoned"}


class DecisionError(RuntimeError):
    """Base class for neutral decision errors."""


class InvalidDecisionError(DecisionError):
    pass


class DecisionConflictError(DecisionError):
    def __init__(self, decision_id: str, expected: int | None, actual: int | None) -> None:
        self.decision_id = decision_id
        self.expected = expected
        self.actual = actual
        super().__init__(f"decision conflict for {decision_id}: expected {expected}, actual {actual}")


class UnknownDecisionError(DecisionError):
    pass


class InvalidDecisionTransitionError(DecisionError):
    pass


class DecisionRenderError(DecisionError):
    pass


def _nonempty(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidDecisionError(f"{name} must be a non-empty string")
    return value


def _optional_text(name: str, value: object | None) -> str | None:
    if value is None:
        return None
    return _nonempty(name, value)


def _strings(name: str, values: Iterable[str] | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        raise InvalidDecisionError(f"{name} must be a list of non-empty strings")
    result = list(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise InvalidDecisionError(f"{name} must be a list of non-empty strings")
    return result


def get_decisions(state: dict[str, Any]) -> dict[str, Any]:
    aggregate = state.get("decisions")
    if aggregate is None:
        return {"revision": 0, "records": {}}
    if not isinstance(aggregate, dict):
        raise InvalidDecisionError("decisions must be an object")
    return copy.deepcopy(aggregate)


def get_decision(state: dict[str, Any], decision_id: str) -> dict[str, Any]:
    record = get_decisions(state)["records"].get(decision_id)
    if not isinstance(record, dict):
        raise UnknownDecisionError(f"unknown decision id: {decision_id}")
    return record


def create_decision(
    project_root: Path,
    task_id: str,
    decision_class: str,
    title: str,
    context: str,
    *,
    user_proposal: str | None = None,
    verified_constraints: Iterable[str] | None = None,
    praxis_challenge: str | None = None,
    alternatives: Iterable[str] | None = None,
    blocked_scopes: Iterable[str] | None = None,
) -> tuple[str, dict[str, Any]]:
    if decision_class not in DURABLE_DECISION_CLASSES:
        raise InvalidDecisionError(f"unsupported durable decision class: {decision_class}")
    title = _nonempty("title", title)
    context = _nonempty("context", context)
    user_proposal = _optional_text("user_proposal", user_proposal)
    praxis_challenge = _optional_text("praxis_challenge", praxis_challenge)
    verified_constraints = _strings("verified_constraints", verified_constraints)
    alternatives = _strings("alternatives", alternatives)
    blocked_scopes = _strings("blocked_scopes", blocked_scopes)
    decision_id = f"decision_{secrets.token_hex(8)}"

    def mutate(state: dict[str, Any]) -> None:
        tasks = state.get("tasks")
        if not isinstance(tasks, dict) or task_id not in tasks:
            raise InvalidDecisionError(f"unknown task id: {task_id}")
        existing = state.get("decisions")
        if existing is None:
            aggregate: dict[str, Any] = {"revision": 0, "records": {}}
        else:
            aggregate = copy.deepcopy(existing)
            aggregate["revision"] += 1
        if decision_id in aggregate["records"]:
            raise InvalidDecisionError(f"decision id collision: {decision_id}")
        aggregate["records"][decision_id] = {
            "revision": 0,
            "task_id": task_id,
            "class": decision_class,
            "status": "open",
            "title": title,
            "context": context,
            "user_proposal": user_proposal,
            "verified_constraints": verified_constraints,
            "praxis_challenge": praxis_challenge,
            "alternatives": alternatives,
            "selected_decision": None,
            "user_reasoning": None,
            "accepted_tradeoffs": [],
            "blocked_scopes": blocked_scopes,
            "implementation_result": None,
            "verification": None,
            "later_evidence": [],
        }
        state["decisions"] = aggregate
        return None

    return decision_id, mutate_latest_state(project_root, mutate)


def _mutate_decision(
    project_root: Path,
    decision_id: str,
    expected_decision_revision: int,
    editor: Callable[[dict[str, Any], dict[str, Any]], bool],
) -> dict[str, Any]:
    def mutate(state: dict[str, Any]) -> None:
        aggregate = state.get("decisions")
        if not isinstance(aggregate, dict):
            raise UnknownDecisionError(f"unknown decision id: {decision_id}")
        record = aggregate["records"].get(decision_id)
        if not isinstance(record, dict):
            raise UnknownDecisionError(f"unknown decision id: {decision_id}")
        actual = record["revision"]
        if expected_decision_revision != actual:
            raise DecisionConflictError(decision_id, expected_decision_revision, actual)
        changed = editor(record, aggregate)
        if not changed:
            return None
        record["revision"] = actual + 1
        aggregate["revision"] += 1
        return None

    return mutate_latest_state(project_root, mutate)


def _require_status(record: dict[str, Any], decision_id: str, required: str) -> None:
    if record["status"] != required:
        raise InvalidDecisionTransitionError(
            f"decision {decision_id} must be {required}, found {record['status']}"
        )


def select_decision(
    project_root: Path,
    decision_id: str,
    expected_decision_revision: int,
    selected_decision: str,
    *,
    user_reasoning: str | None = None,
    accepted_tradeoffs: Iterable[str] | None = None,
) -> dict[str, Any]:
    selected_decision = _nonempty("selected_decision", selected_decision)
    user_reasoning = _optional_text("user_reasoning", user_reasoning)
    accepted = _strings("accepted_tradeoffs", accepted_tradeoffs)

    def edit(record: dict[str, Any], aggregate: dict[str, Any]) -> bool:
        _require_status(record, decision_id, "open")
        record["selected_decision"] = selected_decision
        record["user_reasoning"] = user_reasoning
        record["accepted_tradeoffs"] = accepted
        record["status"] = "selected"
        return True

    return _mutate_decision(project_root, decision_id, expected_decision_revision, edit)


def record_implementation(
    project_root: Path,
    decision_id: str,
    expected_decision_revision: int,
    implementation_result: str,
) -> dict[str, Any]:
    implementation_result = _nonempty("implementation_result", implementation_result)

    def edit(record: dict[str, Any], aggregate: dict[str, Any]) -> bool:
        _require_status(record, decision_id, "selected")
        record["implementation_result"] = implementation_result
        record["status"] = "implemented"
        return True

    return _mutate_decision(project_root, decision_id, expected_decision_revision, edit)


def record_verification(
    project_root: Path,
    decision_id: str,
    expected_decision_revision: int,
    verification: str,
) -> dict[str, Any]:
    verification = _nonempty("verification", verification)

    def edit(record: dict[str, Any], aggregate: dict[str, Any]) -> bool:
        _require_status(record, decision_id, "implemented")
        record["verification"] = verification
        record["status"] = "verified"
        return True

    return _mutate_decision(project_root, decision_id, expected_decision_revision, edit)


def supersede_decision(
    project_root: Path,
    decision_id: str,
    expected_decision_revision: int,
    superseding_decision_id: str,
) -> dict[str, Any]:
    superseding_decision_id = _nonempty("superseding_decision_id", superseding_decision_id)
    if superseding_decision_id == decision_id:
        raise InvalidDecisionError("a decision cannot supersede itself")

    def edit(record: dict[str, Any], aggregate: dict[str, Any]) -> bool:
        if record["status"] not in {"open", "selected", "implemented"}:
            raise InvalidDecisionTransitionError(
                f"decision {decision_id} cannot be superseded from {record['status']}"
            )
        if superseding_decision_id not in aggregate["records"]:
            raise UnknownDecisionError(f"unknown decision id: {superseding_decision_id}")
        record["status"] = "superseded"
        record["superseding_decision_id"] = superseding_decision_id
        return True

    return _mutate_decision(project_root, decision_id, expected_decision_revision, edit)


def abandon_decision(
    project_root: Path,
    decision_id: str,
    expected_decision_revision: int,
) -> dict[str, Any]:
    def edit(record: dict[str, Any], aggregate: dict[str, Any]) -> bool:
        if record["status"] not in {"open", "selected", "implemented"}:
            raise InvalidDecisionTransitionError(
                f"decision {decision_id} cannot be abandoned from {record['status']}"
            )
        record["status"] = "abandoned"
        return True

    return _mutate_decision(project_root, decision_id, expected_decision_revision, edit)


def add_later_evidence(
    project_root: Path,
    decision_id: str,
    expected_decision_revision: int,
    evidence: str,
) -> dict[str, Any]:
    evidence = _nonempty("evidence", evidence)

    def edit(record: dict[str, Any], aggregate: dict[str, Any]) -> bool:
        if evidence in record["later_evidence"]:
            return False
        record["later_evidence"].append(evidence)
        return True

    return _mutate_decision(project_root, decision_id, expected_decision_revision, edit)
