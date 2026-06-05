from app import db
from app.schemas import NormalizedData
from app.services import current_dashboard


def _offline_market_data(_conn):
    return [
        NormalizedData("us10y", "米10年金利", None, "", "2026-01-01", "test", "https://example.com/us10y", "unknown"),
        NormalizedData("dollar_index", "代替ドル指数", None, "", "2026-01-01", "test", "https://example.com/dxy", "unknown"),
        NormalizedData("vix", "VIX", None, "", "2026-01-01", "test", "https://example.com/vix", "unknown"),
        NormalizedData("gold", "GOLD価格", None, "", "2026-01-01", "test", "https://example.com/gold", "unknown"),
        NormalizedData("sp500", "S&P500", None, "", "2026-01-01", "test", "https://example.com/sp500", "unknown"),
    ]


def test_dashboard_payload_shape_without_api_keys(monkeypatch):
    monkeypatch.setattr("app.services.collect_market_data", _offline_market_data)
    conn = db.connect(":memory:")
    try:
        payload = current_dashboard(conn)
        assert payload["summary"]["overall_status"] in {"green", "yellow", "red", "unknown"}
        assert len(payload["indicators"]) == 5
        assert payload["economic_events"]
        assert payload["geo_news"]
        assert all(item["status"] == "unknown" for item in payload["indicators"])
    finally:
        conn.close()
