"""Durable, provenance-preserving Tutor decisions for Praxis."""

from __future__ import annotations

import copy
from pathlib import Path
import secrets
from typing import Any, Iterable

from .state import InvalidStateError, mutate_latest_state


DURABLE_DECISION_CLASSES = {"engineering", "architectural"}
DECISION_STATUSES = {"open", "selected", "implemented", "verified", "superseded", "abandoned"}


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
