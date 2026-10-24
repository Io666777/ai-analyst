"""Поиск товара и всё о нём: итоги, доля, динамика, последний месяц."""

import pandas as pd

from app.analytics.compare import last_full_month_vs_previous
from app.analytics.periods import between, by_period
from app.data import available_fields, extra_fields, numeric_fields, require_field


def find_items(events: pd.DataFrame, query: str) -> list[str]:
    # Все товары, подходящие под запрос, без учёта регистра. Порядок поиска:
    # 1) точное название, 2) точное значение признака (артикул, код), 3) часть названия -
    # сначала те, что начинаются с запроса (см. match_rank)
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

    found = [item for item in items if text in item.lower()]
    return sorted(found, key=lambda item: (match_rank(item, text), item))


def match_rank(item: str, text: str) -> int:
    # Чем раньше в названии совпадение, тем выше в подсказках: на "с" сначала "Снеки",
    # потом "Хлеб Сельский", и лишь затем "Пиво Лидское" (буква внутри слова)
    name = item.lower()
    if name.startswith(text):
        return 0
    if any(word.startswith(text) for word in name.split()):
        return 1
    return 2


def find_item(events: pd.DataFrame, query: str) -> str:
    # Ровно один товар по запросу: "пиво лидское" -> "Пиво Лидское 0.5", "00-0001" -> по артикулу
    found = find_items(events, query)
    if not found:
        raise ValueError(f"Не найдено ничего похожего на «{query}»")
    if len(found) > 1:  # подходит несколько - не угадываем, а просим уточнить
        raise ValueError(f"Под «{query}» подходит несколько: {', '.join(found)}. Уточните")
    return found[0]


def item_names(events: pd.DataFrame, query: str, all_matches: bool = False) -> list[str]:
    # Какие товары смотрим: ровно один по запросу или все подходящие ("всё пиво сразу")
    if not all_matches:
        return [find_item(events, query)]
    items = find_items(events, query)
    if not items:
        raise ValueError(f"Не найдено ничего похожего на «{query}»")
    return items


def item_days(events: pd.DataFrame, items: list[str], start: str, end: str) -> pd.DataFrame:
    # Продажи товаров по дням периода: выручка, штуки и кто продавал (если такие поля есть).
    # День без продаж - строка с нулями: в таблице месяца провал должен быть виден
    fields = available_fields(events)
    sales = between(events[events["object"].isin(items)], start, end)
    days = pd.date_range(start, end, freq="D")
    by_day = sales.groupby(sales["date"].dt.normalize())

    result = pd.DataFrame(index=days)
    for value in ("amount", "quantity"):
        if value in fields:
            result[value] = by_day[value].sum().reindex(days, fill_value=0)
    if "executor" in fields:
        # Сотрудники дня - от продавшего больше к меньшему
        def sellers(day: pd.DataFrame) -> list[str]:
            totals = day.groupby("executor")["amount"].sum().sort_values(ascending=False)
            return [str(name) for name in totals.index]

        names = {day: sellers(group) for day, group in by_day}
        result["executors"] = [names.get(day, []) for day in days]
    return result


def item_detail(
    events: pd.DataFrame,
    query: str,
    period: str = "месяц",
    all_matches: bool = False,
) -> dict:
    # Всё о товаре: итоги, доля в выручке, даты продаж, динамика, последний месяц.
    # all_matches=True - все подходящие товары вместе ("всё пиво сразу")
    fields = available_fields(events)
    items = item_names(events, query, all_matches)
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
    # Только полные периоды - и полные по ВСЕМ данным, а не по датам продаж этого товара.
    # Период без продаж товара - честный ноль, а не пропуск
    full = by_period(events, period, value, full_periods_only=True)
    detail["динамика"] = by_period(sales, period, value).reindex(full.index, fill_value=0)
    try:
        detail["последний_месяц"] = last_full_month_vs_previous(sales, value, all_events=events)
    except ValueError:
        detail["последний_месяц"] = None  # в данных меньше двух полных месяцев
    return detail
