"""Понятный пользователю отчёт о точности прогноза: можно ли верить и почему.

Причины не придумываются, а вычисляются из данных и результатов проверки (evaluate).
"""

import pandas as pd

from app.config import CURRENCY
from app.forecast.models import COUNTRY, INTERVAL_WIDTH, YEAR_DAYS

# Уровни точности по ошибке WAPE: (до скольки %, уровень, что это значит на практике)
QUALITY_LEVELS = [
    (10, "высокая", "прогнозу можно доверять при планировании"),
    (20, "хорошая", "подходит для планирования с небольшим запасом"),
    (35, "средняя", "годится как ориентир, а не как точная цифра"),
    (float("inf"), "низкая", "показывает только общее направление"),
]

ZERO_DAYS_LIMIT = 0.05  # больше 5% дней без продаж - стоит сказать
NOISE_LIMIT = 0.3  # дни отличаются от обычного для своего дня недели больше чем на 30%
SPIKE_RATIO = 2.0  # всплеск - день вдвое выше обычного
SPIKE_DAYS_LIMIT = 0.01  # больше 1% таких дней - стоит сказать
BIAS_LIMIT = 5.0  # итог систематически смещён больше чем на 5%
COVERAGE_GAP = 10.0  # коридор держит обещание хуже, чем на 10 процентных пунктов
DAY_OFF_SHARE = 0.8  # продаж нет в 80% случаев этого дня недели - это выходной, а не пропуски

# Страна праздников -> как назвать её в тексте ("праздники Беларуси")
COUNTRY_NAMES = {"BY": "Беларуси", "RU": "России", "GB": "Великобритании", "UA": "Украины"}
# "по субботам" - для фразы о выходном дне недели
WEEKDAYS_PLURAL = [
    "понедельникам", "вторникам", "средам", "четвергам", "пятницам", "субботам", "воскресеньям",
]  # fmt: skip


def money(value: float) -> str:
    # 1234.5 -> "1 234"
    return f"{value:,.0f}".replace(",", " ")


def days_off(daily: pd.DataFrame) -> list[int]:
    # Постоянные выходные: дни недели (0 - пн ... 6 - вс), когда продаж почти никогда нет
    zero_share = (daily["y"] == 0).groupby(daily["ds"].dt.dayofweek).mean()
    return [int(day) for day, share in zero_share.items() if share >= DAY_OFF_SHARE]


def relative_to_weekday(daily: pd.DataFrame) -> pd.Series:
    # Пятница всегда больше вторника - это не шум. Делим каждый день на среднее для ЕГО
    # дня недели: 1.0 - обычный день, 2.0 - вдвое выше обычного, 0.5 - вдвое ниже.
    # Выходные дни недели не берём: редкая продажа в выходной выглядела бы "всплеском в 10 раз"
    weekday = daily["ds"].dt.dayofweek
    weekday_mean = daily.groupby(weekday)["y"].transform("mean")
    working = (weekday_mean > 0) & ~weekday.isin(days_off(daily))
    return daily.loc[working, "y"] / weekday_mean[working]


def data_diagnostics(daily: pd.DataFrame, country: str = COUNTRY) -> list[str]:
    # Причины неточности, найденные в самих данных. Каждая - с цифрой из данных
    reasons = []
    days = len(daily)
    if days < YEAR_DAYS:
        reasons.append(
            f"История {days} дн. - меньше года: годовая сезонность (лето, зима) не учитывается"
        )

    # Дни без продаж, НЕ считая постоянных выходных: выходной отмечать не нужно
    working_days = ~daily["ds"].dt.dayofweek.isin(days_off(daily))
    zero_share = (daily.loc[working_days, "y"] == 0).mean()
    if zero_share > ZERO_DAYS_LIMIT:
        reasons.append(
            f"{zero_share:.0%} рабочих дней без продаж. Если в эти дни вы не работали - "
            "отметьте их, и прогноз станет точнее"
        )

    # Разброс относительно обычного для дня недели - настоящая непредсказуемость
    relative = relative_to_weekday(daily)
    noise = relative.std()
    if noise > NOISE_LIMIT:
        reasons.append(
            f"Продажи сильно меняются от дня ко дню (примерно ±{noise:.0%}) даже с учётом "
            "дня недели - по отдельным дням прогноз неточный, итог за месяц надёжнее"
        )

    spike_share = (relative > SPIKE_RATIO).mean()
    if spike_share > SPIKE_DAYS_LIMIT:
        holidays = COUNTRY_NAMES.get(country, f"страны {country}")
        reasons.append(
            f"Есть резкие всплески ({spike_share:.0%} дней - вдвое выше обычного): праздники "
            f"или акции. Праздники {holidays} учитываются, а акции стоит отметить"
        )
    return reasons


def days_off_note(daily: pd.DataFrame) -> str | None:
    # Не проблема, а наблюдение: "по субботам продаж нет - похоже, это выходной"
    off = days_off(daily)
    if not off:
        return None
    names = ", ".join(WEEKDAYS_PLURAL[day] for day in off)
    return f"По {names} продаж нет - похоже, это выходной. Прогноз это учитывает"


def quality_level(wape: float) -> tuple[str, str]:
    # Ошибка в % -> (уровень точности, что это значит на практике)
    for limit, level, meaning in QUALITY_LEVELS:
        if wape <= limit:
            return level, meaning
    return QUALITY_LEVELS[-1][1:]


def total_error_text(total_error: float) -> str:
    # 4.2 -> "примерно на 4%", 0.3 -> "меньше чем на 1%"
    if abs(total_error) < 1:
        return "меньше чем на 1%"
    return f"примерно на {abs(total_error):.0f}%"


def quality_report(
    daily: pd.DataFrame,
    comparison: pd.DataFrame,
    model: str | None = None,
    country: str = COUNTRY,
    currency: str = CURRENCY,
) -> dict:
    # Вывод для пользователя по результатам экзамена: точность словами и причины.
    # model - модель, которой построен прогноз. Не указана - лучшая (первая строка сравнения).
    # country - страна праздников, которые учитывал прогноз (для текста причин)
    best_model = model if model is not None else str(comparison.index[0])
    best = comparison.loc[best_model]
    level, meaning = quality_level(best["WAPE_%"])

    summary = (
        f"Прогноз ошибается в среднем на {best['WAPE_%']:.0f}% "
        f"(около {money(best['MAE'])} {currency} в день). "
        f"Итог за период отличается от реальности {total_error_text(best['ошибка_итога_%'])}. "
        f"Точность {level}: {meaning}."
    )

    reasons = data_diagnostics(daily, country)
    if best_model != "Prophet":
        reasons.append(
            "Сложная модель не оказалась точнее простого прогноза «как на прошлой неделе» - "
            "показываем простой. Обычно так бывает при короткой или неравномерной истории"
        )
    bias = best["ошибка_итога_%"]
    if abs(bias) > BIAS_LIMIT:
        direction = "завышает" if bias > 0 else "занижает"
        reasons.append(
            f"Прогноз систематически {direction} итог (на {abs(bias):.0f}%) - возможно, "
            "продажи недавно изменились быстрее, чем раньше"
        )
    coverage = best.get("в_коридоре_%")
    promised = INTERVAL_WIDTH * 100
    if pd.notna(coverage) and coverage < promised - COVERAGE_GAP:
        reasons.append(
            f"Реальность попадала в коридор прогноза в {coverage:.0f}% дней вместо обещанных "
            f"{promised:.0f}% - коридор узковат, на границы стоит смотреть с запасом"
        )

    if not reasons:  # проблем не нашли - объясняем, почему прогноз хороший
        noise = relative_to_weekday(daily).std()
        reasons.append(
            f"Данные хорошо подходят для прогноза: история {len(daily)} дн., продажи ровные "
            f"с учётом дня недели (примерно ±{noise:.0%}), без резких всплесков"
        )
    note = days_off_note(daily)  # выходной - не проблема, а наблюдение: добавляем в конце
    if note:
        reasons.append(note)

    return {
        "модель": best_model,
        "точность": level,
        "ошибка_%": float(best["WAPE_%"]),
        "вывод": summary,
        "причины": reasons,
    }
