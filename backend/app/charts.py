"""Графики: единый стиль, русские подписи, понятные числа.

Функции возвращают рисунок (Figure), а не показывают его. Дальше он:
в Jupyter показывается сам, в Streamlit - через st.pyplot(fig), для бота и курсовой -
сохраняется в PNG: fig.savefig("график.png").
"""

import matplotlib.dates as mdates
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

FIGURE_WIDTH = 10  # ширина рисунка в дюймах
FIGURE_HEIGHT = 4.5  # высота по умолчанию
LINE_COLOR = "#2a6fdb"
MAX_POINTS_WITH_MARKERS = 40  # если точек больше - рисуем линию без кружков

BAR_HEIGHT = 0.45  # сколько дюймов высоты рисунка на один столбец
MIN_BAR_FIGURE_HEIGHT = 2.5  # даже у топ-2 рисунок не ниже этого
BAR_LABEL_SPACE = 1.3  # запас справа под подписи на столбцах: ось длиннее самого длинного на 30%

FORECAST_COLOR = "#e8772e"  # прогноз - другим цветом, чтобы не спутать с фактом
CORRIDOR_ALPHA = 0.2  # прозрачность полосы коридора
HISTORY_PER_HORIZON = 2  # истории на графике вдвое больше, чем горизонт прогноза
MIN_HISTORY_SHOWN = 60  # но не меньше 60 дней

# Подпись оси по полю модели
VALUE_LABELS = {"amount": "Выручка, р.", "quantity": "Количество, шт."}

MONTHS_SHORT = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]


def format_number(value: float, _position: int | None = None) -> str:
    # 150000 -> "150 000". Второй параметр нужен matplotlib, мы его не используем
    return f"{value:,.0f}".replace(",", " ")


def format_month(value: float, _position: int | None = None) -> str:
    # Дата на оси -> "мар 25". matplotlib хранит даты числами, mdates переводит обратно
    date = mdates.num2date(value)
    return f"{MONTHS_SHORT[date.month - 1]} {date:%y}"


def value_label(field: str) -> str:
    # Подпись оси по полю: "amount" -> "Выручка, р.", дополнительное поле - его название
    return VALUE_LABELS.get(field, field)


def new_axes(title: str, height: float = FIGURE_HEIGHT) -> tuple[Figure, Axes]:
    # Пустой рисунок в общем стиле: заголовок слева, лёгкая сетка, без верхней и правой рамки
    figure = Figure(figsize=(FIGURE_WIDTH, height), layout="constrained")
    axes = figure.subplots()
    axes.set_title(title, loc="left", fontweight="bold")
    axes.grid(alpha=0.3)
    axes.spines[["top", "right"]].set_visible(False)
    return figure, axes


def line_chart(series: pd.Series, title: str) -> Figure:
    # Динамика по периодам: результат by_period или "динамика" из item_detail
    figure, axes = new_axes(title)
    marker = "o" if len(series) <= MAX_POINTS_WITH_MARKERS else None
    axes.plot(series.index, series.to_numpy(), color=LINE_COLOR, marker=marker)

    axes.set_ylabel(value_label(str(series.name)))
    axes.set_ylim(bottom=0)  # ось с нуля, иначе небольшие колебания выглядят как обвал
    axes.yaxis.set_major_formatter(FuncFormatter(format_number))
    axes.xaxis.set_major_formatter(FuncFormatter(format_month))
    return figure


def bar_chart(table: pd.DataFrame, title: str) -> Figure:
    # Топ из breakdown: горизонтальные столбцы, лидер сверху, на столбце - сумма и доля
    field = str(table.columns[0])  # первая колонка breakdown - то, что складывали
    values = table[field]
    height = max(MIN_BAR_FIGURE_HEIGHT, BAR_HEIGHT * len(table) + 1)
    figure, axes = new_axes(title, height)

    bars = axes.barh([str(name) for name in table.index], values, color=LINE_COLOR)
    axes.invert_yaxis()  # barh рисует первую строку снизу - переворачиваем, лидер сверху

    # Подписи на столбцах: "137 130 (27,5%)" - или только число, если долей нет
    if "доля_%" in table:
        labels = [
            f"{format_number(value)} ({share:.1f}%)".replace(".", ",")
            for value, share in zip(values, table["доля_%"])
        ]
    else:
        labels = [format_number(value) for value in values]
    axes.bar_label(bars, labels=labels, padding=4)

    axes.set_xlabel(value_label(field))
    axes.set_xlim(right=values.max() * BAR_LABEL_SPACE)  # место справа под подписи
    axes.xaxis.set_major_formatter(FuncFormatter(format_number))
    axes.grid(False, axis="y")  # горизонтальные линии сетки между столбцами не нужны
    return figure


def forecast_chart(
    daily: pd.DataFrame,
    forecast: pd.DataFrame,
    title: str,
    value: str = "amount",
) -> Figure:
    # Факт (конец истории) + прогноз + коридор + черта "сегодня" на стыке.
    # daily - ряд по дням (to_daily), forecast - прогноз (make_forecast()["прогноз"])
    figure, axes = new_axes(title)
    shown_days = max(MIN_HISTORY_SHOWN, HISTORY_PER_HORIZON * len(forecast))
    history = daily.tail(shown_days)  # вся история рядом с коротким прогнозом его "раздавит"

    axes.plot(history["ds"], history["y"], color=LINE_COLOR, label="факт")
    axes.plot(
        forecast["ds"], forecast["yhat"], color=FORECAST_COLOR, linestyle="--", label="прогноз"
    )
    if "yhat_lower" in forecast:  # коридор есть не у всех моделей
        axes.fill_between(
            forecast["ds"],
            forecast["yhat_lower"],
            forecast["yhat_upper"],
            color=FORECAST_COLOR,
            alpha=CORRIDOR_ALPHA,
            label="вероятный диапазон (80%)",
        )
    axes.axvline(history["ds"].iloc[-1], color="gray", linewidth=1)  # черта "сегодня"
    axes.text(history["ds"].iloc[-1], 0, " сегодня", color="gray", va="bottom")

    axes.set_ylabel(value_label(value))
    axes.set_ylim(bottom=0)
    axes.yaxis.set_major_formatter(FuncFormatter(format_number))
    # Отметки строго на 1-е число каждого месяца - иначе подпись "сен 26" повторяется дважды
    axes.xaxis.set_major_locator(mdates.MonthLocator())
    axes.xaxis.set_major_formatter(FuncFormatter(format_month))
    # Легенда под графиком в одну строку, чтобы не закрывать данные
    axes.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False)
    return figure
