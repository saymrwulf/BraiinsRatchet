from decimal import Decimal
import sqlite3
import unittest

from braiins_ratchet.models import MarketSnapshot
from braiins_ratchet.storage import init_db, latest_market_snapshot, market_price_stats, save_market_snapshot


class StorageTests(unittest.TestCase):
    def test_market_snapshot_round_trip_extended_fields(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_db(conn)
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc="2026-04-25T12:00:00+00:00",
                best_price_btc_per_eh_day=Decimal("0.30"),
                best_bid_btc_per_eh_day=Decimal("0.29"),
                best_ask_btc_per_eh_day=Decimal("0.30"),
                fillable_price_btc_per_eh_day=Decimal("0.32"),
                fillable_target_ph=Decimal("10"),
                fillable_available_ph=Decimal("14"),
                suggested_bid_btc_per_eh_day=Decimal("0.33"),
                suggested_overpay_btc_per_eh_day=Decimal("0.01"),
                last_price_btc_per_eh_day=Decimal("0.31"),
                total_hashrate_eh_s=Decimal("0.25"),
                available_hashrate_eh_s=Decimal("0.21"),
                status="SPOT_INSTRUMENT_STATUS_ACTIVE",
                source="test",
            ),
        )

        snapshot = latest_market_snapshot(conn)
        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(snapshot.best_price_btc_per_eh_day, Decimal("0.30"))
        self.assertEqual(snapshot.best_bid_btc_per_eh_day, Decimal("0.29"))
        self.assertEqual(snapshot.best_ask_btc_per_eh_day, Decimal("0.30"))
        self.assertEqual(snapshot.fillable_price_btc_per_eh_day, Decimal("0.32"))
        self.assertEqual(snapshot.fillable_target_ph, Decimal("10"))
        self.assertEqual(snapshot.fillable_available_ph, Decimal("14"))
        self.assertEqual(snapshot.suggested_bid_btc_per_eh_day, Decimal("0.33"))
        self.assertEqual(snapshot.suggested_overpay_btc_per_eh_day, Decimal("0.01"))
        self.assertEqual(snapshot.last_price_btc_per_eh_day, Decimal("0.31"))
        self.assertEqual(snapshot.total_hashrate_eh_s, Decimal("0.25"))
        self.assertEqual(snapshot.available_hashrate_eh_s, Decimal("0.21"))
        self.assertEqual(snapshot.status, "SPOT_INSTRUMENT_STATUS_ACTIVE")

    def test_market_price_stats_can_filter_source(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_db(conn)
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc="2026-04-25T12:00:00+00:00",
                best_price_btc_per_eh_day=Decimal("0.30"),
                source="manual-example",
            ),
        )
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc="2026-04-25T12:00:01+00:00",
                best_price_btc_per_eh_day=Decimal("0.46"),
                source="braiins-public",
            ),
        )

        stats = market_price_stats(conn, 50, source="braiins-public")

        self.assertEqual(stats.count, 1)
        self.assertEqual(stats.min_price, Decimal("0.46"))
        self.assertEqual(stats.avg_price, Decimal("0.46"))
        self.assertEqual(stats.max_price, Decimal("0.46"))


if __name__ == "__main__":
    unittest.main()
