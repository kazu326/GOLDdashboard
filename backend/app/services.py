from __future__ import annotations

from app import db
from app.collectors.market import collect_market_data
from app.scoring.engine import build_dashboard_payload


def refresh_dashboard(conn) -> dict:
    db.init_db(conn)
    market_items = collect_market_data(conn)
    for item in market_items:
        db.insert_market_data(conn, item)
    db.insert_static_links(conn)
    market_rows = db.latest_market_data(conn)
    economic_links = db.get_link_rows(conn, "economic_event_links")
    geo_news_links = db.get_link_rows(conn, "geo_news_links")
    payload, indicator_rows = build_dashboard_payload(market_rows, economic_links, geo_news_links)
    snapshot_id = db.insert_snapshot(conn, payload, indicator_rows)
    payload["snapshot_id"] = snapshot_id
    return payload


def current_dashboard(conn) -> dict:
    db.init_db(conn)
    snapshot = db.latest_snapshot(conn)
    if snapshot:
        return snapshot
    return refresh_dashboard(conn)

