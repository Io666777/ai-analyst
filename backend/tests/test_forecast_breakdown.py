"""Тесты прогноза крупнее дней (app/forecast/breakdown.py): недели, месяцы, год назад."""

import pandas as pd
import pytest

from app.forecast import forecast_by, year_ago


def make_forecast_table(start: str, days: int, value: float = 10.0) -> pd.DataFrame:
    # Прогноз как у Prophet: по 10 р. в день, коридор ±2
    dates = pd.date_range(start, periods=days, freq="D")
    return pd.DataFrame(
        {"ds": dates, "yhat": value, "yhat_lower": value - 2, "yhat_upper": value + 2}
    )


def test_weeks_start_on_monday_edges_are_partial():
    # С четверга 01.10.2026 на 14 дней: неделя чт-вс (4 дня), полная неделя, пн-ср (3 дня)
    weeks = forecast_by(make_forecast_table("2026-10-01", 14), "неделя")
    assert [(f"{row.с:%d.%m}", f"{row.по:%d.%m}") for row in weeks.itertuples()] == [
        ("01.10", "04.10"),
        ("05.10", "11.10"),
        ("12.10", "14.10"),
    ]
    assert weeks["yhat"].tolist() == [40.0, 70.0, 30.0]
    assert weeks["yhat_lower"].tolist() == [32.0, 56.0, 24.0]  # коридор тоже сложен


def test_months_sum_to_total():
    forecast = make_forecast_table("2026-10-15", 60)
    months = forecast_by(forecast, "месяц")
    assert len(months) == 3  # конец октября, ноябрь, половина декабря
    assert months["yhat"].sum() == pytest.approx(forecast["yhat"].sum())


def test_simple_forecast_without_corridor():
    forecast = make_forecast_table("2026-10-01", 7).drop(columns=["yhat_lower", "yhat_upper"])
    weeks = forecast_by(forecast, "неделя")
    assert "yhat_lower" not in weeks


def test_year_ago_same_weekdays():
    # История - 400 дней по 5 р., прогноз - по 10 р.: «в 2 раза больше, чем год назад»
    history = pd.DataFrame({"ds": pd.date_range("2025-09-01", periods=400, freq="D"), "y": 5.0})
    forecast = make_forecast_table("2026-10-06", 14)
    result = year_ago(history, forecast)
    assert result["с"].dayofweek == forecast["ds"].min().dayofweek  # тот же день недели
    assert result["было"] == 70.0
    assert result["изменение_%"] == 100.0


def test_year_ago_needs_a_year():
    history = pd.DataFrame({"ds": pd.date_range("2026-06-01", periods=120, freq="D"), "y": 5.0})
    assert year_ago(history, make_forecast_table("2026-09-29", 14)) is None
