from __future__ import annotations

from dataclasses import dataclass

from .guidance import OperatorState, get_operator_state


@dataclass(frozen=True)
class AutomationPlan:
    kind: str
    title: str
    steps: list[str]
    wait_seconds: int = 0

    @property
    def needs_confirmation(self) -> bool:
        return self.kind not in {"no_action", "external_wait", "manual_exposure_hold"}


def build_automation_plan(conn) -> AutomationPlan:
    state = get_operator_state(conn)
    return build_automation_plan_from_state(state)


def build_automation_plan_from_state(state: OperatorState) -> AutomationPlan:
    if state.active_watch:
        return AutomationPlan(
            kind="external_wait",
            title="No new automation will start because a watch is already running.",
            steps=[
                "Wait for the running watch terminal to finish.",
                "After it finishes, run ./scripts/ratchet or ./scripts/ratchet pipeline again.",
            ],
        )

    if state.active_manual_positions:
        return AutomationPlan(
            kind="manual_exposure_hold",
            title="Hold because manual Braiins exposure is active.",
            steps=[
                "Do not start a new watch.",
                "Keep lifecycle supervision focused on the active manual position.",
                "Close the manual position explicitly when it is truly finished.",
            ],
        )

    if state.completed_watch and state.action == "manual_canary":
        return AutomationPlan(
            kind="wait_then_once",
            title="Wait for post-watch cooldown, then refresh once.",
            wait_seconds=state.completed_watch.remaining_minutes * 60,
            steps=[
                f"Wait until {state.completed_watch.earliest_action_local}.",
                "Run one fresh monitor cycle.",
                "Print the cockpit.",
                "Stop. It will not start another watch automatically.",
            ],
        )

    if not state.has_ocean or not state.has_market:
        return AutomationPlan(
            kind="once_now",
            title="Collect the first fresh sample.",
            steps=[
                "Run one fresh monitor cycle.",
                "Print the cockpit.",
                "Stop.",
            ],
        )

    if not state.is_fresh:
        return AutomationPlan(
            kind="once_now",
            title="Refresh stale market data.",
            steps=[
                "Run one fresh monitor cycle.",
                "Print the cockpit.",
                "Stop.",
            ],
        )

    if state.action == "manual_canary":
        return AutomationPlan(
            kind="watch_2h",
            title="Run one bounded passive watch.",
            steps=[
                "Run a 2-hour watch.",
                "Collect one public/OCEAN sample every 5 minutes.",
                "Write the experiment ledger and run report.",
                "Print the cockpit.",
                "Stop. It will not place orders.",
            ],
        )

    if state.action == "manual_bid":
        return AutomationPlan(
            kind="report_only",
            title="Show the full report for manual review.",
            steps=[
                "Print the full report.",
                "Stop. Any Braiins action remains manual.",
            ],
        )

    return AutomationPlan(
        kind="no_action",
        title="No automation is useful right now.",
        steps=[
            "Do not bid.",
            "Do not start a watch automatically.",
        ],
    )


def render_automation_plan(plan: AutomationPlan) -> str:
    lines = [
        "Automation Proposal",
        "",
        f"I am going to: {plan.title}",
        "",
        "Planned steps:",
    ]
    lines.extend(f"  {index}. {step}" for index, step in enumerate(plan.steps, start=1))
    lines.extend(
        [
            "",
            "Safety:",
            "  This pipeline is monitor-only.",
            "  It never places, changes, or cancels Braiins orders.",
        ]
    )
    if plan.needs_confirmation:
        lines.extend(["", "Are you OK with this? Type yes or no."])
    else:
        lines.extend(["", "No confirmation needed because no automated action will run."])
    return "\n".join(lines)
