from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json
import os
from typing import Any
from urllib.request import Request, urlopen

from .guardrails import token_looks_unsafe
from .models import MarketSnapshot


class BraiinsSafetyError(RuntimeError):
    pass


SATOSHIS_PER_BTC = Decimal("100000000")
PH_PER_EH = Decimal("1000")
DEFAULT_PUBLIC_BASE = "https://hashpower.braiins.com/webapi"


@dataclass(frozen=True)
class BraiinsPublicClient:
    api_base: str = DEFAULT_PUBLIC_BASE

    def get_json(self, path: str) -> object:
        if not path.startswith("/"):
            raise BraiinsSafetyError("API path must start with /")
        request = Request(
            f"{self.api_base.rstrip('/')}{path}",
            headers={"User-Agent": "BraiinsRatchet/0.1 public-market"},
            method="GET",
        )
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_market_snapshot(self) -> MarketSnapshot:
        stats = self.get_json("/spot/stats")
        orderbook = self.get_json("/orderbook")
        if not isinstance(stats, dict):
            raise BraiinsSafetyError("/spot/stats did not return an object")
        if not isinstance(orderbook, dict):
            raise BraiinsSafetyError("/orderbook did not return an object")
        return market_snapshot_from_public_api(stats, orderbook)


@dataclass(frozen=True)
class BraiinsWatcherClient:
    api_base: str
    watcher_token: str

    @classmethod
    def from_env(cls) -> "BraiinsWatcherClient":
        token = os.environ.get("BRAIINS_WATCHER_TOKEN", "").strip()
        api_base = os.environ.get("BRAIINS_API_BASE", "").strip().rstrip("/")
        if not token:
            raise BraiinsSafetyError("BRAIINS_WATCHER_TOKEN is not set")
        if not api_base:
            raise BraiinsSafetyError("BRAIINS_API_BASE is not set")
        if token_looks_unsafe(token):
            raise BraiinsSafetyError("token label looks unsafe; watcher-only token required")
        return cls(api_base=api_base, watcher_token=token)

    def get_json(self, path: str) -> object:
        if not path.startswith("/"):
            raise BraiinsSafetyError("API path must start with /")
        request = Request(
            f"{self.api_base}{path}",
            headers={
                "Authorization": f"Bearer {self.watcher_token}",
                "User-Agent": "BraiinsRatchet/0.1 watcher-only",
            },
            method="GET",
        )
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))


def market_snapshot_from_json_file(path: str) -> MarketSnapshot:
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.loads(handle.read())
    return MarketSnapshot(
        timestamp_utc=str(raw.get("timestamp_utc") or datetime.now(UTC).isoformat(timespec="seconds")),
        best_price_btc_per_eh_day=(
            Decimal(str(raw["best_price_btc_per_eh_day"]))
            if raw.get("best_price_btc_per_eh_day") is not None
            else None
        ),
        best_bid_btc_per_eh_day=_optional_decimal(raw.get("best_bid_btc_per_eh_day")),
        best_ask_btc_per_eh_day=_optional_decimal(raw.get("best_ask_btc_per_eh_day")),
        last_price_btc_per_eh_day=_optional_decimal(raw.get("last_price_btc_per_eh_day")),
        total_hashrate_eh_s=_optional_decimal(raw.get("total_hashrate_eh_s")),
        available_hashrate_eh_s=(
            Decimal(str(raw["available_hashrate_eh_s"]))
            if raw.get("available_hashrate_eh_s") is not None
            else None
        ),
        status=str(raw["status"]) if raw.get("status") is not None else None,
        source=str(raw.get("source") or path),
    )


def market_snapshot_from_public_api(
    stats: dict[str, Any],
    orderbook: dict[str, Any],
    timestamp_utc: str | None = None,
) -> MarketSnapshot:
    best_bid = _best_price_from_orders(orderbook.get("bids"), prefer="max")
    best_ask = _best_price_from_orders(orderbook.get("asks"), prefer="min")
    last_price = _sat_to_btc(stats.get("last_avg_price_sat"))
    total_hashrate = _ph_to_eh(stats.get("hash_rate_available_10m_ph"))
    matched_hashrate = _ph_to_eh(stats.get("hash_rate_matched_10m_ph"))

    available_hashrate = None
    if total_hashrate is not None and matched_hashrate is not None:
        available_hashrate = max(Decimal("0"), total_hashrate - matched_hashrate)

    best_price = best_ask or last_price or best_bid

    return MarketSnapshot(
        timestamp_utc=timestamp_utc or datetime.now(UTC).isoformat(timespec="seconds"),
        best_price_btc_per_eh_day=best_price,
        best_bid_btc_per_eh_day=best_bid,
        best_ask_btc_per_eh_day=best_ask,
        last_price_btc_per_eh_day=last_price,
        total_hashrate_eh_s=total_hashrate,
        available_hashrate_eh_s=available_hashrate,
        status=str(stats["status"]) if stats.get("status") is not None else None,
        source="braiins-public",
    )


def _best_price_from_orders(orders: object, prefer: str) -> Decimal | None:
    if not isinstance(orders, list):
        return None
    prices = [
        price
        for order in orders
        if isinstance(order, dict)
        for price in [_sat_to_btc(order.get("price_sat"))]
        if price is not None
    ]
    if not prices:
        return None
    if prefer == "min":
        return min(prices)
    return max(prices)


def _sat_to_btc(value: object) -> Decimal | None:
    decimal = _optional_decimal(value)
    if decimal is None:
        return None
    return decimal / SATOSHIS_PER_BTC


def _ph_to_eh(value: object) -> Decimal | None:
    decimal = _optional_decimal(value)
    if decimal is None:
        return None
    return decimal / PH_PER_EH


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
