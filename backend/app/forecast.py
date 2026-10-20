"""Прогноз: простой прогноз (точка отсчёта), Prophet, проверка точности."""

import logging
from collections.abc import Callable

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
from app.config import FORECAST_DAYS, MIN_HISTORY_DAYS, RANDOM_SEED, TEST_DAYS  # noqa: E402

# А сам Prophet настраивает сообщения при импорте - поэтому его уровень ставим ПОСЛЕ
logging.getLogger("prophet").setLevel(logging.ERROR)  # предупреждения - см. YEAR_DAYS

WEEK_DAYS = 7
# Годовую сезонность включаем, если истории хотя бы год. Prophet советует 2 года и
# предупреждает, что по одному году она ненадёжна. Поэтому решает проверка точности
# (evaluate): она покажет на спрятанном конце истории, помогает годовая сезонность или нет
YEAR_DAYS = 365
INTERVAL_WIDTH = 0.8  # коридор прогноза: в 8 случаях из 10 реальность окажется внутри
COUNTRY = "BY"  # праздники Беларуси
EVALUATION_WINDOWS = 3  # сколько раз "сдаём экзамен" на разных отрезках истории

HORIZONS = (7, 14, 30, 60, 90)  # на сколько дней вперёд пробуем прогнозировать
MAX_ACCEPTABLE_WAPE = 35.0  # дальше прогноз показывает лишь общее направление (см. отчёт)
# Для дальних горизонтов важнее итог за период: прогноз может "уезжать" в сторону,
# даже если ошибка по дням держится на месте
MAX_ACCEPTABLE_TOTAL_ERROR = 15.0
HISTORY_TO_HORIZON = 3  # горизонт не дальше трети истории - иначе экзамену не хватит отрезков

# Функция прогноза: (ряд по дням, на сколько дней) -> таблица с колонками ds и yhat
Forecaster = Callable[[pd.DataFrame, int], pd.DataFrame]


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


# Модели, которые умеем сравнивать. Новая модель (в дипломе - Chronos) - одна строка здесь
MODELS: dict[str, Forecaster] = {
    "простой прогноз": naive_forecast,
    "Prophet": prophet_forecast,
}


def window_metrics(actual: np.ndarray, forecast: pd.DataFrame) -> dict[str, float]:
    # Насколько прогноз ошибся на одном отрезке. actual - что было на самом деле
    predicted = forecast["yhat"].to_numpy()
    errors = np.abs(actual - predicted)
    total = actual.sum()
    metrics = {
        "MAE": errors.mean(),  # средняя ошибка за день, в рублях
        # WAPE - ошибка в % от продаж. Не MAPE: тот делит на продажи каждого дня и ломается на нулях
        "WAPE_%": errors.sum() / total * 100 if total else np.nan,
        # Ошибка итога за весь период, со знаком: + прогноз завысил, - занизил
        "ошибка_итога_%": (predicted.sum() - total) / total * 100 if total else np.nan,
    }
    if "yhat_lower" in forecast:  # коридор есть только у моделей, которые его считают
        inside = (actual >= forecast["yhat_lower"].to_numpy()) & (
            actual <= forecast["yhat_upper"].to_numpy()
        )
        metrics["в_коридоре_%"] = inside.mean() * 100
    return metrics


def evaluate(
    daily: pd.DataFrame,
    forecaster: Forecaster,
    horizon: int = TEST_DAYS,
    windows: int = EVALUATION_WINDOWS,
) -> dict:
    # "Экзамен на прошлом": прячем последние horizon дней, прогнозируем их по тому, что было
    # раньше, и сравниваем с правдой. Повторяем на нескольких отрезках и усредняем.
    # Модель учится ТОЛЬКО на прошлом - никогда не перемешиваем, иначе точность будет ложной
    windows = min(windows, (len(daily) - MIN_HISTORY_DAYS) // horizon)  # сколько отрезков влезает
    if windows < 1:
        raise ValueError(
            f"Мало данных для проверки на {horizon} дней: "
            f"нужно хотя бы {MIN_HISTORY_DAYS + horizon} дней истории"
        )

    results = []
    for window in range(windows):
        test_end = len(daily) - window * horizon  # каждый следующий отрезок - раньше предыдущего
        train = daily.iloc[: test_end - horizon]  # всё, что было ДО проверяемого отрезка
        actual = daily["y"].iloc[test_end - horizon : test_end].to_numpy()
        results.append(window_metrics(actual, forecaster(train, horizon)))

    averaged = pd.DataFrame(results).mean()  # среднее по отрезкам
    return {
        "отрезков": windows,
        **{name: round(float(value), 1) for name, value in averaged.items()},
    }


def compare_models(
    daily: pd.DataFrame,
    horizon: int = TEST_DAYS,
    models: dict[str, Forecaster] = MODELS,
) -> pd.DataFrame:
    # Один и тот же экзамен для всех моделей. Лучшая (с наименьшей ошибкой WAPE) - сверху
    results = {name: evaluate(daily, forecaster, horizon) for name, forecaster in models.items()}
    return pd.DataFrame(results).T.sort_values("WAPE_%")


def horizon_scan(
    daily: pd.DataFrame,
    forecaster: Forecaster = prophet_forecast,
    horizons: tuple[int, ...] = HORIZONS,
) -> pd.DataFrame:
    # Экзамен на разных горизонтах: "горизонт в днях -> ошибки". Чем дальше, тем обычно хуже.
    # Проверяем только горизонты не дальше трети истории - иначе экзамену не хватит отрезков
    max_horizon = len(daily) // HISTORY_TO_HORIZON
    results = {
        horizon: evaluate(daily, forecaster, horizon)
        for horizon in horizons
        if horizon <= max_horizon and len(daily) >= MIN_HISTORY_DAYS + horizon
    }
    return pd.DataFrame(results).T.rename_axis("горизонт_дней")


def choose_horizon(
    scan: pd.DataFrame,
    max_wape: float = MAX_ACCEPTABLE_WAPE,
    max_total_error: float = MAX_ACCEPTABLE_TOTAL_ERROR,
) -> int | None:
    # Самый дальний горизонт, где приемлемы И ошибка по дням, И ошибка итога за период.
    # Идём от коротких к длинным и останавливаемся на первом провале: если 30 дней не прошли,
    # а 60 "случайно" прошли - это шум, а не точность.
    # None - прогноз ненадёжен даже на самом коротком горизонте
    chosen = None
    for horizon, row in scan.iterrows():  # строк не больше пяти - цикл здесь уместен
        if row["WAPE_%"] > max_wape or abs(row["ошибка_итога_%"]) > max_total_error:
            break
        chosen = int(horizon)
    return chosen
