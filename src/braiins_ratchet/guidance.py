from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .experiments import EXPERIMENT_LOG, REPORTS_DIR
from .storage import latest_market_snapshot, latest_ocean_snapshot, latest_proposal


def build_operator_cockpit(conn) -> str:
    ocean = latest_ocean_snapshot(conn)
    market = latest_market_snapshot(conn)
    proposal = latest_proposal(conn)
    latest_report = _latest_report()
    running_runs = _running_runs()
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
    ]

    if running_runs:
        lines.append(f"  Ledger has unfinished run markers: {', '.join(running_runs)}")

    lines.extend(["", "What You Do Now"])
    lines.extend(
        _next_steps(
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
    lines.extend(["", "Safe Commands"])
    lines.extend(
        [
            "  ./scripts/ratchet next         # read this cockpit",
            "  ./scripts/ratchet once         # fetch one fresh sample and report",
            "  ./scripts/ratchet watch 2      # run a bounded 2-hour experiment",
            "  ./scripts/ratchet experiments  # read the experiment ledger",
            "  ./scripts/ratchet report       # read the latest raw human report",
        ]
    )
    return "\n".join(lines)


def _next_steps(has_ocean: bool, has_market: bool, is_fresh: bool, action: str | None) -> list[str]:
    if not has_ocean or not has_market:
        return [
            "  1. Run: ./scripts/ratchet setup",
            "  2. Run: ./scripts/ratchet once",
            "  3. Then run: ./scripts/ratchet next",
            "  Reason: the cockpit needs at least one OCEAN sample and one Braiins sample.",
        ]

    if not is_fresh:
        return [
            "  1. If a watch is currently running in another terminal, do nothing until it finishes.",
            "  2. If no watch is running, run: ./scripts/ratchet once",
            "  3. Then run: ./scripts/ratchet next",
            "  Reason: the latest Braiins sample is stale; do not interpret old price action as a current signal.",
        ]

    if action == "manual_bid":
        return [
            "  1. Run: ./scripts/ratchet report",
            "  2. Read the Plain English section.",
            "  3. If you manually bid, keep spend tiny and write down the Braiins order parameters.",
            "  4. After the order ends, wait through the maturity window before judging it.",
            "  Reason: manual_bid is the only profit-seeking signal, but execution is still manual.",
        ]

    if action == "manual_canary":
        return [
            "  1. If a watch is currently running in another terminal, do nothing until it finishes.",
            "  2. If no watch is running, run: ./scripts/ratchet watch 2",
            "  3. After the watch finishes, run: ./scripts/ratchet next",
            "  4. Read: ./scripts/ratchet experiments",
            "  Reason: manual_canary means the model sees a bounded learning opportunity, not proven profit.",
        ]

    return [
        "  1. If a watch is currently running in another terminal, do nothing until it finishes.",
        "  2. If no watch is running and you want more data, run: ./scripts/ratchet watch 2",
        "  3. If you are done for now, stop. No action is expected from you.",
        "  Reason: observe means the strategy did not find a useful action window.",
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
