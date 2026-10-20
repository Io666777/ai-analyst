"""Понятный пользователю отчёт о точности прогноза: можно ли верить и почему.

Причины не придумываются, а вычисляются из данных и результатов проверки (evaluate).
"""

import pandas as pd

from app.forecast import INTERVAL_WIDTH, YEAR_DAYS

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


def money(value: float) -> str:
    # 1234.5 -> "1 234"
    return f"{value:,.0f}".replace(",", " ")


def relative_to_weekday(daily: pd.DataFrame) -> pd.Series:
    # Пятница всегда больше вторника - это не шум. Делим каждый день на среднее для ЕГО
    # дня недели: 1.0 - обычный день, 2.0 - вдвое выше обычного, 0.5 - вдвое ниже
    weekday_mean = daily.groupby(daily["ds"].dt.dayofweek)["y"].transform("mean")
    working = weekday_mean > 0  # дни недели, когда бизнес вообще работает
    return daily.loc[working, "y"] / weekday_mean[working]


def data_diagnostics(daily: pd.DataFrame) -> list[str]:
    # Причины неточности, найденные в самих данных. Каждая - с цифрой из данных
    reasons = []
    days = len(daily)
    if days < YEAR_DAYS:
        reasons.append(
            f"История {days} дн. - меньше года: годовая сезонность (лето, зима) не учитывается"
        )

    zero_share = (daily["y"] == 0).mean()
    if zero_share > ZERO_DAYS_LIMIT:
        reasons.append(
            f"{zero_share:.0%} дней без продаж. Если в эти дни вы не работали - отметьте их, "
            "и прогноз станет точнее"
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
        reasons.append(
            f"Есть резкие всплески ({spike_share:.0%} дней - вдвое выше обычного): праздники "
            "или акции. Праздники Беларуси учитываются, а акции стоит отметить"
        )
    return reasons


def quality_level(wape: float) -> tuple[str, str]:
    # Ошибка в % -> (уровень точности, что это значит на практике)
    for limit, level, meaning in QUALITY_LEVELS:
        if wape <= limit:
            return level, meaning
    return QUALITY_LEVELS[-1][1:]


def quality_report(daily: pd.DataFrame, comparison: pd.DataFrame) -> dict:
    # Вывод для пользователя по результатам compare_models: точность словами и причины
    best_model = str(comparison.index[0])  # compare_models ставит лучшую модель первой
    best = comparison.iloc[0]
    level, meaning = quality_level(best["WAPE_%"])

    summary = (
        f"Прогноз ошибается в среднем на {best['WAPE_%']:.0f}% "
        f"(около {money(best['MAE'])} р. в день). "
        f"Итог за период отличается от реальности примерно на {abs(best['ошибка_итога_%']):.0f}%. "
        f"Точность {level}: {meaning}."
    )

    reasons = data_diagnostics(daily)
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

    return {
        "модель": best_model,
        "точность": level,
        "ошибка_%": float(best["WAPE_%"]),
        "вывод": summary,
        "причины": reasons,
    }
