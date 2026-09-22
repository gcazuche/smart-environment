from datetime import UTC, datetime

import pytest

from app.web.reports import csv_text, period_bounds, summary


@pytest.mark.parametrize(("period", "day"), [("today", "20"), ("7d", "14"), ("30d", "22")])
def test_period_uses_brasilia_calendar_and_utc_end(period: str, day: str) -> None:
    now = datetime(2026, 9, 20, 12, 34, 56, tzinfo=UTC)
    bounds = period_bounds(period, now)
    month = "08" if period == "30d" else "09"
    assert bounds == {
        "start": f"2026-{month}-{day}T03:00:00Z",
        "end": "2026-09-20T12:34:56Z",
        "environment_id": None,
    }


def test_utc_early_hours_belong_to_previous_local_day() -> None:
    assert period_bounds(now=datetime(2026, 9, 20, 1, tzinfo=UTC))["start"] == (
        "2026-09-19T03:00:00Z"
    )


def test_period_validates_input_and_canonicalizes_uuid() -> None:
    with pytest.raises(ValueError, match="Período"):
        period_bounds("yesterday")
    with pytest.raises(ValueError, match="fuso"):
        period_bounds(now=datetime(2026, 9, 20))
    with pytest.raises(ValueError, match="Ambiente"):
        period_bounds(environment_id="other-org,or(id)")
    identifier = "A0000000-0000-0000-0000-000000000001"
    assert period_bounds(environment_id=identifier)["environment_id"] == identifier.lower()


@pytest.mark.parametrize("value", ["=1+1", "+CMD()", "-2", "@SUM(A1)", "  =1", "\t2", "\n3"])
def test_csv_neutralizes_formulas(value: str) -> None:
    assert csv_text([[value]]) == f'\ufeff"\'{value}"\r\n'


def test_csv_quotes_semicolons_quotes_and_preserves_unknown() -> None:
    assert csv_text([['Ambiente; "A"', None, 0]]) == '\ufeff"Ambiente; ""A""";"";"0"\r\n'


def test_summary_does_not_sum_people_or_turn_unknown_into_empty() -> None:
    assert summary([])["occupancy_percent"] is None
    result = summary(
        [
            {"camera_id": "one", "observed_minutes": 5, "unknown_minutes": 5, "peak_people": 4},
            {"camera_id": "two", "observed_minutes": 4, "occupied_minutes": 3, "empty_minutes": 1},
        ]
    )
    assert result["occupancy_percent"] == 75
    assert result["unknown_minutes"] == 5
    assert result["camera_count"] == 2
    assert "people_count" not in result
    assert "peak_people" not in result
