"""Подбор горизонта: на сколько дней вперёд прогнозу можно верить."""

import pandas as pd

from app.config import MIN_HISTORY_DAYS
from app.forecast.evaluation import evaluate
from app.forecast.models import Forecaster, prophet_forecast

HORIZONS = (7, 14, 30, 60, 90)  # на сколько дней вперёд пробуем прогнозировать
MAX_ACCEPTABLE_WAPE = 35.0  # дальше прогноз показывает лишь общее направление (см. отчёт)
# Для дальних горизонтов важнее итог за период: прогноз может "уезжать" в сторону,
# даже если ошибка по дням держится на месте
MAX_ACCEPTABLE_TOTAL_ERROR = 15.0
HISTORY_TO_HORIZON = 3  # горизонт не дальше трети истории - иначе экзамену не хватит отрезков


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
