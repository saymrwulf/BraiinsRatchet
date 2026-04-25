from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json
import os
from urllib.request import Request, urlopen

from .guardrails import token_looks_unsafe
from .models import MarketSnapshot


class BraiinsSafetyError(RuntimeError):
    pass


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
    raw = json.loads(open(path, "r", encoding="utf-8").read())
    return MarketSnapshot(
        timestamp_utc=str(raw.get("timestamp_utc") or datetime.now(UTC).isoformat(timespec="seconds")),
        best_price_btc_per_eh_day=(
            Decimal(str(raw["best_price_btc_per_eh_day"]))
            if raw.get("best_price_btc_per_eh_day") is not None
            else None
        ),
        available_hashrate_eh_s=(
            Decimal(str(raw["available_hashrate_eh_s"]))
            if raw.get("available_hashrate_eh_s") is not None
            else None
        ),
        source=str(raw.get("source") or path),
    )
