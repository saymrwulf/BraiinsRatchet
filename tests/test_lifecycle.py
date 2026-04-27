from datetime import UTC, datetime, timedelta
import sqlite3
import unittest

from braiins_ratchet.lifecycle import (
    close_manual_position,
    get_lifecycle_status,
    init_lifecycle_db,
    list_manual_positions,
    open_manual_position,
    render_manual_positions,
    render_lifecycle_status,
    render_supervisor_plan,
)


class LifecycleTests(unittest.TestCase):
    def test_lifecycle_tables_initialize_and_status_defaults(self) -> None:
        conn = sqlite3.connect(":memory:")

        init_lifecycle_db(conn)
        status = get_lifecycle_status(conn)

        self.assertEqual(status.phase, "idle")
        self.assertIsNone(status.next_action_utc)
        self.assertIn("no lifecycle state", status.message)

    def test_lifecycle_status_renders_countdown(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_lifecycle_db(conn)
        next_action = datetime.now(UTC) + timedelta(minutes=5)
        conn.execute("INSERT INTO lifecycle_state (key, value) VALUES (?, ?)", ("phase", "cooldown"))
        conn.execute(
            "INSERT INTO lifecycle_state (key, value) VALUES (?, ?)",
            ("next_action_utc", next_action.isoformat(timespec="seconds")),
        )
        conn.commit()

        text = render_lifecycle_status(conn)

        self.assertIn("Phase: cooldown", text)
        self.assertIn("Countdown:", text)

    def test_supervisor_plan_states_monitor_only_resume_contract(self) -> None:
        text = render_supervisor_plan()

        self.assertIn("Resume persisted lifecycle state", text)
        self.assertIn("Restart ./scripts/ratchet supervise", text)
        self.assertIn("never places", text)

    def test_manual_position_open_blocks_lifecycle_until_closed(self) -> None:
        conn = sqlite3.connect(":memory:")
        init_lifecycle_db(conn)

        position_id = open_manual_position(
            conn,
            venue="braiins",
            description="manual long bid",
            expected_maturity_utc="2026-04-30T00:00:00+00:00",
            payload={"spend_btc": "0.0001"},
        )

        status = get_lifecycle_status(conn)
        active = list_manual_positions(conn, status="active")
        self.assertEqual(status.phase, "manual_exposure_active")
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].id, position_id)
        self.assertIn("manual long bid", render_manual_positions(conn))

        self.assertTrue(close_manual_position(conn, position_id))
        self.assertEqual(list_manual_positions(conn, status="active"), [])
        self.assertEqual(get_lifecycle_status(conn).phase, "idle")


if __name__ == "__main__":
    unittest.main()
