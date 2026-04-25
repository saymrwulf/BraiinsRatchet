from __future__ import annotations

from decimal import Decimal

from .config import GuardrailsConfig
from .models import CandidateOrder


def validate_order(
    order: CandidateOrder,
    guardrails: GuardrailsConfig,
    breakeven_btc_per_eh_day: Decimal | None,
) -> list[str]:
    violations = validate_order_structure(order, guardrails)

    if (
        guardrails.max_price_btc_per_eh_day > 0
        and order.price_btc_per_eh_day > guardrails.max_price_btc_per_eh_day
    ):
        violations.append(
            f"price exceeds max_price_btc_per_eh_day={guardrails.max_price_btc_per_eh_day}"
        )
    if breakeven_btc_per_eh_day and breakeven_btc_per_eh_day > 0:
        required = breakeven_btc_per_eh_day * (Decimal("1") - guardrails.min_discount_to_breakeven)
        if order.price_btc_per_eh_day > required:
            violations.append(
                "price does not clear required discount to breakeven "
                f"({order.price_btc_per_eh_day} > {required})"
            )
    else:
        violations.append("cannot validate discount without breakeven estimate")

    return violations


def validate_order_structure(order: CandidateOrder, guardrails: GuardrailsConfig) -> list[str]:
    violations: list[str] = []

    if not guardrails.recommend_only:
        violations.append("recommend_only must remain true in the PoC")
    if order.spend_btc <= 0:
        violations.append("spend must be positive")
    if order.spend_btc > guardrails.max_manual_order_btc:
        violations.append(f"spend exceeds max_manual_order_btc={guardrails.max_manual_order_btc}")
    if order.price_btc_per_eh_day <= 0:
        violations.append("price must be positive")
    if order.duration_minutes < guardrails.min_duration_minutes:
        violations.append(f"duration below min_duration_minutes={guardrails.min_duration_minutes}")
    if order.duration_minutes > guardrails.max_duration_minutes:
        violations.append(f"duration exceeds max_duration_minutes={guardrails.max_duration_minutes}")

    return violations


def token_looks_unsafe(token: str) -> bool:
    lowered = token.lower()
    unsafe_markers = ("owner", "admin", "trade", "write", "order", "secret")
    return any(marker in lowered for marker in unsafe_markers)
