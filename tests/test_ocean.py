from decimal import Decimal
import unittest

from braiins_ratchet.ocean import parse_dashboard


class OceanParserTests(unittest.TestCase):
    def test_parse_dashboard_values_across_tags(self) -> None:
        snapshot = parse_dashboard(
            """
            <div>OCEAN Hashrate: <span>19.04 Eh/s</span></div>
            <section>Network Difficulty</section><strong>135.59T</strong>
            <section>Average Time to Block</section><small>Based on 24-hour average</small><b>9 hours</b>
            <section>Share Log Window</section><span>1084.76T</span>
            """
        )
        self.assertEqual(snapshot.pool_hashrate_eh_s, Decimal("19.04"))
        self.assertEqual(snapshot.network_difficulty_t, Decimal("135.59"))
        self.assertEqual(snapshot.avg_block_time_hours, Decimal("9"))
        self.assertEqual(snapshot.share_log_window_t, Decimal("1084.76"))


if __name__ == "__main__":
    unittest.main()
