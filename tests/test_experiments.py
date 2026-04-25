from decimal import Decimal
import sqlite3
import unittest

from braiins_ratchet.experiments import summarize_since
from braiins_ratchet.models import MarketSnapshot
from braiins_ratchet.storage import init_db, save_market_snapshot


class ExperimentTests(unittest.TestCase):
    def test_summarize_since_collects_prices_and_proposals_in_window(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_db(conn)
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc="2026-04-25T19:08:52+00:00",
                best_price_btc_per_eh_day=Decimal("0.48024"),
                source="braiins-public",
            ),
        )
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc="2026-04-25T19:13:53+00:00",
                best_price_btc_per_eh_day=Decimal("0.48047"),
                source="braiins-public",
            ),
        )
        conn.execute(
            """
            INSERT INTO proposals (
                timestamp_utc, action, reason, expected_reward_btc, expected_net_btc,
                score_btc, maturity_note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-04-25 19:13:53",
                "manual_canary",
                "inside research loss budget",
                "0.000097",
                "-0.000003",
                "-0.000037",
                "immature",
            ),
        )
        conn.commit()

        summary = summarize_since(
            conn,
            run_id="retro-test",
            started_utc="2026-04-25T19:00:00+00:00",
            ended_utc="2026-04-25T19:20:00+00:00",
            planned_cycles=0,
            interval_seconds=0,
            hypothesis="test hypothesis",
        )

        self.assertEqual(summary.sample_count, 2)
        self.assertEqual(summary.min_price, Decimal("0.48024"))
        self.assertEqual(summary.max_price, Decimal("0.48047"))
        self.assertEqual(summary.actions, {"manual_canary": 1})
        self.assertEqual(summary.min_expected_net, Decimal("-0.000003"))
        self.assertEqual(summary.hypothesis, "test hypothesis")

    def test_summarize_since_respects_end_time(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_db(conn)
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc="2026-04-25T19:08:52+00:00",
                best_price_btc_per_eh_day=Decimal("0.48024"),
                source="braiins-public",
            ),
        )
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc="2026-04-25T21:04:16+00:00",
                best_price_btc_per_eh_day=Decimal("0.48031"),
                source="braiins-public",
            ),
        )

        summary = summarize_since(
            conn,
            run_id="window-test",
            started_utc="2026-04-25T19:00:00+00:00",
            ended_utc="2026-04-25T20:00:00+00:00",
            planned_cycles=0,
            interval_seconds=0,
        )

        self.assertEqual(summary.sample_count, 1)
        self.assertEqual(summary.max_price, Decimal("0.48024"))


if __name__ == "__main__":
    unittest.main()
