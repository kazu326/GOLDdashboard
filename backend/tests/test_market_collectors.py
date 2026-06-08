import pytest
from types import SimpleNamespace

from app.collectors.market import AlphaVantageGoldAdapter, FmpQuoteAdapter, FredSeriesAdapter, adapter_groups


def test_fred_series_assignments():
    groups = adapter_groups()
    real_rate = groups["real_rate"][0]
    nominal_rate = groups["nominal_rate"][0]
    inflation_expectation = groups["inflation_expectation"][0]
    vix = groups["vix"][0]
    assert isinstance(real_rate, FredSeriesAdapter)
    assert isinstance(nominal_rate, FredSeriesAdapter)
    assert isinstance(inflation_expectation, FredSeriesAdapter)
    assert isinstance(vix, FredSeriesAdapter)
    assert real_rate.series_id == "DFII10"
    assert nominal_rate.series_id == "DGS10"
    assert inflation_expectation.series_id == "T10YIE"
    assert vix.series_id == "VIXCLS"
    assert isinstance(groups["sp500"][0], FmpQuoteAdapter)
    assert isinstance(groups["sp500"][1], FmpQuoteAdapter)
    assert groups["sp500"][0].symbol == "^GSPC"
    assert groups["sp500"][1].symbol == "SPY"


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
