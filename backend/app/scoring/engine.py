from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings


SIGNAL_LABELS = {
    "tailwind": "GOLD追い風",
    "headwind": "GOLD向かい風",
    "risk_on": "リスクオン",
    "risk_off": "リスクオフ",
    "normal": "通常",
    "warning": "警戒",
    "stress": "強い市場ストレス",
    "neutral": "中立",
    "unknown": "データ不足",
}

INDICATOR_ORDER = ("gold", "real_rate", "nominal_rate", "inflation_expectation", "dxy", "sp500", "vix")


def _fmt_value(value: float | None, unit: str) -> str:
    if value is None:
        return "データ不足"
    if unit == "%":
        return f"{value:.2f}%"
    if unit == "USD/oz":
        return f"${value:,.2f}"
    return f"{value:,.2f}"


def _fmt_change(change_abs: float | None, change_pct: float | None, unit: str) -> str:
    if change_abs is None and change_pct is None:
        return "前日比: データ不足"
    if unit == "%":
        return f"前日比 {change_abs:+.2f}pt"
    if change_pct is not None:
        return f"前日比 {change_pct:+.2f}%"
    return f"前日比 {change_abs:+.2f}"


def _direction(change: float | None, negative: str, positive: str) -> str:
    if change is None:
        return "unknown"
    if change < 0:
        return negative
    if change > 0:
        return positive
    return "neutral"


def score_indicator(row: dict) -> dict:
    key = row["indicator_key"]
    value = row.get("value")
    change_abs = row.get("change_abs")
    change_pct = row.get("change_pct")
    unit = row.get("unit") or ""

    if row.get("quality") == "unknown" or value is None:
        signal, reason = "unknown", "取得元から有効なデータを取得できませんでした。"
    elif key == "gold":
        signal = _direction(change_pct, "headwind", "tailwind")
        reason = "GOLD価格の前日比です。"
    elif key == "real_rate":
        signal = _direction(change_abs, "tailwind", "headwind")
        reason = "実質金利低下は通常GOLDの追い風、上昇は向かい風です。"
    elif key == "nominal_rate":
        signal = _direction(change_abs, "tailwind", "headwind")
        reason = "名目金利の方向を確認します。"
    elif key == "inflation_expectation":
        signal = _direction(change_abs, "neutral", "tailwind")
        reason = "期待インフレ上昇はGOLDを支えやすい材料です。"
    elif key == "dxy":
        signal = _direction(change_pct, "tailwind", "headwind")
        reason = "ドル安は通常GOLDの追い風、ドル高は向かい風です。"
    elif key == "sp500":
        signal = _direction(change_pct, "risk_off", "risk_on")
        reason = "株価指数の方向からリスク選好を確認します。"
    elif key == "vix":
        signal = "stress" if value >= 30 else "warning" if value >= 20 else "normal"
        reason = "VIX 20以上は警戒、30以上は強い市場ストレスです。"
    else:
        signal, reason = "unknown", "判定ルールがありません。"

    return {
        "indicator_key": key,
        "label": row["label"],
        "signal": signal,
        "signal_label": SIGNAL_LABELS[signal],
        "value": value,
        "change_abs": change_abs,
        "change_pct": change_pct,
        "value_text": _fmt_value(value, unit),
        "change_text": _fmt_change(change_abs, change_pct, unit),
        "reason": reason,
        "source_name": row["source_name"],
        "source_url": row["source_url"],
        "as_of": row["as_of"],
    }


def detect_market_mode(rows: dict[str, dict]) -> dict:
    changes = {key: row.get("change_pct") for key, row in rows.items()}
    required = ("gold", "real_rate", "dxy", "sp500", "vix")
    if any(key not in rows or changes.get(key) is None for key in required):
        return {
            "key": "unknown",
            "label": "データ不足",
            "description": "市場モード判定に必要な前日比が不足しています。",
        }

    gold = changes["gold"]
    real_rate = changes["real_rate"]
    dxy = changes["dxy"]
    sp500 = changes["sp500"]
    vix = changes["vix"]

    if gold > 0 and dxy > 0 and vix > 0:
        return {
            "key": "correlation_break",
            "label": "相関ブレイク警戒",
            "description": "GOLD・DXY・VIXが同時上昇。通常のドル高とGOLD安の関係から外れています。",
        }
    if gold > 0 and real_rate < 0 and dxy < 0:
        return {
            "key": "normal_gold_tailwind",
            "label": "通常の金利低下によるGOLD追い風",
            "description": "実質金利低下とドル安がGOLD上昇を支えています。",
        }
    if real_rate > 0 and dxy > 0:
        return {
            "key": "gold_headwind",
            "label": "金利・ドル高によるGOLD向かい風",
            "description": "実質金利上昇とドル高がGOLDの上値を抑えやすい環境です。",
        }
    if gold > 0 and sp500 < 0 and vix > 0:
        return {
            "key": "risk_off_gold_buying",
            "label": "リスクオフ買いの可能性",
            "description": "株安とVIX上昇を伴うGOLD上昇です。",
        }
    return {"key": "neutral", "label": "中立", "description": "明確な市場モードは検出されていません。"}


def build_dashboard_payload(market_rows: list[dict]) -> tuple[dict, list[dict]]:
    by_raw_key = {row["indicator_key"]: row for row in market_rows}
    indicators = [score_indicator(by_raw_key[key]) for key in INDICATOR_ORDER if key in by_raw_key]
    by_key = {row["indicator_key"]: row for row in indicators}
    mode = detect_market_mode(by_key)
    gold = by_key.get("gold", {})
    vix = by_key.get("vix", {})

    warnings = []
    if mode["key"] == "correlation_break":
        warnings.append("GOLD・DXY・VIXの相関ブレイク")
    if vix.get("signal") == "stress":
        warnings.append("VIX 30以上: 強い市場ストレス")
    elif vix.get("signal") == "warning":
        warnings.append("VIX 20以上: 警戒")
    unknown_count = sum(row["signal"] == "unknown" for row in indicators)
    if unknown_count:
        warnings.append(f"{unknown_count}指標がデータ不足")

    tz = ZoneInfo(settings.timezone)
    payload = {
        "schema_version": 2,
        "updated_at_jst": datetime.now(tz).replace(microsecond=0).isoformat(),
        "summary": {
            "gold_value_text": gold.get("value_text", "データ不足"),
            "gold_change_text": gold.get("change_text", "前日比: データ不足"),
            "market_mode": mode,
            "primary_factor": mode["description"],
            "warning_signals": warnings,
        },
        "indicators": indicators,
        "reference_links": [
            {"label": row["label"], "source_name": row["source_name"], "source_url": row["source_url"]}
            for row in indicators
        ],
        "disclaimer": "このダッシュボードは売買シグナルではなく、市場環境の整理を目的としています。",
    }
    return payload, indicators
