from datetime import UTC, datetime, timedelta
import sqlite3
import unittest

from braiins_ratchet.lifecycle import (
    get_lifecycle_status,
    init_lifecycle_db,
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


if __name__ == "__main__":
    unittest.main()
