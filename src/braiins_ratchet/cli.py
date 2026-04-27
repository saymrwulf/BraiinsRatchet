from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

from .automation import build_automation_plan, render_automation_plan
from .braiins import BraiinsPublicClient, market_snapshot_from_json_file
from .config import load_config
from .experiments import (
    EXPERIMENT_LOG,
    finish_experiment,
    start_experiment,
    summarize_since,
    write_retro_report,
)
from .guidance import build_operator_cockpit
from .monitor import run_cycle
from .ocean import fetch_snapshot
from .report import build_text_report
from .storage import (
    connect,
    init_db,
    latest_market_snapshot,
    latest_ocean_snapshot,
    save_market_snapshot,
    save_ocean_snapshot,
    save_proposal,
)
from .strategy import propose


def cmd_init_db(_: argparse.Namespace) -> int:
    with connect() as conn:
        init_db(conn)
    print("initialized data/ratchet.sqlite")
    return 0


def cmd_collect_ocean(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    snapshot = fetch_snapshot(config.ocean.dashboard_url)
    with connect() as conn:
        init_db(conn)
        save_ocean_snapshot(conn, snapshot)
    print(json.dumps(snapshot.__dict__, default=str, indent=2))
    return 0


def cmd_import_market(args: argparse.Namespace) -> int:
    snapshot = market_snapshot_from_json_file(args.path)
    with connect() as conn:
        init_db(conn)
        save_market_snapshot(conn, snapshot)
    print(json.dumps(snapshot.__dict__, default=str, indent=2))
    return 0


def cmd_collect_braiins_public(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    client = BraiinsPublicClient(api_base=args.base_url.rstrip("/"))
    snapshot = client.fetch_market_snapshot(
        target_ph=config.strategy.shadow_target_ph,
        overpay_btc_per_eh_day=config.strategy.shadow_overpay_btc_per_eh_day,
    )
    with connect() as conn:
        init_db(conn)
        save_market_snapshot(conn, snapshot)
    print(json.dumps(snapshot.__dict__, default=str, indent=2))
    return 0


def cmd_cycle(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    with connect() as conn:
        result = run_cycle(
            conn,
            config,
            collect_ocean=not args.skip_ocean,
            collect_braiins=not args.skip_braiins,
        )
    print(_proposal_json(result))
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    if args.interval_seconds < 30:
        raise SystemExit("interval must be at least 30 seconds")
    if args.cycles < 1:
        raise SystemExit("cycles must be at least 1")

    experiment = start_experiment(args.cycles, args.interval_seconds, args.hypothesis)
    print(f"experiment: {experiment.run_id}")

    with connect() as conn:
        status = "completed"
        return_code = 0
        try:
            for index in range(args.cycles):
                result = run_cycle(conn, config)
                print(
                    f"cycle {index + 1}/{args.cycles}: "
                    f"{result.proposal.action} - {result.proposal.reason}"
                )
                if index + 1 < args.cycles:
                    time.sleep(args.interval_seconds)
        except KeyboardInterrupt:
            status = "interrupted"
            return_code = 130
            print("interrupted: writing partial experiment report before exit")
        report_path = finish_experiment(
            conn,
            experiment.run_id,
            experiment.started_utc,
            args.cycles,
            args.interval_seconds,
            args.hypothesis,
            status=status,
        )
    print(f"experiment_report: {report_path}")
    return return_code


def cmd_evaluate(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    with connect() as conn:
        init_db(conn)
        proposal = propose(config, latest_ocean_snapshot(conn), latest_market_snapshot(conn))
        save_proposal(conn, proposal)
    print(_proposal_json(proposal))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    with connect() as conn:
        init_db(conn)
        print(build_text_report(conn, sample_limit=args.samples))
    return 0


def cmd_next(_: argparse.Namespace) -> int:
    with connect() as conn:
        init_db(conn)
        print(build_operator_cockpit(conn))
    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    with connect() as conn:
        init_db(conn)
        plan = build_automation_plan(conn)
    print(render_automation_plan(plan))
    if not plan.needs_confirmation:
        return 0
    if not args.yes:
        answer = input("> ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Automation cancelled. No action was taken.")
            return 0

    if plan.kind == "wait_then_once":
        _wait_with_progress(plan.wait_seconds)
        _run_one_fresh_cycle(config)
        _print_cockpit()
        return 0
    if plan.kind == "once_now":
        _run_one_fresh_cycle(config)
        _print_cockpit()
        return 0
    if plan.kind == "watch_2h":
        result = cmd_watch(
            argparse.Namespace(
                config=args.config,
                cycles=24,
                interval_seconds=300,
                hypothesis="automation pipeline: bounded passive watch",
            )
        )
        _print_cockpit()
        return result
    if plan.kind == "report_only":
        with connect() as conn:
            init_db(conn)
            print(build_text_report(conn))
        return 0

    print("Automation plan had no executable action.")
    return 0


def cmd_experiments(_: argparse.Namespace) -> int:
    if not EXPERIMENT_LOG.exists():
        print("No experiment log yet. Run ./scripts/ratchet watch 2.")
        return 0
    print(EXPERIMENT_LOG.read_text(encoding="utf-8"))
    return 0


def cmd_retro_report(args: argparse.Namespace) -> int:
    with connect() as conn:
        init_db(conn)
        summary = summarize_since(
            conn,
            run_id=args.run_id,
            started_utc=args.since,
            ended_utc=args.until,
            planned_cycles=0,
            interval_seconds=0,
            hypothesis=args.hypothesis,
        )
        report_path = (
            write_retro_report(conn, args.run_id, args.since, args.until, args.hypothesis)
            if args.write
            else None
        )
    print(
        "\n".join(
            [
                f"run_id: {summary.run_id}",
                f"since: {summary.started_utc}",
                f"until: {summary.ended_utc or 'n/a'}",
                f"collected_samples: {summary.sample_count}",
                f"first_sample_utc: {summary.first_sample_utc or 'n/a'}",
                f"last_sample_utc: {summary.last_sample_utc or 'n/a'}",
                f"action_counts: {summary.actions or {}}",
                f"strategy_price_min_avg_max: {summary.min_price} / {summary.avg_price} / {summary.max_price}",
                f"expected_net_min_avg_max_btc: {summary.min_expected_net} / {summary.avg_expected_net} / {summary.max_expected_net}",
                f"latest_action: {summary.latest_action or 'n/a'}",
                f"latest_reason: {summary.latest_reason or 'n/a'}",
                f"report: {report_path or 'not written; add --write'}",
            ]
        )
    )
    return 0


def cmd_guardrails(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    print(json.dumps(config.guardrails.__dict__, default=str, indent=2))
    return 0


def _proposal_json(proposal: object) -> str:
    def default(value: object) -> object:
        if hasattr(value, "__dict__"):
            return value.__dict__
        return str(value)

    return json.dumps(proposal, default=default, indent=2)


def _run_one_fresh_cycle(config: object) -> None:
    with connect() as conn:
        run_cycle(conn, config)


def _print_cockpit() -> None:
    with connect() as conn:
        init_db(conn)
        print(build_operator_cockpit(conn))


def _wait_with_progress(wait_seconds: int) -> None:
    remaining = max(0, wait_seconds)
    if remaining == 0:
        return
    print(f"Waiting {remaining // 60} minute(s) before the next allowed action.")
    while remaining > 0:
        sleep_for = min(60, remaining)
        time.sleep(sleep_for)
        remaining -= sleep_for
        print(f"Timer: {remaining // 60} minute(s) remaining.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="braiins-ratchet")
    sub = parser.add_subparsers(required=True)

    init = sub.add_parser("init-db", help="create local SQLite database")
    init.set_defaults(func=cmd_init_db)

    ocean = sub.add_parser("collect-ocean", help="collect one OCEAN dashboard snapshot")
    ocean.add_argument("--config")
    ocean.set_defaults(func=cmd_collect_ocean)

    market = sub.add_parser("import-market", help="import manual Braiins market JSON snapshot")
    market.add_argument("path")
    market.set_defaults(func=cmd_import_market)

    braiins = sub.add_parser(
        "collect-braiins-public",
        help="collect one unauthenticated Braiins public market snapshot",
    )
    braiins.add_argument("--config")
    braiins.add_argument("--base-url", default="https://hashpower.braiins.com/webapi")
    braiins.set_defaults(func=cmd_collect_braiins_public)

    cycle = sub.add_parser("cycle", help="collect OCEAN, collect public Braiins, then evaluate")
    cycle.add_argument("--config")
    cycle.add_argument("--skip-ocean", action="store_true")
    cycle.add_argument("--skip-braiins", action="store_true")
    cycle.set_defaults(func=cmd_cycle)

    watch = sub.add_parser("watch", help="run bounded repeated monitor cycles")
    watch.add_argument("--config")
    watch.add_argument("--cycles", type=int, default=3)
    watch.add_argument("--interval-seconds", type=int, default=300)
    watch.add_argument("--hypothesis")
    watch.set_defaults(func=cmd_watch)

    evaluate = sub.add_parser("evaluate", help="emit monitor-only strategy recommendation")
    evaluate.add_argument("--config")
    evaluate.set_defaults(func=cmd_evaluate)

    report = sub.add_parser("report", help="print latest state and proposal")
    report.add_argument("--samples", type=int, default=50)
    report.set_defaults(func=cmd_report)

    next_step = sub.add_parser("next", help="print exactly what the operator should do next")
    next_step.set_defaults(func=cmd_next)

    pipeline = sub.add_parser("pipeline", help="propose and confirm the next automation step")
    pipeline.add_argument("--config")
    pipeline.add_argument("--yes", action="store_true", help="accept the printed plan without prompting")
    pipeline.set_defaults(func=cmd_pipeline)

    experiments = sub.add_parser("experiments", help="print the Karpathy-style experiment log")
    experiments.set_defaults(func=cmd_experiments)

    retro = sub.add_parser("retro-report", help="summarize stored snapshots since an ISO UTC timestamp")
    retro.add_argument("--since", required=True)
    retro.add_argument("--until")
    retro.add_argument("--run-id", default="retro")
    retro.add_argument("--hypothesis")
    retro.add_argument("--write", action="store_true")
    retro.set_defaults(func=cmd_retro_report)

    guardrails = sub.add_parser("guardrails", help="print active guardrails")
    guardrails.add_argument("--config")
    guardrails.set_defaults(func=cmd_guardrails)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
