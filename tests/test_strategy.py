from decimal import Decimal
import unittest

from braiins_ratchet.config import AppConfig, CapitalConfig, GuardrailsConfig, OceanConfig, StrategyConfig
from braiins_ratchet.models import MarketSnapshot, OceanSnapshot
from braiins_ratchet.strategy import propose


class StrategyTests(unittest.TestCase):
    def test_strategy_recommends_observe_without_market(self) -> None:
        config = _config()
        ocean = OceanSnapshot(
            timestamp_utc="2026-04-25T00:00:00+00:00",
            network_difficulty_t=Decimal("135.59"),
            avg_block_time_hours=Decimal("9"),
        )
        proposal = propose(config, ocean, None)
        self.assertEqual(proposal.action, "observe")

    def test_strategy_can_emit_manual_bid_for_deep_discount(self) -> None:
        config = _config()
        ocean = OceanSnapshot(
            timestamp_utc="2026-04-25T00:00:00+00:00",
            network_difficulty_t=Decimal("135.59"),
            avg_block_time_hours=Decimal("9"),
        )
        market = MarketSnapshot(
            timestamp_utc="2026-04-25T00:00:00+00:00",
            best_price_btc_per_eh_day=Decimal("0.30"),
        )
        proposal = propose(config, ocean, market)
        self.assertEqual(proposal.action, "manual_bid")


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
