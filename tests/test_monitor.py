from decimal import Decimal
import sqlite3
import unittest

from braiins_ratchet.config import AppConfig, CapitalConfig, GuardrailsConfig, OceanConfig, StrategyConfig
from braiins_ratchet.models import MarketSnapshot, OceanSnapshot
from braiins_ratchet.monitor import run_cycle
from braiins_ratchet.storage import latest_market_snapshot, latest_ocean_snapshot, latest_proposal


class MonitorTests(unittest.TestCase):
    def test_run_cycle_collects_and_evaluates(self) -> None:
        conn = sqlite3.connect(":memory:")
        result = run_cycle(
            conn,
            _config(),
            ocean_fetcher=lambda _: OceanSnapshot(
                timestamp_utc="2026-04-25T12:00:00+00:00",
                network_difficulty_t=Decimal("135.59"),
                avg_block_time_hours=Decimal("9"),
            ),
            market_fetcher=lambda: MarketSnapshot(
                timestamp_utc="2026-04-25T12:00:01+00:00",
                best_price_btc_per_eh_day=Decimal("0.30"),
                best_ask_btc_per_eh_day=Decimal("0.30"),
                source="test",
            ),
        )

        self.assertEqual(result.proposal.action, "manual_bid")
        self.assertIsNotNone(latest_ocean_snapshot(conn))
        self.assertIsNotNone(latest_market_snapshot(conn))
        self.assertIsNotNone(latest_proposal(conn))


def _config() -> AppConfig:
    return AppConfig(
        capital=CapitalConfig(available_btc=Decimal("0.01638650")),
        ocean=OceanConfig(
            fee_rate=Decimal("0.01"),
            block_subsidy_btc=Decimal("3.125"),
            default_tx_fees_btc=Decimal("0.05"),
            dashboard_url="https://ocean.xyz/dashboard",
        ),
        guardrails=GuardrailsConfig(
            max_manual_order_btc=Decimal("0.00025"),
            max_daily_spend_btc=Decimal("0.00050"),
            max_price_btc_per_eh_day=Decimal("0.42"),
            max_canary_price_btc_per_eh_day=Decimal("0.52"),
            max_canary_expected_loss_btc=Decimal("0.000025"),
            min_discount_to_breakeven=Decimal("0.08"),
            min_duration_minutes=30,
            max_duration_minutes=720,
            recommend_only=True,
        ),
        strategy=StrategyConfig(
            target_duration_minutes=180,
            target_spend_btc=Decimal("0.00010"),
            risk_lambda=Decimal("0.35"),
        ),
    )


if __name__ == "__main__":
    unittest.main()
