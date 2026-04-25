from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


BTC = Decimal


@dataclass(frozen=True)
class OceanSnapshot:
    timestamp_utc: str
    pool_hashrate_eh_s: Decimal | None = None
    network_difficulty_t: Decimal | None = None
    share_log_window_t: Decimal | None = None
    avg_block_time_hours: Decimal | None = None
    source: str = "ocean"


@dataclass(frozen=True)
class MarketSnapshot:
    timestamp_utc: str
    best_price_btc_per_eh_day: Decimal | None
    best_bid_btc_per_eh_day: Decimal | None = None
    best_ask_btc_per_eh_day: Decimal | None = None
    last_price_btc_per_eh_day: Decimal | None = None
    total_hashrate_eh_s: Decimal | None = None
    available_hashrate_eh_s: Decimal | None = None
    status: str | None = None
    source: str = "manual"


@dataclass(frozen=True)
class PriceStats:
    count: int
    min_price: Decimal | None
    avg_price: Decimal | None
    max_price: Decimal | None


@dataclass(frozen=True)
class CandidateOrder:
    price_btc_per_eh_day: Decimal
    spend_btc: Decimal
    duration_minutes: int
    objective: str = "manual-canary"

    @property
    def implied_hashrate_eh_s(self) -> Decimal:
        days = Decimal(self.duration_minutes) / Decimal(1440)
        if days <= 0 or self.price_btc_per_eh_day <= 0:
            return Decimal("0")
        return self.spend_btc / (self.price_btc_per_eh_day * days)


@dataclass(frozen=True)
class StrategyProposal:
    action: Literal["observe", "manual_canary", "manual_bid"]
    reason: str
    order: CandidateOrder | None
    breakeven_btc_per_eh_day: Decimal | None
    expected_reward_btc: Decimal
    expected_net_btc: Decimal
    score_btc: Decimal
    maturity_note: str
