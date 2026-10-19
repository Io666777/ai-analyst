"""Аналитика по событиям универсальной модели: итоги, сравнения, топы."""

import pandas as pd

from app.model import available_fields

# Понятное название периода -> код периода в pandas (ME - конец месяца, YE - конец года)
PERIODS = {"день": "D", "неделя": "W", "месяц": "ME", "год": "YE"}


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

    return {
        "было": before,
        "стало": after,
        "изменение": change,
        "изменение_%": change / before * 100 if before else None,  # на ноль делить нельзя
        "предупреждения": warnings,
    }
