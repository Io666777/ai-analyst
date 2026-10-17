"""Общие настройки проекта: пути к данным и параметры анализа."""

from pathlib import Path

# Пути
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
REAL_DIR = DATA_DIR / "real"

# Прогноз
MIN_HISTORY_DAYS = 30  # меньше - прогноз не строим, честно пишем "мало данных"
FORECAST_DAYS = 30  # на сколько дней вперёд прогнозируем
TEST_DAYS = 30  # сколько последних дней откладываем для проверки точности

# Воспроизводимость результатов (генерация тестовых данных, выборки)
RANDOM_SEED = 42
