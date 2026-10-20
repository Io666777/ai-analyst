"""Тесты отчёта о точности прогноза для пользователя (app/forecast_report.py)."""

import numpy as np
import pandas as pd
import pytest
from conftest import noise_daily, weekly_daily

from app.forecast_report import (
    data_diagnostics,
    days_off,
    days_off_note,
    quality_level,
    quality_report,
    total_error_text,
)

# ---------- уровни и тексты ----------


@pytest.mark.parametrize(
    ("wape", "level"),
    [(5, "высокая"), (10, "высокая"), (15, "хорошая"), (30, "средняя"), (50, "низкая")],
)
def test_quality_level(wape, level):
    assert quality_level(wape)[0] == level


def test_total_error_text():
    assert total_error_text(0.3) == "меньше чем на 1%"
    assert total_error_text(-4.6) == "примерно на 5%"  # знак не важен - говорим о величине


# ---------- причины из данных ----------


def test_diagnostics_good_data_has_no_problems():
    # Год идеальной недели: история длинная, ровная, без нулей и всплесков
    assert data_diagnostics(weekly_daily(365)) == []


def test_diagnostics_short_history():
    reasons = data_diagnostics(weekly_daily(120))
    assert any("меньше года" in reason for reason in reasons)


def test_diagnostics_zero_days():
    daily = weekly_daily(365)
    daily.loc[daily.index % 10 == 0, "y"] = 0  # каждый 10-й день без продаж
    assert any("без продаж" in reason for reason in data_diagnostics(daily))


def test_diagnostics_noise():
    assert any("меняются от дня ко дню" in reason for reason in data_diagnostics(noise_daily(365)))


def test_diagnostics_spikes():
    daily = weekly_daily(365)
    daily.loc[[50, 150, 250, 300], "y"] *= 4  # четыре дня вчетверо выше обычного
    assert any("всплески" in reason for reason in data_diagnostics(daily))


def test_diagnostics_names_the_right_country():
    # Прогноз с праздниками Великобритании - и в тексте должна быть Великобритания
    daily = weekly_daily(365)
    daily.loc[[50, 150, 250, 300], "y"] *= 4
    reasons = " ".join(data_diagnostics(daily, country="GB"))
    assert "Великобритании" in reasons
    assert "Беларуси" not in reasons


@pytest.fixture
def closed_on_saturdays() -> pd.DataFrame:
    # Магазин не работает по субботам (как настоящий Online Retail), но раз в год
    # в субботу случилась продажа - это не должно выглядеть всплеском
    daily = weekly_daily(365)
    saturdays = daily["ds"].dt.dayofweek == 5
    daily.loc[saturdays, "y"] = 0
    daily.loc[daily[saturdays].index[10], "y"] = 50
    return daily


def test_days_off_found(closed_on_saturdays):
    assert days_off(closed_on_saturdays) == [5]
    assert "субботам" in days_off_note(closed_on_saturdays)


def test_days_off_are_not_problems(closed_on_saturdays):
    # Выходной - не "дни без продаж, которые стоит отметить" и не "всплеск"
    assert data_diagnostics(closed_on_saturdays) == []


def test_report_mentions_day_off(closed_on_saturdays):
    report = quality_report(closed_on_saturdays, make_comparison(Prophet=GOOD))
    assert "хорошо подходят" in report["причины"][0]  # проблем нет
    assert "субботам" in report["причины"][-1]  # а выходной упомянут как наблюдение


# ---------- quality_report ----------


def make_comparison(**rows: dict) -> pd.DataFrame:
    # Таблица сравнения моделей, как у compare_models
    return pd.DataFrame(rows).T


GOOD = {"MAE": 10.0, "WAPE_%": 8.0, "ошибка_итога_%": 2.0, "в_коридоре_%": 82.0}


def test_report_good_forecast_explains_why():
    report = quality_report(weekly_daily(365), make_comparison(Prophet=GOOD))
    assert report["точность"] == "высокая"
    assert "8%" in report["вывод"]
    assert "хорошо подходят" in report["причины"][0]  # объясняем, почему прогноз хороший


def test_report_uses_given_model():
    # Прогноз построен простой моделью - отчёт должен описывать именно её
    comparison = make_comparison(
        Prophet=GOOD, **{"простой прогноз": {**GOOD, "WAPE_%": 25.0, "в_коридоре_%": np.nan}}
    )
    report = quality_report(weekly_daily(365), comparison, model="простой прогноз")
    assert report["ошибка_%"] == 25.0
    assert any("простого прогноза" in reason for reason in report["причины"])


def test_report_bias_and_narrow_corridor():
    bad = {"MAE": 10.0, "WAPE_%": 15.0, "ошибка_итога_%": -12.0, "в_коридоре_%": 55.0}
    reasons = quality_report(weekly_daily(365), make_comparison(Prophet=bad))["причины"]
    assert any("занижает итог" in reason for reason in reasons)
    assert any("коридор узковат" in reason for reason in reasons)
