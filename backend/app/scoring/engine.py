from __future__ import annotations

from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings


STATUS_LABELS = {
    "green": "追い風",
    "yellow": "中立",
    "red": "注意",
    "unknown": "要確認",
}


def _fmt_value(value: float | None, unit: str) -> str:
    if value is None:
        return "要確認"
    if unit == "%":
        return f"{value:.2f}%"
    if unit == "USD/oz":
        return f"${value:,.2f}"
    if unit == "index":
        return f"{value:.2f}"
    return f"{value:,.2f}"


def _fmt_change(change_abs: float | None, change_pct: float | None, unit: str) -> str:
    if change_abs is None and change_pct is None:
        return "前回比は要確認"
    if unit == "%":
        return f"前回比 {change_abs:+.2f}pt"
    if change_pct is not None:
        return f"前回比 {change_pct:+.2f}%"
    return f"前回比 {change_abs:+.2f}"


def score_indicator(row: dict) -> dict:
    key = row["indicator_key"]
    value = row.get("value")
    change_abs = row.get("change_abs")
    change_pct = row.get("change_pct")
    unit = row.get("unit") or ""
    if row.get("quality") == "unknown" or value is None:
        status = "unknown"
        reason = "無料データを安定取得できなかったため、原典確認が必要です。"
    elif key == "us10y":
        status = "green" if (change_abs or 0) <= -0.05 else "red" if (change_abs or 0) >= 0.05 else "yellow"
        reason = "GOLD目線では米金利低下は追い風、上昇は注意材料として扱います。"
    elif key == "dollar_index":
        status = "green" if (change_pct or 0) <= -0.25 else "red" if (change_pct or 0) >= 0.25 else "yellow"
        reason = "ドル安はGOLDの追い風、ドル高は注意材料として扱います。"
    elif key == "vix":
        status = "green" if value < 15 else "red" if value >= 25 else "yellow"
        reason = "VIXは市場ストレスの確認材料です。高い場合は注意度を上げます。"
    elif key == "gold":
        status = "green" if (change_pct or 0) >= 0.3 else "red" if (change_pct or 0) <= -0.3 else "yellow"
        reason = "GOLD価格の方向感を環境認識として表示します。"
    elif key == "sp500":
        status = "red" if (change_pct or 0) <= -1.0 else "green" if (change_pct or 0) >= 1.0 else "yellow"
        reason = "株価指数はリスク選好の補助確認として扱います。"
    else:
        status = "unknown"
        reason = "Phase 1ではリンク確認を優先します。"

    return {
        "indicator_key": key,
        "label": row["label"],
        "status": status,
        "status_label": STATUS_LABELS[status],
        "value_text": _fmt_value(value, unit),
        "change_text": _fmt_change(change_abs, change_pct, unit),
        "comment": row.get("comment") or _fmt_change(change_abs, change_pct, unit),
        "reason": reason,
        "source_name": row["source_name"],
        "source_url": row["source_url"],
        "as_of": row["as_of"],
    }


def build_dashboard_payload(
    market_rows: list[dict],
    economic_links: list[dict],
    geo_news_links: list[dict],
) -> tuple[dict, list[dict]]:
    indicators = [score_indicator(row) for row in market_rows]
    known_statuses = [row["status"] for row in indicators if row["status"] != "unknown"]
    counts = Counter(known_statuses)
    if not known_statuses:
        overall = "unknown"
    elif counts["red"] >= 2:
        overall = "red"
    elif counts["green"] >= 3 and counts["red"] == 0:
        overall = "green"
    else:
        overall = "yellow"

    caution_points = counts["red"]
    if any(row["indicator_key"] == "vix" and row["status"] == "red" for row in indicators):
        caution_points += 1
    if economic_links:
        caution_points += 1
    if geo_news_links:
        caution_points += 1
    caution_level = "高" if caution_points >= 3 else "中" if caution_points >= 1 else "低"

    tz = ZoneInfo(settings.timezone)
    updated_at = datetime.now(tz).replace(microsecond=0).isoformat()
    important_event_summary = "公式カレンダーを確認"
    if economic_links:
        important_event_summary = economic_links[0]["title"]

    payload = {
        "updated_at_jst": updated_at,
        "summary": {
            "overall_status": overall,
            "overall_label": STATUS_LABELS[overall],
            "caution_level": caution_level,
            "headline": "GOLD環境を30秒で確認",
            "important_event_summary": important_event_summary,
        },
        "indicators": indicators,
        "economic_events": economic_links,
        "geo_news": geo_news_links,
        "reference_links": [
            {"label": row["label"], "source_name": row["source_name"], "source_url": row["source_url"]}
            for row in indicators
        ],
        "disclaimer": "このダッシュボードは投資助言ではなく、市場環境の整理と原典確認を目的としています。",
    }
    return payload, indicators

