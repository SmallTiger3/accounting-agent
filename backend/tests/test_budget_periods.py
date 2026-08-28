from datetime import date

import pytest

from app.services.budget_periods import clamp_period_to_today, get_period_bounds


def test_monthly_period_uses_complete_month_for_past_month():
    assert get_period_bounds("monthly", 2025, 2) == (date(2025, 2, 1), date(2025, 2, 28))


def test_monthly_period_handles_december():
    assert get_period_bounds("monthly", 2025, 12) == (date(2025, 12, 1), date(2025, 12, 31))


def test_yearly_period_covers_the_full_year():
    assert get_period_bounds("yearly", 2025) == (date(2025, 1, 1), date(2025, 12, 31))


def test_weekly_period_starts_on_monday():
    assert get_period_bounds("weekly", 2026, 8, date(2026, 8, 28)) == (
        date(2026, 8, 24), date(2026, 8, 30)
    )


def test_current_period_is_clamped_at_today():
    assert clamp_period_to_today(date(2026, 8, 1), date(2026, 8, 31), date(2026, 8, 28)) == (
        date(2026, 8, 1), date(2026, 8, 28)
    )


def test_past_period_is_not_clamped():
    assert clamp_period_to_today(date(2025, 2, 1), date(2025, 2, 28), date(2026, 8, 28)) == (
        date(2025, 2, 1), date(2025, 2, 28)
    )


def test_future_period_is_not_clamped():
    assert clamp_period_to_today(date(2026, 9, 1), date(2026, 9, 30), date(2026, 8, 28)) == (
        date(2026, 9, 1), date(2026, 9, 30)
    )


def test_unknown_period_is_rejected():
    with pytest.raises(ValueError):
        get_period_bounds("daily", 2026, 8)
