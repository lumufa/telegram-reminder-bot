from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

DURATION_PATTERN = re.compile(r"^(\d+)([smhd])$")
UNIT_TO_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_duration(token: str) -> timedelta:
    match = DURATION_PATTERN.match(token.lower())
    if not match:
        raise ValueError(
            f"Invalid duration: {token!r}. Expected formats: 30s, 15m, 2h, 1d."
        )
    value, unit = int(match.group(1)), match.group(2)
    return timedelta(seconds=value * UNIT_TO_SECONDS[unit])


def fire_time_from_now(token: str) -> datetime:
    return datetime.now(timezone.utc) + parse_duration(token)
