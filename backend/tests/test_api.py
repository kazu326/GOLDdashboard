from fastapi.testclient import TestClient

from app.main import app


def _offline_dashboard(_conn):
    return {
        "snapshot_id": 1,
        "updated_at_jst": "2026-01-01T07:00:00+09:00",
        "summary": {
            "overall_status": "unknown",
            "overall_label": "要確認",
            "caution_level": "中",
            "headline": "GOLD環境を30秒で確認",
            "important_event_summary": "公式カレンダーを確認",
        },
        "indicators": [
            {
                "indicator_key": "gold",
                "label": "GOLD価格",
                "status": "unknown",
                "status_label": "要確認",
                "value_text": "要確認",
                "change_text": "前回比は要確認",
                "comment": "取得できませんでした。原典を確認してください。",
                "reason": "無料データを安定取得できなかったため、原典確認が必要です。",
                "source_name": "test",
                "source_url": "https://example.com",
                "as_of": "2026-01-01",
            }
        ],
        "economic_events": [],
        "geo_news": [],
        "reference_links": [],
        "disclaimer": "投資助言ではありません。",
    }


def test_health_endpoint():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}


def test_dashboard_endpoint_returns_json(monkeypatch):
    monkeypatch.setattr("app.main.current_dashboard", _offline_dashboard)
    client = TestClient(app)
    response = client.get("/api/dashboard/current")
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["overall_status"] == "unknown"
    assert payload["indicators"][0]["status_label"] == "要確認"
