"""Аналитика по событиям универсальной модели: итоги, сравнения, топы."""

import pandas as pd

from app.model import available_fields

# Понятное название периода -> код периода в pandas (ME - конец месяца, YE - конец года)
PERIODS = {"день": "D", "неделя": "W", "месяц": "ME", "год": "YE"}

MONTH_NAMES = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]  # fmt: skip


def by_period(events: pd.DataFrame, period: str = "месяц", value: str = "amount") -> pd.Series:
    # Сумма value (по умолчанию - выручка) за каждый период: день, неделю, месяц, год
    if period not in PERIODS:
        raise ValueError(f"Неизвестный период «{period}». Есть: {', '.join(PERIODS)}")
    if value not in available_fields(events):
        raise ValueError(f"В данных нет поля «{value}»")
    # resample раскладывает строки по периодам по дате и складывает каждый период
    return events.set_index("date")[value].resample(PERIODS[period]).sum()


def period_total(events: pd.DataFrame, start: str, end: str, value: str = "amount") -> float:
    # Сумма value с start по end ВКЛЮЧИТЕЛЬНО: "2025-03-01", "2025-03-31" - весь март.
    # Берём даты раньше следующего дня после end, иначе 31.03 в 15:00 не попадёт в март
    start_date = pd.Timestamp(start)
    after_end = pd.Timestamp(end) + pd.Timedelta(days=1)
    in_period = (events["date"] >= start_date) & (events["date"] < after_end)
    return float(events.loc[in_period, value].sum())


def compare_periods(
    events: pd.DataFrame,
    first: tuple[str, str],
    second: tuple[str, str],
    value: str = "amount",
) -> dict:
    # Сравнивает два периода: было, стало, изменение в деньгах и в процентах
    if value not in available_fields(events):
        raise ValueError(f"В данных нет поля «{value}»")
    before = period_total(events, *first, value=value)
    after = period_total(events, *second, value=value)
    change = after - before

    # Предупреждаем, если период выходит за пределы данных - сравнение будет нечестным
    data_start, data_end = events["date"].min(), events["date"].max()
    warnings = [
        f"Период {start} - {end} выходит за пределы данных "
        f"({data_start:%d.%m.%Y} - {data_end:%d.%m.%Y}), сравнение может быть неверным"
        for start, end in (first, second)
        if pd.Timestamp(start) < data_start.normalize() or pd.Timestamp(end) > data_end
    ]

    percent = round(change / before * 100, 1) if before else None  # на ноль делить нельзя
    return {
        "было": round(before, 2),  # округляем до копеек: 17104.800000000003 -> 17104.8
        "стало": round(after, 2),
        "изменение": round(change, 2),
        "изменение_%": percent,
        "предупреждения": warnings,
    }


def last_full_month(events: pd.DataFrame) -> pd.Period | None:
    # Последний месяц, за который есть данные ЦЕЛИКОМ: с 1-го до последнего числа.
    # Данные по 15 октября -> октябрь недописан -> последний полный месяц - сентябрь
    data_start, data_end = events["date"].min(), events["date"].max()
    month = data_end.to_period("M")  # месяц последней даты, например 2026-10
    if data_end.normalize() < month.end_time.normalize():
        month -= 1  # последний месяц не закончился - берём предыдущий
    if month.start_time < data_start.normalize():
        return None  # и этот месяц неполный: данные начались позже его 1-го числа
    return month


def month_bounds(month: pd.Period) -> tuple[str, str]:
    # Месяц -> первый и последний день: 2026-02 -> ("2026-02-01", "2026-02-28")
    return f"{month.start_time:%Y-%m-%d}", f"{month.end_time:%Y-%m-%d}"


def month_name(month: pd.Period) -> str:
    # 2026-09 -> "сентябрь 2026"
    return f"{MONTH_NAMES[month.month - 1]} {month.year}"


def last_full_month_vs_previous(events: pd.DataFrame, value: str = "amount") -> dict:
    # Последний полный месяц против предыдущего: "как прошёл последний месяц?"
    month = last_full_month(events)
    if month is None or (month - 1).start_time < events["date"].min().normalize():
        raise ValueError("Мало данных: для сравнения нужно хотя бы два полных месяца")
    previous = month - 1

    result = compare_periods(events, month_bounds(previous), month_bounds(month), value)

    # Месяцы бывают разной длины (28-31 день), поэтому считаем и среднее за день
    per_day_before = result["было"] / previous.days_in_month
    per_day_after = result["стало"] / month.days_in_month
    per_day_percent = (
        round((per_day_after - per_day_before) / per_day_before * 100, 1)
        if per_day_before
        else None
    )

    return {
        "месяц": month_name(month),
        "прошлый_месяц": month_name(previous),
        **result,
        "в_день_было": round(per_day_before, 2),
        "в_день_стало": round(per_day_after, 2),
        "изменение_в_день_%": per_day_percent,
    }
