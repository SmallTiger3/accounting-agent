from datetime import date, timedelta
from typing import Optional, Tuple


def get_period_bounds(
    period: str,
    year: int,
    month: Optional[int] = None,
    reference_date: Optional[date] = None,
) -> Tuple[date, date]:
    if period not in {"weekly", "monthly", "yearly"}:
        raise ValueError(f"Unsupported budget period: {period}")

    if period == "yearly":
        return date(year, 1, 1), date(year, 12, 31)

    if period == "weekly":
        anchor = reference_date or date(year, month or 1, 1)
        start = anchor - timedelta(days=anchor.weekday())
        return start, start + timedelta(days=6)

    target_month = month or 1
    start = date(year, target_month, 1)
    if target_month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, target_month + 1, 1) - timedelta(days=1)
    return start, end


def clamp_period_to_today(
    start: date, end: date, today: Optional[date] = None
) -> Tuple[date, date]:
    current = today or date.today()
    if start <= current <= end:
        return start, current
    return start, end
