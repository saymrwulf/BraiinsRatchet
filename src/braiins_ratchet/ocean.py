from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import html
import re
from urllib.request import Request, urlopen

from .models import OceanSnapshot


NUMBER = r"([0-9]+(?:\.[0-9]+)?)"


def fetch_dashboard_html(url: str, timeout_seconds: int = 15) -> str:
    request = Request(url, headers={"User-Agent": "BraiinsRatchet/0.1 monitor-only"})
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="replace")


def _find_decimal(patterns: tuple[str, ...], text: str) -> Decimal | None:
    without_tags = re.sub(r"<[^>]+>", " ", text)
    normalized = html.unescape(re.sub(r"\s+", " ", without_tags))
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return Decimal(match.group(1))
    return None


def parse_dashboard(html_text: str, source: str = "ocean-dashboard") -> OceanSnapshot:
    return OceanSnapshot(
        timestamp_utc=datetime.now(UTC).isoformat(timespec="seconds"),
        pool_hashrate_eh_s=_find_decimal(
            (
                rf"OCEAN Hashrate:\s*{NUMBER}\s*Eh/s",
                rf"{NUMBER}\s*EH/s\s*Pool Hashrate",
                rf"Pool Hashrate\s*{NUMBER}\s*EH/s",
            ),
            html_text,
        ),
        network_difficulty_t=_find_decimal(
            (
                rf"{NUMBER}\s*T\s*Network Difficulty",
                rf"Network Difficulty\s*{NUMBER}\s*T",
            ),
            html_text,
        ),
        share_log_window_t=_find_decimal(
            (
                rf"{NUMBER}\s*T\s*Share Log",
                rf"Share Log.*?{NUMBER}\s*T",
            ),
            html_text,
        ),
        avg_block_time_hours=_find_decimal(
            (
                rf"{NUMBER}\s*h\s*Avg Block Time",
                rf"Avg Block Time\s*{NUMBER}\s*h",
                rf"Average Time to Block.*?{NUMBER}\s*hours",
            ),
            html_text,
        ),
        source=source,
    )


def fetch_snapshot(url: str) -> OceanSnapshot:
    return parse_dashboard(fetch_dashboard_html(url), source=url)
