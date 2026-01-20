from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List


def entries_for_habit(data: Dict[str, Any], habit_id: str) -> List[Dict[str, Any]]:
    return [e for e in data.get("entries", []) if e.get("habit_id") == habit_id]


def totals_by_day(entries: List[Dict[str, Any]]) -> Dict[str, int]:
    totals: Dict[str, int]  = {}
    for e in entries:
        d = e.get("date")
        v = int(e.get("value", 0))
        if d:
            totals[d] = totals.get(d, 0) + v
    return totals


def sum_last_n_days(totals: Dict[str, int], n: int, today: date | None = None) -> int:
    today = today or date.today()
    total = 0
    for i in range(n):
        d = (today - timedelta(days=i)).isoformat()
        total += totals.get(d, 0)
    return total


def streak_days_meeting_target(
    totals: Dict[str, int],
    target_per_day: int,
    today: date | None = None,
) -> int:
    # Streak counts consecutive days (ending today) where totals[day] >= target.
    today = today or date.today()
    streak = 0
    cur = today
    while True:
        d = cur.isoformat()
        if totals.get(d, 0) >= target_per_day:
            streak += 1
            cur = cur - timedelta(days=1)
        else:
            break
    return streak


def weekly_total(totals: Dict[str, int], today: date | None = None) -> int:
    return sum_last_n_days(totals, 7, today=today)


def monthly_total(totals: Dict[str, int], today: date | None = None) -> int:
    # just enough to start. May expand later
    return sum_last_n_days(totals, 30, today=today)


def last_n_days_values(totals: dict[str, int], n: int, today: date | None = None) -> list[int]:
    today = today or date.today()
    vals: list[int] = []
    # do mais antigo -> mais recente (bonito para sparkline)
    for i in range(n - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        vals.append(int(totals.get(d, 0)))
    return vals