from decimal import Decimal
import sqlite3
import unittest

from braiins_ratchet.models import CandidateOrder, MarketSnapshot, OceanSnapshot, StrategyProposal
from braiins_ratchet.report import build_text_report
from braiins_ratchet.storage import init_db, save_market_snapshot, save_ocean_snapshot, save_proposal


class ReportTests(unittest.TestCase):
    def test_report_includes_latest_state_and_proposal(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_db(conn)
        save_ocean_snapshot(
            conn,
            OceanSnapshot(
                timestamp_utc="2026-04-25T12:00:00+00:00",
                pool_hashrate_eh_s=Decimal("19.04"),
                network_difficulty_t=Decimal("135.59"),
                share_log_window_t=Decimal("1084.76"),
                avg_block_time_hours=Decimal("9"),
            ),
        )
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc="2026-04-25T12:00:01+00:00",
                best_price_btc_per_eh_day=Decimal("0.30"),
                best_bid_btc_per_eh_day=Decimal("0.29"),
                best_ask_btc_per_eh_day=Decimal("0.30"),
                available_hashrate_eh_s=Decimal("0.21"),
                status="SPOT_INSTRUMENT_STATUS_ACTIVE",
            ),
        )
        save_proposal(
            conn,
            StrategyProposal(
                action="manual_bid",
                reason="test",
                order=CandidateOrder(
                    price_btc_per_eh_day=Decimal("0.30"),
                    spend_btc=Decimal("0.00010"),
                    duration_minutes=180,
                ),
                breakeven_btc_per_eh_day=Decimal("0.46"),
                expected_reward_btc=Decimal("0.00015"),
                expected_net_btc=Decimal("0.00005"),
                score_btc=Decimal("0.00001"),
                maturity_note="wait",
            ),
        )

        report = build_text_report(conn)

        self.assertIn("Strategy action: manual_bid", report)
        self.assertIn("best_ask_btc_per_eh_day: 0.30", report)
        self.assertIn("network_difficulty_t: 135.59", report)
        self.assertIn("implied_hashrate_eh_s", report)


if __name__ == "__main__":
    unittest.main()
