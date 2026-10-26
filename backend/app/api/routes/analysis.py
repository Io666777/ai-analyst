"""Ручки разделов анализа: обзор, топ, товар, сравнение, прогноз. Отдают числа - рисует фронт."""

from datetime import date
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, status

from app.analytics import (
    between,
    breakdown,
    by_period,
    compare_breakdown,
    compare_periods,
    daily_totals,
    find_items,
    incomplete_periods,
    item_days,
    item_detail,
    item_names,
    last_full_month_vs_previous,
)
from app.api.dependencies import PreparedSession
from app.api.schemas import (
    Accuracy,
    Catalog,
    Choice,
    CompareRow,
    Comparison,
    Daily,
    Estimate,
    Forecast,
    ForecastPeriod,
    ForecastPoint,
    ItemDay,
    ItemDays,
    ItemDetail,
    ItemsFound,
    ModelScore,
    MonthSummary,
    Overview,
    PeriodTotal,
    SeriesPoint,
    Top,
    TopRow,
    YearAgo,
)
from app.api.sessions import Session
from app.data import FIELDS, available_fields, numeric_fields
from app.forecast import STEP_ESTIMATE, STEP_FORECAST, STEP_NONE, make_forecast, to_daily

router = APIRouter(prefix="/analysis", tags=["анализ"])

MONTH_FORMAT = "%Y-%m"  # период точки графика по месяцам: "2026-09"
NOT_GROUPED = ("date", "price", "receipt")  # топ по дате, цене или номеру чека бессмыслен
MAX_TOP = 50  # больше строк в топе не показываем - это уже не топ, а таблица
MAX_SUGGESTIONS = 20  # подсказок при вводе названия - не больше
DAY_FORMAT = "%Y-%m-%d"  # период точки графика по дням: "2026-10-01"

# Ступенька холодного старта -> короткий код для фронта
STEP_CODES = {STEP_NONE: "none", STEP_ESTIMATE: "estimate", STEP_FORECAST: "forecast"}
# На графике прогноза - конец истории: вдвое длиннее прогноза, но не меньше 60 дней.
# Вся история рядом с коротким прогнозом его "раздавила" бы
HISTORY_PER_HORIZON = 2
MIN_HISTORY_SHOWN = 60
FORECAST_CACHE_KEY = "forecast"

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


MAX_DAILY_DAYS = 366  # по дням - не больше года: длиннее таблица уже не читается


@router.get("/daily", summary="Выручка по дням периода")
def daily(
    session: PreparedSession,
    date_from: Annotated[date, Query(description="С какого дня")],
    date_to: Annotated[date, Query(description="По какой день, включительно")],
) -> Daily:
    """Каждый день периода, дни без продаж - нулём. Для таблички «месяц по дням» в обзоре."""
    check_period(date_from, date_to)
    if (date_to - date_from).days >= MAX_DAILY_DAYS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"По дням - не больше {MAX_DAILY_DAYS} дней"
        )
    totals = daily_totals(session.events, date_from.isoformat(), date_to.isoformat())
    return Daily(
        currency=session.currency,
        date_from=date_from,
        date_to=date_to,
        total=round(float(totals.sum()), 2),
        days=to_points(totals, DAY_FORMAT),
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


def check_period(start: date | None, end: date | None) -> None:
    # Начало позже конца - понятная ошибка, а не пустой результат
    if start and end and start > end:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Начало периода ({start:%d.%m.%Y}) позже конца ({end:%d.%m.%Y})",
        )


@router.get("/top", summary="Топ: лучшие или худшие товары, категории, бренды")
def top(
    session: PreparedSession,
    by: Annotated[str, Query(description="Поле из списка available")] = "object",
    top: Annotated[int, Query(ge=1, le=MAX_TOP, description="Сколько строк")] = 10,
    worst: Annotated[bool, Query(description="true - худшие вместо лучших")] = False,
    date_from: Annotated[date | None, Query(description="С какого дня; нет - с начала")] = None,
    date_to: Annotated[date | None, Query(description="По какой день; нет - до конца")] = None,
) -> Top:
    """Выручка по выбранному полю за период и доля от всей выручки периода
    (а не только от топа)."""
    check_period(date_from, date_to)
    available = groupable_fields(session.events)
    labels = {choice.value: choice.label for choice in available}
    if by not in labels:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Топ по «{by}» не построить. Можно по: {', '.join(labels)}",
        )
    events = between(
        session.events,
        date_from.isoformat() if date_from else None,
        date_to.isoformat() if date_to else None,
    )
    table = breakdown(events, by=by, top=top, worst=worst)
    return Top(
        by=by,
        by_label=labels[by],
        worst=worst,
        currency=session.currency,
        date_from=date_from or session.events["date"].min().date(),
        date_to=date_to or session.events["date"].max().date(),
        total=round(float(events["amount"].sum()), 2),
        available=available,
        rows=[
            TopRow(name=str(name), value=float(row["amount"]), share_percent=float(row["доля_%"]))
            for name, row in table.iterrows()
        ],
    )


MAX_CATALOG = 5000  # больше товаров в списке не листают - их ищут по названию или артикулу


@router.get("/catalog", summary="Все товары - список под поиском")
def catalog(session: PreparedSession) -> Catalog:
    """Все товары с выручкой и долей, от самых продаваемых. Фронт фильтрует список сам
    на каждую букву - без запроса на сервер."""
    if "object" not in available_fields(session.events):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "В данных нет колонки с товаром")
    table = breakdown(session.events, by="object", top=MAX_CATALOG)
    return Catalog(
        currency=session.currency,
        total=int(session.events["object"].nunique()),
        items=[
            TopRow(name=str(name), value=float(row["amount"]), share_percent=float(row["доля_%"]))
            for name, row in table.iterrows()
        ],
    )


@router.get("/items", summary="Поиск товара: подсказки при вводе")
def search_items(session: PreparedSession, q: ItemQuery) -> ItemsFound:
    """Ищет по точному названию, затем по артикулу и другим признакам, затем по части названия."""
    found = find_items(session.events, q)
    return ItemsFound(query=q, items=found[:MAX_SUGGESTIONS], total=len(found))


def check_items(events: pd.DataFrame, query: str, all_matches: bool) -> list[str]:
    # Товары по запросу - или понятная ошибка: не нашлось (404), подходит несколько (400)
    found = find_items(events, query)
    if not found:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Не найдено ничего похожего на «{query}»")
    if len(found) > 1 and not all_matches:
        names = ", ".join(found[:MAX_SUGGESTIONS])
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Под «{query}» подходит несколько: {names}. Уточните"
        )
    return item_names(events, query, all_matches)


@router.get("/item/days", summary="Товар по дням периода")
def item_by_days(
    session: PreparedSession,
    q: ItemQuery,
    date_from: Annotated[date, Query(description="С какого дня")],
    date_to: Annotated[date, Query(description="По какой день, включительно")],
    all_matches: Annotated[
        bool, Query(alias="all", description="true - все подходящие товары вместе")
    ] = False,
) -> ItemDays:
    """Выручка, штуки и кто продавал - за каждый день периода. Для таблицы «месяц товара»."""
    check_period(date_from, date_to)
    if (date_to - date_from).days >= MAX_DAILY_DAYS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"По дням - не больше {MAX_DAILY_DAYS} дней"
        )
    items = check_items(session.events, q, all_matches)
    table = item_days(session.events, items, date_from.isoformat(), date_to.isoformat())
    has_quantity = "quantity" in table
    has_executors = "executors" in table
    return ItemDays(
        name=items[0] if len(items) == 1 else f"{q} (позиций: {len(items)})",
        currency=session.currency,
        date_from=date_from,
        date_to=date_to,
        total=round(float(table["amount"].sum()), 2),
        quantity=float(table["quantity"].sum()) if has_quantity else None,
        has_executors=has_executors,
        days=[
            ItemDay(
                period=f"{day:{DAY_FORMAT}}",
                amount=round(float(row["amount"]), 2),
                quantity=float(row["quantity"]) if has_quantity else None,
                executors=row["executors"] if has_executors else [],
            )
            for day, row in table.iterrows()
        ],
    )


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
    check_items(session.events, q, all_matches)
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


def percent_change(before: float, after: float) -> float | None:
    # Изменение в %; было 0 - процента нет: на ноль делить нельзя
    return round((after - before) / before * 100, 1) if before else None


def period_total(date_from: date, date_to: date, value: float) -> PeriodTotal:
    # Итог периода и среднее за день. Дней - включая оба края: с 1 по 31 марта - 31 день
    days = (date_to - date_from).days + 1
    return PeriodTotal(
        date_from=date_from,
        date_to=date_to,
        days=days,
        value=value,
        per_day=round(value / days, 2),
    )


@router.get("/compare", summary="Сравнение двух периодов")
def compare(
    session: PreparedSession,
    first_from: Annotated[date, Query(description="Первый период (было): с")],
    first_to: Annotated[date, Query(description="Первый период: по, включительно")],
    second_from: Annotated[date, Query(description="Второй период (стало): с")],
    second_to: Annotated[date, Query(description="Второй период: по, включительно")],
) -> Comparison:
    """Было и стало: итог, изменение в деньгах и %, в среднем за день.
    Период за пределами данных - предупреждение: сравнение может быть нечестным."""
    check_period(first_from, first_to)
    check_period(second_from, second_to)
    result = compare_periods(
        session.events,
        (first_from.isoformat(), first_to.isoformat()),
        (second_from.isoformat(), second_to.isoformat()),
    )
    first = period_total(first_from, first_to, result["было"])
    second = period_total(second_from, second_to, result["стало"])
    comparison = Comparison(
        currency=session.currency,
        first=first,
        second=second,
        change=result["изменение"],
        change_percent=result["изменение_%"],
        per_day_change_percent=percent_change(first.per_day, second.per_day),
        warnings=result["предупреждения"],
    )
    # Разбивка по товарам - если товар размечен: что выросло, что просело
    if "object" in available_fields(session.events):
        table = compare_breakdown(
            session.events,
            (first_from.isoformat(), first_to.isoformat()),
            (second_from.isoformat(), second_to.isoformat()),
        )
        comparison.by_label = FIELDS["object"]
        comparison.rows = [
            CompareRow(
                name=str(name),
                first=float(row["было"]),
                second=float(row["стало"]),
                change=float(row["изменение"]),
                change_percent=percent_change(row["было"], row["стало"]),
            )
            for name, row in table.iterrows()
        ]
    return comparison


def forecast_points(table: pd.DataFrame) -> list[ForecastPoint]:
    # Таблица прогноза (ds, yhat, коридор - если модель его считает) -> точки для графика
    has_corridor = "yhat_lower" in table
    return [
        ForecastPoint(
            period=f"{row.ds:{DAY_FORMAT}}",
            value=round(float(row.yhat), 2),
            lower=round(float(row.yhat_lower), 2) if has_corridor else None,
            upper=round(float(row.yhat_upper), 2) if has_corridor else None,
        )
        for row in table.itertuples()
    ]


def build_forecast(session: Session) -> Forecast:
    # Долгий расчёт: make_forecast (экзамен моделей, выбор горизонта) -> ответ для фронта
    result = make_forecast(session.events, country=session.country, currency=session.currency)
    response = Forecast(
        step=STEP_CODES[result["ступенька"]],
        message=result["сообщение"],
        currency=session.currency,
        history_days=result["история_дней"],
    )
    if result["ступенька"] == STEP_ESTIMATE:
        response.estimate = Estimate(
            per_day=result["в_среднем_в_день"],
            by_weekday=result["по_дням_недели"],
            projection=result["если_так_пойдёт_дальше"],
        )
    if result["ступенька"] != STEP_FORECAST:
        return response

    accuracy = result["точность"]
    daily = to_daily(session.events)
    shown = max(MIN_HISTORY_SHOWN, HISTORY_PER_HORIZON * result["горизонт_дней"])
    history = pd.Series(daily["y"].to_numpy(), index=daily["ds"]).tail(shown)

    response.model = result["модель"]
    response.horizon_days = result["горизонт_дней"]
    response.total = result["итого"]
    response.corridor = result.get("коридор")
    response.accuracy = Accuracy(
        level=accuracy["точность"],
        error_percent=round(accuracy["ошибка_%"], 1),
        summary=accuracy["вывод"],
        reasons=accuracy["причины"],
    )
    response.history = to_points(history, DAY_FORMAT)
    response.points = forecast_points(result["прогноз"])
    response.weeks = forecast_periods(result["по_неделям"])
    response.months = forecast_periods(result["по_месяцам"])
    if result["год_назад"]:
        ago = result["год_назад"]
        response.year_ago = YearAgo(
            date_from=ago["с"].date(),
            date_to=ago["по"].date(),
            value=ago["было"],
            change_percent=ago["изменение_%"],
        )
    response.models = [
        ModelScore(
            model=score["модель"],
            error_percent=round(score["ошибка_%"], 1),
            total_error_percent=round(score["ошибка_итога_%"], 1),
            chosen=score["модель"] == result["модель"],
        )
        for score in result["экзамен"]
    ]
    return response


def forecast_periods(table: pd.DataFrame) -> list[ForecastPeriod]:
    # Прогноз по неделям или месяцам (forecast_by) -> строки для фронта
    has_corridor = "yhat_lower" in table
    return [
        ForecastPeriod(
            date_from=row["с"].date(),
            date_to=row["по"].date(),
            value=float(row["yhat"]),
            lower=float(row["yhat_lower"]) if has_corridor else None,
            upper=float(row["yhat_upper"]) if has_corridor else None,
        )
        for _, row in table.iterrows()
    ]


@router.post("/forecast", summary="Прогноз: посчитать или отдать уже посчитанный")
def forecast(session: PreparedSession) -> Forecast:
    """Программа сама проверяет модели на прошлом, выбирает лучшую и горизонт, которому можно
    верить. Считается от нескольких секунд до минуты - один раз: дальше ответ из памяти сессии,
    пока не поменяли разметку или настройки."""
    # Обычная функция, не async: FastAPI выполняет её в отдельном потоке,
    # и пока считается прогноз, остальные запросы сервера отвечают как обычно
    with session.lock:  # двойной клик: второй запрос подождёт первый и возьмёт готовое
        if FORECAST_CACHE_KEY not in session.cache:
            session.cache[FORECAST_CACHE_KEY] = build_forecast(session)
        return session.cache[FORECAST_CACHE_KEY]
