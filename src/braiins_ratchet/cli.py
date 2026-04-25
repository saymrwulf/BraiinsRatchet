from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

from .braiins import BraiinsPublicClient, market_snapshot_from_json_file
from .config import load_config
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

    with connect() as conn:
        for index in range(args.cycles):
            result = run_cycle(conn, config)
            print(f"cycle {index + 1}/{args.cycles}: {result.proposal.action} - {result.proposal.reason}")
            if index + 1 < args.cycles:
                time.sleep(args.interval_seconds)
    return 0


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
    watch.set_defaults(func=cmd_watch)

    evaluate = sub.add_parser("evaluate", help="emit monitor-only strategy recommendation")
    evaluate.add_argument("--config")
    evaluate.set_defaults(func=cmd_evaluate)

    report = sub.add_parser("report", help="print latest state and proposal")
    report.add_argument("--samples", type=int, default=50)
    report.set_defaults(func=cmd_report)

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
