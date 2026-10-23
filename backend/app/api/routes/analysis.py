"""Ручки разделов анализа: обзор, топ, товар, сравнение, прогноз. Отдают числа - рисует фронт."""

import pandas as pd
from fastapi import APIRouter

from app.analytics import by_period, incomplete_periods, last_full_month_vs_previous
from app.api.dependencies import PreparedSession
from app.api.schemas import MonthSummary, Overview, SeriesPoint

router = APIRouter(prefix="/analysis", tags=["анализ"])

MONTH_FORMAT = "%Y-%m"  # период точки графика по месяцам: "2026-09"


def to_points(series: pd.Series, period_format: str) -> list[SeriesPoint]:
    # Ряд pandas (дата -> значение) -> точки для графика на фронте
    return [
        SeriesPoint(period=f"{moment:{period_format}}", value=round(float(value), 2))
        for moment, value in series.items()
    ]


def month_summary(events: pd.DataFrame) -> MonthSummary:
    # Последний полный месяц против предыдущего - ключи для фронта вместо русских
    month = last_full_month_vs_previous(events)
    return MonthSummary(
        month=month["месяц"],
        previous_month=month["прошлый_месяц"],
        before=month["было"],
        after=month["стало"],
        change=month["изменение"],
        change_percent=month["изменение_%"],
        per_day_before=month["в_день_было"],
        per_day_after=month["в_день_стало"],
        per_day_change_percent=month["изменение_в_день_%"],
    )


@router.get("/overview", summary="Обзор: как прошёл месяц и выручка по месяцам")
def overview(session: PreparedSession) -> Overview:
    """Первый экран после разметки. Неполные крайние месяцы на график не попадают -
    иначе месяц из 9 дней выглядел бы как обвал продаж."""
    events = session.events
    try:
        last_month, note = month_summary(events), None
    except ValueError as error:  # меньше двух полных месяцев - сравнивать не с чем
        last_month, note = None, str(error)

    return Overview(
        currency=session.currency,
        date_from=events["date"].min().date(),
        date_to=events["date"].max().date(),
        total=round(float(events["amount"].sum()), 2),
        last_month=last_month,
        last_month_note=note,
        monthly=to_points(by_period(events, "месяц", full_periods_only=True), MONTH_FORMAT),
        incomplete=incomplete_periods(events),
    )
