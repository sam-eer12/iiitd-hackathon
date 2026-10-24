"""Injectable system clock for deterministic evaluation and time boundaries."""

from datetime import UTC, datetime, timedelta, timezone
from typing import Protocol

try:
    from zoneinfo import ZoneInfo

    IST = ZoneInfo("Asia/Kolkata")
except Exception:
    IST = timezone(timedelta(hours=5, minutes=30))

DEMO_CLOCK_ISO = "2026-10-24T09:00:00+05:30"


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    def __init__(self, fixed_time: datetime | str):
        if isinstance(fixed_time, str):
            self._time = datetime.fromisoformat(fixed_time)
            if self._time.tzinfo is None:
                self._time = self._time.replace(tzinfo=UTC)
        else:
            self._time = fixed_time if fixed_time.tzinfo else fixed_time.replace(tzinfo=UTC)

    def now(self) -> datetime:
        return self._time


# Default system clock instance
system_clock = SystemClock()


def get_demo_clock() -> FixedClock:
    return FixedClock(DEMO_CLOCK_ISO)
