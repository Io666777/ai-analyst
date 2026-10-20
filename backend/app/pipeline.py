"""Конвейер: соединяет модули в цепочки - точки входа для интерфейса.

prepare_events: файл -> загрузка -> очистка -> события универсальной модели
make_forecast:  события -> ступенька холодного старта -> лучшая модель -> горизонт -> прогноз
"""

from pathlib import Path

import pandas as pd

from app.cleaner import clean
from app.config import FORECAST_DAYS
from app.forecast import (
    MODELS,
    WEEK_DAYS,
    choose_horizon,
    horizon_scan,
    to_daily,
)
from app.forecast_report import money, quality_report
from app.loader import load
from app.model import KIND_SALE, available_fields, to_events

# Ступеньки холодного старта
STEP_NONE = "нет прогноза"  # меньше недели истории
STEP_ESTIMATE = "оценка"  # простые средние: мало данных для экзамена или прогноз ненадёжен
STEP_FORECAST = "прогноз"  # полноценный прогноз лучшей модели с проверенной точностью

RECENT_DAYS = 14  # оценка "если так пойдёт дальше" - по последним двум неделям
WEEKDAY_NAMES = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def prepare_events(
    path: Path,
    mapping: dict[str, str],
    kind: str = KIND_SALE,
    sheet: str | None = None,
) -> tuple[pd.DataFrame, dict]:
    # Файл + словарь ролей -> события и общий отчёт. Точка входа для интерфейса
    sheets = load(path)
    if not sheets:
        raise ValueError("В файле нет данных")

    sheet_name = sheet if sheet is not None else next(iter(sheets))  # не указали лист - первый
    if sheet_name not in sheets:
        raise ValueError(f"В файле нет листа «{sheet_name}». Есть: {', '.join(sheets)}")

    cleaned, clean_report = clean(sheets[sheet_name], mapping)
    events = to_events(cleaned, mapping, kind)

    report = {
        "файл": Path(path).name,
        "лист": sheet_name,
        **clean_report,  # всё из отчёта очистки: сколько строк было, удалено, стало
        "поля": available_fields(events),
    }
    return events, report


def simple_estimate(daily: pd.DataFrame, reason: str) -> dict:
    # Ступенька "оценка": простые средние вместо прогноза. reason - почему не прогноз.
    # Место для профилей сфер: здесь появится поправка на типичный сезон сферы бизнеса
    per_day = float(daily["y"].tail(RECENT_DAYS).mean())
    weekday_means = daily.groupby(daily["ds"].dt.dayofweek)["y"].mean()
    by_weekday = {
        WEEKDAY_NAMES[day]: round(float(value), 2) for day, value in weekday_means.items()
    }
    projection = per_day * FORECAST_DAYS
    return {
        "ступенька": STEP_ESTIMATE,
        "история_дней": len(daily),
        "в_среднем_в_день": round(per_day, 2),
        "по_дням_недели": by_weekday,
        "если_так_пойдёт_дальше": round(projection, 2),
        "сообщение": (
            f"{reason} Пока - оценка: в среднем {money(per_day)} р. в день "
            f"(за последние {min(RECENT_DAYS, len(daily))} дн.). Если так пойдёт дальше, "
            f"за {FORECAST_DAYS} дней будет около {money(projection)} р."
        ),
    }


def compare_at(scans: dict[str, pd.DataFrame], horizon: int) -> pd.DataFrame:
    # Ошибки всех моделей на одном горизонте, лучшая (меньше WAPE) - первой
    comparison = pd.DataFrame({name: scan.loc[horizon] for name, scan in scans.items()}).T
    return comparison.sort_values("WAPE_%")


def best_model(scans: dict[str, pd.DataFrame]) -> str:
    # Лучшая модель по экзамену на ОДНОМ и том же горизонте - самом дальнем, общем для всех
    common_horizon = min(scan.index.max() for scan in scans.values())
    return str(compare_at(scans, common_horizon).index[0])


def make_forecast(events: pd.DataFrame, value: str = "amount") -> dict:
    # Главная функция прогноза: события -> ступенька -> модель -> горизонт -> прогноз и отчёт
    daily = to_daily(events, value)
    days = len(daily)

    if days < WEEK_DAYS:
        return {
            "ступенька": STEP_NONE,
            "история_дней": days,
            "сообщение": (
                f"Данных пока {days} дн. Прогноз появится через {WEEK_DAYS - days} дн., "
                "а пока доступны итоги и топы"
            ),
        }

    # Экзамен по горизонтам для каждой модели. Пустая таблица - для экзамена мало данных
    scans = {name: horizon_scan(daily, forecaster) for name, forecaster in MODELS.items()}
    if any(scan.empty for scan in scans.values()):
        return simple_estimate(daily, f"Для проверенного прогноза данных мало ({days} дн.).")

    model_name = best_model(scans)
    horizon = choose_horizon(scans[model_name])
    if horizon is None:
        return simple_estimate(daily, "По этим данным прогноз ненадёжен даже на неделю.")

    forecast = MODELS[model_name](daily, horizon)
    # Отчёт о точности - по экзамену именно на том горизонте, на который строим прогноз
    comparison = compare_at(scans, horizon)
    result = {
        "ступенька": STEP_FORECAST,
        "история_дней": days,
        "модель": model_name,
        "горизонт_дней": horizon,
        "прогноз": forecast,
        "итого": round(float(forecast["yhat"].sum()), 2),
        "точность": quality_report(daily, comparison, model=model_name),
    }
    if "yhat_lower" in forecast:  # коридор есть не у всех моделей
        result["коридор"] = (
            round(float(forecast["yhat_lower"].sum()), 2),
            round(float(forecast["yhat_upper"].sum()), 2),
        )
    result["сообщение"] = (
        f"Прогноз на {horizon} дн. ({model_name}): около {money(result['итого'])} р. "
        f"{result['точность']['вывод']}"
    )
    return result
