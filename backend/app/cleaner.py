"""Очистка данных: приведение значений к нормальным типам."""

import pandas as pd

TOTAL_WORDS = ("итого", "всего", "total")  # слова, с которых начинаются итоговые строки


def to_number(values: pd.Series) -> pd.Series:
    # "1 200,50 руб" -> 1200.5. Что не получилось превратить в число - станет пустым (NaN)
    if pd.api.types.is_numeric_dtype(values):
        return values  # уже числа - ничего не делаем
    text = values.astype(str).str.replace(r"[^\d,.\-]", "", regex=True)  # оставить цифры , . -
    text = text.str.replace(",", ".", regex=False)  # дробная часть - через точку
    text = text.str.rstrip(".")  # точка в конце осталась от "руб." - убираем
    return pd.to_numeric(text, errors="coerce")


def to_date(values: pd.Series) -> pd.Series:
    # "01.10.24", "01.10.2025 09:00", "2025-10-01" -> дата
    # Что не похоже на дату (например "Итого") - станет пустым (NaT)
    if pd.api.types.is_datetime64_any_dtype(values):
        return values  # уже даты - ничего не делаем
    text = values.astype(str).str.strip()
    is_iso = text.str.match(r"^\d{4}-\d{2}-\d{2}")  # формат "год-месяц-день": 2025-10-01
    # Наш формат: dayfirst=True - день первым (03.04 - это 3 апреля), "mixed" - форматы разные
    dates = pd.to_datetime(text.where(~is_iso), dayfirst=True, format="mixed", errors="coerce")
    # Международный формат разбираем отдельно, иначе dayfirst перепутает месяц и день
    iso_dates = pd.to_datetime(text.where(is_iso), format="ISO8601", errors="coerce")
    return dates.fillna(iso_dates)


def drop_totals(df: pd.DataFrame, words: tuple[str, ...] = TOTAL_WORDS) -> pd.DataFrame:
    # Убирает итоговые строки: хотя бы одна ячейка начинается со слова из words.
    # words можно передать свои, например ("итого", "сумма по документу")
    words = tuple(word.strip().lower() for word in words)  # регистр и пробелы не важны
    text = df.astype(str).apply(lambda column: column.str.strip().str.lower())
    starts_with_total = text.apply(lambda column: column.str.startswith(words))
    is_total_row = starts_with_total.any(axis=1)  # True, если в строке есть хоть одно такое слово
    return df[~is_total_row]  # оставляем только строки, которые НЕ итоговые
