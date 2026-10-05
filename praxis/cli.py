"""Praxis command-line entry point."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
from pathlib import Path
from typing import Any

from . import __version__
from .decisions import (
    DecisionConflictError,
    DecisionError,
    DecisionRenderError,
    InvalidDecisionError,
    InvalidDecisionTransitionError,
    UnknownDecisionError,
    UnknownTaskError,
    abandon_decision,
    add_later_evidence,
    create_decision,
    decisions_status,
    record_implementation,
    record_verification,
    render_decisions,
    select_decision,
    supersede_decision,
)
from .fingerprints import EvidenceError
from .locking import LockTimeoutError
from .project import UnsafeStatePathError, discover_project_root
from .project_map import (
    InvalidProjectModelError,
    ProjectModelError,
    ProjectModelRenderError,
    SectionConflictError,
    UnknownSectionError,
    project_model_status,
    refresh_staleness,
    remove_section,
    render_project_model,
    upsert_section,
)
from .state import (
    InvalidStateError,
    MalformedStateError,
    PraxisStateError,
    RevisionConflictError,
    StateNotInitializedError,
    StateReadError,
    StateWriteError,
    UnsupportedFormatError,
    enable_state,
    load_state,
    pause_state,
)
from .tasks import InvalidTaskError, create_task, update_task


class CliUsageError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)


def _add_cwd(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cwd", required=True)


def _add_decision_target(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument("--decision-id", required=True)
    parser.add_argument("--expected-decision-revision", type=int, required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(prog="praxis")
    parser.add_argument("--version", action="version", version=f"Praxis {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    status = subparsers.add_parser("status")
    _add_cwd(status)

    enable = subparsers.add_parser("enable")
    _add_cwd(enable)
    enable.add_argument("--expected-revision", type=int)

    pause = subparsers.add_parser("pause")
    _add_cwd(pause)
    pause.add_argument("--expected-revision", type=int, required=True)

    task_create = subparsers.add_parser("task-create")
    _add_cwd(task_create)
    task_create.add_argument("--expected-revision", type=int, required=True)
    task_create.add_argument("--host", required=True)
    task_create.add_argument("--conversation-id")
    task_create.add_argument("--title")

    task_update = subparsers.add_parser("task-update")
    _add_cwd(task_update)
    task_update.add_argument("--expected-revision", type=int, required=True)
    task_update.add_argument("--task-id", required=True)
    task_update.add_argument("--stage")
    task_update.add_argument("--status")
    task_update.add_argument("--pending-choice", nargs="*")
    task_update.add_argument("--title")

    map_status = subparsers.add_parser("map-status")
    _add_cwd(map_status)

    map_upsert = subparsers.add_parser("map-upsert")
    _add_cwd(map_upsert)
    map_upsert.add_argument("--section-id", required=True)
    map_upsert.add_argument("--title", required=True)
    map_upsert.add_argument("--content", required=True)
    map_upsert.add_argument("--evidence", nargs="*", default=[])
    map_upsert.add_argument("--expected-section-revision", type=int)

    map_remove = subparsers.add_parser("map-remove")
    _add_cwd(map_remove)
    map_remove.add_argument("--section-id", required=True)
    map_remove.add_argument("--expected-section-revision", type=int, required=True)

    map_check = subparsers.add_parser("map-check")
    _add_cwd(map_check)

    map_render = subparsers.add_parser("map-render")
    _add_cwd(map_render)

    decision_status = subparsers.add_parser("decision-status")
    _add_cwd(decision_status)
    decision_status.add_argument("--task-id")

    decision_create = subparsers.add_parser("decision-create")
    _add_cwd(decision_create)
    decision_create.add_argument("--task-id", required=True)
    decision_create.add_argument("--class", dest="decision_class", required=True)
    decision_create.add_argument("--title", required=True)
    decision_create.add_argument("--context", required=True)
    decision_create.add_argument("--user-proposal")
    decision_create.add_argument("--verified-constraint", action="append", default=[])
    decision_create.add_argument("--praxis-challenge")
    decision_create.add_argument("--alternative", action="append", default=[])
    decision_create.add_argument("--blocked-scope", action="append", default=[])

    decision_select = subparsers.add_parser("decision-select")
    _add_decision_target(decision_select)
    decision_select.add_argument("--selected-decision", required=True)
    decision_select.add_argument("--user-reasoning")
    decision_select.add_argument("--accepted-tradeoff", action="append", default=[])

    decision_implemented = subparsers.add_parser("decision-implemented")
    _add_decision_target(decision_implemented)
    decision_implemented.add_argument("--result", required=True)

    decision_verify = subparsers.add_parser("decision-verify")
    _add_decision_target(decision_verify)
    decision_verify.add_argument("--result", required=True)

    decision_supersede = subparsers.add_parser("decision-supersede")
    _add_decision_target(decision_supersede)
    decision_supersede.add_argument("--superseding-decision-id", required=True)

    decision_abandon = subparsers.add_parser("decision-abandon")
    _add_decision_target(decision_abandon)

    decision_evidence = subparsers.add_parser("decision-evidence")
    _add_decision_target(decision_evidence)
    decision_evidence.add_argument("--evidence", required=True)

    decision_render = subparsers.add_parser("decision-render")
    _add_cwd(decision_render)
    return parser


def _success(project_root: Path, state: dict[str, Any] | None, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": True,
        "project_root": str(project_root),
        "active": bool(state is not None and state["enabled"]),
        "state": state,
    }
    payload.update(extra)
    return payload


def _error_code(error: Exception) -> str:
    if isinstance(error, RevisionConflictError):
        return "revision_conflict"
    if isinstance(error, DecisionConflictError):
        return "decision_conflict"
    if isinstance(error, UnknownTaskError):
        return "unknown_task"
    if isinstance(error, UnknownDecisionError):
        return "unknown_decision"
    if isinstance(error, InvalidDecisionTransitionError):
        return "invalid_transition"
    if isinstance(error, DecisionRenderError):
        return "decision_render_failed"
    if isinstance(error, InvalidDecisionError):
        return "invalid_decision"
    if isinstance(error, DecisionError):
        return "invalid_decision"
    if isinstance(error, SectionConflictError):
        return "section_conflict"
    if isinstance(error, UnknownSectionError):
        return "unknown_section"
    if isinstance(error, ProjectModelRenderError):
        return "project_model_render_failed"
    if isinstance(error, InvalidProjectModelError):
        return "invalid_project_model"
    if isinstance(error, EvidenceError):
        return "invalid_evidence"
    if isinstance(error, ProjectModelError):
        return "invalid_project_model"
    if isinstance(error, InvalidTaskError):
        return "invalid_task"
    if isinstance(error, MalformedStateError):
        return "malformed_state"
    if isinstance(error, StateReadError):
        return "state_read_failed"
    if isinstance(error, UnsupportedFormatError):
        return "unsupported_format"
    if isinstance(error, InvalidStateError):
        return "invalid_state"
    if isinstance(error, StateNotInitializedError):
        return "state_not_initialized"
    if isinstance(error, StateWriteError):
        return "state_write_failed"
    if isinstance(error, UnsafeStatePathError):
        return "unsafe_state_path"
    if isinstance(error, LockTimeoutError):
        return "lock_timeout"
    return "invalid_request"


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _decision_success(project_root: Path, state: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return _success(project_root, state, decisions=decisions_status(project_root), **extra)


def _run_command(args: argparse.Namespace) -> dict[str, Any]:
    project_root = discover_project_root(args.cwd)
    if args.command == "status":
        return _success(project_root, load_state(project_root))
    if args.command == "enable":
        state = enable_state(project_root, expected_revision=args.expected_revision)
        return _success(project_root, state)
    if args.command == "pause":
        state = pause_state(project_root, args.expected_revision)
        return _success(project_root, state)
    if args.command == "task-create":
        task_id, state = create_task(
            project_root,
            args.expected_revision,
            host=args.host,
            conversation_id=args.conversation_id,
            title=args.title,
        )
        return _success(project_root, state, task_id=task_id)
    if args.command == "task-update":
        state = update_task(
            project_root,
            args.expected_revision,
            args.task_id,
            stage=args.stage,
            status=args.status,
            pending_choices=args.pending_choice,
            title=args.title,
        )
        return _success(project_root, state, task_id=args.task_id)
    if args.command == "map-status":
        state = load_state(project_root)
        return _success(project_root, state, project_model=project_model_status(project_root))
    if args.command == "map-upsert":
        state = upsert_section(
            project_root,
            args.section_id,
            args.title,
            args.content,
            args.evidence,
            expected_section_revision=args.expected_section_revision,
        )
        return _success(project_root, state, project_model=project_model_status(project_root))
    if args.command == "map-remove":
        state = remove_section(
            project_root,
            args.section_id,
            args.expected_section_revision,
        )
        return _success(project_root, state, project_model=project_model_status(project_root))
    if args.command == "map-check":
        state = refresh_staleness(project_root)
        return _success(project_root, state, project_model=project_model_status(project_root))
    if args.command == "map-render":
        code_path = render_project_model(project_root)
        state = load_state(project_root)
        return _success(
            project_root,
            state,
            project_model=project_model_status(project_root),
            code_path=str(code_path),
        )
    if args.command == "decision-status":
        state = load_state(project_root)
        return _success(project_root, state, decisions=decisions_status(project_root, task_id=args.task_id))
    if args.command == "decision-create":
        decision_id, state = create_decision(
            project_root,
            args.task_id,
            args.decision_class,
            args.title,
            args.context,
            user_proposal=args.user_proposal,
            verified_constraints=args.verified_constraint,
            praxis_challenge=args.praxis_challenge,
            alternatives=args.alternative,
            blocked_scopes=args.blocked_scope,
        )
        return _decision_success(project_root, state, decision_id=decision_id)
    if args.command == "decision-select":
        state = select_decision(
            project_root,
            args.decision_id,
            args.expected_decision_revision,
            args.selected_decision,
            user_reasoning=args.user_reasoning,
            accepted_tradeoffs=args.accepted_tradeoff,
        )
        return _decision_success(project_root, state, decision_id=args.decision_id)
    if args.command == "decision-implemented":
        state = record_implementation(
            project_root,
            args.decision_id,
            args.expected_decision_revision,
            args.result,
        )
        return _decision_success(project_root, state, decision_id=args.decision_id)
    if args.command == "decision-verify":
        state = record_verification(
            project_root,
            args.decision_id,
            args.expected_decision_revision,
            args.result,
        )
        return _decision_success(project_root, state, decision_id=args.decision_id)
    if args.command == "decision-supersede":
        state = supersede_decision(
            project_root,
            args.decision_id,
            args.expected_decision_revision,
            args.superseding_decision_id,
        )
        return _decision_success(project_root, state, decision_id=args.decision_id)
    if args.command == "decision-abandon":
        state = abandon_decision(project_root, args.decision_id, args.expected_decision_revision)
        return _decision_success(project_root, state, decision_id=args.decision_id)
    if args.command == "decision-evidence":
        state = add_later_evidence(
            project_root,
            args.decision_id,
            args.expected_decision_revision,
            args.evidence,
        )
        return _decision_success(project_root, state, decision_id=args.decision_id)
    if args.command == "decision-render":
        decisions_path = render_decisions(project_root)
        state = load_state(project_root)
        return _success(
            project_root,
            state,
            decisions=decisions_status(project_root),
            decisions_path=str(decisions_path),
        )
    raise CliUsageError("a Praxis command is required")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command is None:
            parser.print_help()
            return 0
        payload = _run_command(args)
    except (
        PraxisStateError,
        DecisionError,
        ProjectModelError,
        EvidenceError,
        UnsafeStatePathError,
        LockTimeoutError,
        ValueError,
    ) as error:
        _emit({"ok": False, "error": {"code": _error_code(error), "message": str(error)}})
        return 2
    _emit(payload)
    return 0
