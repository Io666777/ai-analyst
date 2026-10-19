"""Загрузка файлов с данными: CSV и Excel."""

from pathlib import Path

import pandas as pd

CSV_ENCODINGS = ("utf-8-sig", "cp1251")
HEADER_SEARCH_ROWS = 20  # шапку таблицы ищем только в первых 20 строках
EXCEL_SUFFIXES = (".xlsx", ".xls")


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


def read_excel(path: Path) -> dict[str, pd.DataFrame]:
    # sheet_name=None - читаем все листы сразу, header=None - без заголовка, "сырыми"
    sheets = pd.read_excel(path, sheet_name=None, header=None)
    tables = {}
    for sheet_name, raw in sheets.items():
        # Убираем полностью пустые строки и колонки, нумерацию строк начинаем заново
        raw = raw.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
        if raw.empty:
            continue  # пустой лист - пропускаем
        header_row = find_header_row(raw)
        table = raw.iloc[header_row + 1 :].reset_index(drop=True)  # всё, что ниже шапки
        table.columns = [str(name).strip() for name in raw.iloc[header_row]]  # шапка
        tables[sheet_name] = table.infer_objects()  # вернуть колонкам с числами числовой тип
    return tables


def load(path: Path) -> dict[str, pd.DataFrame]:
    # Единая точка входа: любой файл -> словарь {название листа: таблица}
    path = Path(path)
    suffix = path.suffix.lower()  # расширение файла: ".csv", ".xlsx"...
    if suffix == ".csv":
        return {path.stem: read_csv(path)}  # у CSV один "лист" - называем его по имени файла
    if suffix in EXCEL_SUFFIXES:
        return read_excel(path)
    raise ValueError(f"Формат {suffix} не поддерживается: нужен Excel (.xlsx, .xls) или CSV")
