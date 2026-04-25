from __future__ import annotations

from decimal import Decimal

from .config import AppConfig
from .ev import breakeven_btc_per_eh_day, downside_penalty, expected_reward_for_order
from .guardrails import validate_order
from .models import CandidateOrder, MarketSnapshot, OceanSnapshot, StrategyProposal


def propose(
    config: AppConfig,
    ocean: OceanSnapshot | None,
    market: MarketSnapshot | None,
) -> StrategyProposal:
    if ocean is None or ocean.network_difficulty_t is None:
        return _observe("missing OCEAN difficulty snapshot")
    if market is None or market.best_price_btc_per_eh_day is None:
        breakeven = breakeven_btc_per_eh_day(
            ocean.network_difficulty_t,
            config.ocean.expected_block_reward_btc,
            config.ocean.fee_rate,
        )
        return StrategyProposal(
            action="observe",
            reason="missing Braiins market price snapshot",
            order=None,
            breakeven_btc_per_eh_day=breakeven,
            expected_reward_btc=Decimal("0"),
            expected_net_btc=Decimal("0"),
            score_btc=Decimal("0"),
            maturity_note=_maturity_note(ocean),
        )

    breakeven = breakeven_btc_per_eh_day(
        ocean.network_difficulty_t,
        config.ocean.expected_block_reward_btc,
        config.ocean.fee_rate,
    )
    spend = min(config.strategy.target_spend_btc, config.guardrails.max_manual_order_btc)
    order = CandidateOrder(
        price_btc_per_eh_day=market.best_price_btc_per_eh_day,
        spend_btc=spend,
        duration_minutes=config.strategy.target_duration_minutes,
    )
    expected_reward = expected_reward_for_order(
        order,
        ocean.network_difficulty_t,
        config.ocean.expected_block_reward_btc,
        config.ocean.fee_rate,
    )
    expected_net = expected_reward - order.spend_btc
    score = expected_net - downside_penalty(expected_reward, config.strategy.risk_lambda)

    violations = validate_order(order, config.guardrails, breakeven)
    if violations:
        return StrategyProposal(
            action="observe",
            reason="guardrail blocked: " + "; ".join(violations),
            order=order,
            breakeven_btc_per_eh_day=breakeven,
            expected_reward_btc=expected_reward,
            expected_net_btc=expected_net,
            score_btc=score,
            maturity_note=_maturity_note(ocean),
        )

    if score <= 0:
        return StrategyProposal(
            action="observe",
            reason=f"risk-adjusted score is not positive ({score})",
            order=order,
            breakeven_btc_per_eh_day=breakeven,
            expected_reward_btc=expected_reward,
            expected_net_btc=expected_net,
            score_btc=score,
            maturity_note=_maturity_note(ocean),
        )

    return StrategyProposal(
        action="manual_bid",
        reason="market price clears configured guardrails and positive risk-adjusted score",
        order=order,
        breakeven_btc_per_eh_day=breakeven,
        expected_reward_btc=expected_reward,
        expected_net_btc=expected_net,
        score_btc=score,
        maturity_note=_maturity_note(ocean),
    )


def _observe(reason: str) -> StrategyProposal:
    return StrategyProposal(
        action="observe",
        reason=reason,
        order=None,
        breakeven_btc_per_eh_day=None,
        expected_reward_btc=Decimal("0"),
        expected_net_btc=Decimal("0"),
        score_btc=Decimal("0"),
        maturity_note="no maturity estimate without OCEAN snapshot",
    )


def _maturity_note(ocean: OceanSnapshot) -> str:
    if ocean.avg_block_time_hours is None:
        return "treat canary as immature until the OCEAN share-log window has elapsed"
    window_hours = ocean.avg_block_time_hours * Decimal("8")
    return f"treat canary as immature for about {window_hours} hours after spend"
