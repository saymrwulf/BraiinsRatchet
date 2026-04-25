from decimal import Decimal
import unittest

from braiins_ratchet.ev import breakeven_btc_per_eh_day


class EvTests(unittest.TestCase):
    def test_breakeven_near_expected_current_scale(self) -> None:
        value = breakeven_btc_per_eh_day(
            network_difficulty_t=Decimal("135.59"),
            expected_block_reward_btc=Decimal("3.175"),
            pool_fee_rate=Decimal("0.01"),
        )
        self.assertGreater(value, Decimal("0.45"))
        self.assertLess(value, Decimal("0.47"))


if __name__ == "__main__":
    unittest.main()
