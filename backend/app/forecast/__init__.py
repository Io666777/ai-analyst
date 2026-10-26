"""Прогноз: модели, экзамен на прошлом, подбор горизонта, отчёт о точности.

Разложен по шагам:
    models     - модели: простой прогноз (точка отсчёта) и Prophet, ряд по дням
    evaluation - экзамен на прошлом: метрики ошибки, сравнение моделей
    horizon    - на сколько дней вперёд прогнозу можно верить
    report     - понятный пользователю отчёт о точности: можно ли верить и почему
    breakdown  - прогноз по неделям и месяцам, тот же период год назад
    auto       - всё сразу (make_forecast): ступенька холодного старта, модель, горизонт

Всё нужное собрано здесь, поэтому снаружи импорт короткий: from app.forecast import make_forecast
"""

from app.forecast.auto import (
    STEP_ESTIMATE,
    STEP_FORECAST,
    STEP_NONE,
    best_model,
    compare_at,
    make_forecast,
    simple_estimate,
)
from app.forecast.breakdown import YEAR_AGO_DAYS, forecast_by, year_ago
from app.forecast.evaluation import EVALUATION_WINDOWS, compare_models, evaluate, window_metrics
from app.forecast.horizon import (
    HORIZONS,
    MAX_ACCEPTABLE_TOTAL_ERROR,
    MAX_ACCEPTABLE_WAPE,
    choose_horizon,
    horizon_scan,
)
from app.forecast.models import (
    COUNTRY,
    INTERVAL_WIDTH,
    MODELS,
    WEEK_DAYS,
    YEAR_DAYS,
    Forecaster,
    models_for,
    naive_forecast,
    prophet_forecast,
    to_daily,
)
from app.forecast.report import (
    COUNTRY_NAMES,
    data_diagnostics,
    days_off,
    days_off_note,
    money,
    quality_level,
    quality_report,
    total_error_text,
)

__all__ = [
    "COUNTRY",
    "COUNTRY_NAMES",
    "EVALUATION_WINDOWS",
    "HORIZONS",
    "INTERVAL_WIDTH",
    "MAX_ACCEPTABLE_TOTAL_ERROR",
    "MAX_ACCEPTABLE_WAPE",
    "MODELS",
    "STEP_ESTIMATE",
    "STEP_FORECAST",
    "STEP_NONE",
    "WEEK_DAYS",
    "YEAR_AGO_DAYS",
    "YEAR_DAYS",
    "Forecaster",
    "best_model",
    "choose_horizon",
    "compare_at",
    "compare_models",
    "data_diagnostics",
    "days_off",
    "days_off_note",
    "evaluate",
    "forecast_by",
    "horizon_scan",
    "make_forecast",
    "models_for",
    "money",
    "naive_forecast",
    "prophet_forecast",
    "quality_level",
    "quality_report",
    "simple_estimate",
    "to_daily",
    "total_error_text",
    "window_metrics",
    "year_ago",
]
