from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from app.config import settings
from app.schemas import NormalizedData


SCHEMA = """
CREATE TABLE IF NOT EXISTS market_data_points (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  indicator_key TEXT NOT NULL,
  label TEXT NOT NULL,
  value REAL,
  unit TEXT,
  as_of TEXT NOT NULL,
  source_name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  quality TEXT NOT NULL,
  change_abs REAL,
  change_pct REAL,
  comment TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_time_jst TEXT NOT NULL,
  overall_status TEXT NOT NULL,
  caution_level TEXT NOT NULL,
  headline TEXT NOT NULL,
  important_event_summary TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS indicator_statuses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id INTEGER NOT NULL,
  indicator_key TEXT NOT NULL,
  status TEXT NOT NULL,
  label TEXT NOT NULL,
  value_text TEXT NOT NULL,
  comment TEXT NOT NULL,
  reason TEXT NOT NULL,
  source_name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  FOREIGN KEY(snapshot_id) REFERENCES market_snapshots(id)
);

CREATE TABLE IF NOT EXISTS source_fetches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  status TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS reference_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  label TEXT NOT NULL,
  source_name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS economic_event_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  source_name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  note TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS geo_news_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  source_name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  note TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS discord_notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id INTEGER,
  scheduled_for_jst TEXT,
  sent_at TEXT,
  status TEXT NOT NULL,
  response_code INTEGER,
  error_message TEXT,
  payload_json TEXT,
  FOREIGN KEY(snapshot_id) REFERENCES market_snapshots(id)
);
"""


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or settings.sqlite_path
    if path not in (":memory:", ""):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def session(db_path: str | None = None) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def log_fetch(conn: sqlite3.Connection, provider: str, endpoint: str, status: str, error: str = "") -> None:
    conn.execute(
        """
        INSERT INTO source_fetches(provider, endpoint, status, fetched_at, error_message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (provider, endpoint, status, utc_now(), error),
    )


def insert_market_data(conn: sqlite3.Connection, item: NormalizedData) -> None:
    conn.execute(
        """
        INSERT INTO market_data_points(
          indicator_key, label, value, unit, as_of, source_name, source_url, quality,
          change_abs, change_pct, comment, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item.indicator_key,
            item.label,
            item.value,
            item.unit,
            item.as_of,
            item.source_name,
            item.source_url,
            item.quality,
            item.change_abs,
            item.change_pct,
            item.comment,
            utc_now(),
        ),
    )


def latest_market_data(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT * FROM market_data_points
        WHERE id IN (
          SELECT MAX(id) FROM market_data_points GROUP BY indicator_key
        )
        ORDER BY indicator_key
        """
    ).fetchall()
    return [dict(row) for row in rows]


def insert_static_links(conn: sqlite3.Connection) -> None:
    now = utc_now()
    conn.execute("DELETE FROM economic_event_links")
    conn.execute("DELETE FROM geo_news_links")
    conn.executemany(
        """
        INSERT INTO economic_event_links(title, source_name, source_url, note, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                "米重要経済指標カレンダー",
                "BEA Release Schedule",
                "https://www.bea.gov/news/schedule",
                "GDP、PCE、貿易統計など。必要に応じて原典確認。",
                now,
            ),
            (
                "雇用・物価関連リリース",
                "BLS Economic Releases",
                "https://www.bls.gov/schedule/news_release/",
                "CPI、雇用統計、PPIなど。Phase 1ではリンク確認を優先。",
                now,
            ),
            (
                "FOMC・Fed統計予定",
                "Federal Reserve",
                "https://www.federalreserve.gov/newsevents/calendar.htm",
                "FOMC、議長発言、Fed関連イベント確認用。",
                now,
            ),
        ],
    )
    conn.executemany(
        """
        INSERT INTO geo_news_links(title, source_name, source_url, note, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                "地政学・紛争ニュース",
                "ReliefWeb",
                "https://reliefweb.int/updates",
                "紛争・災害・人道関連の原典確認。",
                now,
            ),
            (
                "グローバルニュースイベント",
                "GDELT",
                "https://www.gdeltproject.org/",
                "世界ニュースイベントの確認。Phase 1ではリンク中心。",
                now,
            ),
            (
                "米制裁・財務省発表",
                "U.S. Treasury Press Releases",
                "https://home.treasury.gov/news/press-releases",
                "制裁・地政学リスク確認用。",
                now,
            ),
        ],
    )


def get_link_rows(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    if table not in {"economic_event_links", "geo_news_links"}:
        raise ValueError("Unsupported table")
    rows = conn.execute(f"SELECT title, source_name, source_url, note FROM {table} ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def insert_snapshot(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    indicator_rows: list[dict[str, Any]],
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO market_snapshots(
          snapshot_time_jst, overall_status, caution_level, headline,
          important_event_summary, payload_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["updated_at_jst"],
            payload["summary"]["overall_status"],
            payload["summary"]["caution_level"],
            payload["summary"]["headline"],
            payload["summary"]["important_event_summary"],
            json.dumps(payload, ensure_ascii=False),
            utc_now(),
        ),
    )
    if cursor.lastrowid is None:
        raise RuntimeError("Failed to create market snapshot")
    snapshot_id = int(cursor.lastrowid)
    for row in indicator_rows:
        conn.execute(
            """
            INSERT INTO indicator_statuses(
              snapshot_id, indicator_key, status, label, value_text, comment,
              reason, source_name, source_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                row["indicator_key"],
                row["status"],
                row["label"],
                row["value_text"],
                row["comment"],
                row["reason"],
                row["source_name"],
                row["source_url"],
            ),
        )
    return snapshot_id


def latest_snapshot(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM market_snapshots ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        return None
    payload = json.loads(row["payload_json"])
    payload["snapshot_id"] = row["id"]
    return payload


def log_discord(
    conn: sqlite3.Connection,
    status: str,
    payload: dict[str, Any],
    snapshot_id: int | None = None,
    response_code: int | None = None,
    error_message: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO discord_notifications(
          snapshot_id, scheduled_for_jst, sent_at, status, response_code,
          error_message, payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot_id,
            None,
            utc_now(),
            status,
            response_code,
            error_message,
            json.dumps(payload, ensure_ascii=False),
        ),
    )
