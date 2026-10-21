"""Итоги по периодам: день, неделя, месяц, год."""

import pandas as pd

from app.model import require_field

# Понятное название периода -> код периода в pandas (ME - конец месяца, YE - конец года)
PERIODS = {"день": "D", "неделя": "W", "месяц": "ME", "год": "YE"}

MONTH_NAMES = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]  # fmt: skip


def month_name(month: pd.Period) -> str:
    # 2026-09 -> "сентябрь 2026"
    return f"{MONTH_NAMES[month.month - 1]} {month.year}"


def by_period(
    events: pd.DataFrame,
    period: str = "месяц",
    value: str = "amount",
    full_periods_only: bool = False,
) -> pd.Series:
    # Сумма value (по умолчанию - выручка) за каждый период: день, неделю, месяц, год.
    # full_periods_only=True - без неполных крайних периодов: данные по 9 декабря дали бы
    # "декабрь" из 9 дней, и на графике это выглядело бы как обвал продаж
    if period not in PERIODS:
        raise ValueError(f"Неизвестный период «{period}». Есть: {', '.join(PERIODS)}")
    require_field(events, value, numeric=True)
    # resample раскладывает строки по периодам по дате и складывает каждый период
    totals = events.set_index("date")[value].resample(PERIODS[period]).sum()
    if not full_periods_only or totals.empty:
        return totals

    periods = totals.index.to_period()  # 31.12.2011 -> декабрь 2011: у него есть начало и конец
    first_complete = events["date"].min().normalize() <= periods[0].start_time
    last_complete = events["date"].max().normalize() >= periods[-1].end_time.normalize()
    return totals.iloc[(0 if first_complete else 1) : (None if last_complete else -1)]


def incomplete_periods(events: pd.DataFrame, period: str = "месяц") -> list[str]:
    # Какие крайние периоды неполные - чтобы честно сказать, почему их нет на графике.
    # Например: ["декабрь 2011 (данные по 09.12.2011)"]
    periods = events.set_index("date").resample(PERIODS[period]).size().index.to_period()
    start, end = events["date"].min().normalize(), events["date"].max().normalize()

    def label(item: pd.Period) -> str:
        return month_name(item) if period == "месяц" else str(item)

    result = []
    if start > periods[0].start_time:
        result.append(f"{label(periods[0])} (данные с {start:%d.%m.%Y})")
    if end < periods[-1].end_time.normalize():
        result.append(f"{label(periods[-1])} (данные по {end:%d.%m.%Y})")
    return result


def period_total(events: pd.DataFrame, start: str, end: str, value: str = "amount") -> float:
    # Сумма value с start по end ВКЛЮЧИТЕЛЬНО: "2025-03-01", "2025-03-31" - весь март.
    # Берём даты раньше следующего дня после end, иначе 31.03 в 15:00 не попадёт в март
    start_date = pd.Timestamp(start)
    after_end = pd.Timestamp(end) + pd.Timedelta(days=1)
    in_period = (events["date"] >= start_date) & (events["date"] < after_end)
    return float(events.loc[in_period, value].sum())
