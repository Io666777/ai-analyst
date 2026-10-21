"""Подготовка данных целиком: файл или таблица -> события универсальной модели.

prepare_events: файл -> загрузка -> очистка -> события
prepare_table:  уже прочитанная таблица -> очистка -> события
"""

from pathlib import Path

import pandas as pd

from app.data.cleaner import clean
from app.data.loader import load
from app.data.model import KIND_SALE, available_fields, exclude_objects, to_events


def prepare_events(
    path: Path,
    mapping: dict[str, str],
    kind: str = KIND_SALE,
    sheet: str | None = None,
    exclude: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    # Файл + словарь ролей -> события и общий отчёт. Точка входа для интерфейса.
    # exclude - товары, которые пользователь решил не учитывать (доставка, комиссии...)
    sheets = load(path)
    if not sheets:
        raise ValueError("В файле нет данных")

    sheet_name = sheet if sheet is not None else next(iter(sheets))  # не указали лист - первый
    if sheet_name not in sheets:
        raise ValueError(f"В файле нет листа «{sheet_name}». Есть: {', '.join(sheets)}")

    events, table_report = prepare_table(sheets[sheet_name], mapping, kind, exclude)
    return events, {"файл": Path(path).name, "лист": sheet_name, **table_report}


def prepare_table(
    table: pd.DataFrame,
    mapping: dict[str, str],
    kind: str = KIND_SALE,
    exclude: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    # То же, но для уже прочитанной таблицы: очистка -> события -> исключения.
    # Отдельно от чтения файла - чтобы интерфейс читал большой файл один раз
    cleaned, clean_report = clean(table, mapping)
    events = to_events(cleaned, mapping, kind)

    report = {
        **clean_report,  # всё из отчёта очистки: сколько строк было, удалено, стало
        "поля": available_fields(events),
    }
    if exclude:
        events, exclude_report = exclude_objects(events, exclude)
        report.update(exclude_report)
    return events, report
