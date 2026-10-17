"""Загрузка файлов с данными: CSV и Excel."""

from pathlib import Path

import pandas as pd

CSV_ENCODINGS = ("utf-8-sig", "cp1251")
HEADER_SEARCH_ROWS = 20  # шапку таблицы ищем только в первых 20 строках


def guess_separator(header_line: str) -> str:

    return ";" if header_line.count(";") >= header_line.count(",") else ","


def read_csv(path: Path) -> pd.DataFrame:

    for encoding in CSV_ENCODINGS:
        try:
            with path.open(encoding=encoding) as file:
                separator = guess_separator(file.readline())
            return pd.read_csv(path, sep=separator, encoding=encoding)
        except UnicodeDecodeError:
            continue  # кодировка не подошла - пробуем следующую
    raise ValueError(f"Не удалось определить кодировку файла {path.name}")


def find_header_row(raw: pd.DataFrame) -> int:
    # Шапка таблицы - первая строка, где заполнено хотя бы полколонок
    filled_cells = raw.head(HEADER_SEARCH_ROWS).notna().sum(axis=1)
    header_rows = filled_cells[filled_cells >= raw.shape[1] / 2]
    if header_rows.empty:
        return 0  # не нашли - считаем, что шапка в первой строке
    return int(header_rows.index[0])
