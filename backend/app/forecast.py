"""Прогноз: простой прогноз (точка отсчёта), Prophet, проверка точности."""

import numpy as np
import pandas as pd

from app.analytics import by_period
from app.config import FORECAST_DAYS

WEEK_DAYS = 7


def to_daily(events: pd.DataFrame, value: str = "amount") -> pd.DataFrame:
    # События -> ряд по дням: колонки ds (дата) и y (значение) - так их называет Prophet.
    # Дни без продаж становятся нулями, а не пропадают
    daily = by_period(events, "день", value)
    return pd.DataFrame({"ds": daily.index, "y": daily.to_numpy()})


def naive_forecast(daily: pd.DataFrame, days: int = FORECAST_DAYS) -> pd.DataFrame:
    # Простой прогноз "как на прошлой неделе": последние 7 дней повторяем по кругу.
    # Это точка отсчёта: хорошая модель должна быть точнее
    if len(daily) < WEEK_DAYS:
        raise ValueError(f"Для простого прогноза нужно хотя бы {WEEK_DAYS} дней истории")
    last_week = daily["y"].tail(WEEK_DAYS).to_numpy()
    future_dates = pd.date_range(daily["ds"].iloc[-1] + pd.Timedelta(days=1), periods=days)
    # np.resize повторяет неделю, пока не наберётся нужное количество дней
    return pd.DataFrame({"ds": future_dates, "yhat": np.resize(last_week, days)})
