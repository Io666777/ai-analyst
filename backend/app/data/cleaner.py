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


def strip_text(values: pd.Series) -> pd.Series:
    # "  Капучино " -> "Капучино". Тип "string" сохраняет пустые значения пустыми, а не "nan"
    return values.astype("string").str.strip()


# Какую функцию применять к колонке с какой ролью.
# Роли, которых здесь нет (phone, email, ignore), не трогаем
CONVERTERS = {
    "date": to_date,
    "amount": to_number,
    "price": to_number,
    "quantity": to_number,
    "object": strip_text,
    "category": strip_text,
    "executor": strip_text,
    "person": strip_text,
    "receipt": strip_text,  # номер чека - текст: "А-0012" или "00012" (нули в начале важны)
    "attribute": strip_text,  # признак (артикул, бренд...) - текст, по той же причине
    "measure": to_number,  # показатель (скидка, себестоимость...) - число
}


def clean(
    df: pd.DataFrame,
    mapping: dict[str, str],
    total_words: tuple[str, ...] = TOTAL_WORDS,
) -> tuple[pd.DataFrame, dict]:
    # Чистит таблицу по словарю "колонка -> роль". Возвращает чистую таблицу и отчёт о чистке
    missing = [column for column in mapping if column not in df.columns]
    if missing:
        raise ValueError(f"В таблице нет колонок: {', '.join(missing)}")

    # 1. Убираем итоговые и полностью пустые строки
    result = drop_totals(df, total_words).dropna(how="all").copy()
    rows_after_totals = len(result)

    # 2. Каждой колонке - своё преобразование по её роли
    for column, role in mapping.items():
        converter = CONVERTERS.get(role)
        if converter:
            result[column] = converter(result[column])

    # 3. Строки без даты удаляем: событие без даты не привязать ко времени
    date_columns = [column for column, role in mapping.items() if role == "date"]
    result = result.dropna(subset=date_columns)

    report = {
        "строк_было": len(df),
        "удалено_итоговых_и_пустых": len(df) - rows_after_totals,
        "удалено_без_даты": rows_after_totals - len(result),
        "строк_стало": len(result),
        "пустых_значений": {column: int(result[column].isna().sum()) for column in mapping},
    }
    return result.reset_index(drop=True), report
