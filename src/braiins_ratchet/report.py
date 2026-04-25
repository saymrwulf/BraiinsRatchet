from __future__ import annotations

from .models import MarketSnapshot, OceanSnapshot, PriceStats, StrategyProposal
from .storage import latest_market_snapshot, latest_ocean_snapshot, latest_proposal, market_price_stats


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


def _fmt(value: object) -> str:
    if value is None:
        return "n/a"
    return str(value)
