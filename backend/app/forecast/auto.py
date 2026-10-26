"""Прогноз автоматически: события -> ступенька холодного старта -> лучшая модель -> горизонт.

Главная функция прогноза для интерфейсов - make_forecast: всё остальное она решает сама.
"""

import pandas as pd

from app.config import CURRENCY, FORECAST_DAYS
from app.forecast.breakdown import forecast_by, year_ago
from app.forecast.horizon import choose_horizon, horizon_scan
from app.forecast.models import COUNTRY, WEEK_DAYS, models_for, to_daily
from app.forecast.report import money, quality_report

# Ступеньки холодного старта
STEP_NONE = "нет прогноза"  # меньше недели истории
STEP_ESTIMATE = "оценка"  # простые средние: мало данных для экзамена или прогноз ненадёжен
STEP_FORECAST = "прогноз"  # полноценный прогноз лучшей модели с проверенной точностью

RECENT_DAYS = 14  # оценка "если так пойдёт дальше" - по последним двум неделям
WEEKDAY_NAMES = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def sentence(text: str) -> str:
    # Точка в конце предложения ровно одна: "около 5 р." и "около 5 £." (а не "р.." и "£")
    return text.rstrip(".") + "."


def simple_estimate(daily: pd.DataFrame, reason: str, currency: str = CURRENCY) -> dict:
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
            f"{reason} Пока - оценка: в среднем {money(per_day)} {currency} в день "
            f"(за последние {min(RECENT_DAYS, len(daily))} дн.). Если так пойдёт дальше, "
            + sentence(f"за {FORECAST_DAYS} дней будет около {money(projection)} {currency}")
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


def make_forecast(
    events: pd.DataFrame,
    value: str = "amount",
    country: str = COUNTRY,
    currency: str = CURRENCY,
) -> dict:
    # Главная функция прогноза: события -> ступенька -> модель -> горизонт -> прогноз и отчёт.
    # country - чьи праздники учитывать: "BY" Беларусь, "RU" Россия, "GB" Великобритания...
    # currency - валюта для текстов: "р.", "$", "£"...
    models = models_for(country)
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
    scans = {name: horizon_scan(daily, forecaster) for name, forecaster in models.items()}
    if any(scan.empty for scan in scans.values()):
        reason = f"Для проверенного прогноза данных мало ({days} дн.)."
        return simple_estimate(daily, reason, currency)

    model_name = best_model(scans)
    horizon = choose_horizon(scans[model_name])
    if horizon is None:
        reason = "По этим данным прогноз ненадёжен даже на неделю."
        return simple_estimate(daily, reason, currency)

    forecast = models[model_name](daily, horizon)
    # Отчёт о точности - по экзамену именно на том горизонте, на который строим прогноз
    comparison = compare_at(scans, horizon)
    result = {
        "ступенька": STEP_FORECAST,
        "история_дней": days,
        "модель": model_name,
        "горизонт_дней": horizon,
        "прогноз": forecast,
        "итого": round(float(forecast["yhat"].sum()), 2),
        "точность": quality_report(
            daily, comparison, model=model_name, country=country, currency=currency
        ),
        # Экзамен всех моделей на том же горизонте - видно, почему выбрана эта
        "экзамен": [
            {
                "модель": str(name),
                "ошибка_%": float(row["WAPE_%"]),
                "ошибка_итога_%": float(row["ошибка_итога_%"]),
            }
            for name, row in comparison.iterrows()
        ],
        "по_неделям": forecast_by(forecast, "неделя"),
        "по_месяцам": forecast_by(forecast, "месяц"),
        "год_назад": year_ago(daily, forecast),
    }
    if "yhat_lower" in forecast:  # коридор есть не у всех моделей
        result["коридор"] = (
            round(float(forecast["yhat_lower"].sum()), 2),
            round(float(forecast["yhat_upper"].sum()), 2),
        )
    result["сообщение"] = (
        sentence(
            f"Прогноз на {horizon} дн. ({model_name}): около {money(result['итого'])} {currency}"
        )
        + f" {result['точность']['вывод']}"
    )
    return result
