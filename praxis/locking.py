"""Cross-process write locking for Praxis project state."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import time

from .project import UnsafeStatePathError, state_directory


class LockTimeoutError(RuntimeError):
    """Raised when another writer holds the Praxis state lock too long."""


class StateLock:
    def __init__(
        self,
        project_root: Path,
        *,
        timeout: float = 2.0,
        poll_interval: float = 0.05,
    ) -> None:
        if timeout < 0:
            raise ValueError("timeout must be non-negative")
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        self.project_root = Path(project_root).resolve()
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.path = state_directory(self.project_root, create=True) / ".write-lock"
        self._acquired = False

    def acquire(self) -> None:
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                os.mkdir(self.path, 0o700)
            except FileExistsError:
                mode = self.path.lstat().st_mode
                if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                    raise UnsafeStatePathError(
                        f"Praxis write lock must be a real directory: {self.path}"
                    )
                if time.monotonic() >= deadline:
                    raise LockTimeoutError(f"timed out waiting for Praxis state lock: {self.path}")
                time.sleep(self.poll_interval)
                continue
            self._acquired = True
            return

    def release(self) -> None:
        if not self._acquired:
            return
        os.rmdir(self.path)
        self._acquired = False

    def __enter__(self) -> "StateLock":
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()
