from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .braiins import market_snapshot_from_json_file
from .config import load_config
from .ocean import fetch_snapshot
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


def cmd_evaluate(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    with connect() as conn:
        init_db(conn)
        proposal = propose(config, latest_ocean_snapshot(conn), latest_market_snapshot(conn))
        save_proposal(conn, proposal)
    print(_proposal_json(proposal))
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

    evaluate = sub.add_parser("evaluate", help="emit monitor-only strategy recommendation")
    evaluate.add_argument("--config")
    evaluate.set_defaults(func=cmd_evaluate)

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
