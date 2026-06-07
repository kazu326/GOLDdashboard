from __future__ import annotations

import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app import db
from app.config import settings


def build_discord_payload(snapshot: dict) -> dict:
    summary = snapshot["summary"]
    mode = summary["market_mode"]
    indicator_lines = [
        f"{item['label']}: {item['signal_label']} / {item['value_text']} / {item['change_text']}"
        for item in snapshot.get("indicators", [])
    ]
    warnings = "\n".join(summary["warning_signals"]) or "なし"
    return {
        "username": "GOLD Market Brief",
        "embeds": [
            {
                "title": f"GOLD市場モード: {mode['label']}",
                "description": "\n".join(indicator_lines),
                "url": settings.dashboard_public_url,
                "fields": [
                    {"name": "主要因", "value": summary["primary_factor"], "inline": False},
                    {"name": "警戒シグナル", "value": warnings, "inline": False},
                    {"name": "ダッシュボード", "value": settings.dashboard_public_url, "inline": False},
                ],
                "footer": {"text": "売買シグナルではなく、市場環境の整理です。"},
            }
        ],
    }


def send_discord_summary(conn, snapshot: dict) -> dict:
    payload = build_discord_payload(snapshot)
    snapshot_id = snapshot.get("snapshot_id")
    if not settings.discord_webhook_url:
        db.log_discord(conn, "skipped", payload, snapshot_id=snapshot_id, error_message="DISCORD_WEBHOOK_URL is not set")
        return {"status": "skipped", "reason": "DISCORD_WEBHOOK_URL is not set"}

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        settings.discord_webhook_url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "GOLDdashboard/0.2"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=12) as response:
                code = response.getcode()
                db.log_discord(conn, "sent", payload, snapshot_id=snapshot_id, response_code=code)
                return {"status": "sent", "response_code": code}
        except HTTPError as exc:
            if exc.code == 429 and attempt < 2:
                time.sleep(float(exc.headers.get("Retry-After", "1")))
                continue
            db.log_discord(conn, "error", payload, snapshot_id=snapshot_id, response_code=exc.code, error_message=str(exc))
            return {"status": "error", "response_code": exc.code, "error": str(exc)}
        except URLError as exc:
            if attempt < 2:
                time.sleep(1 + attempt)
                continue
            db.log_discord(conn, "error", payload, snapshot_id=snapshot_id, error_message=str(exc))
            return {"status": "error", "error": str(exc)}
    return {"status": "error", "error": "unreachable"}
