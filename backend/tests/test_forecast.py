"""Тесты прогноза (app/forecast.py) на рядах, где правильный ответ известен заранее."""

import numpy as np
import pandas as pd
import pytest
from conftest import weekly_daily

from app.forecast import (
    MODELS,
    choose_horizon,
    compare_models,
    evaluate,
    horizon_scan,
    naive_forecast,
    prophet_forecast,
    to_daily,
    window_metrics,
)
from app.model import to_events

# ---------- to_daily ----------


def test_to_daily_fills_missing_days_with_zero():
    # Продажи 1-го и 3-го числа: 2-е должно появиться с нулём, а не пропасть
    table = pd.DataFrame(
        {"Дата": pd.to_datetime(["2026-01-01", "2026-01-03"]), "Сумма": [10.0, 30.0]}
    )
    events = to_events(table, {"Дата": "date", "Сумма": "amount"})
    daily = to_daily(events)
    assert list(daily.columns) == ["ds", "y"]
    assert daily["y"].tolist() == [10.0, 0.0, 30.0]


def test_to_daily_sums_visits_of_one_day():
    # Два визита в один день (с разным временем) -> одна строка с суммой
    table = pd.DataFrame(
        {
            "Дата": pd.to_datetime(["2026-01-01 10:00", "2026-01-01 18:00"]),
            "Сумма": [40.0, 25.0],
        }
    )
    events = to_events(table, {"Дата": "date", "Сумма": "amount"})
    assert to_daily(events)["y"].tolist() == [65.0]


# ---------- naive_forecast ----------


def test_naive_forecast_repeats_last_week(weekly_120):
    forecast = naive_forecast(weekly_120, days=10)
    assert len(forecast) == 10
    assert forecast["ds"].iloc[0] == weekly_120["ds"].iloc[-1] + pd.Timedelta(days=1)
    # Первые 7 дней прогноза = последние 7 дней истории, дальше - снова по кругу
    last_week = weekly_120["y"].tail(7).tolist()
    assert forecast["yhat"].tolist() == last_week + last_week[:3]


def test_naive_forecast_needs_a_week():
    with pytest.raises(ValueError, match="7 дней"):
        naive_forecast(weekly_daily(5))


# ---------- prophet_forecast ----------


def test_prophet_forecast_shape_and_corridor(weekly_120):
    forecast = prophet_forecast(weekly_120, days=14)
    assert list(forecast.columns) == ["ds", "yhat", "yhat_lower", "yhat_upper"]
    assert len(forecast) == 14
    assert (forecast["yhat_lower"] <= forecast["yhat"]).all()
    assert (forecast["yhat"] <= forecast["yhat_upper"]).all()


def test_prophet_finds_weekends(weekly_120):
    # Prophet должен сам найти недельный ритм: выходные выше будней
    forecast = prophet_forecast(weekly_120, days=14)
    weekend = forecast["ds"].dt.dayofweek >= 4  # пт, сб, вс
    assert forecast.loc[weekend, "yhat"].mean() > forecast.loc[~weekend, "yhat"].mean() + 30


def test_prophet_never_negative():
    # Продажи падают к нулю - продолжение линии ушло бы в минус, но продаж меньше нуля не бывает
    dates = pd.date_range("2026-01-01", periods=60)
    falling = pd.DataFrame({"ds": dates, "y": np.maximum(0, 100 - 2 * np.arange(60)).astype(float)})
    forecast = prophet_forecast(falling, days=30)
    assert (forecast[["yhat", "yhat_lower", "yhat_upper"]] >= 0).all().all()


def test_prophet_reproducible(weekly_120):
    # Коридор строится случайным моделированием - но со фиксированным seed результат одинаков
    first = prophet_forecast(weekly_120, days=7)
    second = prophet_forecast(weekly_120, days=7)
    pd.testing.assert_frame_equal(first, second)


# ---------- window_metrics ----------


def test_window_metrics_by_hand():
    # Ошибки по дням: 2, 2, 0, 10. Сумма факта 100, прогноза 110
    actual = np.array([10.0, 20.0, 30.0, 40.0])
    forecast = pd.DataFrame(
        {
            "yhat": [12.0, 18.0, 30.0, 50.0],
            "yhat_lower": [5.0, 15.0, 25.0, 45.0],  # последний день (40) - вне коридора
            "yhat_upper": [15.0, 25.0, 35.0, 55.0],
        }
    )
    metrics = window_metrics(actual, forecast)
    # approx - "примерно равно": дробные числа в компьютере хранятся с крошечной погрешностью
    assert metrics["MAE"] == pytest.approx(3.5)  # (2 + 2 + 0 + 10) / 4
    assert metrics["WAPE_%"] == pytest.approx(14.0)  # 14 / 100
    assert metrics["ошибка_итога_%"] == pytest.approx(10.0)  # (110 - 100) / 100, завысил
    assert metrics["в_коридоре_%"] == pytest.approx(75.0)  # 3 дня из 4


def test_window_metrics_without_corridor():
    metrics = window_metrics(np.array([10.0, 10.0]), pd.DataFrame({"yhat": [10.0, 10.0]}))
    assert "в_коридоре_%" not in metrics  # у простого прогноза коридора нет
    assert metrics["WAPE_%"] == 0


# ---------- evaluate и compare_models ----------


def test_evaluate_naive_is_exact_on_perfect_week(weekly_120):
    # На идеальном недельном ряде "как на прошлой неделе" не ошибается вообще
    result = evaluate(weekly_120, naive_forecast, horizon=14)
    assert result["отрезков"] == 3
    assert result["WAPE_%"] == 0
    assert result["ошибка_итога_%"] == 0


def test_evaluate_never_shows_the_future(weekly_120):
    # "Шпионская" модель запоминает, на чём её учили. Последний день обучения
    # всегда должен быть раньше первого проверяемого дня - модель не видит будущее
    seen = []

    def spy(train: pd.DataFrame, days: int) -> pd.DataFrame:
        seen.append((train["ds"].max(), len(train)))
        return naive_forecast(train, days)

    evaluate(weekly_120, spy, horizon=14)
    for window, (train_end, train_size) in enumerate(seen):
        test_start = weekly_120["ds"].iloc[len(weekly_120) - (window + 1) * 14]
        assert train_end < test_start
        assert train_size == len(weekly_120) - (window + 1) * 14


def test_evaluate_fewer_windows_when_history_is_short():
    # 70 дней: на обучение нужно 30, остаётся 40 - влезает только 2 отрезка по 14
    assert evaluate(weekly_daily(70), naive_forecast, horizon=14)["отрезков"] == 2


def test_evaluate_too_little_data():
    with pytest.raises(ValueError, match="Мало данных"):
        evaluate(weekly_daily(40), naive_forecast, horizon=14)


def test_compare_models_best_first(weekly_120):
    # "Модель" из одних нулей заведомо хуже простого прогноза
    def zeros(train: pd.DataFrame, days: int) -> pd.DataFrame:
        dates = pd.date_range(train["ds"].iloc[-1] + pd.Timedelta(days=1), periods=days)
        return pd.DataFrame({"ds": dates, "yhat": 0.0})

    result = compare_models(weekly_120, horizon=14, models={"нули": zeros, **MODELS})
    assert result.index[-1] == "нули"
    assert result["WAPE_%"].is_monotonic_increasing  # отсортировано: лучшая сверху


# ---------- горизонт ----------


def test_horizon_scan_limited_by_third_of_history():
    # 60 дней истории -> горизонт не дальше 20 дней -> проверяем только 7 и 14
    scan = horizon_scan(weekly_daily(60), naive_forecast)
    assert scan.index.tolist() == [7, 14]


def test_horizon_scan_empty_for_short_history():
    assert horizon_scan(weekly_daily(20), naive_forecast).empty


def make_scan(wape: list[float], total: list[float]) -> pd.DataFrame:
    # Таблица экзамена по горизонтам 7, 14, 30, 60 с заданными ошибками
    return pd.DataFrame({"WAPE_%": wape, "ошибка_итога_%": total}, index=pd.Index([7, 14, 30, 60]))


def test_choose_horizon_longest_acceptable():
    assert choose_horizon(make_scan([5, 10, 20, 30], [1, 2, 3, 4])) == 60


def test_choose_horizon_stops_at_first_failure():
    # 30 дней не прошли (40%), а 60 "случайно" прошли - это шум, выбираем 14
    assert choose_horizon(make_scan([5, 10, 40, 20], [1, 1, 1, 1])) == 14


def test_choose_horizon_total_error_matters():
    # По дням всё прошло, но итог на 30 днях уехал на 20% - выбираем 14
    assert choose_horizon(make_scan([5, 10, 20, 30], [1, -2, 20, 5])) == 14


def test_choose_horizon_none_when_even_a_week_fails():
    assert choose_horizon(make_scan([50, 50, 50, 50], [1, 1, 1, 1])) is None
