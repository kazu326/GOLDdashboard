from __future__ import annotations

from app import db
from app.collectors.market import collect_market_data
from app.freshness import assess_freshness
from app.scoring.engine import build_dashboard_payload


INDICATOR_KEYS = {"gold", "real_rate", "nominal_rate", "inflation_expectation", "dxy", "sp500", "vix"}


def refresh_dashboard(conn) -> dict:
    db.init_db(conn)
    market_items = collect_market_data(conn)
    for item in market_items:
        db.insert_market_data(conn, assess_freshness(item))
    market_rows = [row for row in db.latest_market_data(conn) if row["indicator_key"] in INDICATOR_KEYS]
    payload, indicator_rows = build_dashboard_payload(market_rows)
    snapshot_id = db.insert_snapshot(conn, payload, indicator_rows)
    payload["snapshot_id"] = snapshot_id
    return payload


def current_dashboard(conn) -> dict:
    db.init_db(conn)
    snapshot = db.latest_snapshot(conn)
    if snapshot and snapshot.get("schema_version") == 3:
        return snapshot
    return refresh_dashboard(conn)
