from __future__ import annotations

from decimal import Decimal

from .config import AppConfig
from .ev import breakeven_btc_per_eh_day, downside_penalty, expected_reward_for_order
from .guardrails import validate_order, validate_order_structure
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
    if not violations and score > 0:
        return StrategyProposal(
            action="manual_bid",
            reason="profit-seeking bid clears discount guardrails and positive risk-adjusted score",
            order=order,
            breakeven_btc_per_eh_day=breakeven,
            expected_reward_btc=expected_reward,
            expected_net_btc=expected_net,
            score_btc=score,
            maturity_note=_maturity_note(ocean),
        )

    canary_violations = _validate_canary(order, config, expected_net)
    if not canary_violations:
        return StrategyProposal(
            action="manual_canary",
            reason=(
                "bounded research canary: profit guardrails not cleared, "
                f"but expected_net={expected_net} is within loss budget "
                f"{config.guardrails.max_canary_expected_loss_btc}"
            ),
            order=order,
            breakeven_btc_per_eh_day=breakeven,
            expected_reward_btc=expected_reward,
            expected_net_btc=expected_net,
            score_btc=score,
            maturity_note=_maturity_note(ocean),
        )

    return StrategyProposal(
        action="observe",
        reason=(
            "no experiment recommended: "
            + "; ".join(violations + canary_violations)
            + f"; risk_adjusted_score={score}"
        ),
        order=order,
        breakeven_btc_per_eh_day=breakeven,
        expected_reward_btc=expected_reward,
        expected_net_btc=expected_net,
        score_btc=score,
        maturity_note=_maturity_note(ocean),
    )


def _validate_canary(order: CandidateOrder, config: AppConfig, expected_net: Decimal) -> list[str]:
    violations = validate_order_structure(order, config.guardrails)
    if (
        config.guardrails.max_canary_price_btc_per_eh_day > 0
        and order.price_btc_per_eh_day > config.guardrails.max_canary_price_btc_per_eh_day
    ):
        violations.append(
            "price exceeds max_canary_price_btc_per_eh_day="
            f"{config.guardrails.max_canary_price_btc_per_eh_day}"
        )
    if expected_net < -config.guardrails.max_canary_expected_loss_btc:
        violations.append(
            f"expected loss {abs(expected_net)} exceeds canary budget "
            f"{config.guardrails.max_canary_expected_loss_btc}"
        )
    return violations


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
