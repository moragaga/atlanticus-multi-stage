from datetime import date

import pytest

from ada.ui.branding import BrandDefinitionError, MonthDayWindow


def test_regular_window_is_inclusive() -> None:
    window = MonthDayWindow(9, 1, 9, 30)

    assert window.is_active(date(2026, 9, 1))
    assert window.is_active(date(2026, 9, 30))
    assert not window.is_active(date(2026, 8, 31))
    assert not window.is_active(date(2026, 10, 1))


def test_window_can_cross_year_boundary() -> None:
    window = MonthDayWindow(12, 26, 1, 2)

    assert window.is_active(date(2026, 12, 26))
    assert window.is_active(date(2026, 12, 31))
    assert window.is_active(date(2027, 1, 1))
    assert window.is_active(date(2027, 1, 2))
    assert not window.is_active(date(2027, 1, 3))


def test_invalid_month_day_is_rejected() -> None:
    with pytest.raises(BrandDefinitionError, match='Invalid start month/day'):
        MonthDayWindow(9, 31, 10, 1)
