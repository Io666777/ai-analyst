"""Универсальная модель данных: таблица любого бизнеса -> одинаковые колонки."""

import pandas as pd

# Типы событий
KIND_SALE = "sale"  # продажа
KIND_PURCHASE = "purchase"  # закупка
KIND_STOCK = "stock"  # остаток на складе

# Основные поля: у каждого особый смысл и своя логика в аналитике.
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

# Дополнительные поля - любые другие колонки. Сохраняются под своим названием:
# признак - текст, по нему группируют, фильтруют и ищут (артикул, бренд, филиал)
# показатель - число, его складывают (скидка, себестоимость)
ROLE_ATTRIBUTE = "attribute"
ROLE_MEASURE = "measure"
EXTRA_ROLES = (ROLE_ATTRIBUTE, ROLE_MEASURE)

# Колонки модели: все основные поля + тип события. Дополнительные идут после них
EVENT_COLUMNS = [*FIELDS, "kind"]

# Роль колонки = название основного поля. Роли person, phone, email, ignore в модель не попадают


def to_events(df: pd.DataFrame, mapping: dict[str, str], kind: str = KIND_SALE) -> pd.DataFrame:
    # Очищенная таблица -> события: основные поля (EVENT_COLUMNS) + дополнительные
    roles = [role for role in mapping.values() if role in FIELDS]
    if "date" not in roles:
        raise ValueError("Не указана колонка с датой")
    duplicated = sorted({role for role in roles if roles.count(role) > 1})
    if duplicated:
        raise ValueError(f"Одна роль назначена нескольким колонкам: {', '.join(duplicated)}")

    extras = [column for column, role in mapping.items() if role in EXTRA_ROLES]
    clashes = [column for column in extras if column in EVENT_COLUMNS]
    if clashes:
        raise ValueError(f"Название совпадает с основным полем: {', '.join(clashes)}")

    # {"Дата чека": "date", "Выручка, руб": "amount", ...} - старое название -> новое
    renames = {column: role for column, role in mapping.items() if role in FIELDS}
    events = df[list(renames)].rename(columns=renames)  # берём нужные колонки и переименовываем
    events["kind"] = kind
    # reindex - ставит колонки в стандартном порядке; каких нет - появятся пустыми
    events = events.reindex(columns=EVENT_COLUMNS)
    events[extras] = df[extras]  # дополнительные поля - под своими названиями, в конце
    return events


def extra_fields(events: pd.DataFrame) -> list[str]:
    # Дополнительные поля: все колонки, которых нет среди основных
    return [column for column in events.columns if column not in EVENT_COLUMNS]


def available_fields(events: pd.DataFrame) -> list[str]:
    # Какие поля реально заполнены у этого бизнеса (хотя бы одно значение):
    # сначала основные из каталога, потом дополнительные
    fields = [field for field in FIELDS if field in events] + extra_fields(events)
    return [field for field in fields if events[field].notna().any()]


def numeric_fields(events: pd.DataFrame) -> list[str]:
    # Заполненные числовые поля - их можно складывать (выручка, количество, скидка...)
    return [
        field
        for field in available_fields(events)
        if field != "date" and pd.api.types.is_numeric_dtype(events[field])
    ]
