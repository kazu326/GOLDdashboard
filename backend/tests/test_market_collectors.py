import pytest
from types import SimpleNamespace

from app.collectors.market import AlphaVantageGoldAdapter, FredSeriesAdapter, adapter_groups


def test_fred_series_assignments():
    groups = adapter_groups()
    assert isinstance(groups["real_rate"][0], FredSeriesAdapter)
    assert groups["real_rate"][0].series_id == "DFII10"
    assert groups["nominal_rate"][0].series_id == "DGS10"
    assert groups["inflation_expectation"][0].series_id == "T10YIE"
    assert groups["vix"][0].series_id == "VIXCLS"


def test_alpha_vantage_gold_uses_spot_and_daily_history(monkeypatch):
    monkeypatch.setattr("app.collectors.market.settings", SimpleNamespace(alpha_vantage_api_key="test"))
    responses = iter(
        [
            {"price": "3000", "timestamp": "2026-06-07T00:00:00Z"},
            {"data": [{"date": "2026-06-06", "close": "2970"}]},
        ]
    )
    monkeypatch.setattr("app.collectors.market.fetch_json", lambda _url: next(responses))
    item = AlphaVantageGoldAdapter().fetch()
    assert item.value == 3000
    assert item.change_abs == 30
    assert item.change_pct == pytest.approx(1.010101)
