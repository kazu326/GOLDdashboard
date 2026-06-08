from datetime import date

from app.freshness import assess_freshness
from app.schemas import NormalizedData


def _item(as_of: str, value: float | None = 10.0, change_pct: float | None = 1.0):
    return NormalizedData(
        indicator_key="sp500",
        label="S&P500",
        value=value,
        unit="",
        as_of=as_of,
        source_name="FRED SP500",
        source_url="https://fred.stlouisfed.org/series/SP500",
        quality="ok",
        change_pct=change_pct,
        source_series="SP500",
    )


def test_freshness_latest_business_day_is_fresh():
    item = assess_freshness(_item("2026-06-08"), today=date(2026, 6, 8))
    assert item.freshness_status == "fresh"
    assert item.used_in_market_mode is True


def test_freshness_one_business_day_old_is_caution():
    item = assess_freshness(_item("2026-06-05"), today=date(2026, 6, 8))
    assert item.freshness_status == "caution"
    assert item.used_in_market_mode is True


def test_freshness_two_business_days_old_is_stale_reference_only():
    item = assess_freshness(_item("2026-06-04"), today=date(2026, 6, 8))
    assert item.freshness_status == "stale"
    assert item.used_in_market_mode is False


def test_freshness_three_business_days_old_is_excluded():
    item = assess_freshness(_item("2026-06-03"), today=date(2026, 6, 8))
    assert item.freshness_status == "excluded"
    assert item.used_in_market_mode is False


def test_missing_value_or_change_is_excluded():
    assert assess_freshness(_item("2026-06-08", value=None), today=date(2026, 6, 8)).freshness_status == "excluded"
    assert assess_freshness(_item("2026-06-08", change_pct=None), today=date(2026, 6, 8)).freshness_status == "excluded"
