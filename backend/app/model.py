"""Универсальная модель данных: таблица любого бизнеса -> одинаковые колонки."""

import pandas as pd

# Типы событий
KIND_SALE = "sale"  # продажа
KIND_PURCHASE = "purchase"  # закупка
KIND_STOCK = "stock"  # остаток на складе

# Каталог полей: всё, что программа умеет анализировать, с описаниями.
# Описания пригодятся в интерфейсе, в промте нейросети и в тексте курсовой
FIELDS = {
    "date": "дата и время события",
    "object": "товар или услуга",
    "category": "группа товаров или услуг",
    "quantity": "количество",
    "amount": "сумма в деньгах",
    "receipt": "номер чека или документа",
    "executor": "мастер, продавец, сотрудник",
}

# Колонки универсальной модели: все поля каталога + тип события
EVENT_COLUMNS = [*FIELDS, "kind"]

# Роль колонки = название поля модели. Роль из каталога FIELDS попадает в модель,
# остальные роли (person, phone, email, ignore) - нет


def to_events(df: pd.DataFrame, mapping: dict[str, str], kind: str = KIND_SALE) -> pd.DataFrame:
    # Очищенная таблица -> события универсальной модели (колонки EVENT_COLUMNS)
    roles = [role for role in mapping.values() if role in FIELDS]
    if "date" not in roles:
        raise ValueError("Не указана колонка с датой")
    duplicated = sorted({role for role in roles if roles.count(role) > 1})
    if duplicated:
        raise ValueError(f"Одна роль назначена нескольким колонкам: {', '.join(duplicated)}")

    # {"Дата чека": "date", "Выручка, руб": "amount", ...} - старое название -> новое
    renames = {column: role for column, role in mapping.items() if role in FIELDS}
    events = df[list(renames)].rename(columns=renames)  # берём нужные колонки и переименовываем
    events["kind"] = kind
    # reindex - ставит колонки в стандартном порядке; каких нет - появятся пустыми
    return events.reindex(columns=EVENT_COLUMNS)


def available_fields(events: pd.DataFrame) -> list[str]:
    # Какие поля каталога реально заполнены у этого бизнеса (хотя бы одно значение)
    return [field for field in FIELDS if field in events and events[field].notna().any()]
