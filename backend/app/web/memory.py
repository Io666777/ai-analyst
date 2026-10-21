"""Память сессии: тяжёлое считаем один раз, чужие данные не храним.

Streamlit при каждом клике выполняет страницу заново, сверху вниз. Чтобы файл не читался
и прогноз не считался при каждом клике, результаты запоминаются - в памяти сессии.
"""

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from app.loader import load


def remembered(key: tuple, compute: Callable[[], Any], message: str) -> Any:
    # Посчитать один раз и запомнить - как st.cache_data, но с важным отличием:
    # st.cache_data общий для ВСЕХ посетителей сервера, а эта память - у каждого своя
    # (st.session_state) и исчезает, когда посетитель закрывает вкладку
    cache = st.session_state.setdefault("cache", {})
    if key not in cache:
        with st.spinner(message):
            cache[key] = compute()
    return cache[key]


def forget_previous_file(file_id: str) -> None:
    # Открыли другой файл - всё запомненное о прежнем удаляем, а не копим в памяти
    if st.session_state.get("file_id") != file_id:
        st.session_state["file_id"] = file_id
        st.session_state["cache"] = {}
        st.session_state["forecast"] = False


def read_table(name: str, data: bytes) -> pd.DataFrame:
    # Файл -> таблица без сохранения на диск сервера. Функциям чтения нужен путь, поэтому
    # кладём файл во временную папку, читаем, и папка удаляется вместе с файлом
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / Path(name).name  # имя без чужих папок: "../x.csv" -> "x.csv"
        path.write_bytes(data)
        return next(iter(load(path).values()))  # первый лист
