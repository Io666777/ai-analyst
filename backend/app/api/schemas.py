"""Модели запросов и ответов API: точная структура JSON для Swagger и типов TypeScript фронта.

Ключи - английские (удобно во фронте), тексты для человека - русские.
"""

from datetime import date

from pydantic import BaseModel, Field

from app.config import CURRENCY
from app.forecast import COUNTRY


class ColumnPreview(BaseModel):
    # Колонка файла: название и несколько значений - по ним человек понимает, что в ней
    name: str = Field(examples=["Дата чека"])
    examples: list[str] = Field(examples=[["01.10.24", "02.10.24", "03.10.24"]])


class FileOpened(BaseModel):
    # Ответ на загрузку файла или открытие примера
    session_id: str = Field(description="Номер сессии: присылать в заголовке X-Session-Id")
    file_name: str = Field(examples=["cafe.csv"])
    rows: int = Field(description="Строк в таблице (первый лист)", examples=[2921])
    columns: list[ColumnPreview]
    mapping: dict[str, str] | None = Field(
        default=None,
        description="Готовая разметка колонок - есть только у тестовых примеров",
        examples=[{"Дата чека": "date", "Выручка, руб": "amount"}],
    )


class ExampleInfo(BaseModel):
    # Тестовый бизнес, который можно открыть без своего файла
    name: str = Field(examples=["cafe.csv"])
    title: str = Field(examples=["Кафе: кофе, десерты, обеды - 2 года"])


# ---------- справочник ----------


class Choice(BaseModel):
    # Вариант для выпадающего списка: значение и как его показать человеку
    value: str = Field(examples=["date"])
    label: str = Field(examples=["дата"])


class Options(BaseModel):
    # Всё, из чего пользователь выбирает при настройке
    roles: list[Choice] = Field(description="Роли колонок для разметки")
    countries: list[Choice] = Field(description="Страны праздников для прогноза")
    default_country: str = Field(examples=["BY"])
    default_currency: str = Field(examples=["р."])


# ---------- разметка ----------


class MappingRequest(BaseModel):
    mapping: dict[str, str] = Field(
        description="Колонка файла -> роль из справочника (/api/options)",
        examples=[{"Дата чека": "date", "Позиция": "object", "Выручка, руб": "amount"}],
    )


class PreparationReport(BaseModel):
    # Что программа сделала с данными - человек видит, что ничего не потерялось молча
    rows_before: int = Field(description="Строк в файле")
    removed_totals_and_empty: int = Field(description="Удалено итоговых («Итого») и пустых строк")
    removed_without_date: int = Field(description="Удалено строк без даты")
    rows_after: int = Field(description="Строк после очистки")
    empty_values: dict[str, int] = Field(description="Пустых значений по колонкам")


class PreparedData(BaseModel):
    # Ответ на разметку: данные готовы к анализу
    report: PreparationReport
    fields: list[str] = Field(
        description="Поля, которые есть в данных: основные (date, object, amount...) "
        "и дополнительные под своими названиями",
        examples=[["date", "object", "category", "quantity", "amount"]],
    )
    date_from: date
    date_to: date
    suggested_exclusions: list[str] = Field(
        description="Похоже на служебные строки (доставка, комиссии) - решает пользователь",
        examples=[["Доставка курьером"]],
    )


# ---------- настройки ----------


class SettingsRequest(BaseModel):
    exclude: list[str] = Field(
        default_factory=list, description="Товары, которые не учитывать (служебные строки)"
    )
    currency: str = Field(default=CURRENCY, min_length=1, max_length=10, examples=["р."])
    country: str = Field(default=COUNTRY, description="Код страны праздников из /api/options")


class SettingsApplied(BaseModel):
    exclude: list[str]
    currency: str
    country: str
    excluded_rows: int = Field(description="Сколько строк убрано исключениями")
    excluded_amount: float = Field(description="На какую сумму")


# ---------- анализ: общее ----------


class SeriesPoint(BaseModel):
    # Точка графика: период и значение. Период - "2026-09" (месяц) или "2026-09-15" (день)
    period: str = Field(examples=["2026-09"])
    value: float = Field(examples=[18740.0])


# ---------- анализ: обзор ----------


class MonthSummary(BaseModel):
    # Последний полный месяц против предыдущего: "как прошёл месяц?"
    month: str = Field(examples=["сентябрь 2026"])
    previous_month: str = Field(examples=["август 2026"])
    before: float = Field(description="Выручка за прошлый месяц")
    after: float = Field(description="Выручка за последний полный месяц")
    change: float = Field(description="Изменение в деньгах")
    change_percent: float | None = Field(description="Изменение в %; нет - если было 0")
    per_day_before: float = Field(description="В среднем за день, прошлый месяц")
    per_day_after: float = Field(description="В среднем за день, последний месяц")
    per_day_change_percent: float | None = Field(
        description="Изменение в среднем за день, %: честнее, месяцы разной длины"
    )


class Overview(BaseModel):
    # Первый экран после разметки
    currency: str
    date_from: date
    date_to: date
    total: float = Field(description="Выручка за весь период (с учётом исключений)")
    last_month: MonthSummary | None = Field(
        description="Нет, если в данных меньше двух полных месяцев - тогда см. last_month_note"
    )
    last_month_note: str | None = Field(
        default=None, examples=["Мало данных: для сравнения нужно хотя бы два полных месяца"]
    )
    monthly: list[SeriesPoint] = Field(description="Выручка по полным месяцам - для графика")
    incomplete: list[str] = Field(
        description="Неполные месяцы, которых нет на графике",
        examples=[["декабрь 2011 (данные по 09.12.2011)"]],
    )
