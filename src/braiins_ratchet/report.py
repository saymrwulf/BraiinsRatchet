from __future__ import annotations

from decimal import Decimal

from .models import MarketSnapshot, OceanSnapshot, PriceStats, StrategyProposal
from .storage import latest_market_snapshot, latest_ocean_snapshot, latest_proposal, market_price_stats

SATOSHIS_PER_BTC = Decimal("100000000")


def build_text_report(conn, *, sample_limit: int = 50) -> str:
    ocean = latest_ocean_snapshot(conn)
    market = latest_market_snapshot(conn)
    proposal = latest_proposal(conn)
    stats = market_price_stats(conn, sample_limit, source="braiins-public")

    lines = ["Braiins Ratchet Report", ""]
    lines.extend(_ocean_lines(ocean))
    lines.append("")
    lines.extend(_market_lines(market, stats))
    lines.append("")
    lines.extend(_proposal_lines(proposal))
    lines.append("")
    lines.extend(_plain_english_lines(ocean, market, proposal))
    return "\n".join(lines)


def _ocean_lines(ocean: OceanSnapshot | None) -> list[str]:
    if ocean is None:
        return ["OCEAN: no snapshot stored"]
    return [
        f"OCEAN snapshot: {ocean.timestamp_utc}",
        f"  pool_hashrate_eh_s: {_fmt(ocean.pool_hashrate_eh_s)}",
        f"  network_difficulty_t: {_fmt(ocean.network_difficulty_t)}",
        f"  share_log_window_t: {_fmt(ocean.share_log_window_t)}",
        f"  avg_block_time_hours: {_fmt(ocean.avg_block_time_hours)}",
    ]


def _market_lines(market: MarketSnapshot | None, stats: PriceStats) -> list[str]:
    if market is None:
        return ["Braiins market: no snapshot stored"]
    return [
        f"Braiins market snapshot: {market.timestamp_utc}",
        f"  status: {market.status or 'unknown'}",
        f"  best_bid_btc_per_eh_day: {_fmt(market.best_bid_btc_per_eh_day)}",
        f"  best_ask_btc_per_eh_day: {_fmt(market.best_ask_btc_per_eh_day)}",
        f"  fillable_target_ph: {_fmt(market.fillable_target_ph)}",
        f"  fillable_price_btc_per_eh_day: {_fmt(market.fillable_price_btc_per_eh_day)}",
        f"  suggested_bid_btc_per_eh_day: {_fmt(market.suggested_bid_btc_per_eh_day)}",
        f"  last_price_btc_per_eh_day: {_fmt(market.last_price_btc_per_eh_day)}",
        f"  available_hashrate_eh_s: {_fmt(market.available_hashrate_eh_s)}",
        f"  sampled_strategy_price_count: {stats.count}",
        f"  sampled_strategy_price_min_avg_max: {_fmt(stats.min_price)} / {_fmt(stats.avg_price)} / {_fmt(stats.max_price)}",
    ]


def _proposal_lines(proposal: StrategyProposal | None) -> list[str]:
    if proposal is None:
        return ["Strategy: no proposal stored"]
    lines = [
        f"Strategy action: {proposal.action}",
        f"  reason: {proposal.reason}",
        f"  breakeven_btc_per_eh_day: {_fmt(proposal.breakeven_btc_per_eh_day)}",
        f"  expected_reward_btc: {_fmt(proposal.expected_reward_btc)}",
        f"  expected_net_btc: {_fmt(proposal.expected_net_btc)}",
        f"  score_btc: {_fmt(proposal.score_btc)}",
        f"  maturity: {proposal.maturity_note}",
    ]
    if proposal.order is not None:
        lines.extend(
            [
                f"  proposed_price_btc_per_eh_day: {_fmt(proposal.order.price_btc_per_eh_day)}",
                f"  proposed_spend_btc: {_fmt(proposal.order.spend_btc)}",
                f"  proposed_duration_minutes: {proposal.order.duration_minutes}",
                f"  implied_hashrate_eh_s: {_fmt(proposal.order.implied_hashrate_eh_s)}",
            ]
        )
    return lines


def _plain_english_lines(
    ocean: OceanSnapshot | None,
    market: MarketSnapshot | None,
    proposal: StrategyProposal | None,
) -> list[str]:
    lines = ["Plain English"]
    if ocean is None or market is None or proposal is None:
        return lines + ["  Not enough data yet. Run ./scripts/ratchet once."]

    lines.append(f"  Decision: {_decision_sentence(proposal)}")

    if market.best_ask_btc_per_eh_day is not None and market.fillable_price_btc_per_eh_day is not None:
        gap = market.fillable_price_btc_per_eh_day - market.best_ask_btc_per_eh_day
        lines.append(
            "  Market depth: the visible best ask is "
            f"{market.best_ask_btc_per_eh_day}, but enough depth for "
            f"{_fmt(market.fillable_target_ph)} PH/s starts at {market.fillable_price_btc_per_eh_day} "
            f"(gap {gap})."
        )
    elif market.best_ask_btc_per_eh_day is not None:
        lines.append(
            "  Market depth: only the visible best ask was available; fillable depth was not computed."
        )

    if proposal.breakeven_btc_per_eh_day is not None and proposal.order is not None:
        edge = proposal.breakeven_btc_per_eh_day - proposal.order.price_btc_per_eh_day
        lines.append(
            "  Price check: proposed price is "
            f"{proposal.order.price_btc_per_eh_day}; estimated breakeven is "
            f"{proposal.breakeven_btc_per_eh_day}; edge is {edge} BTC/EH/day."
        )

    if proposal.order is not None:
        lines.append(
            "  Manual canary card: spend "
            f"{proposal.order.spend_btc} BTC (~{_btc_to_sats(proposal.order.spend_btc)} sats), "
            f"duration {proposal.order.duration_minutes} minutes, estimated speed "
            f"{proposal.order.implied_hashrate_eh_s * Decimal('1000')} PH/s."
        )

    lines.append(
        "  Expected result: "
        f"{proposal.expected_net_btc} BTC (~{_btc_to_sats(proposal.expected_net_btc)} sats) before luck; "
        "this is a model estimate, not a promise."
    )
    lines.append(f"  Wait time: {proposal.maturity_note}.")
    lines.append(
        "  Rule: manual_canary means buying information with bounded downside; "
        "manual_bid means the stricter profit-seeking guardrails cleared."
    )
    return lines


def _decision_sentence(proposal: StrategyProposal) -> str:
    if proposal.action == "observe":
        return "do nothing."
    if proposal.action == "manual_canary":
        return "a tiny manual research canary is allowed by the loss budget, but this is not a profit signal."
    return "a manual profit-seeking bid cleared the stricter guardrails."


def _btc_to_sats(value: Decimal) -> str:
    sats = value * SATOSHIS_PER_BTC
    return str(sats.quantize(Decimal("1")))


def _fmt(value: object) -> str:
    if value is None:
        return "n/a"
    return str(value)
