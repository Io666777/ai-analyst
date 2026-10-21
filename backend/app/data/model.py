"""Универсальная модель данных: таблица любого бизнеса -> одинаковые колонки."""

import re

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
    "price": "цена за единицу",
    "receipt": "номер чека или документа",
    "executor": "мастер, продавец, сотрудник",
}

# Поля, которые нельзя складывать: сумма цен за месяц ничего не значит
NOT_ADDITIVE = ("price",)

# Дополнительные поля - любые другие колонки. Сохраняются под своим названием:
# признак - текст, по нему группируют, фильтруют и ищут (артикул, бренд, филиал)
# показатель - число, его складывают (скидка, себестоимость)
ROLE_ATTRIBUTE = "attribute"
ROLE_MEASURE = "measure"
EXTRA_ROLES = (ROLE_ATTRIBUTE, ROLE_MEASURE)

# Колонки модели: все основные поля + тип события. Дополнительные идут после них
EVENT_COLUMNS = [*FIELDS, "kind"]

# Слова, по которым узнаём служебные строки среди "товаров": доставка, комиссии, корректировки.
# Их программа только ПРЕДЛАГАЕТ исключить - решает пользователь
SERVICE_WORDS = (
    "доставка", "комиссия", "корректировка", "скидка", "услуги банка",
    "postage", "carriage", "manual", "fee", "adjust", "bank charges", "commission",
    "discount", "samples",
)  # fmt: skip
# \b - граница слова: "fee" найдёт "AMAZON FEE", но не "COFFEE"
SERVICE_PATTERN = re.compile(r"\b(" + "|".join(map(re.escape, SERVICE_WORDS)) + r")\b", re.I)

# Роль колонки = название основного поля. Роли person, phone, email, ignore в модель не попадают

# Роли для разметки колонок в интерфейсах: (роль, как её показать пользователю)
ROLE_CHOICES = [
    ("date", "дата"),
    ("object", "товар / услуга"),
    ("category", "категория"),
    ("quantity", "количество"),
    ("amount", "сумма, деньги"),
    ("price", "цена за единицу (если суммы нет - посчитается сама)"),
    ("executor", "сотрудник"),
    ("receipt", "номер чека"),
    (ROLE_ATTRIBUTE, "другой признак (текст: артикул, бренд...)"),
    (ROLE_MEASURE, "другое число (скидка...)"),
    ("person", "клиент (в анализ не попадёт)"),
]
ROLE_IGNORE = "ignore"  # колонка не нужна


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
    # В выгрузке нет суммы, но есть цена и количество - считаем сумму сами.
    # Так бывает часто: отчёты "по позициям" из 1С, интернет-магазинов
    if "amount" not in roles and {"price", "quantity"} <= set(roles):
        events["amount"] = events["price"] * events["quantity"]
    # reindex - ставит колонки в стандартном порядке; каких нет - появятся пустыми
    events = events.reindex(columns=EVENT_COLUMNS)
    events[extras] = df[extras]  # дополнительные поля - под своими названиями, в конце
    return events


def suggest_exclusions(events: pd.DataFrame) -> list[str]:
    # Товары, похожие на служебные строки (доставка, комиссия...) - кандидаты на исключение
    names = events["object"].dropna().unique()
    return sorted(str(name) for name in names if SERVICE_PATTERN.search(str(name)))


def exclude_objects(events: pd.DataFrame, names: list[str]) -> tuple[pd.DataFrame, dict]:
    # Убирает из событий указанные товары (без учёта регистра) и отчитывается, что убрано
    lowered = {name.strip().lower() for name in names}
    excluded = events["object"].str.lower().isin(lowered).fillna(False).to_numpy(dtype=bool)
    report = {
        "исключено_строк": int(excluded.sum()),
        "исключено_на_сумму": round(float(events.loc[excluded, "amount"].sum()), 2),
        "исключены": sorted(events.loc[excluded, "object"].dropna().unique().tolist()),
    }
    return events[~excluded].reset_index(drop=True), report


def extra_fields(events: pd.DataFrame) -> list[str]:
    # Дополнительные поля: все колонки, которых нет среди основных
    return [column for column in events.columns if column not in EVENT_COLUMNS]


def available_fields(events: pd.DataFrame) -> list[str]:
    # Какие поля реально заполнены у этого бизнеса (хотя бы одно значение):
    # сначала основные из каталога, потом дополнительные
    fields = [field for field in FIELDS if field in events] + extra_fields(events)
    return [field for field in fields if events[field].notna().any()]


def numeric_fields(events: pd.DataFrame) -> list[str]:
    # Заполненные числовые поля, которые можно складывать (выручка, количество, скидка...)
    return [
        field
        for field in available_fields(events)
        if field != "date"
        and field not in NOT_ADDITIVE
        and pd.api.types.is_numeric_dtype(events[field])
    ]


def require_field(events: pd.DataFrame, field: str, numeric: bool = False) -> None:
    # Проверка перед расчётом: поле есть в данных, а если нужно складывать - оно числовое
    if field not in available_fields(events):
        raise ValueError(f"В данных нет поля «{field}»")
    if numeric and field not in numeric_fields(events):
        raise ValueError(f"Поле «{field}» не числовое - его нельзя складывать")
