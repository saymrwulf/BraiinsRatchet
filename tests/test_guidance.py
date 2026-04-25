from decimal import Decimal
from datetime import UTC, datetime
import sqlite3
import unittest

from braiins_ratchet.guidance import build_operator_cockpit
from braiins_ratchet.models import CandidateOrder, MarketSnapshot, OceanSnapshot, StrategyProposal
from braiins_ratchet.storage import init_db, save_market_snapshot, save_ocean_snapshot, save_proposal


class GuidanceTests(unittest.TestCase):
    def test_empty_database_tells_operator_to_setup_and_sample(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_db(conn)

        text = build_operator_cockpit(conn)

        self.assertIn("Braiins Ratchet Cockpit", text)
        self.assertIn("./scripts/ratchet setup", text)
        self.assertIn("./scripts/ratchet once", text)

    def test_manual_canary_tells_operator_to_watch_not_escalate(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_db(conn)
        save_ocean_snapshot(
            conn,
            OceanSnapshot(
                timestamp_utc=datetime.now(UTC).isoformat(timespec="seconds"),
                pool_hashrate_eh_s=Decimal("16.95"),
            ),
        )
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc=datetime.now(UTC).isoformat(timespec="seconds"),
                best_price_btc_per_eh_day=Decimal("0.48031"),
                source="braiins-public",
            ),
        )
        save_proposal(
            conn,
            StrategyProposal(
                action="manual_canary",
                reason="inside research loss budget",
                order=CandidateOrder(
                    price_btc_per_eh_day=Decimal("0.48031"),
                    spend_btc=Decimal("0.00010"),
                    duration_minutes=180,
                ),
                breakeven_btc_per_eh_day=Decimal("0.46634"),
                expected_reward_btc=Decimal("0.000097"),
                expected_net_btc=Decimal("-0.000003"),
                score_btc=Decimal("-0.000037"),
                maturity_note="treat canary as immature",
            ),
        )

        text = build_operator_cockpit(conn)

        self.assertIn("Latest strategy action: manual_canary", text)
        self.assertIn("./scripts/ratchet watch 2", text)
        self.assertIn("not proven profit", text)

    def test_stale_market_data_routes_operator_to_once(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_db(conn)
        save_ocean_snapshot(
            conn,
            OceanSnapshot(
                timestamp_utc="2000-01-01T00:00:00+00:00",
                pool_hashrate_eh_s=Decimal("16.95"),
            ),
        )
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc="2000-01-01T00:00:01+00:00",
                best_price_btc_per_eh_day=Decimal("0.48031"),
                source="braiins-public",
            ),
        )
        save_proposal(
            conn,
            StrategyProposal(
                action="manual_canary",
                reason="inside research loss budget",
                order=None,
                breakeven_btc_per_eh_day=Decimal("0.46634"),
                expected_reward_btc=Decimal("0.000097"),
                expected_net_btc=Decimal("-0.000003"),
                score_btc=Decimal("-0.000037"),
                maturity_note="treat canary as immature",
            ),
        )

        text = build_operator_cockpit(conn)

        self.assertIn("Braiins sample freshness: stale", text)
        self.assertIn("run: ./scripts/ratchet once", text)
        self.assertIn("do not interpret old price action", text)


if __name__ == "__main__":
    unittest.main()
