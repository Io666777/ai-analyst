"""Общие заготовки для тестов прогноза: ряды, где правильный ответ известен заранее."""

import numpy as np
import pandas as pd
import pytest

from app.model import to_events

# Идеальная неделя: пн-чт по 100, пт 150, сб 160, вс 140. Без случайностей
WEEK_PATTERN = [100, 100, 100, 100, 150, 160, 140]
FIRST_MONDAY = "2026-01-05"


def weekly_daily(days: int, noise: float = 0) -> pd.DataFrame:
    # Ряд по дням (ds, y), где каждая неделя одинаковая.
    # noise - небольшой случайный разброс: на идеально ровном ряде Prophet учится очень долго
    dates = pd.date_range(FIRST_MONDAY, periods=days)
    values = np.array([float(WEEK_PATTERN[date.dayofweek]) for date in dates])
    if noise:
        values += np.random.default_rng(0).normal(0, noise, days)
    return pd.DataFrame({"ds": dates, "y": values})


def noise_daily(days: int) -> pd.DataFrame:
    # Ряд из чистого шума: случайные числа без закономерностей
    rng = np.random.default_rng(0)
    dates = pd.date_range(FIRST_MONDAY, periods=days)
    return pd.DataFrame({"ds": dates, "y": rng.exponential(100, days)})


def daily_to_events(daily: pd.DataFrame) -> pd.DataFrame:
    # Ряд по дням -> события универсальной модели (для make_forecast)
    table = pd.DataFrame({"Дата": daily["ds"], "Сумма": daily["y"]})
    return to_events(table, {"Дата": "date", "Сумма": "amount"})


@pytest.fixture
def weekly_120() -> pd.DataFrame:
    return weekly_daily(120)
