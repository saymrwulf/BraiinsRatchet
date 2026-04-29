from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
import os
import time

from .config import AppConfig
from .experiments import ACTIVE_WATCH, finish_experiment, start_experiment
from .guidance import POST_WATCH_COOLDOWN_MINUTES, build_operator_cockpit, get_operator_state
from .storage import connect, init_db
from .watch_loop import run_watch_loop


DEFAULT_WATCH_CYCLES = 24
DEFAULT_INTERVAL_SECONDS = 300
MAX_CONSECUTIVE_CYCLE_FAILURES = 3


@dataclass(frozen=True)
class LifecycleStatus:
    phase: str
    next_action_utc: str | None
    last_run_id: str | None
    message: str


@dataclass(frozen=True)
class ManualPosition:
    id: int
    opened_utc: str
    closed_utc: str | None
    status: str
    venue: str
    description: str
    expected_maturity_utc: str | None
    payload_json: str


def init_lifecycle_db(conn) -> None:
    init_db(conn)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS lifecycle_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS lifecycle_events (
            id INTEGER PRIMARY KEY,
            timestamp_utc TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS manual_positions (
            id INTEGER PRIMARY KEY,
            opened_utc TEXT NOT NULL,
            closed_utc TEXT,
            status TEXT NOT NULL,
            venue TEXT NOT NULL,
            description TEXT NOT NULL,
            expected_maturity_utc TEXT,
            payload_json TEXT NOT NULL
        );
        """
    )
    conn.commit()


def get_lifecycle_status(conn) -> LifecycleStatus:
    init_lifecycle_db(conn)
    state = _read_state(conn)
    return LifecycleStatus(
        phase=state.get("phase", "idle"),
        next_action_utc=state.get("next_action_utc"),
        last_run_id=state.get("last_run_id"),
        message=state.get("message", "no lifecycle state recorded yet"),
    )


def render_lifecycle_status(conn) -> str:
    status = get_lifecycle_status(conn)
    positions = list_manual_positions(conn, status="active")
    lines = [
        "Braiins Ratchet Lifecycle",
        "",
        f"Phase: {status.phase}",
        f"Next action UTC: {status.next_action_utc or 'now'}",
        f"Last run id: {status.last_run_id or 'none'}",
        f"Message: {status.message}",
    ]
    if status.next_action_utc:
        remaining = _seconds_until(status.next_action_utc)
        lines.append(f"Countdown: {_format_duration(remaining)}")
    if positions:
        lines.extend(["", "Active Manual Exposure"])
        for position in positions:
            lines.append(
                f"  #{position.id} {position.venue}: {position.description} "
                f"(expected maturity: {position.expected_maturity_utc or 'unknown'})"
            )
    return "\n".join(lines)


def render_supervisor_plan() -> str:
    return "\n".join(
        [
            "Forever Supervisor Proposal",
            "",
            "I am going to take over the monitor-only autoresearch lifecycle.",
            "",
            "Loop:",
            "  1. Resume persisted lifecycle state from data/ratchet.sqlite.",
            "  2. If cooldown is active, wait until the persisted next-action time.",
            "  3. If manual Braiins exposure is active, hold and do not start new experiments.",
            "  4. Run one 2-hour passive watch when the lifecycle is ready.",
            "  5. Write the experiment ledger and run report.",
            "  6. Enter post-watch cooldown.",
            "  7. Repeat forever until you stop the process.",
            "",
            "Crash/reboot behavior:",
            "  Restart ./scripts/ratchet supervise and it resumes from SQLite.",
            "",
            "Safety:",
            "  This supervisor is monitor-only.",
            "  It never places, changes, or cancels Braiins orders.",
            "  If you manually start a Braiins order, record it separately; this daemon will not infer owner-token state.",
            "",
            "Are you OK with this? Type yes or no.",
        ]
    )


def run_supervisor(config: AppConfig, *, once: bool = False) -> int:
    with connect() as conn:
        init_lifecycle_db(conn)
        recover_stale_active_watch(conn)
        _record_event(conn, "supervisor_started", {"once": once})

    while True:
        with connect() as conn:
            init_lifecycle_db(conn)
            recover_stale_active_watch(conn)
            active_positions = list_manual_positions(conn, status="active")
            if active_positions:
                _handle_manual_exposure(conn, active_positions)
                if once:
                    return 0
                time.sleep(60)
                continue
            report_cooldown_seconds = _sync_recent_watch_cooldown(conn)
            if report_cooldown_seconds > 0:
                _print_timer("Report cooldown", report_cooldown_seconds)
                if once:
                    return 0
                _sleep_with_progress(report_cooldown_seconds)
                continue
            state = _read_state(conn)
            phase = state.get("phase", "idle")
            next_action_utc = state.get("next_action_utc")

        if phase == "cooldown" and next_action_utc:
            remaining = _seconds_until(next_action_utc)
            if remaining > 0:
                _print_timer("Lifecycle cooldown", remaining)
                if once:
                    return 0
                _sleep_with_progress(remaining)

        run_id = _run_watch_stage(config)
        next_action = datetime.now(UTC) + timedelta(minutes=POST_WATCH_COOLDOWN_MINUTES)
        with connect() as conn:
            init_lifecycle_db(conn)
            _write_state(
                conn,
                {
                    "phase": "cooldown",
                    "next_action_utc": next_action.isoformat(timespec="seconds"),
                    "last_run_id": run_id,
                    "message": "watch complete; cooldown active before next research stage",
                },
            )
            _record_event(
                conn,
                "watch_completed",
                {"run_id": run_id, "next_action_utc": next_action.isoformat(timespec="seconds")},
            )
            print(
                build_operator_cockpit(
                    conn,
                    engine_running=True,
                    engine_detail="forever monitor engine is running inside this supervisor process",
                )
            )
        if once:
            return 0


def recover_stale_active_watch(conn) -> str | None:
    init_lifecycle_db(conn)
    payload = _read_active_watch_payload()
    if payload is None:
        return None

    pid = payload.get("pid")
    if isinstance(pid, int) and _pid_exists(pid):
        return None

    run_id = str(payload.get("run_id") or "recovered-watch")
    started_utc = str(payload.get("started_utc") or datetime.now(UTC).isoformat(timespec="seconds"))
    planned_cycles = _safe_int(payload.get("planned_cycles"), DEFAULT_WATCH_CYCLES)
    interval_seconds = _safe_int(payload.get("interval_seconds"), DEFAULT_INTERVAL_SECONDS)
    report_path = finish_experiment(
        conn,
        run_id,
        started_utc,
        planned_cycles,
        interval_seconds,
        "recovered stale watch after the monitor engine stopped before final bookkeeping",
        status="recovered_after_crash",
    )
    next_action = datetime.now(UTC) + timedelta(minutes=POST_WATCH_COOLDOWN_MINUTES)
    _write_state(
        conn,
        {
            "phase": "cooldown",
            "next_action_utc": next_action.isoformat(timespec="seconds"),
            "last_run_id": run_id,
            "message": "watch recovered after engine crash; partial report written; cooldown active",
        },
    )
    _record_event(
        conn,
        "watch_recovered_after_crash",
        {
            "run_id": run_id,
            "stale_pid": pid,
            "report": report_path,
            "next_action_utc": next_action.isoformat(timespec="seconds"),
        },
    )
    return report_path


def _run_watch_stage(config: AppConfig) -> str:
    experiment = start_experiment(
        DEFAULT_WATCH_CYCLES,
        DEFAULT_INTERVAL_SECONDS,
        "forever supervisor: bounded passive watch stage",
    )
    with connect() as conn:
        init_lifecycle_db(conn)
        _write_state(
            conn,
            {
                "phase": "watching",
                "next_action_utc": "",
                "last_run_id": experiment.run_id,
                "message": "2-hour passive watch is running",
            },
        )
        _record_event(conn, "watch_started", {"run_id": experiment.run_id})

        summary = run_watch_loop(
            conn,
            config,
            planned_cycles=DEFAULT_WATCH_CYCLES,
            interval_seconds=DEFAULT_INTERVAL_SECONDS,
            max_consecutive_failures=MAX_CONSECUTIVE_CYCLE_FAILURES,
            on_cycle=_print_cycle_result,
            on_failure=lambda index, total, exc, consecutive: _record_cycle_failure(
                conn,
                experiment.run_id,
                index,
                total,
                exc,
                consecutive,
            ),
            sleep=time.sleep,
        )
        if summary.status == "interrupted":
            print("interrupted: writing partial experiment report before exit", flush=True)
        elif summary.failed_cycles:
            print(
                f"watch degraded: {summary.failed_cycles} failed cycle(s), "
                f"{summary.successful_cycles} successful cycle(s); writing {summary.status} report",
                flush=True,
            )
        report_path = finish_experiment(
            conn,
            experiment.run_id,
            experiment.started_utc,
            DEFAULT_WATCH_CYCLES,
            DEFAULT_INTERVAL_SECONDS,
            "forever supervisor: bounded passive watch stage",
            status=summary.status,
        )
        _record_event(
            conn,
            "watch_report_written",
            {
                "run_id": experiment.run_id,
                "report": report_path,
                "status": summary.status,
                "successful_cycles": summary.successful_cycles,
                "failed_cycles": summary.failed_cycles,
                "last_error": summary.last_error,
            },
        )
    return experiment.run_id


def _print_cycle_result(index: int, total: int, result) -> None:
    print(
        f"cycle {index}/{total}: "
        f"{result.proposal.action} - {result.proposal.reason}",
        flush=True,
    )


def _record_cycle_failure(
    conn,
    run_id: str,
    index: int,
    total: int,
    exc: Exception,
    consecutive_failures: int,
) -> None:
    message = f"{type(exc).__name__}: {exc}"
    print(
        f"cycle {index}/{total}: transient_error - {message} "
        f"(consecutive failures: {consecutive_failures}/{MAX_CONSECUTIVE_CYCLE_FAILURES})",
        flush=True,
    )
    _record_event(
        conn,
        "watch_cycle_failed",
        {
            "run_id": run_id,
            "cycle": index,
            "planned_cycles": total,
            "consecutive_failures": consecutive_failures,
            "error": message,
        },
    )


def _sync_recent_watch_cooldown(conn) -> int:
    operator_state = get_operator_state(conn)
    completed = operator_state.completed_watch
    if completed is None or completed.remaining_minutes <= 0:
        return 0

    state = _read_state(conn)
    if state.get("phase") != "cooldown" or state.get("next_action_utc") != completed.earliest_action_utc:
        _write_state(
            conn,
            {
                "phase": "cooldown",
                "next_action_utc": completed.earliest_action_utc,
                "last_run_id": completed.report_path,
                "message": "recent watch report is cooling down before next research stage",
            },
        )
        _record_event(
            conn,
            "cooldown_synced_from_report",
            {
                "report": completed.report_path,
                "next_action_utc": completed.earliest_action_utc,
                "remaining_minutes": completed.remaining_minutes,
            },
        )
    return completed.remaining_minutes * 60


def open_manual_position(
    conn,
    *,
    venue: str,
    description: str,
    expected_maturity_utc: str | None,
    payload: dict[str, object] | None = None,
) -> int:
    init_lifecycle_db(conn)
    opened = datetime.now(UTC).isoformat(timespec="seconds")
    cursor = conn.execute(
        """
        INSERT INTO manual_positions (
            opened_utc, closed_utc, status, venue, description,
            expected_maturity_utc, payload_json
        )
        VALUES (?, NULL, 'active', ?, ?, ?, ?)
        """,
        (
            opened,
            venue,
            description,
            expected_maturity_utc,
            json.dumps(payload or {}, sort_keys=True),
        ),
    )
    position_id = int(cursor.lastrowid)
    _write_state(
        conn,
        {
            "phase": "manual_exposure_active",
            "next_action_utc": expected_maturity_utc or "",
            "last_run_id": _read_state(conn).get("last_run_id", ""),
            "message": f"manual exposure active: position #{position_id}",
        },
    )
    _record_event(
        conn,
        "manual_position_opened",
        {"position_id": position_id, "venue": venue, "description": description},
    )
    return position_id


def close_manual_position(conn, position_id: int) -> bool:
    init_lifecycle_db(conn)
    closed = datetime.now(UTC).isoformat(timespec="seconds")
    cursor = conn.execute(
        """
        UPDATE manual_positions
        SET status = 'closed', closed_utc = ?
        WHERE id = ? AND status = 'active'
        """,
        (closed, position_id),
    )
    if cursor.rowcount == 0:
        conn.commit()
        return False
    _record_event(conn, "manual_position_closed", {"position_id": position_id})
    if not list_manual_positions(conn, status="active"):
        state = _read_state(conn)
        _write_state(
            conn,
            {
                "phase": "idle",
                "next_action_utc": "",
                "last_run_id": state.get("last_run_id", ""),
                "message": "manual exposure closed; lifecycle ready",
            },
        )
    return True


def list_manual_positions(conn, *, status: str | None = None) -> list[ManualPosition]:
    init_lifecycle_db(conn)
    where = "WHERE status = ?" if status else ""
    params: tuple[object, ...] = (status,) if status else ()
    rows = conn.execute(
        f"""
        SELECT id, opened_utc, closed_utc, status, venue, description,
               expected_maturity_utc, payload_json
        FROM manual_positions
        {where}
        ORDER BY id DESC
        """,
        params,
    ).fetchall()
    return [
        ManualPosition(
            id=int(row[0]),
            opened_utc=row[1],
            closed_utc=row[2],
            status=row[3],
            venue=row[4],
            description=row[5],
            expected_maturity_utc=row[6],
            payload_json=row[7],
        )
        for row in rows
    ]


def render_manual_positions(conn) -> str:
    positions = list_manual_positions(conn)
    if not positions:
        return "Manual Positions\n\nNo manual positions recorded."
    lines = ["Manual Positions", ""]
    for position in positions:
        lines.extend(
            [
                f"#{position.id} {position.status} {position.venue}",
                f"  opened_utc: {position.opened_utc}",
                f"  closed_utc: {position.closed_utc or 'n/a'}",
                f"  expected_maturity_utc: {position.expected_maturity_utc or 'n/a'}",
                f"  description: {position.description}",
            ]
        )
    return "\n".join(lines)


def _handle_manual_exposure(conn, positions: list[ManualPosition]) -> None:
    next_maturity = _earliest_maturity(positions)
    now = datetime.now(UTC)
    if next_maturity and next_maturity > now:
        phase = "manual_exposure_active"
        message = "manual Braiins exposure active; supervisor will not start new experiments"
        next_action = next_maturity.isoformat(timespec="seconds")
    else:
        phase = "manual_exposure_review"
        message = "manual exposure needs review or explicit close before lifecycle resumes"
        next_action = ""
    state = _read_state(conn)
    _write_state(
        conn,
        {
            "phase": phase,
            "next_action_utc": next_action,
            "last_run_id": state.get("last_run_id", ""),
            "message": message,
        },
    )
    _record_event(
        conn,
        "manual_exposure_hold",
        {"active_position_ids": [position.id for position in positions], "phase": phase},
    )
    print(render_lifecycle_status(conn), flush=True)


def _earliest_maturity(positions: list[ManualPosition]) -> datetime | None:
    maturities = [
        _parse_utc(position.expected_maturity_utc)
        for position in positions
        if position.expected_maturity_utc
    ]
    parsed = [maturity for maturity in maturities if maturity is not None]
    return min(parsed) if parsed else None


def _read_state(conn) -> dict[str, str]:
    rows = conn.execute("SELECT key, value FROM lifecycle_state").fetchall()
    return {row[0]: row[1] for row in rows}


def _read_active_watch_payload() -> dict[str, object] | None:
    try:
        return json.loads(ACTIVE_WATCH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _safe_int(value: object, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _write_state(conn, values: dict[str, str]) -> None:
    conn.execute("DELETE FROM lifecycle_state")
    for key, value in values.items():
        conn.execute(
            "INSERT INTO lifecycle_state (key, value) VALUES (?, ?)",
            (key, value),
        )
    conn.commit()


def _record_event(conn, event_type: str, payload: dict[str, object]) -> None:
    conn.execute(
        """
        INSERT INTO lifecycle_events (timestamp_utc, event_type, payload_json)
        VALUES (?, ?, ?)
        """,
        (datetime.now(UTC).isoformat(timespec="seconds"), event_type, json.dumps(payload, sort_keys=True)),
    )
    conn.commit()


def _seconds_until(timestamp_utc: str) -> int:
    target = _parse_utc(timestamp_utc)
    if target is None:
        return 0
    return max(0, int((target - datetime.now(UTC)).total_seconds()))


def _parse_utc(timestamp_utc: str | None) -> datetime | None:
    if not timestamp_utc:
        return None
    try:
        target = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
    except ValueError:
        return None
    if target.tzinfo is None:
        target = target.replace(tzinfo=UTC)
    return target.astimezone(UTC)


def _sleep_with_progress(seconds: int) -> None:
    remaining = max(0, seconds)
    while remaining > 0:
        sleep_for = min(60, remaining)
        time.sleep(sleep_for)
        remaining -= sleep_for
        _print_timer("Lifecycle cooldown", remaining)


def _print_timer(label: str, seconds: int) -> None:
    print(f"{label}: {_format_duration(seconds)} remaining", flush=True)


def _format_duration(seconds: int) -> str:
    seconds = max(0, seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"
