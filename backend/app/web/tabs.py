"""Вкладки страницы: обзор, топ, товар, сравнение периодов, прогноз."""

import pandas as pd
import streamlit as st

from app.analytics import (
    breakdown,
    by_period,
    compare_periods,
    incomplete_periods,
    item_detail,
    last_full_month_vs_previous,
)
from app.charts import bar_chart, forecast_chart, line_chart
from app.forecast import money, to_daily
from app.model import FIELDS, available_fields, numeric_fields
from app.pipeline import STEP_FORECAST, make_forecast
from app.web.memory import remembered

# Поля, по которым топ не строят: дата, цена за штуку, номер чека
NOT_GROUPED = ("date", "price", "receipt")


def percent_or_none(value: float | None, suffix: str = "") -> str | None:
    # Подпись изменения под крупной цифрой: "-7.6%". Нет процента (было 0) - нет подписи
    return f"{value}%{suffix}" if value is not None else None


def overview_tab(events: pd.DataFrame, report: dict, currency: str) -> None:
    try:
        month = last_full_month_vs_previous(events)
        columns = st.columns(3)
        columns[0].metric(
            f"Выручка: {month['месяц']}",
            f"{money(month['стало'])} {currency}",
            percent_or_none(month["изменение_%"], " к прошлому месяцу"),
        )
        columns[1].metric(
            "В среднем в день",
            f"{money(month['в_день_стало'])} {currency}",
            percent_or_none(month["изменение_в_день_%"]),
        )
        columns[2].metric(
            f"Выручка: {month['прошлый_месяц']}", f"{money(month['было'])} {currency}"
        )
    except ValueError as error:  # меньше двух полных месяцев
        st.info(str(error))

    monthly = by_period(events, "месяц", full_periods_only=True)
    st.pyplot(line_chart(monthly, "Выручка по месяцам", currency))
    skipped = incomplete_periods(events)
    if skipped:
        st.caption(f"Неполные месяцы не показаны: {', '.join(skipped)}")
    with st.expander("Как подготовлены данные"):
        st.json(report)


def top_tab(events: pd.DataFrame, currency: str) -> None:
    numeric = numeric_fields(events)
    fields = [f for f in available_fields(events) if f not in numeric and f not in NOT_GROUPED]
    left, middle, right = st.columns(3)
    by = left.selectbox("По чему", fields, format_func=lambda field: FIELDS.get(field, field))
    top = middle.slider("Сколько показать", 3, 30, 10)
    worst = right.toggle("Худшие вместо лучших")
    table = breakdown(events, by=by, top=top, worst=worst)
    title = f"{'Худшие' if worst else 'Топ'}: {FIELDS.get(by, by)}"
    st.pyplot(bar_chart(table, title, currency))
    st.dataframe(table)


def item_tab(events: pd.DataFrame, currency: str) -> None:
    left, right = st.columns([3, 1])
    query = left.text_input("Название, его часть или артикул")
    all_matches = right.toggle("Все подходящие вместе")
    if not query:
        return
    try:
        detail = item_detail(events, query, all_matches=all_matches)
    except ValueError as error:  # "не найдено" или "подходит несколько - уточните"
        st.warning(str(error))
        return
    st.subheader(detail["товар"])
    columns = st.columns(3)
    columns[0].metric("Выручка", f"{money(detail.get('выручка', 0))} {currency}")
    columns[1].metric("Доля выручки", f"{detail.get('доля_выручки_%', 0)}%")
    columns[2].metric("Количество", money(detail.get("количество", 0)))
    st.caption(
        f"Продажи с {detail['первая_продажа']:%d.%m.%Y} по {detail['последняя_продажа']:%d.%m.%Y}"
    )
    if not detail["динамика"].empty:
        st.pyplot(line_chart(detail["динамика"], f"{detail['товар']}: выручка", currency))
    if len(detail["позиции"]) > 1:
        st.write("Позиции:", ", ".join(detail["позиции"]))


def compare_tab(events: pd.DataFrame, currency: str) -> None:
    start, end = events["date"].min().date(), events["date"].max().date()
    left, right = st.columns(2)
    # Календарь выбора периода: пока выбрана только первая дата - ждём вторую
    first = left.date_input("Первый период", (start, end), min_value=start, max_value=end)
    second = right.date_input("Второй период", (start, end), min_value=start, max_value=end)
    if len(first) < 2 or len(second) < 2:
        st.info("Выберите в календаре начало и конец обоих периодов")
        return
    result = compare_periods(
        events,
        tuple(f"{day:%Y-%m-%d}" for day in first),
        tuple(f"{day:%Y-%m-%d}" for day in second),
    )
    columns = st.columns(3)
    columns[0].metric("Было", f"{money(result['было'])} {currency}")
    columns[1].metric("Стало", f"{money(result['стало'])} {currency}")
    columns[2].metric(
        "Изменение",
        f"{money(result['изменение'])} {currency}",
        percent_or_none(result["изменение_%"]),
    )
    for warning in result["предупреждения"]:
        st.warning(warning)


def forecast_tab(settings: tuple, events: pd.DataFrame, country: str, currency: str) -> None:
    # Прогноз считается несколько секунд (на большом файле - минуту), поэтому - по кнопке.
    # settings - разметка и исключения: поменялись - прогноз считается заново
    if st.button("Посчитать прогноз", type="primary"):
        st.session_state["forecast"] = True
    if not st.session_state.get("forecast"):
        st.caption("Программа проверит модели на прошлом и сама выберет, на сколько дней вперёд")
        return
    result = remembered(
        ("прогноз", *settings, country, currency),
        lambda: make_forecast(events, country=country, currency=currency),
        "Проверяю модели на прошлом и подбираю горизонт...",
    )
    st.write(result["сообщение"])
    if result["ступенька"] != STEP_FORECAST:
        return
    chart_title = f"Прогноз на {result['горизонт_дней']} дн. ({result['модель']})"
    st.pyplot(forecast_chart(to_daily(events), result["прогноз"], chart_title, currency=currency))
    st.markdown("**Почему такая точность:**")
    for reason in result["точность"]["причины"]:
        st.markdown(f"- {reason}")
