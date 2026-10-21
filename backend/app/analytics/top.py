"""Топы: лучшие и худшие товары, категории, сотрудники, бренды..."""

import pandas as pd

from app.model import require_field


def breakdown(
    events: pd.DataFrame,
    by: str = "object",
    value: str = "amount",
    top: int = 10,
    worst: bool = False,
) -> pd.DataFrame:
    # Топ по полю by (товар, категория, мастер, любой признак - бренд, филиал...):
    # сумма value и доля в общем итоге. worst=True - наоборот, худшие
    require_field(events, by)
    require_field(events, value, numeric=True)

    totals = events.groupby(by)[value].sum().sort_values(ascending=worst)
    share = totals / totals.sum() * 100  # доля от ВСЕГО итога, а не только от топа
    result = pd.DataFrame({value: totals.round(2), "доля_%": share.round(1)})
    return result.head(top)
