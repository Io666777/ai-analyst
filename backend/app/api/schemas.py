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
        description="Предложенная разметка: у своего файла - угадана правилами, "
        "у тестового примера - эталон",
        examples=[{"Дата чека": "date", "Выручка, руб": "amount"}],
    )
    confidence: dict[str, float] | None = Field(
        default=None,
        description="Уверенность в роли каждой колонки, 0-1: ниже 0.7 - попросить проверить. "
        "У примеров нет: эталон проверен",
        examples=[{"Дата чека": 0.9, "Выручка, руб": 0.4}],
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


class Daily(BaseModel):
    # Выручка по дням периода - для таблицы «месяц по дням»
    currency: str
    date_from: date
    date_to: date
    total: float = Field(description="Выручка за весь период")
    days: list[SeriesPoint] = Field(description="Каждый день периода; без продаж - 0")


# ---------- анализ: топ ----------


class TopRow(BaseModel):
    name: str = Field(examples=["Пиво Лидское 0.5"])
    value: float = Field(description="Выручка", examples=[137130.0])
    share_percent: float = Field(description="Доля от всей выручки, %", examples=[27.5])


class Top(BaseModel):
    by: str = Field(description="По какому полю построен топ", examples=["object"])
    by_label: str = Field(examples=["товар или услуга"])
    worst: bool = Field(description="true - худшие, false - лучшие")
    currency: str
    date_from: date = Field(description="Период топа: с (если не задан - начало данных)")
    date_to: date = Field(description="Период топа: по, включительно")
    total: float = Field(description="Вся выручка за период - от неё считается доля")
    available: list[Choice] = Field(description="По каким полям можно строить топ")
    rows: list[TopRow]


# ---------- анализ: товар ----------


class Catalog(BaseModel):
    # Все товары - для списка под поиском: фильтруется на фронте по мере ввода
    currency: str
    total: int = Field(description="Сколько товаров всего")
    items: list[TopRow] = Field(
        description="Товары от самых продаваемых; не больше 5000 - дальше список не листают"
    )


class ItemsFound(BaseModel):
    # Подсказки при вводе названия
    query: str = Field(examples=["пиво"])
    items: list[str] = Field(examples=[["Пиво Аливария 0.5", "Пиво Лидское 0.5"]])
    total: int = Field(description="Сколько нашлось всего (в items - не больше 20)")


class ItemDetail(BaseModel):
    # Всё о товаре или о нескольких товарах вместе
    name: str = Field(
        description="Название, а для нескольких товаров - запрос и их число",
        examples=["Пиво Лидское 0.5"],
    )
    items: list[str] = Field(description="Какие товары вошли")
    currency: str
    first_sale: date
    last_sale: date
    amount: float = Field(description="Выручка за весь период")
    share_percent: float = Field(description="Доля от всей выручки, %")
    quantity: float | None = Field(description="Продано штук - если в данных есть количество")
    monthly: list[SeriesPoint] = Field(
        description="Выручка по полным месяцам всех данных; месяц без продаж - 0"
    )
    last_month: MonthSummary | None = Field(
        description="Последний полный месяц против прошлого; нет - если полных месяцев меньше двух"
    )


class ItemDay(BaseModel):
    # День продаж товара - строка таблицы «месяц товара»
    period: str = Field(examples=["2026-09-15"])
    amount: float = Field(description="Выручка товара за день")
    quantity: float | None = Field(description="Продано штук; нет - если количества нет в данных")
    executors: list[str] = Field(
        description="Кто продавал - от продавшего больше; пусто, если сотрудника нет в данных"
    )


class ItemDays(BaseModel):
    # Товар по дням периода
    name: str
    currency: str
    date_from: date
    date_to: date
    total: float = Field(description="Выручка товара за период")
    quantity: float | None = Field(description="Продано штук за период")
    has_executors: bool = Field(description="Есть ли в данных сотрудники - показывать ли колонку")
    days: list[ItemDay] = Field(description="Каждый день периода; без продаж - нули")


# ---------- анализ: сравнение периодов ----------


class PeriodTotal(BaseModel):
    date_from: date
    date_to: date
    days: int = Field(description="Дней в периоде, включая оба края")
    value: float = Field(description="Выручка за период")
    per_day: float = Field(description="В среднем за день")


class CompareRow(BaseModel):
    # Товар в сравнении: было, стало и разница
    name: str = Field(examples=["Пиво Лидское 0.5"])
    first: float = Field(description="Выручка в первом периоде (было)")
    second: float = Field(description="Выручка во втором периоде (стало)")
    change: float = Field(description="Стало минус было")
    change_percent: float | None = Field(description="Изменение в %; нет - если было 0")


class Comparison(BaseModel):
    currency: str
    first: PeriodTotal = Field(description="Было - первый период")
    second: PeriodTotal = Field(description="Стало - второй период")
    change: float = Field(description="Изменение в деньгах")
    change_percent: float | None = Field(description="Изменение в %; нет - если было 0")
    per_day_change_percent: float | None = Field(
        description="Изменение в среднем за день, % - честнее, если периоды разной длины"
    )
    warnings: list[str] = Field(
        description="Например: период выходит за пределы данных - сравнение может быть неверным"
    )
    by_label: str | None = Field(
        default=None, description="По чему разбивка rows; нет - товара в данных нет"
    )
    rows: list[CompareRow] = Field(
        default_factory=list,
        description="Было и стало по товарам: самые заметные, с наибольшей выручкой",
    )


# ---------- анализ: прогноз ----------


class ForecastPoint(BaseModel):
    # День прогноза: значение и коридор (в 8 случаях из 10 реальность внутри)
    period: str = Field(examples=["2026-10-01"])
    value: float
    lower: float | None = Field(description="Нижняя граница коридора; нет - у простого прогноза")
    upper: float | None = Field(description="Верхняя граница коридора")


class Accuracy(BaseModel):
    # Насколько верить прогнозу - по экзамену на прошлом
    level: str = Field(examples=["высокая"])
    error_percent: float = Field(description="Ошибка по дням в % (WAPE)", examples=[8.0])
    summary: str = Field(description="Вывод словами")
    reasons: list[str] = Field(description="Почему такая точность - вычислено из данных")


class ForecastPeriod(BaseModel):
    # Прогноз за неделю или месяц - строка таблицы «сколько ждать»
    date_from: date = Field(description="С какого дня (крайние периоды бывают неполными)")
    date_to: date
    value: float = Field(description="Ожидаемая выручка за период")
    lower: float | None = Field(description="Нижняя граница коридора; нет - у простого прогноза")
    upper: float | None = None


class YearAgo(BaseModel):
    # Тот же период год назад (52 недели - дни недели совпадают)
    date_from: date
    date_to: date
    value: float = Field(description="Выручка тогда")
    change_percent: float | None = Field(description="Прогноз против тогда, %; нет - было 0")


class ModelScore(BaseModel):
    # Экзамен модели на прошлом - на том же горизонте, что и прогноз
    model: str = Field(examples=["Prophet"])
    error_percent: float = Field(description="Ошибка по дням, % (WAPE)")
    total_error_percent: float = Field(description="Ошибка итога за период, % (+ завысила)")
    chosen: bool = Field(description="Эта модель выбрана для прогноза")


class Estimate(BaseModel):
    # Ступенька "оценка": простые средние вместо прогноза
    per_day: float = Field(description="В среднем в день за последние 2 недели")
    by_weekday: dict[str, float] = Field(examples=[{"пн": 520.0, "сб": 910.0}])
    projection: float = Field(description="Если так пойдёт дальше - за 30 дней")


class Forecast(BaseModel):
    step: str = Field(
        description="none - мало данных (меньше недели), estimate - простые средние, "
        "forecast - прогноз с проверенной точностью",
        examples=["forecast"],
    )
    message: str = Field(description="Итог словами - показать пользователю как есть")
    currency: str
    history_days: int = Field(description="Сколько дней истории")
    model: str | None = Field(default=None, examples=["Prophet"])
    horizon_days: int | None = Field(default=None, description="На сколько дней вперёд")
    total: float | None = Field(default=None, description="Итог прогноза за весь горизонт")
    corridor: tuple[float, float] | None = Field(default=None, description="Коридор итога")
    accuracy: Accuracy | None = None
    history: list[SeriesPoint] = Field(
        default_factory=list, description="Конец истории по дням - для графика «факт + прогноз»"
    )
    points: list[ForecastPoint] = Field(default_factory=list, description="Прогноз по дням")
    weeks: list[ForecastPeriod] = Field(default_factory=list, description="Прогноз по неделям")
    months: list[ForecastPeriod] = Field(default_factory=list, description="Прогноз по месяцам")
    year_ago: YearAgo | None = Field(
        default=None, description="Тот же период год назад; нет - истории меньше года"
    )
    models: list[ModelScore] = Field(
        default_factory=list, description="Экзамен моделей: лучшая (выбранная) - первой"
    )
    estimate: Estimate | None = None
