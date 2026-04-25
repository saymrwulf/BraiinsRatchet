from decimal import Decimal
import unittest

from braiins_ratchet.config import GuardrailsConfig
from braiins_ratchet.guardrails import token_looks_unsafe, validate_order
from braiins_ratchet.models import CandidateOrder


class GuardrailTests(unittest.TestCase):
    def test_guardrails_block_high_price(self) -> None:
        guardrails = GuardrailsConfig(
            max_manual_order_btc=Decimal("0.00025"),
            max_daily_spend_btc=Decimal("0.00050"),
            max_price_btc_per_eh_day=Decimal("0.42"),
            min_discount_to_breakeven=Decimal("0.08"),
            min_duration_minutes=30,
            max_duration_minutes=720,
            recommend_only=True,
        )
        order = CandidateOrder(
            price_btc_per_eh_day=Decimal("0.50"),
            spend_btc=Decimal("0.00010"),
            duration_minutes=180,
        )
        violations = validate_order(order, guardrails, Decimal("0.46"))
        self.assertTrue(violations)

    def test_token_label_screening(self) -> None:
        self.assertTrue(token_looks_unsafe("owner-secret-token"))
        self.assertFalse(token_looks_unsafe("watcher-readonly-token"))


if __name__ == "__main__":
    unittest.main()
