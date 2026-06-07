from fastapi.testclient import TestClient

from app.main import app


def _offline_dashboard(_conn):
    return {
        "schema_version": 2,
        "snapshot_id": 1,
        "updated_at_jst": "2026-01-01T07:00:00+09:00",
        "summary": {
            "gold_value_text": "データ不足",
            "gold_change_text": "前日比: データ不足",
            "market_mode": {"key": "unknown", "label": "データ不足", "description": "不足"},
            "primary_factor": "不足",
            "warning_signals": ["1指標がデータ不足"],
        },
        "indicators": [],
        "reference_links": [],
        "disclaimer": "売買シグナルではありません。",
    }


def test_health_endpoint():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_dashboard_endpoint_returns_v2_without_news(monkeypatch):
    monkeypatch.setattr("app.main.current_dashboard", _offline_dashboard)
    payload = TestClient(app).get("/api/dashboard/current").json()
    assert payload["schema_version"] == 2
    assert payload["summary"]["market_mode"]["key"] == "unknown"
    assert "economic_events" not in payload
    assert "geo_news" not in payload
