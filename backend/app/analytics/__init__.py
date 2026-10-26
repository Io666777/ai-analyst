"""Аналитика по событиям универсальной модели: итоги, сравнения, топы, товары.

Разложена по темам:
    periods - итоги по периодам (день, неделя, месяц, год), неполные периоды
    compare - сравнение двух периодов, "как прошёл последний месяц"
    top     - топы: лучшие и худшие товары, категории, бренды...
    items   - поиск товара и всё о нём

Всё нужное собрано здесь, поэтому снаружи импорт прежний: from app.analytics import by_period
"""

from app.analytics.compare import (
    compare_breakdown,
    compare_periods,
    last_full_month,
    last_full_month_vs_previous,
    month_bounds,
)
from app.analytics.items import find_item, find_items, item_days, item_detail, item_names
from app.analytics.periods import (
    MONTH_NAMES,
    PERIODS,
    between,
    by_period,
    daily_totals,
    incomplete_periods,
    month_name,
    period_total,
)
from app.analytics.top import breakdown

__all__ = [
    "MONTH_NAMES",
    "PERIODS",
    "between",
    "breakdown",
    "by_period",
    "compare_breakdown",
    "compare_periods",
    "daily_totals",
    "find_item",
    "find_items",
    "incomplete_periods",
    "item_days",
    "item_detail",
    "item_names",
    "last_full_month",
    "last_full_month_vs_previous",
    "month_bounds",
    "month_name",
    "period_total",
]
