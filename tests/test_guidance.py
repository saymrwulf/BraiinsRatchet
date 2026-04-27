from decimal import Decimal
from datetime import UTC, datetime
import sqlite3
import unittest

from braiins_ratchet.guidance import (
    CompletedWatch,
    _cooldown_status_lines,
    _do_this_now,
    _pathway_forecast,
    build_operator_cockpit,
)
from braiins_ratchet.models import CandidateOrder, MarketSnapshot, OceanSnapshot, StrategyProposal
from braiins_ratchet.storage import init_db, save_market_snapshot, save_ocean_snapshot, save_proposal


class GuidanceTests(unittest.TestCase):
    def test_empty_database_tells_operator_to_setup_and_sample(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_db(conn)

        text = build_operator_cockpit(conn)

        self.assertIn("Braiins Ratchet Cockpit", text)
        self.assertIn("./scripts/ratchet setup", text)
        self.assertIn("./scripts/ratchet once", text)

    def test_manual_canary_tells_operator_to_watch_not_escalate(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_db(conn)
        save_ocean_snapshot(
            conn,
            OceanSnapshot(
                timestamp_utc=datetime.now(UTC).isoformat(timespec="seconds"),
                pool_hashrate_eh_s=Decimal("16.95"),
            ),
        )
        save_market_snapshot(
            conn,
            MarketSnapshot(
                timestamp_utc=datetime.now(UTC).isoformat(timespec="seconds"),
                best_price_btc_per_eh_day=Decimal("0.48031"),
                source="braiins-public",
            ),
        )
        save_proposal(
            conn,
            StrategyProposal(
                action="manual_canary",
                reason="inside research loss budget",
                order=CandidateOrder(
                    price_btc_per_eh_day=Decimal("0.48031"),
                    spend_btc=Decimal("0.00010"),
                    duration_minutes=180,
                ),
                breakeven_btc_per_eh_day=Decimal("0.46634"),
                expected_reward_btc=Decimal("0.000097"),
                expected_net_btc=Decimal("-0.000003"),
                score_btc=Decimal("-0.000037"),
                maturity_note="treat canary as immature",
            ),
        )

        text = build_operator_cockpit(conn)

        self.assertIn("Latest strategy action: manual_canary", text)
        self.assertIn("./scripts/ratchet watch 2", text)
        self.assertIn("not proven profit", text)
        self.assertIn("Ratchet Pathway Forecast", text)
        self.assertIn("Immediate, very likely", text)
        self.assertIn("Midterm, likely", text)
        self.assertIn("Longterm, possible", text)

    def test_stale_market_data_routes_operator_to_once(self) -> None:
        lines = _do_this_now(
            active_watch=None,
            active_manual_positions=[],
            completed_watch=None,
            has_ocean=True,
            has_market=True,
            is_fresh=False,
            action="manual_canary",
        )

        text = "\n".join(lines)

        self.assertIn("./scripts/ratchet once", text)
        self.assertIn("latest Braiins sample is stale", text)

    def test_recent_completed_watch_stops_identical_watch_loop(self) -> None:
        lines = _do_this_now(
            active_watch=None,
            active_manual_positions=[],
            completed_watch=_completed_watch(age_minutes=4),
            has_ocean=True,
            has_market=True,
            is_fresh=True,
            action="manual_canary",
        )

        text = "\n".join(lines)

        self.assertIn("STOP.", text)
        self.assertIn("Do not start another identical watch now.", text)
        self.assertIn("./scripts/ratchet once", text)

    def test_recent_completed_watch_forecast_enters_cooldown(self) -> None:
        lines = _pathway_forecast(
            active_watch=None,
            active_manual_positions=[],
            completed_watch=_completed_watch(age_minutes=4),
            has_ocean=True,
            has_market=True,
            is_fresh=True,
            action="manual_canary",
        )

        text = "\n".join(lines)

        self.assertIn("Immediate, certain: stop this stage", text)
        self.assertIn("Midterm, likely: after cooldown", text)

    def test_active_manual_exposure_blocks_new_experiments(self) -> None:
        lines = _do_this_now(
            active_watch=None,
            active_manual_positions=["#1 braiins long order"],
            completed_watch=None,
            has_ocean=True,
            has_market=True,
            is_fresh=True,
            action="manual_canary",
        )

        text = "\n".join(lines)

        self.assertIn("HOLD.", text)
        self.assertIn("Manual Braiins exposure is active", text)
        self.assertIn("position close POSITION_ID", text)

    def test_cooldown_status_includes_timer_and_progress_bar(self) -> None:
        lines = _cooldown_status_lines(_completed_watch(age_minutes=90))

        text = "\n".join(lines)

        self.assertIn("Cooldown progress: [#####---------------] 25%", text)
        self.assertIn("Earliest next action: 2026-04-28T00:00:00+02:00", text)
        self.assertIn("Cooldown remaining: 270 minutes", text)


def _completed_watch(age_minutes: int) -> CompletedWatch:
    return CompletedWatch(
        report_path="reports/run-example.md",
        age_minutes=age_minutes,
        remaining_minutes=360 - age_minutes,
        cooldown_minutes=360,
        earliest_action_utc="2026-04-27T22:00:00+00:00",
        earliest_action_local="2026-04-28T00:00:00+02:00",
    )


if __name__ == "__main__":
    unittest.main()
