from decimal import Decimal
import unittest

from braiins_ratchet.braiins import fillable_ask_for_target, market_snapshot_from_public_api


class BraiinsPublicParserTests(unittest.TestCase):
    def test_public_snapshot_uses_depth_aware_suggested_bid_as_buy_reference(self) -> None:
        stats = {
            "status": "SPOT_INSTRUMENT_STATUS_ACTIVE",
            "last_avg_price_sat": 31000000,
            "hash_rate_available_10m_ph": 250,
            "hash_rate_matched_10m_ph": 40,
        }
        orderbook = {
            "bids": [{"price_sat": 29000000}, {"price_sat": 28000000}],
            "asks": [
                {"price_sat": 30000000, "hash_rate_available_ph": 4},
                {"price_sat": 32000000, "hash_rate_available_ph": 10},
            ],
        }

        snapshot = market_snapshot_from_public_api(
            stats,
            orderbook,
            timestamp_utc="2026-04-25T12:00:00+00:00",
            target_ph=Decimal("10"),
            overpay_btc_per_eh_day=Decimal("0.01"),
        )

        self.assertEqual(snapshot.best_price_btc_per_eh_day, Decimal("0.33"))
        self.assertEqual(snapshot.best_bid_btc_per_eh_day, Decimal("0.29"))
        self.assertEqual(snapshot.best_ask_btc_per_eh_day, Decimal("0.3"))
        self.assertEqual(snapshot.fillable_price_btc_per_eh_day, Decimal("0.32"))
        self.assertEqual(snapshot.fillable_target_ph, Decimal("10"))
        self.assertEqual(snapshot.fillable_available_ph, Decimal("14"))
        self.assertEqual(snapshot.suggested_bid_btc_per_eh_day, Decimal("0.33"))
        self.assertEqual(snapshot.last_price_btc_per_eh_day, Decimal("0.31"))
        self.assertEqual(snapshot.total_hashrate_eh_s, Decimal("0.25"))
        self.assertEqual(snapshot.available_hashrate_eh_s, Decimal("0.21"))
        self.assertEqual(snapshot.status, "SPOT_INSTRUMENT_STATUS_ACTIVE")

    def test_public_snapshot_falls_back_to_last_price_without_asks(self) -> None:
        snapshot = market_snapshot_from_public_api(
            {"last_avg_price_sat": 31000000},
            {"bids": [{"price_sat": 29000000}], "asks": []},
            timestamp_utc="2026-04-25T12:00:00+00:00",
        )

        self.assertEqual(snapshot.best_price_btc_per_eh_day, Decimal("0.31"))
        self.assertEqual(snapshot.best_bid_btc_per_eh_day, Decimal("0.29"))
        self.assertIsNone(snapshot.best_ask_btc_per_eh_day)

    def test_fillable_ask_uses_limit_minus_used_when_available_absent(self) -> None:
        depth = fillable_ask_for_target(
            [
                {"price_sat": 30000000, "hash_rate_limit_ph": 5, "hash_rate_matched_ph": 3},
                {"price_sat": 31000000, "hash_rate_limit_ph": 8, "hash_rate_matched_ph": 1},
            ],
            Decimal("6"),
        )

        self.assertEqual(depth.price_btc_per_eh_day, Decimal("0.31"))
        self.assertEqual(depth.available_ph, Decimal("9"))

    def test_fillable_ask_supports_public_camel_case_orderbook(self) -> None:
        depth = fillable_ask_for_target(
            [
                {
                    "price_sat": 46090000,
                    "hashRateAvailable": 106,
                    "hashRateMatched": 106,
                },
                {
                    "price_sat": 47486000,
                    "hashRateAvailable": 576,
                    "hashRateMatched": 182,
                },
            ],
            Decimal("10"),
        )

        self.assertEqual(depth.price_btc_per_eh_day, Decimal("0.47486"))
        self.assertEqual(depth.available_ph, Decimal("394"))


if __name__ == "__main__":
    unittest.main()
