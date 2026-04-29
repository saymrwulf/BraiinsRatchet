from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from braiins_ratchet import engine


class EngineStatusTests(unittest.TestCase):
    def test_engine_status_reports_not_running_without_pid(self) -> None:
        with _isolated_engine_paths() as paths:
            with patch.object(engine, "_find_supervisor_pid", return_value=None):
                status = engine.get_engine_status()

        self.assertFalse(status.running)
        self.assertIsNone(status.pid)
        self.assertEqual(status.log_path, "logs/supervisor.log")
        self.assertFalse(paths["pid"].exists())

    def test_engine_status_clears_stale_pid_file(self) -> None:
        with _isolated_engine_paths() as paths:
            paths["pid"].parent.mkdir(parents=True, exist_ok=True)
            paths["pid"].write_text("999999", encoding="utf-8")
            with (
                patch.object(engine, "_pid_matches_supervisor", return_value=False),
                patch.object(engine, "_find_supervisor_pid", return_value=None),
            ):
                status = engine.get_engine_status()

            self.assertFalse(status.running)
            self.assertFalse(paths["pid"].exists())

    def test_engine_status_records_discovered_supervisor_pid(self) -> None:
        with _isolated_engine_paths() as paths:
            with patch.object(engine, "_find_supervisor_pid", return_value=12345):
                status = engine.get_engine_status()

            self.assertTrue(status.running)
            self.assertEqual(status.pid, 12345)
            self.assertEqual(paths["pid"].read_text(encoding="utf-8"), "12345")

    def test_engine_status_uses_active_watch_when_process_table_is_unavailable(self) -> None:
        with _isolated_engine_paths() as paths:
            paths["active_watch"].parent.mkdir(parents=True, exist_ok=True)
            paths["active_watch"].write_text('{"pid": 456, "run_id": "run-example"}', encoding="utf-8")
            with (
                patch.object(engine, "_find_supervisor_pid", return_value=None),
                patch.object(engine, "_pid_exists", return_value=True),
            ):
                status = engine.get_engine_status()

            self.assertTrue(status.running)
            self.assertEqual(status.pid, 456)
            self.assertIn("watch is running", status.detail)
            self.assertEqual(paths["pid"].read_text(encoding="utf-8"), "456")

    def test_render_engine_status_is_noob_readable(self) -> None:
        text = engine.render_engine_status(
            engine.EngineStatus(
                running=True,
                pid=123,
                detail="forever monitor engine is running as pid 123",
                log_path="logs/supervisor.log",
            )
        )

        self.assertIn("Running: yes", text)
        self.assertIn("PID: 123", text)
        self.assertIn("monitor-only", text)
        self.assertIn("never places", text)

    def test_stop_engine_handles_process_that_already_exited(self) -> None:
        with _isolated_engine_paths():
            with (
                patch.object(
                    engine,
                    "get_engine_status",
                    return_value=engine.EngineStatus(
                        running=True,
                        pid=123,
                        detail="running",
                        log_path="logs/supervisor.log",
                    ),
                ),
                patch.object(engine.os, "kill", side_effect=ProcessLookupError),
            ):
                status = engine.stop_engine()

        self.assertFalse(status.running)
        self.assertIn("already exited", status.detail)


class _isolated_engine_paths:
    def __enter__(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        self.paths = {
            "root": root,
            "data": root / "data",
            "logs": root / "logs",
            "pid": root / "data" / "supervisor.pid",
            "log": root / "logs" / "supervisor.log",
            "active_watch": root / "reports" / "ACTIVE_WATCH.json",
        }
        self.patcher = patch.multiple(
            engine,
            REPO_ROOT=self.paths["root"],
            DATA_DIR=self.paths["data"],
            LOG_DIR=self.paths["logs"],
            SUPERVISOR_PID=self.paths["pid"],
            SUPERVISOR_LOG=self.paths["log"],
            ACTIVE_WATCH=self.paths["active_watch"],
        )
        self.patcher.start()
        return self.paths

    def __exit__(self, exc_type, exc, tb):
        self.patcher.stop()
        self.tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
