"""Конвейер: файл -> загрузка -> очистка -> события универсальной модели."""

from pathlib import Path

import pandas as pd

from app.cleaner import clean
from app.loader import load
from app.model import KIND_SALE, available_fields, to_events


def prepare_events(
    path: Path,
    mapping: dict[str, str],
    kind: str = KIND_SALE,
    sheet: str | None = None,
) -> tuple[pd.DataFrame, dict]:
    # Файл + словарь ролей -> события и общий отчёт. Точка входа для интерфейса
    sheets = load(path)
    if not sheets:
        raise ValueError("В файле нет данных")

    sheet_name = sheet if sheet is not None else next(iter(sheets))  # не указали лист - первый
    if sheet_name not in sheets:
        raise ValueError(f"В файле нет листа «{sheet_name}». Есть: {', '.join(sheets)}")

    cleaned, clean_report = clean(sheets[sheet_name], mapping)
    events = to_events(cleaned, mapping, kind)

    report = {
        "файл": Path(path).name,
        "лист": sheet_name,
        **clean_report,  # всё из отчёта очистки: сколько строк было, удалено, стало
        "поля": available_fields(events),
    }
    return events, report
