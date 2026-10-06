"""Host-neutral activation diagnostics and bounded hook observations."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

from .agents import fallback_status
from .locking import StateLock
from .project import UnsafeStatePathError, state_directory, state_file
from .state import load_state


def _observation_path(project_root: Path) -> Path:
    path = state_directory(project_root) / "hook-observations.json"
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return path
    if not stat.S_ISREG(mode):
        raise UnsafeStatePathError("Hook observations must be a regular file, not a symlink")
    return path


def read_observations(project_root: Path) -> dict:
    path = _observation_path(project_root)
    if not path.exists():
        return {"format_version": 1, "hosts": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("format_version") != 1 or not isinstance(value.get("hosts"), dict):
        raise ValueError("Unsupported or malformed hook observations")
    fields = {"event", "source", "status", "timestamp", "project_root", "adapter_root"}
    for host, events in value["hosts"].items():
        if not isinstance(host, str) or not isinstance(events, dict):
            raise ValueError("Malformed hook observation host")
        for event, record in events.items():
            if not isinstance(record, dict) or set(record) != fields or record["event"] != event:
                raise ValueError("Malformed hook observation record")
            if record["source"] is not None and not isinstance(record["source"], str):
                raise ValueError("Malformed hook source")
            if any(not isinstance(record[key], str) or not record[key] for key in fields - {"source"}):
                raise ValueError("Malformed hook observation value")
    return value


def record_hook(project_root: Path, *, host: str, event: str, source: str | None,
                status: str, adapter_root: Path) -> None:
    # A hook on an uninitialized project must not create .praxis/.
    if not state_file(project_root).exists():
        return
    with StateLock(project_root, timeout=0.1):
        value = read_observations(project_root)
        # ponytail: latest result per event; use a bounded history if older failures matter.
        value["hosts"].setdefault(host, {})[event] = {
            "event": event, "source": source, "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project_root": str(project_root), "adapter_root": str(adapter_root),
        }
        path = _observation_path(project_root)
        fd, name = tempfile.mkstemp(prefix=".hook-observations-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(value, stream, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            _observation_path(project_root)
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)


def doctor_status(project_root: Path, *, host: str = "codex", plugin_root: Path | None = None,
                  host_config: Path | None = None) -> dict:
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", host):
        raise ValueError("Invalid host name")
    report = {"model_delivery": "unknown", "host_invocation": "unknown"}
    try:
        state = load_state(project_root)
        report["activation"] = {"status": "uninitialized" if state is None else
                                "enabled" if state["enabled"] else "paused"}
    except (RuntimeError, OSError, ValueError, UnicodeError) as error:
        report["activation"] = {"status": "error", "error_type": type(error).__name__}
    try:
        report["agents_fallback"] = fallback_status(project_root)
    except (RuntimeError, OSError, ValueError, UnicodeError) as error:
        report["agents_fallback"] = {"status": "error", "error_type": type(error).__name__}
    try:
        records = read_observations(project_root)["hosts"].get(host, {})
        report["observations"] = {"status": "observed" if records else "not_observed", "events": records,
                                  "meaning": "Script invocation only; manual execution is indistinguishable from a host call."}
    except (RuntimeError, OSError, ValueError, UnicodeError) as error:
        report["observations"] = {"status": "error", "error_type": type(error).__name__}
    root = Path(plugin_root) if plugin_root is not None else Path(__file__).resolve().parents[1]
    script = root / "plugins" / host / "hooks" / "praxis_context.py"
    if not script.is_file():
        report["adapter"] = {"status": "unavailable", "path": str(script),
                             "hint": "Pass --plugin-root with the installed plugin checkout."}
        return report
    argv = [sys.executable, str(script), "--doctor", "--cwd", str(project_root)]
    if host_config is not None:
        argv += ["--host-config", str(host_config)]
    try:
        result = subprocess.run(argv, input="", capture_output=True, text=True, timeout=10, shell=False)
        if result.returncode != 0:
            report["adapter"] = {"status": "error", "returncode": result.returncode}
        elif not result.stdout.strip():
            report["adapter"] = {"status": "unsupported", "path": str(script),
                                 "hint": "This adapter does not support doctor; update the installed plugin or inspect the source checkout."}
        else:
            value = json.loads(result.stdout)
            if not isinstance(value, dict):
                raise ValueError("Adapter diagnostic output must be an object")
            report["adapter"] = value
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report["adapter"] = {"status": "error", "error_type": type(error).__name__}
    return report
