"""Ручки разделов анализа: обзор, топ, товар, сравнение, прогноз. Отдают числа - рисует фронт."""

from typing import Annotated

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, status

from app.analytics import breakdown, by_period, incomplete_periods, last_full_month_vs_previous
from app.api.dependencies import PreparedSession
from app.api.schemas import Choice, MonthSummary, Overview, SeriesPoint, Top, TopRow
from app.data import FIELDS, available_fields, numeric_fields

router = APIRouter(prefix="/analysis", tags=["анализ"])

MONTH_FORMAT = "%Y-%m"  # период точки графика по месяцам: "2026-09"
NOT_GROUPED = ("date", "price", "receipt")  # топ по дате, цене или номеру чека бессмыслен
MAX_TOP = 50  # больше строк в топе не показываем - это уже не топ, а таблица


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


def groupable_fields(events: pd.DataFrame) -> list[Choice]:
    # По чему можно строить топ: текстовые поля, кроме даты, цены и номера чека.
    # Подпись - описание основного поля или название дополнительного ("Бренд")
    numeric = numeric_fields(events)
    return [
        Choice(value=field, label=FIELDS.get(field, field))
        for field in available_fields(events)
        if field not in numeric and field not in NOT_GROUPED
    ]


@router.get("/top", summary="Топ: лучшие или худшие товары, категории, бренды")
def top(
    session: PreparedSession,
    by: Annotated[str, Query(description="Поле из списка available")] = "object",
    top: Annotated[int, Query(ge=1, le=MAX_TOP, description="Сколько строк")] = 10,
    worst: Annotated[bool, Query(description="true - худшие вместо лучших")] = False,
) -> Top:
    """Выручка по выбранному полю и доля от всей выручки (а не только от топа)."""
    available = groupable_fields(session.events)
    labels = {choice.value: choice.label for choice in available}
    if by not in labels:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Топ по «{by}» не построить. Можно по: {', '.join(labels)}",
        )
    table = breakdown(session.events, by=by, top=top, worst=worst)
    return Top(
        by=by,
        by_label=labels[by],
        worst=worst,
        currency=session.currency,
        available=available,
        rows=[
            TopRow(name=str(name), value=float(row["amount"]), share_percent=float(row["доля_%"]))
            for name, row in table.iterrows()
        ],
    )
