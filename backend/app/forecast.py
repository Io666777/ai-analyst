"""Прогноз: простой прогноз (точка отсчёта), Prophet, проверка точности."""

import logging

import numpy as np
import pandas as pd

# Prophet пишет много служебных сообщений - приглушаем их. Делаем это ДО импорта:
# "Importing plotly failed" появляется прямо при импорте (plotly не нужен - графики в charts.py)
logging.getLogger("prophet.plot").disabled = True
# cmdstanpy ("Chain [1] start processing") настраивает свои сообщения при первом обучении,
# но только если у него ещё нет обработчика. Даём пустой - и он нашу настройку не трогает
_cmdstanpy_logger = logging.getLogger("cmdstanpy")
_cmdstanpy_logger.addHandler(logging.NullHandler())
_cmdstanpy_logger.propagate = False
_cmdstanpy_logger.setLevel(logging.WARNING)

from prophet import Prophet  # noqa: E402 - импорт после настройки логов, иначе они не приглушатся

from app.analytics import by_period  # noqa: E402
from app.config import FORECAST_DAYS, RANDOM_SEED  # noqa: E402

# А сам Prophet настраивает сообщения при импорте - поэтому его уровень ставим ПОСЛЕ
logging.getLogger("prophet").setLevel(logging.ERROR)  # предупреждения - см. YEAR_DAYS

WEEK_DAYS = 7
# Годовую сезонность включаем, если истории хотя бы год. Prophet советует 2 года и
# предупреждает, что по одному году она ненадёжна. Поэтому решает проверка точности
# (evaluate): она покажет на спрятанном конце истории, помогает годовая сезонность или нет
YEAR_DAYS = 365
INTERVAL_WIDTH = 0.8  # коридор прогноза: в 8 случаях из 10 реальность окажется внутри
COUNTRY = "BY"  # праздники Беларуси


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


def prophet_forecast(daily: pd.DataFrame, days: int = FORECAST_DAYS) -> pd.DataFrame:
    # Прогноз Prophet: тренд + недельная (и годовая, если есть год истории) сезонность
    # + праздники Беларуси. Возвращает прогноз yhat и коридор yhat_lower - yhat_upper
    model = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=len(daily) >= YEAR_DAYS,  # волну длиной в год не увидеть за 3 месяца
        daily_seasonality=False,  # у нас данные по дням, внутридневной сезонности нет
        interval_width=INTERVAL_WIDTH,
    )
    model.add_country_holidays(country_name=COUNTRY)
    model.fit(daily)

    future = model.make_future_dataframe(periods=days, include_history=False)
    # Коридор Prophet считает, моделируя тысячу случайных вариантов будущего.
    # Фиксируем случайность - иначе границы коридора чуть меняются от запуска к запуску
    np.random.seed(RANDOM_SEED)
    forecast = model.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    # Продажи не бывают отрицательными, а математика Prophet иногда даёт меньше нуля
    columns = ["yhat", "yhat_lower", "yhat_upper"]
    forecast[columns] = forecast[columns].clip(lower=0)
    return forecast.reset_index(drop=True)
