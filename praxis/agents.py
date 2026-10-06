"""Explicit, removable AGENTS.md activation fallback."""

from pathlib import Path
import os
import stat
import tempfile

from .project import UnsafeStatePathError


START = "<!-- praxis:tutor-fallback:start -->"
END = "<!-- praxis:tutor-fallback:end -->"
BLOCK = f"""\n{START}
## Praxis activation fallback

Before proposing a solution or editing for a software task, run `praxis status --cwd .`.
If the CLI is unavailable, use `python3 -m praxis status --cwd .` (`py -3` on Windows).
Only when the returned `active` is true, load and follow the shared Praxis Tutor Skill.
If uninitialized or paused, continue ordinary work without activating tutoring.
If the check fails, report the failure; do not infer activation or silently reset state.
A preference answer does not select an implementation. Resolve consequential choices
with the user; execute mechanical work within an already delegated scope without
repeated confirmation. This block is removable with `praxis agents-fallback --cwd . --remove`.
{END}
"""


def _read(project_root: Path) -> tuple[Path, str]:
    path = project_root / "AGENTS.md"
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return path, ""
    if not stat.S_ISREG(mode):
        raise UnsafeStatePathError("AGENTS.md must be a regular file, not a symlink")
    return path, path.read_text(encoding="utf-8")


def _region(text: str) -> tuple[int, int] | None:
    if START not in text and END not in text:
        return None
    if text.count(START) != 1 or text.count(END) != 1 or text.index(END) < text.index(START):
        raise ValueError("Malformed or duplicate Praxis fallback markers; preserve and repair AGENTS.md manually")
    start = text.index(START)
    end = text.index(END) + len(END)
    if start and text[start - 1] == "\n":
        start -= 1
    if text[end:end + 1] == "\n":
        end += 1
    return start, end


def fallback_status(project_root: Path) -> dict:
    path, text = _read(project_root)
    return {"installed": _region(text) is not None, "path": str(path)}


def set_fallback(project_root: Path, *, remove: bool = False) -> dict:
    path, text = _read(project_root)
    region = _region(text)
    updated = text
    if remove and region is not None:
        updated = text[:region[0]] + text[region[1]:]
    elif not remove and region is None:
        updated = text + BLOCK
    if updated != text:
        mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
        fd, name = tempfile.mkstemp(prefix=".praxis-agents-", dir=project_root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                os.chmod(name, mode)
                stream.write(updated)
                stream.flush()
                os.fsync(stream.fileno())
            # Refuse replacement if another editor changed the original meanwhile.
            if _read(project_root)[1] != text:
                raise ValueError("AGENTS.md changed during fallback update; retry after rereading")
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    return {"installed": not remove, "path": str(path), "changed": updated != text,
            "notice": "Removable AGENTS.md fallback removed." if remove else
                      "Installed a removable AGENTS.md fallback; live activation state remains authoritative."}
