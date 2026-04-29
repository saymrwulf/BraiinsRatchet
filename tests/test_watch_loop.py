import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from braiins_ratchet.watch_loop import run_watch_loop


class WatchLoopTests(unittest.TestCase):
    def test_single_network_failure_creates_partial_report_not_crash(self) -> None:
        conn = sqlite3.connect(":memory:")
        result = SimpleNamespace(proposal=SimpleNamespace(action="manual_canary", reason="ok"))
        failures: list[str] = []

        with patch("braiins_ratchet.watch_loop.run_cycle", side_effect=[result, RuntimeError("HTTP 520")]):
            summary = run_watch_loop(
                conn,
                SimpleNamespace(),
                planned_cycles=2,
                interval_seconds=1,
                on_failure=lambda *_args: failures.append("failed"),
                sleep=lambda _seconds: None,
            )

        self.assertEqual(summary.status, "partial")
        self.assertEqual(summary.successful_cycles, 1)
        self.assertEqual(summary.failed_cycles, 1)
        self.assertFalse(summary.stopped_early)
        self.assertEqual(failures, ["failed"])

    def test_consecutive_failures_stop_early(self) -> None:
        conn = sqlite3.connect(":memory:")

        with patch("braiins_ratchet.watch_loop.run_cycle", side_effect=RuntimeError("offline")):
            summary = run_watch_loop(
                conn,
                SimpleNamespace(),
                planned_cycles=24,
                interval_seconds=1,
                max_consecutive_failures=3,
                sleep=lambda _seconds: None,
            )

        self.assertEqual(summary.status, "failed")
        self.assertEqual(summary.successful_cycles, 0)
        self.assertEqual(summary.failed_cycles, 3)
        self.assertTrue(summary.stopped_early)

    def test_keyboard_interrupt_returns_interrupted_summary(self) -> None:
        conn = sqlite3.connect(":memory:")

        with patch("braiins_ratchet.watch_loop.run_cycle", side_effect=KeyboardInterrupt):
            summary = run_watch_loop(
                conn,
                SimpleNamespace(),
                planned_cycles=24,
                interval_seconds=1,
                sleep=lambda _seconds: None,
            )

        self.assertEqual(summary.status, "interrupted")
        self.assertEqual(summary.successful_cycles, 0)
        self.assertEqual(summary.failed_cycles, 0)
        self.assertTrue(summary.stopped_early)


if __name__ == "__main__":
    unittest.main()
