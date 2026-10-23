"""Ручки разделов анализа: обзор, топ, товар, сравнение, прогноз. Отдают числа - рисует фронт."""

from typing import Annotated

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, status

from app.analytics import (
    breakdown,
    by_period,
    find_items,
    incomplete_periods,
    item_detail,
    last_full_month_vs_previous,
)
from app.api.dependencies import PreparedSession
from app.api.schemas import (
    Choice,
    ItemDetail,
    ItemsFound,
    MonthSummary,
    Overview,
    SeriesPoint,
    Top,
    TopRow,
)
from app.data import FIELDS, available_fields, numeric_fields

router = APIRouter(prefix="/analysis", tags=["анализ"])

MONTH_FORMAT = "%Y-%m"  # период точки графика по месяцам: "2026-09"
NOT_GROUPED = ("date", "price", "receipt")  # топ по дате, цене или номеру чека бессмыслен
MAX_TOP = 50  # больше строк в топе не показываем - это уже не топ, а таблица
MAX_SUGGESTIONS = 20  # подсказок при вводе названия - не больше

# Запрос товара: название, его часть или артикул
ItemQuery = Annotated[
    str, Query(min_length=1, max_length=100, description="Название, его часть или артикул")
]


def to_points(series: pd.Series, period_format: str) -> list[SeriesPoint]:
    # Ряд pandas (дата -> значение) -> точки для графика на фронте
    return [
        SeriesPoint(period=f"{moment:{period_format}}", value=round(float(value), 2))
        for moment, value in series.items()
    ]


def to_month_summary(month: dict) -> MonthSummary:
    # Результат last_full_month_vs_previous -> ключи для фронта вместо русских.
    # Общий для обзора и товара
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
        last_month, note = to_month_summary(last_full_month_vs_previous(events)), None
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


@router.get("/items", summary="Поиск товара: подсказки при вводе")
def search_items(session: PreparedSession, q: ItemQuery) -> ItemsFound:
    """Ищет по точному названию, затем по артикулу и другим признакам, затем по части названия."""
    found = find_items(session.events, q)
    return ItemsFound(query=q, items=found[:MAX_SUGGESTIONS], total=len(found))


@router.get("/item", summary="Товар: всё о нём")
def item(
    session: PreparedSession,
    q: ItemQuery,
    # В адресе - ?all=true, в коде - all_matches: имя all занято встроенной функцией Python
    all_matches: Annotated[
        bool, Query(alias="all", description="true - все подходящие товары вместе")
    ] = False,
) -> ItemDetail:
    """Выручка, доля, количество, даты продаж, динамика по месяцам и последний месяц.
    Подходит несколько товаров, а all=false - просим уточнить, а не угадываем."""
    found = find_items(session.events, q)
    if not found:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Не найдено ничего похожего на «{q}»")
    if len(found) > 1 and not all_matches:
        names = ", ".join(found[:MAX_SUGGESTIONS])
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Под «{q}» подходит несколько: {names}. Уточните"
        )

    detail = item_detail(session.events, q, all_matches=all_matches)
    last_month = detail["последний_месяц"]
    return ItemDetail(
        name=detail["товар"],
        items=detail["позиции"],
        currency=session.currency,
        first_sale=detail["первая_продажа"].date(),
        last_sale=detail["последняя_продажа"].date(),
        amount=detail["выручка"],
        share_percent=detail["доля_выручки_%"],
        quantity=detail.get("количество"),
        monthly=to_points(detail["динамика"], MONTH_FORMAT),
        last_month=to_month_summary(last_month) if last_month else None,
    )
