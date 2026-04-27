import unittest

from braiins_ratchet.automation import build_automation_plan_from_state, render_automation_plan
from braiins_ratchet.guidance import CompletedWatch, OperatorState


class AutomationTests(unittest.TestCase):
    def test_completed_watch_plan_waits_then_refreshes_once(self) -> None:
        plan = build_automation_plan_from_state(
            _state(
                action="manual_canary",
                completed_watch=_completed_watch(remaining_minutes=42),
            )
        )

        self.assertEqual(plan.kind, "wait_then_once")
        self.assertEqual(plan.wait_seconds, 42 * 60)
        rendered = render_automation_plan(plan)
        self.assertIn("Wait until 2026-04-28T00:00:00+02:00.", rendered)
        self.assertIn("Are you OK with this? Type yes or no.", rendered)

    def test_manual_canary_plan_runs_one_bounded_watch(self) -> None:
        plan = build_automation_plan_from_state(_state(action="manual_canary"))

        self.assertEqual(plan.kind, "watch_2h")
        rendered = render_automation_plan(plan)
        self.assertIn("Run a 2-hour watch.", rendered)
        self.assertIn("It never places", rendered)

    def test_active_watch_plan_does_not_prompt(self) -> None:
        plan = build_automation_plan_from_state(_state(active_watch="run pid=1"))

        self.assertEqual(plan.kind, "external_wait")
        self.assertFalse(plan.needs_confirmation)

    def test_manual_exposure_hold_does_not_prompt(self) -> None:
        plan = build_automation_plan_from_state(
            _state(active_manual_positions=["#1 braiins long order"])
        )

        self.assertEqual(plan.kind, "manual_exposure_hold")
        self.assertFalse(plan.needs_confirmation)
        self.assertIn("manual Braiins exposure", render_automation_plan(plan))


def _state(
    *,
    action: str | None = None,
    active_watch: str | None = None,
    completed_watch: CompletedWatch | None = None,
    active_manual_positions: list[str] | None = None,
) -> OperatorState:
    return OperatorState(
        has_ocean=True,
        has_market=True,
        action=action,
        active_watch=active_watch,
        completed_watch=completed_watch,
        is_fresh=True,
        freshness_minutes=0,
        latest_report="reports/run-example.md",
        running_runs=[],
        latest_ocean_timestamp="2026-04-27T12:00:00+00:00",
        latest_market_timestamp="2026-04-27T12:00:00+00:00",
        active_manual_positions=active_manual_positions or [],
    )


def _completed_watch(remaining_minutes: int) -> CompletedWatch:
    return CompletedWatch(
        report_path="reports/run-example.md",
        age_minutes=360 - remaining_minutes,
        remaining_minutes=remaining_minutes,
        cooldown_minutes=360,
        earliest_action_utc="2026-04-27T22:00:00+00:00",
        earliest_action_local="2026-04-28T00:00:00+02:00",
    )


if __name__ == "__main__":
    unittest.main()
