from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
import uuid

from .config import REPO_ROOT
from .report import build_text_report


REPORTS_DIR = REPO_ROOT / "reports"
EXPERIMENT_LOG = REPORTS_DIR / "EXPERIMENT_LOG.md"


@dataclass(frozen=True)
class ExperimentRun:
    run_id: str
    started_utc: str


@dataclass(frozen=True)
class ExperimentSummary:
    run_id: str
    started_utc: str
    ended_utc: str | None
    planned_cycles: int
    interval_seconds: int
    sample_count: int
    first_sample_utc: str | None
    last_sample_utc: str | None
    actions: dict[str, int]
    min_price: Decimal | None
    avg_price: Decimal | None
    max_price: Decimal | None
    min_expected_net: Decimal | None
    avg_expected_net: Decimal | None
    max_expected_net: Decimal | None
    latest_action: str | None
    latest_reason: str | None
    hypothesis: str


def start_experiment(planned_cycles: int, interval_seconds: int, hypothesis: str | None) -> ExperimentRun:
    run_id = f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"
    started = datetime.now(UTC).isoformat(timespec="seconds")
    normalized_hypothesis = hypothesis or _default_hypothesis()
    _ensure_log()
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {run_id}\n\n"
            f"- status: running\n"
            f"- started_utc: {started}\n"
            f"- planned_cycles: {planned_cycles}\n"
            f"- interval_seconds: {interval_seconds}\n"
            f"- planned_duration_minutes: {(planned_cycles * interval_seconds) / 60:.1f}\n"
            f"- hypothesis: {normalized_hypothesis}\n"
            "- plan: collect public Braiins depth, collect OCEAN state, compute shadow canary, store every proposal.\n"
            "- operator_action: none by default; manual action only if report later says manual_canary or manual_bid and operator agrees.\n"
        )
    return ExperimentRun(run_id=run_id, started_utc=started)


def finish_experiment(
    conn,
    run_id: str,
    started_utc: str,
    planned_cycles: int,
    interval_seconds: int,
    hypothesis: str | None = None,
    status: str = "completed",
) -> str:
    ended = datetime.now(UTC).isoformat(timespec="seconds")
    summary = summarize_since(
        conn,
        run_id=run_id,
        started_utc=started_utc,
        ended_utc=ended,
        planned_cycles=planned_cycles,
        interval_seconds=interval_seconds,
        hypothesis=hypothesis,
    )
    text_report = build_text_report(conn)
    report_path = REPORTS_DIR / f"{run_id}.md"
    report_path.write_text(_render_run_report(summary, text_report), encoding="utf-8")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(_render_log_completion(summary, report_path, status))
    return str(report_path.relative_to(REPO_ROOT))


def write_retro_report(
    conn,
    run_id: str,
    started_utc: str,
    ended_utc: str | None,
    hypothesis: str | None = None,
) -> str:
    _ensure_log()
    summary = summarize_since(
        conn,
        run_id=run_id,
        started_utc=started_utc,
        ended_utc=ended_utc,
        planned_cycles=0,
        interval_seconds=0,
        hypothesis=hypothesis or "Retroactively embed an already completed manual watch into the ratchet ledger.",
    )
    report_path = REPORTS_DIR / f"{run_id}.md"
    report_path.write_text(_render_run_report(summary, build_text_report(conn)), encoding="utf-8")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {run_id}\n\n"
            "- status: retroactive\n"
            f"- started_utc: {summary.started_utc}\n"
            f"- ended_utc: {summary.ended_utc or 'n/a'}\n"
            f"- hypothesis: {summary.hypothesis}\n"
            "- plan: reconstruct from stored snapshots because this run happened before automatic run bookkeeping existed.\n"
            f"- collected_samples: {summary.sample_count}\n"
            f"- action_counts: {_fmt_actions(summary.actions)}\n"
            f"- report: {report_path.relative_to(REPO_ROOT)}\n"
            f"- adaptation: {_interpret(summary)}\n"
        )
    return str(report_path.relative_to(REPO_ROOT))


def summarize_since(
    conn,
    run_id: str,
    started_utc: str,
    ended_utc: str | None,
    planned_cycles: int,
    interval_seconds: int,
    hypothesis: str | None = None,
) -> ExperimentSummary:
    ended_filter = "AND datetime(timestamp_utc) <= datetime(?)" if ended_utc else ""
    params: tuple[object, ...] = (
        (started_utc, ended_utc) if ended_utc else (started_utc,)
    )
    market_rows = conn.execute(
        f"""
        SELECT timestamp_utc, best_price_btc_per_eh_day
        FROM market_snapshots
        WHERE datetime(timestamp_utc) >= datetime(?) {ended_filter} AND source = 'braiins-public'
        ORDER BY timestamp_utc ASC
        """,
        params,
    ).fetchall()
    proposal_rows = conn.execute(
        f"""
        SELECT timestamp_utc, action, reason, expected_net_btc
        FROM proposals
        WHERE datetime(timestamp_utc) >= datetime(?) {ended_filter}
        ORDER BY timestamp_utc ASC
        """,
        params,
    ).fetchall()

    prices = [Decimal(row[1]) for row in market_rows if row[1] is not None]
    expected_nets = [Decimal(row[3]) for row in proposal_rows if row[3] is not None]
    actions: dict[str, int] = {}
    for row in proposal_rows:
        actions[row[1]] = actions.get(row[1], 0) + 1

    latest = proposal_rows[-1] if proposal_rows else None
    return ExperimentSummary(
        run_id=run_id,
        started_utc=started_utc,
        ended_utc=ended_utc,
        planned_cycles=planned_cycles,
        interval_seconds=interval_seconds,
        sample_count=len(market_rows),
        first_sample_utc=market_rows[0][0] if market_rows else None,
        last_sample_utc=market_rows[-1][0] if market_rows else None,
        actions=actions,
        min_price=min(prices) if prices else None,
        avg_price=sum(prices) / Decimal(len(prices)) if prices else None,
        max_price=max(prices) if prices else None,
        min_expected_net=min(expected_nets) if expected_nets else None,
        avg_expected_net=sum(expected_nets) / Decimal(len(expected_nets)) if expected_nets else None,
        max_expected_net=max(expected_nets) if expected_nets else None,
        latest_action=latest[1] if latest else None,
        latest_reason=latest[2] if latest else None,
        hypothesis=hypothesis or _default_hypothesis(),
    )


def _render_run_report(summary: ExperimentSummary, latest_report: str) -> str:
    return (
        f"# {summary.run_id}\n\n"
        "## Ratchet Question\n\n"
        f"{summary.hypothesis}\n\n"
        "## Run Summary\n\n"
        f"- started_utc: {summary.started_utc}\n"
        f"- ended_utc: {summary.ended_utc or 'n/a'}\n"
        f"- planned_cycles: {summary.planned_cycles}\n"
        f"- interval_seconds: {summary.interval_seconds}\n"
        f"- collected_samples: {summary.sample_count}\n"
        f"- first_sample_utc: {summary.first_sample_utc or 'n/a'}\n"
        f"- last_sample_utc: {summary.last_sample_utc or 'n/a'}\n"
        f"- action_counts: {_fmt_actions(summary.actions)}\n"
        f"- strategy_price_min_avg_max: {_fmt(summary.min_price)} / {_fmt(summary.avg_price)} / {_fmt(summary.max_price)}\n"
        f"- expected_net_min_avg_max_btc: {_fmt(summary.min_expected_net)} / {_fmt(summary.avg_expected_net)} / {_fmt(summary.max_expected_net)}\n\n"
        "## Interpretation\n\n"
        f"{_interpret(summary)}\n\n"
        "## Operator Reading\n\n"
        f"{_plain_english(summary)}\n\n"
        "## Current Full Report Context\n\n"
        "The block below is the latest complete human report available when this markdown was written. "
        "For retroactive reports, the authoritative reconstructed run data is the summary above.\n\n"
        "```text\n"
        f"{latest_report}\n"
        "```\n"
    )


def _render_log_completion(summary: ExperimentSummary, report_path: Path, status: str) -> str:
    return (
        "\n"
        f"- status_update: {status}\n"
        f"- ended_utc: {summary.ended_utc or 'n/a'}\n"
        f"- collected_samples: {summary.sample_count}\n"
        f"- action_counts: {_fmt_actions(summary.actions)}\n"
        f"- strategy_price_min_avg_max: {_fmt(summary.min_price)} / {_fmt(summary.avg_price)} / {_fmt(summary.max_price)}\n"
        f"- expected_net_min_avg_max_btc: {_fmt(summary.min_expected_net)} / {_fmt(summary.avg_expected_net)} / {_fmt(summary.max_expected_net)}\n"
        f"- latest_action: {summary.latest_action or 'n/a'}\n"
        f"- latest_reason: {summary.latest_reason or 'n/a'}\n"
        f"- report: {report_path.relative_to(REPO_ROOT)}\n"
        f"- adaptation: {_interpret(summary)}\n"
    )


def _ensure_log() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if not EXPERIMENT_LOG.exists():
        EXPERIMENT_LOG.write_text(
            "# Experiment Log\n\n"
            "Karpathy-style ratchet rule: every run states a hypothesis, collects data, scores the current strategy, and records the next adaptation.\n",
            encoding="utf-8",
        )


def _default_hypothesis() -> str:
    return (
        "Depth-aware fillable price plus a small overpay cushion is a better canary trigger "
        "than raw best ask."
    )


def _interpret(summary: ExperimentSummary) -> str:
    if summary.sample_count == 0:
        return "No samples were collected. Treat run as failed instrumentation, not strategy evidence."
    if summary.latest_action == "manual_bid":
        return "Profit-seeking guardrails cleared at least at the end of the run; inspect report before manual action."
    if summary.latest_action == "manual_canary":
        if summary.avg_expected_net is not None and summary.avg_expected_net > Decimal("0"):
            return (
                "The run repeatedly found bounded canary conditions and average modeled net was slightly positive. "
                "Next ratchet: keep spend tiny, test whether the same window survives a lower overpay cushion."
            )
        return (
            "The run repeatedly found bounded canary conditions, but modeled net was negative on average. "
            "Next ratchet: do not escalate spend; test a smaller depth target or a lower overpay cushion."
        )
    return "The run did not find an action window; keep collecting or adjust one strategy parameter."


def _plain_english(summary: ExperimentSummary) -> str:
    if summary.sample_count == 0:
        return (
            "This is not evidence about the market. It means the instrumentation did not collect usable "
            "Braiins public samples in the selected time window."
        )
    action_text = _fmt_actions(summary.actions)
    return (
        f"This run collected {summary.sample_count} public Braiins market samples. "
        f"The strategy outcomes were: {action_text}. "
        f"Expected net ranged from {_fmt(summary.min_expected_net)} to {_fmt(summary.max_expected_net)} BTC. "
        "For ratcheting, do not ask whether one line was green or red. Ask whether this run changed one "
        "control knob: depth target, overpay cushion, canary spend, duration, or timing window."
    )


def _fmt(value: object) -> str:
    return "n/a" if value is None else str(value)


def _fmt_actions(actions: dict[str, int]) -> str:
    if not actions:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(actions.items()))
