"""Project-boundary and Praxis state-path helpers."""

from __future__ import annotations

from pathlib import Path
import stat


class UnsafeStatePathError(RuntimeError):
    """Raised when Praxis state would traverse an unsafe filesystem entry."""


def discover_project_root(cwd: str | Path) -> Path:
    """Return the nearest Git boundary, or the supplied cwd when no Git exists."""

    path = Path(cwd).resolve()
    if not path.is_dir():
        raise ValueError(f"working directory does not exist: {path}")

    for directory in (path, *path.parents):
        marker = directory / ".git"
        try:
            marker.lstat()
        except FileNotFoundError:
            continue
        return directory
    return path


def _validate_directory(path: Path) -> None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise UnsafeStatePathError(f"Praxis state directory must be a real directory: {path}")


def state_directory(project_root: Path, *, create: bool = False) -> Path:
    root = Path(project_root).resolve()
    directory = root / ".praxis"
    _validate_directory(directory)
    if create and not directory.exists():
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        _validate_directory(directory)
    return directory


def state_file(project_root: Path) -> Path:
    path = state_directory(project_root) / "state.json"
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return path
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise UnsafeStatePathError(f"Praxis state file must be a real file: {path}")
    return path
