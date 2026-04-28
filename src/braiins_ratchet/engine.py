from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import signal
import subprocess
import sys

from .config import REPO_ROOT
from .storage import DATA_DIR


LOG_DIR = REPO_ROOT / "logs"
SUPERVISOR_LOG = LOG_DIR / "supervisor.log"
SUPERVISOR_PID = DATA_DIR / "supervisor.pid"


@dataclass(frozen=True)
class EngineStatus:
    running: bool
    pid: int | None
    detail: str
    log_path: str


def get_engine_status() -> EngineStatus:
    pid = _pid_from_file()
    if pid is not None and _pid_matches_supervisor(pid):
        return EngineStatus(
            running=True,
            pid=pid,
            detail=f"forever monitor engine is running as pid {pid}",
            log_path=str(SUPERVISOR_LOG.relative_to(REPO_ROOT)),
        )

    discovered = _find_supervisor_pid()
    if discovered is not None:
        SUPERVISOR_PID.parent.mkdir(parents=True, exist_ok=True)
        SUPERVISOR_PID.write_text(str(discovered), encoding="utf-8")
        return EngineStatus(
            running=True,
            pid=discovered,
            detail=f"forever monitor engine is running as pid {discovered}",
            log_path=str(SUPERVISOR_LOG.relative_to(REPO_ROOT)),
        )

    if pid is not None:
        _clear_pid_file()
    return EngineStatus(
        running=False,
        pid=None,
        detail="forever monitor engine is not running",
        log_path=str(SUPERVISOR_LOG.relative_to(REPO_ROOT)),
    )


def start_engine() -> EngineStatus:
    current = get_engine_status()
    if current.running:
        return current

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

    log_handle = SUPERVISOR_LOG.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "-m", "braiins_ratchet.cli", "supervise", "--yes"],
        cwd=REPO_ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    log_handle.close()
    SUPERVISOR_PID.write_text(str(process.pid), encoding="utf-8")
    return EngineStatus(
        running=True,
        pid=process.pid,
        detail=f"forever monitor engine started as pid {process.pid}",
        log_path=str(SUPERVISOR_LOG.relative_to(REPO_ROOT)),
    )


def stop_engine() -> EngineStatus:
    status = get_engine_status()
    if not status.running or status.pid is None:
        _clear_pid_file()
        return EngineStatus(
            running=False,
            pid=None,
            detail="forever monitor engine was not running",
            log_path=str(SUPERVISOR_LOG.relative_to(REPO_ROOT)),
        )

    try:
        os.kill(status.pid, signal.SIGTERM)
    except ProcessLookupError:
        _clear_pid_file()
        return EngineStatus(
            running=False,
            pid=None,
            detail=f"forever monitor engine pid {status.pid} already exited",
            log_path=str(SUPERVISOR_LOG.relative_to(REPO_ROOT)),
        )
    _clear_pid_file()
    return EngineStatus(
        running=False,
        pid=None,
        detail=f"sent SIGTERM to forever monitor engine pid {status.pid}",
        log_path=str(SUPERVISOR_LOG.relative_to(REPO_ROOT)),
    )


def render_engine_status(status: EngineStatus) -> str:
    lines = [
        "Braiins Ratchet Engine",
        "",
        f"Running: {'yes' if status.running else 'no'}",
        f"PID: {status.pid or 'none'}",
        f"Detail: {status.detail}",
        f"Log: {status.log_path}",
        "",
        "Safety: monitor-only; never places, changes, or cancels Braiins orders.",
    ]
    return "\n".join(lines)


def _pid_from_file() -> int | None:
    try:
        text = SUPERVISOR_PID.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _clear_pid_file() -> None:
    try:
        SUPERVISOR_PID.unlink()
    except FileNotFoundError:
        pass


def _pid_matches_supervisor(pid: int) -> bool:
    command = _command_for_pid(pid)
    return command is not None and _is_supervisor_command(command)


def _command_for_pid(pid: int) -> str | None:
    try:
        output = subprocess.check_output(
            ["ps", "-p", str(pid), "-o", "command="],
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    command = output.strip()
    return command or None


def _find_supervisor_pid() -> int | None:
    try:
        output = subprocess.check_output(
            ["ps", "-axo", "pid=,command="],
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    current_pid = os.getpid()
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        pid_text, _, command = stripped.partition(" ")
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        if pid == current_pid:
            continue
        if _is_supervisor_command(command):
            return pid
    return None


def _is_supervisor_command(command: str) -> bool:
    return (
        "braiins_ratchet.cli supervise" in command
        or "./scripts/ratchet supervise" in command
    )
