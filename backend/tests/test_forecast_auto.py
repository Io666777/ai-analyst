"""Тесты автоматического прогноза (app/forecast/auto.py): ступеньки холодного старта."""

import pytest
from conftest import daily_to_events, noise_daily, weekly_daily

from app.config import FORECAST_DAYS
from app.forecast import MODELS, STEP_ESTIMATE, STEP_FORECAST, STEP_NONE, make_forecast


def test_make_forecast_currency_in_message():
    result = make_forecast(daily_to_events(weekly_daily(20)), currency="£")
    assert "£." in result["сообщение"]  # ровно одна точка в конце
    assert "р." not in result["сообщение"]


def test_make_forecast_no_forecast_under_a_week():
    result = make_forecast(daily_to_events(weekly_daily(4)))
    assert result["ступенька"] == STEP_NONE
    assert "через 3 дн." in result["сообщение"]


def test_make_forecast_estimate_for_short_history():
    # 20 дней - мало для экзамена: простые средние вместо прогноза
    daily = weekly_daily(20)
    result = make_forecast(daily_to_events(daily))
    assert result["ступенька"] == STEP_ESTIMATE
    per_day = daily["y"].tail(14).mean()
    # Программа округляет до копеек - сравниваем с точностью до копейки
    assert result["в_среднем_в_день"] == pytest.approx(per_day, abs=0.01)
    assert result["если_так_пойдёт_дальше"] == pytest.approx(per_day * FORECAST_DAYS, abs=0.01)
    assert result["по_дням_недели"]["сб"] == 160  # суббота в идеальной неделе


def test_make_forecast_full_forecast():
    daily = weekly_daily(120, noise=5)  # немного шума, как в жизни - иначе Prophet учится долго
    result = make_forecast(daily_to_events(daily))
    assert result["ступенька"] == STEP_FORECAST
    assert result["модель"] in MODELS
    assert result["горизонт_дней"] <= len(daily) // 3  # не дальше трети истории
    assert len(result["прогноз"]) == result["горизонт_дней"]
    assert result["точность"]["точность"] == "высокая"  # идеальная неделя предсказуема


def test_make_forecast_falls_back_when_unreliable():
    # Чистый шум: ни одна модель не проходит экзамен даже на неделю - честная оценка
    result = make_forecast(daily_to_events(noise_daily(120)))
    assert result["ступенька"] == STEP_ESTIMATE
    assert "ненадёжен" in result["сообщение"]
