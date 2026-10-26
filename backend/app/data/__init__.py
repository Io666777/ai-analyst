"""Подготовка данных: файл любого бизнеса -> события универсальной модели.

Разложена по шагам:
    loader  - загрузка Excel и CSV "как есть"
    cleaner - очистка: даты, числа, строки "Итого"
    detect  - автоопределение ролей колонок правилами: по названию и значениям
    model   - универсальная модель: одинаковые колонки для любого бизнеса, роли колонок
    prepare - все шаги сразу: файл (или таблица) -> события

Всё нужное собрано здесь, поэтому снаружи импорт короткий: from app.data import prepare_events
"""

from app.data.cleaner import TOTAL_WORDS, clean, drop_totals, strip_text, to_date, to_number
from app.data.detect import detect_roles
from app.data.loader import (
    CSV_ENCODINGS,
    EXCEL_SUFFIXES,
    column_names,
    find_header_row,
    guess_separator,
    load,
    read_csv,
    read_excel,
)
from app.data.model import (
    EVENT_COLUMNS,
    FIELDS,
    KIND_PURCHASE,
    KIND_SALE,
    KIND_STOCK,
    NOT_ADDITIVE,
    ROLE_ATTRIBUTE,
    ROLE_CHOICES,
    ROLE_IGNORE,
    ROLE_MEASURE,
    available_fields,
    exclude_objects,
    extra_fields,
    numeric_fields,
    require_field,
    suggest_exclusions,
    to_events,
)
from app.data.prepare import prepare_events, prepare_table

__all__ = [
    "CSV_ENCODINGS",
    "EVENT_COLUMNS",
    "EXCEL_SUFFIXES",
    "FIELDS",
    "KIND_PURCHASE",
    "KIND_SALE",
    "KIND_STOCK",
    "NOT_ADDITIVE",
    "ROLE_ATTRIBUTE",
    "ROLE_CHOICES",
    "ROLE_IGNORE",
    "ROLE_MEASURE",
    "TOTAL_WORDS",
    "available_fields",
    "clean",
    "column_names",
    "detect_roles",
    "drop_totals",
    "exclude_objects",
    "extra_fields",
    "find_header_row",
    "guess_separator",
    "load",
    "numeric_fields",
    "prepare_events",
    "prepare_table",
    "read_csv",
    "read_excel",
    "require_field",
    "strip_text",
    "suggest_exclusions",
    "to_date",
    "to_events",
    "to_number",
]
