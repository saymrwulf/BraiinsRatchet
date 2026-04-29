from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import time

from .config import AppConfig
from .monitor import CycleResult, run_cycle


@dataclass(frozen=True)
class WatchLoopSummary:
    status: str
    planned_cycles: int
    successful_cycles: int
    failed_cycles: int
    stopped_early: bool
    last_error: str | None


CycleCallback = Callable[[int, int, CycleResult], None]
FailureCallback = Callable[[int, int, Exception, int], None]
SleepCallback = Callable[[int], None]


def run_watch_loop(
    conn,
    config: AppConfig,
    *,
    planned_cycles: int,
    interval_seconds: int,
    max_consecutive_failures: int = 3,
    on_cycle: CycleCallback | None = None,
    on_failure: FailureCallback | None = None,
    sleep: SleepCallback = time.sleep,
) -> WatchLoopSummary:
    successful_cycles = 0
    failed_cycles = 0
    consecutive_failures = 0
    last_error: str | None = None
    status = "completed"
    stopped_early = False

    for index in range(planned_cycles):
        try:
            result = run_cycle(conn, config)
        except KeyboardInterrupt:
            status = "interrupted"
            stopped_early = True
            break
        except Exception as exc:
            failed_cycles += 1
            consecutive_failures += 1
            last_error = f"{type(exc).__name__}: {exc}"
            status = "partial_failed" if successful_cycles else "failed"
            if on_failure:
                on_failure(index + 1, planned_cycles, exc, consecutive_failures)
            if consecutive_failures >= max_consecutive_failures:
                stopped_early = True
                break
        else:
            successful_cycles += 1
            consecutive_failures = 0
            if on_cycle:
                on_cycle(index + 1, planned_cycles, result)

        if index + 1 < planned_cycles:
            sleep(interval_seconds)

    if status != "interrupted":
        if failed_cycles and successful_cycles:
            status = "partial_failed" if stopped_early else "partial"
        elif failed_cycles:
            status = "failed"
        else:
            status = "completed"

    return WatchLoopSummary(
        status=status,
        planned_cycles=planned_cycles,
        successful_cycles=successful_cycles,
        failed_cycles=failed_cycles,
        stopped_early=stopped_early,
        last_error=last_error,
    )
