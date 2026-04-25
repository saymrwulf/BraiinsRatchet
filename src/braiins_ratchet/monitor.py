from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .braiins import BraiinsPublicClient
from .config import AppConfig
from .models import MarketSnapshot, OceanSnapshot, StrategyProposal
from .ocean import fetch_snapshot as fetch_ocean_snapshot
from .storage import (
    init_db,
    latest_market_snapshot,
    latest_ocean_snapshot,
    save_market_snapshot,
    save_ocean_snapshot,
    save_proposal,
)
from .strategy import propose


OceanFetcher = Callable[[str], OceanSnapshot]
MarketFetcher = Callable[[], MarketSnapshot]


@dataclass(frozen=True)
class CycleResult:
    ocean: OceanSnapshot | None
    market: MarketSnapshot | None
    proposal: StrategyProposal


def run_cycle(
    conn,
    config: AppConfig,
    *,
    collect_ocean: bool = True,
    collect_braiins: bool = True,
    ocean_fetcher: OceanFetcher = fetch_ocean_snapshot,
    market_fetcher: MarketFetcher | None = None,
) -> CycleResult:
    init_db(conn)

    ocean = latest_ocean_snapshot(conn)
    market = latest_market_snapshot(conn)

    if collect_ocean:
        ocean = ocean_fetcher(config.ocean.dashboard_url)
        save_ocean_snapshot(conn, ocean)

    if collect_braiins:
        fetcher = market_fetcher or BraiinsPublicClient().fetch_market_snapshot
        market = fetcher()
        save_market_snapshot(conn, market)

    proposal = propose(config, ocean, market)
    save_proposal(conn, proposal)

    return CycleResult(ocean=ocean, market=market, proposal=proposal)
