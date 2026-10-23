"""Ручки настройки: справочник, разметка колонок, настройки анализа."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentSession, PreparedSession
from app.api.schemas import (
    Choice,
    MappingRequest,
    Options,
    PreparationReport,
    PreparedData,
    SettingsApplied,
    SettingsRequest,
)
from app.config import CURRENCY
from app.data import (
    ROLE_CHOICES,
    ROLE_IGNORE,
    available_fields,
    exclude_objects,
    prepare_table,
    suggest_exclusions,
)
from app.forecast import COUNTRY, COUNTRY_NAMES

router = APIRouter(tags=["настройка"])

ROLE_LABELS = {**dict(ROLE_CHOICES), ROLE_IGNORE: "не нужна"}
NO_AMOUNT = "Нужна колонка с суммой - или цена и количество, тогда сумма посчитается сама"


@router.get("/options", summary="Справочник: роли колонок, страны")
def get_options() -> Options:
    """Из чего выбирают при разметке и настройке - фронт не держит эти списки у себя."""
    return Options(
        roles=[Choice(value=value, label=label) for value, label in ROLE_LABELS.items()],
        countries=[Choice(value=code, label=name) for code, name in COUNTRY_NAMES.items()],
        default_country=COUNTRY,
        default_currency=CURRENCY,
    )


@router.put("/session/mapping", summary="Разметить колонки")
def set_mapping(request: MappingRequest, session: CurrentSession) -> PreparedData:
    """Роли колонок -> очистка -> события. Прежние настройки и посчитанное сбрасываются."""
    unknown = sorted({role for role in request.mapping.values() if role not in ROLE_LABELS})
    if unknown:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Неизвестные роли: {', '.join(unknown)}")
    try:
        events, report = prepare_table(session.table, request.mapping)
    except ValueError as error:  # нет колонки в файле, нет даты, одна роль у двух колонок...
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None
    if events.empty:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "После очистки не осталось ни одной строки"
        )
    if "amount" not in available_fields(events):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, NO_AMOUNT)

    session.mapping = request.mapping
    session.prepared = session.events = events
    session.report = report
    session.exclude = []
    session.cache.clear()  # посчитанное по старой разметке больше неверно

    return PreparedData(
        report=PreparationReport(
            rows_before=report["строк_было"],
            removed_totals_and_empty=report["удалено_итоговых_и_пустых"],
            removed_without_date=report["удалено_без_даты"],
            rows_after=report["строк_стало"],
            empty_values=report["пустых_значений"],
        ),
        fields=report["поля"],
        date_from=events["date"].min().date(),
        date_to=events["date"].max().date(),
        suggested_exclusions=suggest_exclusions(events),
    )


@router.put("/session/settings", summary="Настройки анализа")
def set_settings(request: SettingsRequest, session: PreparedSession) -> SettingsApplied:
    """Служебные строки, которые не учитывать, валюта и страна праздников для прогноза."""
    country = request.country.upper()
    if country not in COUNTRY_NAMES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Нет праздников для страны «{request.country}». Есть: {', '.join(COUNTRY_NAMES)}",
        )
    events, excluded = exclude_objects(session.prepared, request.exclude)

    session.events = events
    session.exclude = request.exclude
    session.currency = request.currency.strip()
    session.country = country
    session.cache.clear()  # прогноз при других настройках получится другим

    return SettingsApplied(
        exclude=session.exclude,
        currency=session.currency,
        country=session.country,
        excluded_rows=excluded["исключено_строк"],
        excluded_amount=excluded["исключено_на_сумму"],
    )
