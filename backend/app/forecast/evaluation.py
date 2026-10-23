"""Экзамен на прошлом: прячем конец истории, прогнозируем его и сравниваем с правдой."""

import numpy as np
import pandas as pd

from app.config import MIN_HISTORY_DAYS, TEST_DAYS
from app.forecast.models import MODELS, Forecaster

EVALUATION_WINDOWS = 3  # сколько раз "сдаём экзамен" на разных отрезках истории


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
