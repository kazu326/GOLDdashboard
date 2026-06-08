from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings
from app.schemas import NormalizedData


FRESHNESS_LABELS = {
    "fresh": "最新",
    "caution": "古い可能性",
    "stale": "参考扱い",
    "excluded": "除外",
}

DAILY_MACRO_SERIES = {"DFII10", "DGS10", "T10YIE"}


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def latest_business_day(today: date | None = None) -> date:
    current = today or datetime.now(ZoneInfo(settings.timezone)).date()
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current


def business_days_between(start: date, end: date) -> int:
    if start >= end:
        return 0
    days = 0
    current = start
    while current < end:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days += 1
    return days


def assess_freshness(item: NormalizedData, today: date | None = None) -> NormalizedData:
    data_date = _parse_date(item.as_of)
    if item.is_unknown or item.value is None or item.change_pct is None or data_date is None:
        return replace(item, freshness_status="excluded", used_in_market_mode=False)

    age = business_days_between(data_date, latest_business_day(today))
    if age <= 0:
        return replace(item, freshness_status="fresh", used_in_market_mode=True)
    if age == 1:
        return replace(item, freshness_status="caution", used_in_market_mode=True)
    if age == 2:
        return replace(item, freshness_status="stale", used_in_market_mode=False)
    return replace(item, freshness_status="excluded", used_in_market_mode=False)


def usage_label(freshness_status: str, used_in_market_mode: bool) -> str:
    if used_in_market_mode:
        return "使用"
    if freshness_status == "stale":
        return "参考"
    return "除外"

