from __future__ import annotations

from decimal import Decimal, getcontext

from .models import CandidateOrder

getcontext().prec = 28

HASHES_PER_EH = Decimal("1000000000000000000")
SECONDS_PER_DAY = Decimal("86400")
TWO_POW_32 = Decimal(2) ** Decimal(32)


def breakeven_btc_per_eh_day(
    network_difficulty_t: Decimal,
    expected_block_reward_btc: Decimal,
    pool_fee_rate: Decimal,
) -> Decimal:
    difficulty = network_difficulty_t * Decimal("1000000000000")
    expected_blocks_per_eh_day = HASHES_PER_EH * SECONDS_PER_DAY / (difficulty * TWO_POW_32)
    return expected_blocks_per_eh_day * expected_block_reward_btc * (Decimal("1") - pool_fee_rate)


def expected_reward_for_order(
    order: CandidateOrder,
    network_difficulty_t: Decimal,
    expected_block_reward_btc: Decimal,
    pool_fee_rate: Decimal,
) -> Decimal:
    price = breakeven_btc_per_eh_day(
        network_difficulty_t=network_difficulty_t,
        expected_block_reward_btc=expected_block_reward_btc,
        pool_fee_rate=pool_fee_rate,
    )
    days = Decimal(order.duration_minutes) / Decimal(1440)
    return order.implied_hashrate_eh_s * days * price


def downside_penalty(expected_reward_btc: Decimal, risk_lambda: Decimal) -> Decimal:
    # Mining rewards are lumpy. Penalize exposure until enough observations justify relaxing it.
    return expected_reward_btc * risk_lambda
