from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess

from .experiments import ACTIVE_WATCH, EXPERIMENT_LOG, REPORTS_DIR
from .storage import latest_market_snapshot, latest_ocean_snapshot, latest_proposal

POST_WATCH_COOLDOWN_MINUTES = 360


@dataclass(frozen=True)
class CompletedWatch:
    report_path: str
    age_minutes: int
    remaining_minutes: int
    cooldown_minutes: int
    earliest_action_utc: str
    earliest_action_local: str


@dataclass(frozen=True)
class OperatorState:
    has_ocean: bool
    has_market: bool
    action: str | None
    active_watch: str | None
    completed_watch: CompletedWatch | None
    is_fresh: bool
    freshness_minutes: int | None
    latest_report: str | None
    running_runs: list[str]
    latest_ocean_timestamp: str | None
    latest_market_timestamp: str | None
    active_manual_positions: list[str]


def get_operator_state(conn) -> OperatorState:
    ocean = latest_ocean_snapshot(conn)
    market = latest_market_snapshot(conn)
    proposal = latest_proposal(conn)
    latest_report = _latest_report()
    freshness = _freshness_minutes(market.timestamp_utc if market else None)
    return OperatorState(
        has_ocean=ocean is not None,
        has_market=market is not None,
        action=proposal.action if proposal else None,
        active_watch=_active_watch(),
        completed_watch=_recent_completed_watch(latest_report, market.timestamp_utc if market else None),
        is_fresh=freshness is not None and freshness <= 30,
        freshness_minutes=freshness,
        latest_report=latest_report,
        running_runs=_running_runs(),
        latest_ocean_timestamp=ocean.timestamp_utc if ocean else None,
        latest_market_timestamp=market.timestamp_utc if market else None,
        active_manual_positions=_active_manual_positions(conn),
    )


def build_operator_cockpit(conn) -> str:
    state = get_operator_state(conn)

    lines = [
        "Braiins Ratchet Cockpit",
        "",
        "Situation",
        f"  Database: {'ready' if state.has_ocean or state.has_market or state.action else 'empty'}",
        f"  Latest OCEAN sample: {state.latest_ocean_timestamp or 'none'}",
        f"  Latest Braiins sample: {state.latest_market_timestamp or 'none'}",
        f"  Braiins sample freshness: {_freshness_text(state.freshness_minutes)}",
        f"  Latest strategy action: {state.action or 'none'}",
        f"  Latest run report: {state.latest_report or 'none yet'}",
        f"  Experiment ledger: {EXPERIMENT_LOG.relative_to(REPORTS_DIR.parent) if EXPERIMENT_LOG.exists() else 'none yet'}",
        f"  Active watch: {state.active_watch or 'none detected'}",
        f"  Active manual exposure: {_manual_exposure_text(state.active_manual_positions)}",
        f"  Research stage: {_research_stage(state.active_watch, state.completed_watch)}",
    ]

    if state.completed_watch:
        lines.extend(_cooldown_status_lines(state.completed_watch))

    if state.running_runs:
        lines.append(f"  Ledger has unfinished run markers: {', '.join(state.running_runs)}")

    lines.extend(["", "DO THIS NOW"])
    lines.extend(
        _do_this_now(
            active_watch=state.active_watch,
            active_manual_positions=state.active_manual_positions,
            completed_watch=state.completed_watch,
            has_ocean=state.has_ocean,
            has_market=state.has_market,
            is_fresh=state.is_fresh,
            action=state.action,
        )
    )
    lines.extend(["", "Ratchet Pathway Forecast"])
    lines.extend(
        _pathway_forecast(
            active_watch=state.active_watch,
            active_manual_positions=state.active_manual_positions,
            completed_watch=state.completed_watch,
            has_ocean=state.has_ocean,
            has_market=state.has_market,
            is_fresh=state.is_fresh,
            action=state.action,
        )
    )
    lines.extend(["", "How To Interpret The Current Action"])
    lines.extend(_action_explanation(state.action))
    lines.extend(["", "Ratchet Rule"])
    lines.extend(
        [
            "  One run is not a verdict. One run is a measurement.",
            "  Change only one knob at a time: depth target, overpay cushion, canary spend, duration, or timing window.",
            "  Do not increase spend until multiple mature runs point in the same direction.",
        ]
    )
    lines.extend(["", "Reference Commands"])
    lines.extend(
        [
            "  Ignore this list unless DO THIS NOW explicitly tells you to use one.",
            "  ./scripts/ratchet next         # read this cockpit",
            "  ./scripts/ratchet once         # fetch one fresh sample and report",
            "  ./scripts/ratchet watch 2      # run a bounded 2-hour experiment",
            "  ./scripts/ratchet engine start # start the monitor-only forever engine",
            "  ./scripts/ratchet experiments  # read the experiment ledger",
            "  ./scripts/ratchet report       # read the latest raw human report",
        ]
    )
    return "\n".join(lines)


def _do_this_now(
    active_watch: str | None,
    active_manual_positions: list[str],
    completed_watch: CompletedWatch | None,
    has_ocean: bool,
    has_market: bool,
    is_fresh: bool,
    action: str | None,
) -> list[str]:
    if active_watch:
        return [
            "  WAIT.",
            "  The running watch process is in control. Do not start another ratchet command.",
            "  You can leave it alone; it will write the experiment report when it finishes.",
            "  After the watch terminal finishes by itself, run exactly:",
            "    ./scripts/ratchet",
        ]

    if active_manual_positions:
        return [
            "  HOLD.",
            "  Manual Braiins exposure is active. Do not start new watch experiments.",
            "  Keep supervisor running or check status with:",
            "    ./scripts/ratchet supervise --status",
            "  When the Braiins position is really finished, close it with:",
            "    ./scripts/ratchet position close POSITION_ID",
        ]

    if completed_watch and action == "manual_canary":
        return [
            "  STOP.",
            f"  The latest 2-hour watch already finished {completed_watch.age_minutes} minutes ago.",
            f"  Report written: {completed_watch.report_path}",
            "  Do not start another identical watch now.",
            f"  Earliest next action: {completed_watch.earliest_action_local}",
            f"  Time remaining: {completed_watch.remaining_minutes} minutes.",
            "  At or after that time, run exactly:",
            "    ./scripts/ratchet once",
            "  Reason: this ratchet stage is complete; repeating it immediately would be loop-chasing, not research.",
        ]

    if not has_ocean or not has_market:
        return [
            "  Run exactly:",
            "    ./scripts/ratchet setup",
            "  Reason: local setup is missing. The setup command will print the next command.",
        ]

    if not is_fresh:
        return [
            "  Run exactly:",
            "    ./scripts/ratchet once",
            "  Reason: the latest Braiins sample is stale. The once command will fetch a fresh sample and print this cockpit again.",
        ]

    if action == "manual_bid":
        return [
            "  Run exactly:",
            "    ./scripts/ratchet report",
            "  Then read only the Plain English section.",
            "  Manual Braiins action is allowed only after that report still says manual_bid.",
            "  Reason: manual_bid is the only profit-seeking signal, but execution is still manual.",
        ]

    if action == "manual_canary":
        return [
            "  Run exactly:",
            "    ./scripts/ratchet watch 2",
            "  Then leave that terminal alone for about 2 hours.",
            "  The watch command keeps control, writes the run report, and prints this cockpit again when it ends.",
            "  Reason: manual_canary means the model sees a bounded learning opportunity, not proven profit.",
        ]

    return [
        "  STOP.",
        "  No Braiins action is expected from you.",
        "  If you want to continue passive learning later, run exactly:",
        "    ./scripts/ratchet watch 2",
        "  Reason: observe means the strategy did not find a useful action window.",
    ]


def _pathway_forecast(
    active_watch: str | None,
    active_manual_positions: list[str],
    completed_watch: CompletedWatch | None,
    has_ocean: bool,
    has_market: bool,
    is_fresh: bool,
    action: str | None,
) -> list[str]:
    if active_watch:
        return [
            "  Planning probabilities are workflow estimates, not profit probabilities.",
            "  Immediate, very likely: wait for the running watch to finish; workload is zero until it ends.",
            "  Midterm, likely: read the final cockpit and ledger summary; workload is about 5 minutes.",
            "  Longterm, possible: adjust one strategy knob if the report says the run taught us something.",
        ]

    if active_manual_positions:
        return [
            "  Planning probabilities are workflow estimates, not profit probabilities.",
            "  Immediate, certain: supervise the active manual exposure; workload is observation only.",
            "  Midterm, likely: close the position manually when Braiins/OCEAN state confirms it is done.",
            "  Longterm, possible: resume passive ratchet experiments only after exposure is closed.",
        ]

    if completed_watch and action == "manual_canary":
        return [
            "  Planning probabilities are workflow estimates, not profit probabilities.",
            f"  Immediate, certain: stop this stage and keep {completed_watch.report_path} as the evidence artifact.",
            "  Midterm, likely: after cooldown, refresh with one once command and compare against this report.",
            "  Longterm, possible: adjust exactly one knob only if repeated reports show the same pattern.",
        ]

    if not has_ocean or not has_market:
        return [
            "  Planning probabilities are workflow estimates, not profit probabilities.",
            "  Immediate, certain: initialize local state; workload is one setup command.",
            "  Midterm, very likely: collect the first live sample; workload is one once command.",
            "  Longterm, likely: start passive watch experiments after fresh data exists.",
        ]

    if not is_fresh:
        return [
            "  Planning probabilities are workflow estimates, not profit probabilities.",
            "  Immediate, certain: refresh stale data with one once command; workload is under a minute.",
            "  Midterm, likely: if the fresh state still says manual_canary, run a 2-hour watch.",
            "  Longterm, possible: compare this fresh run against prior reports before changing any knob.",
        ]

    if action == "manual_bid":
        return [
            "  Planning probabilities are workflow estimates, not profit probabilities.",
            "  Immediate, certain: inspect the full report before any manual Braiins action.",
            "  Midterm, possible: manually place a tiny order only if the report still says manual_bid.",
            "  Longterm, uncertain: wait through maturity and compare realized outcome against modeled EV.",
        ]

    if action == "manual_canary":
        return [
            "  Planning probabilities are workflow estimates, not profit probabilities.",
            "  Immediate, very likely: run a 2-hour passive watch; workload is start command plus waiting.",
            "  Midterm, likely: use the generated run report to decide one next knob to test.",
            "  Longterm, possible: only after repeated mature evidence, consider a manual canary spend.",
        ]

    return [
        "  Planning probabilities are workflow estimates, not profit probabilities.",
        "  Immediate, certain: do not bid.",
        "  Midterm, possible: run another passive watch later if you want more market coverage.",
        "  Longterm, possible: change one strategy knob only after multiple observe windows are logged.",
    ]


def _action_explanation(action: str | None) -> list[str]:
    if action == "manual_bid":
        return [
            "  manual_bid: stricter profit-seeking guardrails cleared.",
            "  This does not place an order. You still decide manually in Braiins.",
        ]
    if action == "manual_canary":
        return [
            "  manual_canary: a tiny research canary is inside the configured loss budget.",
            "  Treat it as buying information. It can lose money and still be scientifically useful.",
        ]
    if action == "observe":
        return [
            "  observe: do not bid.",
            "  The correct action is either wait, collect more samples, or change one research knob later.",
        ]
    return [
        "  none: no strategy proposal exists yet.",
        "  Run ./scripts/ratchet once to create the first proposal.",
    ]


def _latest_report() -> str | None:
    if not REPORTS_DIR.exists():
        return None
    reports = sorted(
        (path for path in REPORTS_DIR.glob("*.md") if path.name != EXPERIMENT_LOG.name),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not reports:
        return None
    return str(reports[0].relative_to(REPORTS_DIR.parent))


def _active_manual_positions(conn) -> list[str]:
    try:
        rows = conn.execute(
            """
            SELECT id, venue, description, expected_maturity_utc
            FROM manual_positions
            WHERE status = 'active'
            ORDER BY id DESC
            """
        ).fetchall()
    except Exception:
        return []
    return [
        f"#{row[0]} {row[1]} {row[2]} maturity={row[3] or 'unknown'}"
        for row in rows
    ]


def _manual_exposure_text(positions: list[str]) -> str:
    if not positions:
        return "none recorded"
    return "; ".join(positions)


def _recent_completed_watch(latest_report: str | None, latest_market_timestamp: str | None) -> CompletedWatch | None:
    if latest_report is None:
        return None
    report_path = REPORTS_DIR.parent / latest_report
    if not report_path.name.startswith("run-") or not report_path.exists():
        return None
    market_dt = _parse_utc(latest_market_timestamp)
    if market_dt is not None and report_path.stat().st_mtime < market_dt.timestamp():
        return None
    age_seconds = datetime.now(UTC).timestamp() - report_path.stat().st_mtime
    age_minutes = max(0, int(age_seconds // 60))
    if age_minutes > POST_WATCH_COOLDOWN_MINUTES:
        return None
    remaining_minutes = max(0, POST_WATCH_COOLDOWN_MINUTES - age_minutes)
    earliest_action = datetime.fromtimestamp(report_path.stat().st_mtime, UTC)
    earliest_action = earliest_action.replace(microsecond=0)
    earliest_action = earliest_action.timestamp() + (POST_WATCH_COOLDOWN_MINUTES * 60)
    earliest_action_utc = datetime.fromtimestamp(earliest_action, UTC)
    earliest_action_local = earliest_action_utc.astimezone()
    return CompletedWatch(
        report_path=latest_report,
        age_minutes=age_minutes,
        remaining_minutes=remaining_minutes,
        cooldown_minutes=POST_WATCH_COOLDOWN_MINUTES,
        earliest_action_utc=earliest_action_utc.isoformat(timespec="seconds"),
        earliest_action_local=earliest_action_local.isoformat(timespec="seconds"),
    )


def _research_stage(active_watch: str | None, completed_watch: CompletedWatch | None) -> str:
    if active_watch:
        return "watch running"
    if completed_watch:
        return (
            "post-watch cooldown "
            f"({completed_watch.remaining_minutes} minutes left, report {completed_watch.report_path})"
        )
    return "ready"


def _cooldown_status_lines(completed_watch: CompletedWatch) -> list[str]:
    elapsed = min(completed_watch.cooldown_minutes, completed_watch.age_minutes)
    percent = int((elapsed / completed_watch.cooldown_minutes) * 100)
    return [
        f"  Cooldown progress: {_progress_bar(elapsed, completed_watch.cooldown_minutes)} {percent}%",
        f"  Earliest next action: {completed_watch.earliest_action_local}",
        f"  Cooldown remaining: {completed_watch.remaining_minutes} minutes",
    ]


def _progress_bar(elapsed: int, total: int, width: int = 20) -> str:
    if total <= 0:
        return "[" + ("#" * width) + "]"
    filled = min(width, max(0, int(round((elapsed / total) * width))))
    return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"


def _running_runs() -> list[str]:
    if not EXPERIMENT_LOG.exists():
        return []
    current_run: str | None = None
    running: list[str] = []
    completed: set[str] = set()
    for line in EXPERIMENT_LOG.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current_run = line.removeprefix("## ").strip()
        elif current_run and line.strip() == "- status: running":
            running.append(current_run)
        elif current_run and line.startswith("- status_update:"):
            completed.add(current_run)
    return [run for run in running if run not in completed]


def _active_watch() -> str | None:
    from_state_file = _active_watch_from_state_file()
    if from_state_file:
        return from_state_file
    return _active_watch_from_process_table()


def _active_watch_from_state_file() -> str | None:
    if not ACTIVE_WATCH.exists():
        return None
    try:
        payload = json.loads(ACTIVE_WATCH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "state file exists but is unreadable"
    pid = payload.get("pid")
    run_id = payload.get("run_id", "unknown-run")
    if isinstance(pid, int) and _pid_exists(pid):
        return f"{run_id} pid={pid}"
    return None


def _active_watch_from_process_table() -> str | None:
    if os.environ.get("BRAIINS_RATCHET_IGNORE_PROCESS_WATCH") == "1":
        return None
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
        if "braiins_ratchet.cli watch" in command or "./scripts/ratchet watch" in command:
            return f"process pid={pid}"
    return None


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _freshness_minutes(timestamp_utc: str | None) -> int | None:
    parsed = _parse_utc(timestamp_utc)
    if parsed is None:
        return None
    age = datetime.now(UTC) - parsed
    return max(0, int(age.total_seconds() // 60))


def _parse_utc(timestamp_utc: str | None) -> datetime | None:
    if not timestamp_utc:
        return None
    try:
        parsed = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _freshness_text(freshness: int | None) -> str:
    if freshness is None:
        return "unknown"
    if freshness <= 30:
        return f"fresh ({freshness} minutes old)"
    return f"stale ({freshness} minutes old)"
