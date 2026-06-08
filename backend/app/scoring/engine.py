from __future__ import annotations

from datetime import datetime
from typing import cast
from zoneinfo import ZoneInfo

from app.config import settings
from app.freshness import FRESHNESS_LABELS, usage_label


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
    used_in_market_mode = bool(row.get("used_in_market_mode", True))
    freshness_status = row.get("freshness_status") or "fresh"

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
        "source_series": row.get("source_series") or row["source_name"],
        "source_url": row["source_url"],
        "as_of": row["as_of"],
        "data_date": row["as_of"],
        "fetched_at": row.get("fetched_at") or row.get("created_at", ""),
        "freshness_status": freshness_status,
        "freshness_label": FRESHNESS_LABELS.get(freshness_status, freshness_status),
        "used_in_market_mode": used_in_market_mode,
        "market_mode_usage": usage_label(freshness_status, used_in_market_mode),
    }


def detect_market_mode(rows: dict[str, dict]) -> dict:
    rows = {key: row for key, row in rows.items() if row.get("used_in_market_mode", True)}
    changes = {key: row.get("change_pct") for key, row in rows.items()}

    def has_changes(*keys: str) -> bool:
        return all(key in rows and changes.get(key) is not None for key in keys)

    def change(key: str) -> float:
        return cast(float, changes[key])

    if not has_changes("gold", "dxy", "vix"):
        core_data_missing = True
    else:
        core_data_missing = False

    if has_changes("gold", "dxy", "vix"):
        gold = change("gold")
        dxy = change("dxy")
        vix = change("vix")
        if gold > 0 and dxy > 0 and vix > 0:
            return {
                "key": "correlation_break",
                "label": "相関ブレイク警戒",
                "description": "GOLD・DXY・VIXが同時上昇。通常のドル高とGOLD安の関係から外れています。",
            }
        if gold < 0 and dxy > 0 and vix > 0:
            return {
                "key": "risk_off_dollar_buying",
                "label": "リスクオフのドル買い優勢",
                "description": (
                    "市場ストレスは上昇していますが、GOLDは下落し、DXYが上昇しています。"
                    "有事の金買いではなく、ドル買い・現金化需要が優勢な状態です。"
                    "GOLDはドル高や高めの実質金利に押されている可能性があります。"
                ),
            }

    if has_changes("gold", "real_rate", "dxy"):
        gold = change("gold")
        real_rate = change("real_rate")
        dxy = change("dxy")
        if gold > 0 and real_rate < 0 and dxy < 0:
            return {
                "key": "normal_gold_tailwind",
                "label": "通常の金利低下によるGOLD追い風",
                "description": "実質金利低下とドル安がGOLD上昇を支えています。",
            }

    if has_changes("real_rate", "dxy"):
        real_rate = change("real_rate")
        dxy = change("dxy")
        if real_rate > 0 and dxy > 0:
            return {
                "key": "gold_headwind",
                "label": "金利・ドル高によるGOLD向かい風",
                "description": "実質金利上昇とドル高がGOLDの上値を抑えやすい環境です。",
            }

    if has_changes("gold", "sp500", "vix"):
        gold = change("gold")
        sp500 = change("sp500")
        vix = change("vix")
        if gold > 0 and sp500 < 0 and vix > 0:
            return {
                "key": "risk_off_gold_buying",
                "label": "リスクオフ買いの可能性",
                "description": "株安とVIX上昇を伴うGOLD上昇です。",
            }

    if core_data_missing:
        return {
            "key": "unknown",
            "label": "データ不足",
            "description": "市場モード判定に必要な前日比が不足しています。",
        }
    return {"key": "neutral", "label": "中立", "description": "明確な市場モードは検出されていません。"}


def build_dashboard_payload(market_rows: list[dict]) -> tuple[dict, list[dict]]:
    by_raw_key = {row["indicator_key"]: row for row in market_rows}
    indicators = [score_indicator(by_raw_key[key]) for key in INDICATOR_ORDER if key in by_raw_key]
    by_key = {row["indicator_key"]: row for row in indicators}
    mode_rows = {key: row for key, row in by_key.items() if row["used_in_market_mode"]}
    mode = detect_market_mode(mode_rows)
    gold = by_key.get("gold", {})
    vix = by_key.get("vix", {})

    warnings = []
    if mode["key"] == "correlation_break":
        warnings.append("GOLD・DXY・VIXの相関ブレイク")
    if mode["key"] == "risk_off_dollar_buying":
        warnings.append("リスクオフ下のドル買い優勢")
    if vix.get("signal") == "stress":
        warnings.append("VIX 30以上: 強い市場ストレス")
    elif vix.get("signal") == "warning":
        warnings.append("VIX 20以上: 警戒")
    unknown_count = sum(row["signal"] == "unknown" for row in indicators)
    if unknown_count:
        warnings.append(f"{unknown_count}指標がデータ不足")
    stale_or_excluded = [row for row in indicators if row["freshness_status"] in {"stale", "excluded"}]
    if stale_or_excluded:
        warnings.append(f"{len(stale_or_excluded)}指標が判定から除外または参考扱い")
    sp500 = by_key.get("sp500")
    if sp500 and sp500["freshness_status"] in {"stale", "excluded"}:
        warnings.append("S&P500データが古いため、リスクオン/リスクオフ判定は参考扱い")

    freshness_counts = {
        status: sum(row["freshness_status"] == status for row in indicators)
        for status in ("fresh", "caution", "stale", "excluded")
    }
    old_count = freshness_counts["caution"] + freshness_counts["stale"] + freshness_counts["excluded"]
    mode_assessment = "通常利用"
    if freshness_counts["excluded"]:
        mode_assessment = "一部除外"
    elif freshness_counts["stale"]:
        mode_assessment = "一部参考扱い"
    elif freshness_counts["caution"]:
        mode_assessment = "一部遅延あり"

    tz = ZoneInfo(settings.timezone)
    payload = {
        "schema_version": 3,
        "updated_at_jst": datetime.now(tz).replace(microsecond=0).isoformat(),
        "summary": {
            "gold_value_text": gold.get("value_text", "データ不足"),
            "gold_change_text": gold.get("change_text", "前日比: データ不足"),
            "market_mode": mode,
            "primary_factor": mode["description"],
            "warning_signals": warnings,
            "data_freshness": {
                "label": "DATA FRESHNESS",
                "summary_text": f"{len(indicators)}指標中 {old_count}指標が古い可能性",
                "market_mode_assessment": mode_assessment,
                "counts": freshness_counts,
            },
        },
        "indicators": indicators,
        "reference_links": [
            {"label": row["label"], "source_name": row["source_name"], "source_url": row["source_url"]}
            for row in indicators
        ],
        "disclaimer": "このダッシュボードは売買シグナルではなく、市場環境の整理を目的としています。",
    }
    return payload, indicators
