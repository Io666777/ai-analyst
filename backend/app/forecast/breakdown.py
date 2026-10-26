"""Прогноз крупнее, чем по дням: по неделям и месяцам, и сравнение с тем же периодом год назад."""

import pandas as pd

# Год назад - ровно 52 недели: понедельник сравнивается с понедельником.
# 365 дней сдвинули бы дни недели, и выходные «съехали» бы на будни
YEAR_AGO_DAYS = 364


def forecast_by(forecast: pd.DataFrame, period: str) -> pd.DataFrame:
    # Сумма прогноза (и коридора, если он есть) по неделям ("неделя") или месяцам ("месяц").
    # Крайние периоды неполные - у каждого честные даты "с" и "по", а не календарные границы
    dates = forecast["ds"]
    if period == "неделя":
        key = (dates - pd.to_timedelta(dates.dt.dayofweek, unit="D")).dt.normalize()  # понедельник
    elif period == "месяц":
        key = dates.dt.to_period("M")
    else:
        raise ValueError(f"Неизвестный период «{period}». Есть: неделя, месяц")

    columns = [column for column in ("yhat", "yhat_lower", "yhat_upper") if column in forecast]
    grouped = forecast.groupby(key)
    result = grouped[columns].sum().round(2)
    result["с"] = grouped["ds"].min().to_numpy()
    result["по"] = grouped["ds"].max().to_numpy()
    return result.reset_index(drop=True)


def year_ago(daily: pd.DataFrame, forecast: pd.DataFrame) -> dict | None:
    # Тот же период год назад: сколько было тогда и на сколько прогноз больше или меньше.
    # None - истории меньше года, сравнивать не с чем
    start = forecast["ds"].min() - pd.Timedelta(days=YEAR_AGO_DAYS)
    end = forecast["ds"].max() - pd.Timedelta(days=YEAR_AGO_DAYS)
    if start < daily["ds"].min():
        return None
    in_period = (daily["ds"] >= start) & (daily["ds"] <= end)
    before = float(daily.loc[in_period, "y"].sum())
    after = float(forecast["yhat"].sum())
    return {
        "с": start,
        "по": end,
        "было": round(before, 2),
        "изменение_%": round((after - before) / before * 100, 1) if before else None,
    }
