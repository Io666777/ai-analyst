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

FIGURE_SIZE = (10, 4.5)  # ширина и высота рисунка в дюймах
LINE_COLOR = "#2a6fdb"
MAX_POINTS_WITH_MARKERS = 40  # если точек больше - рисуем линию без кружков

# Подпись оси по полю модели. Для дополнительных полей подписью будет их название
VALUE_LABELS = {"amount": "Выручка, р.", "quantity": "Количество, шт."}

MONTHS_SHORT = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]


def format_number(value: float, _position: int | None = None) -> str:
    # 150000 -> "150 000". Второй параметр нужен matplotlib, мы его не используем
    return f"{value:,.0f}".replace(",", " ")


def format_month(value: float, _position: int | None = None) -> str:
    # Дата на оси -> "мар 25". matplotlib хранит даты числами, mdates переводит обратно
    date = mdates.num2date(value)
    return f"{MONTHS_SHORT[date.month - 1]} {date:%y}"


def new_axes() -> tuple[Figure, Axes]:
    # Пустой рисунок в общем стиле: лёгкая сетка, без верхней и правой рамки
    figure = Figure(figsize=FIGURE_SIZE, layout="constrained")
    axes = figure.subplots()
    axes.grid(alpha=0.3)
    axes.spines[["top", "right"]].set_visible(False)
    axes.yaxis.set_major_formatter(FuncFormatter(format_number))
    return figure, axes


def line_chart(series: pd.Series, title: str) -> Figure:
    # Динамика по периодам: результат by_period или "динамика" из item_detail
    figure, axes = new_axes()
    marker = "o" if len(series) <= MAX_POINTS_WITH_MARKERS else None
    axes.plot(series.index, series.to_numpy(), color=LINE_COLOR, marker=marker)

    axes.set_title(title, loc="left", fontweight="bold")
    axes.set_ylabel(VALUE_LABELS.get(str(series.name), str(series.name)))
    axes.set_ylim(bottom=0)  # ось с нуля, иначе небольшие колебания выглядят как обвал
    axes.xaxis.set_major_formatter(FuncFormatter(format_month))
    return figure
