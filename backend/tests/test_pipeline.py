"""Интеграционные тесты конвейера (app/pipeline.py) на тестовых файлах из data/synthetic."""

import json

import pytest
from conftest import daily_to_events, noise_daily, weekly_daily

from app.cleaner import to_number
from app.config import FORECAST_DAYS, SYNTHETIC_DIR
from app.forecast import MODELS
from app.loader import load
from app.model import EVENT_COLUMNS
from app.pipeline import (
    STEP_ESTIMATE,
    STEP_FORECAST,
    STEP_NONE,
    make_forecast,
    prepare_events,
)

TEST_FILES = ["shop.xlsx", "cafe.csv", "salon.xlsx"]


def read_mapping(file_name: str) -> dict[str, str]:
    # Эталон разметки колонок из .json рядом с тестовым файлом
    path = (SYNTHETIC_DIR / file_name).with_suffix(".json")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("file_name", TEST_FILES)
def test_prepare_events_structure(file_name):
    events, report = prepare_events(SYNTHETIC_DIR / file_name, read_mapping(file_name))
    # Сначала основные колонки в стандартном порядке, после них - дополнительные (если есть)
    assert list(events.columns[: len(EVENT_COLUMNS)]) == EVENT_COLUMNS
    assert events["date"].notna().all()  # у каждого события есть дата
    assert report["строк_стало"] == len(events)
    assert report["удалено_итоговых_и_пустых"] == 1  # строка "Итого"


@pytest.mark.parametrize("file_name", TEST_FILES)
def test_prepare_events_total_matches_file(file_name):
    # Сумма после всего конвейера совпадает со строкой "Итого", которую записал генератор
    mapping = read_mapping(file_name)
    amount_column = next(column for column, role in mapping.items() if role == "amount")
    raw_table = list(load(SYNTHETIC_DIR / file_name).values())[0]
    total_in_file = to_number(raw_table[amount_column]).iloc[-1]  # последняя строка - "Итого"

    events, _ = prepare_events(SYNTHETIC_DIR / file_name, mapping)
    assert events["amount"].sum() == pytest.approx(total_in_file)


def test_prepare_events_exclude():
    # Исключённый товар пропадает из событий, а отчёт говорит, сколько и на какую сумму
    mapping = read_mapping("shop.xlsx")
    full, _ = prepare_events(SYNTHETIC_DIR / "shop.xlsx", mapping)
    events, report = prepare_events(
        SYNTHETIC_DIR / "shop.xlsx", mapping, exclude=["Пиво Лидское 0.5"]
    )
    beer = full["object"] == "Пиво Лидское 0.5"
    assert "Пиво Лидское 0.5" not in events["object"].to_numpy()
    assert report["исключено_строк"] == beer.sum()
    assert report["исключено_на_сумму"] == pytest.approx(full.loc[beer, "amount"].sum())


def test_make_forecast_currency_in_message():
    result = make_forecast(daily_to_events(weekly_daily(20)), currency="£")
    assert "£." in result["сообщение"]  # ровно одна точка в конце
    assert "р." not in result["сообщение"]


def test_prepare_events_wrong_sheet():
    with pytest.raises(ValueError, match="Лист2"):
        prepare_events(SYNTHETIC_DIR / "shop.xlsx", read_mapping("shop.xlsx"), sheet="Лист2")


# ---------- make_forecast: ступеньки холодного старта ----------


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
