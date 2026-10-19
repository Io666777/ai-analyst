"""Аналитика по событиям универсальной модели: итоги, сравнения, топы."""

import pandas as pd

from app.model import available_fields, extra_fields, numeric_fields

# Понятное название периода -> код периода в pandas (ME - конец месяца, YE - конец года)
PERIODS = {"день": "D", "неделя": "W", "месяц": "ME", "год": "YE"}

MONTH_NAMES = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]  # fmt: skip


def require_field(events: pd.DataFrame, field: str, numeric: bool = False) -> None:
    # Проверка перед расчётом: поле есть в данных, а если нужно складывать - оно числовое
    if field not in available_fields(events):
        raise ValueError(f"В данных нет поля «{field}»")
    if numeric and field not in numeric_fields(events):
        raise ValueError(f"Поле «{field}» не числовое - его нельзя складывать")


def by_period(events: pd.DataFrame, period: str = "месяц", value: str = "amount") -> pd.Series:
    # Сумма value (по умолчанию - выручка) за каждый период: день, неделю, месяц, год
    if period not in PERIODS:
        raise ValueError(f"Неизвестный период «{period}». Есть: {', '.join(PERIODS)}")
    require_field(events, value, numeric=True)
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
    require_field(events, value, numeric=True)
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


def breakdown(
    events: pd.DataFrame,
    by: str = "object",
    value: str = "amount",
    top: int = 10,
    worst: bool = False,
) -> pd.DataFrame:
    # Топ по полю by (товар, категория, мастер, любой признак - бренд, филиал...):
    # сумма value и доля в общем итоге. worst=True - наоборот, худшие
    require_field(events, by)
    require_field(events, value, numeric=True)

    totals = events.groupby(by)[value].sum().sort_values(ascending=worst)
    share = totals / totals.sum() * 100  # доля от ВСЕГО итога, а не только от топа
    result = pd.DataFrame({value: totals.round(2), "доля_%": share.round(1)})
    return result.head(top)


def find_items(events: pd.DataFrame, query: str) -> list[str]:
    # Все товары, подходящие под запрос, без учёта регистра. Порядок поиска:
    # 1) точное название, 2) точное значение признака (артикул, код), 3) часть названия
    require_field(events, "object")
    items = events["object"].dropna().unique()
    text = query.strip().lower()

    exact = [item for item in items if item.lower() == text]
    if exact:
        return exact

    text_extras = [field for field in extra_fields(events) if field not in numeric_fields(events)]
    for field in text_extras:
        # fillna(False) - у строк без значения признака совпадения нет
        matches = events[field].str.lower().eq(text).fillna(False)
        found = events.loc[matches, "object"].dropna().unique()
        if len(found):
            return sorted(found)

    return sorted(item for item in items if text in item.lower())


def find_item(events: pd.DataFrame, query: str) -> str:
    # Ровно один товар по запросу: "пиво лидское" -> "Пиво Лидское 0.5", "00-0001" -> по артикулу
    found = find_items(events, query)
    if not found:
        raise ValueError(f"Не найдено ничего похожего на «{query}»")
    if len(found) > 1:  # подходит несколько - не угадываем, а просим уточнить
        raise ValueError(f"Под «{query}» подходит несколько: {', '.join(found)}. Уточните")
    return found[0]


def item_detail(
    events: pd.DataFrame,
    query: str,
    period: str = "месяц",
    all_matches: bool = False,
) -> dict:
    # Всё о товаре: итоги, доля в выручке, даты продаж, динамика, последний месяц.
    # all_matches=True - все подходящие товары вместе ("всё пиво сразу")
    fields = available_fields(events)
    if all_matches:
        items = find_items(events, query)
        if not items:
            raise ValueError(f"Не найдено ничего похожего на «{query}»")
    else:
        items = [find_item(events, query)]
    sales = events[events["object"].isin(items)]  # только продажи этих товаров

    detail = {
        "товар": items[0] if len(items) == 1 else f"{query} (позиций: {len(items)})",
        "позиции": items,
        "первая_продажа": sales["date"].min(),
        "последняя_продажа": sales["date"].max(),
    }
    if "amount" in fields:
        # float() - обычное число Python вместо np.float64, чтобы красиво выводилось
        item_amount = float(sales["amount"].sum())
        detail["выручка"] = round(item_amount, 2)
        detail["доля_выручки_%"] = round(item_amount / events["amount"].sum() * 100, 1)
    if "quantity" in fields:
        detail["количество"] = float(sales["quantity"].sum())

    # Динамику считаем по деньгам, а если их нет - по штукам
    value = "amount" if "amount" in fields else "quantity"
    detail["динамика"] = by_period(sales, period, value)
    try:
        detail["последний_месяц"] = last_full_month_vs_previous(sales, value)
    except ValueError:
        detail["последний_месяц"] = None  # товар продаётся меньше двух полных месяцев
    return detail
