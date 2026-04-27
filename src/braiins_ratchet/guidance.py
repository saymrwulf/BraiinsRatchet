from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess

from .experiments import ACTIVE_WATCH, EXPERIMENT_LOG, REPORTS_DIR
from .storage import latest_market_snapshot, latest_ocean_snapshot, latest_proposal


def build_operator_cockpit(conn) -> str:
    ocean = latest_ocean_snapshot(conn)
    market = latest_market_snapshot(conn)
    proposal = latest_proposal(conn)
    latest_report = _latest_report()
    running_runs = _running_runs()
    active_watch = _active_watch()
    freshness = _freshness_minutes(market.timestamp_utc if market else None)
    is_fresh = freshness is not None and freshness <= 30

    lines = [
        "Braiins Ratchet Cockpit",
        "",
        "Situation",
        f"  Database: {'ready' if ocean or market or proposal else 'empty'}",
        f"  Latest OCEAN sample: {ocean.timestamp_utc if ocean else 'none'}",
        f"  Latest Braiins sample: {market.timestamp_utc if market else 'none'}",
        f"  Braiins sample freshness: {_freshness_text(freshness)}",
        f"  Latest strategy action: {proposal.action if proposal else 'none'}",
        f"  Latest run report: {latest_report or 'none yet'}",
        f"  Experiment ledger: {EXPERIMENT_LOG.relative_to(REPORTS_DIR.parent) if EXPERIMENT_LOG.exists() else 'none yet'}",
        f"  Active watch: {active_watch or 'none detected'}",
    ]

    if running_runs:
        lines.append(f"  Ledger has unfinished run markers: {', '.join(running_runs)}")

    lines.extend(["", "DO THIS NOW"])
    lines.extend(
        _do_this_now(
            active_watch=active_watch,
            has_ocean=ocean is not None,
            has_market=market is not None,
            is_fresh=is_fresh,
            action=proposal.action if proposal else None,
        )
    )
    lines.extend(["", "Ratchet Pathway Forecast"])
    lines.extend(
        _pathway_forecast(
            active_watch=active_watch,
            has_ocean=ocean is not None,
            has_market=market is not None,
            is_fresh=is_fresh,
            action=proposal.action if proposal else None,
        )
    )
    lines.extend(["", "How To Interpret The Current Action"])
    lines.extend(_action_explanation(proposal.action if proposal else None))
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
            "  ./scripts/ratchet experiments  # read the experiment ledger",
            "  ./scripts/ratchet report       # read the latest raw human report",
        ]
    )
    return "\n".join(lines)


def _do_this_now(
    active_watch: str | None,
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
    if not timestamp_utc:
        return None
    try:
        parsed = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    age = datetime.now(UTC) - parsed.astimezone(UTC)
    return max(0, int(age.total_seconds() // 60))


def _freshness_text(freshness: int | None) -> str:
    if freshness is None:
        return "unknown"
    if freshness <= 30:
        return f"fresh ({freshness} minutes old)"
    return f"stale ({freshness} minutes old)"
