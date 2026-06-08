import json

from app import db
from app.schemas import NormalizedData
from app.services import current_dashboard


KEYS = ("gold", "real_rate", "nominal_rate", "inflation_expectation", "dxy", "sp500", "vix")


def _offline_market_data(_conn):
    return [
        NormalizedData(key, key, None, "", "2026-01-01", "test", f"https://example.com/{key}", "unknown")
        for key in KEYS
    ]


def test_dashboard_payload_shape_without_api_keys(monkeypatch):
    monkeypatch.setattr("app.services.collect_market_data", _offline_market_data)
    conn = db.connect(":memory:")
    try:
        payload = current_dashboard(conn)
        assert payload["schema_version"] == 3
        assert len(payload["indicators"]) == 7
        assert all(item["signal"] == "unknown" for item in payload["indicators"])
        assert "economic_events" not in payload
        assert "geo_news" not in payload
    finally:
        conn.close()


def test_old_snapshot_is_refreshed(monkeypatch):
    monkeypatch.setattr("app.services.collect_market_data", _offline_market_data)
    conn = db.connect(":memory:")
    try:
        db.init_db(conn)
        old = {"summary": {"overall_status": "yellow"}, "indicators": []}
        conn.execute(
            """
            INSERT INTO market_snapshots(
              snapshot_time_jst, overall_status, caution_level, headline,
              important_event_summary, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("2026-01-01", "yellow", "中", "old", "old", json.dumps(old), db.utc_now()),
        )
        assert current_dashboard(conn)["schema_version"] == 3
    finally:
        conn.close()
