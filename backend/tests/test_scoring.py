import pytest

from app.scoring.engine import build_dashboard_payload, detect_market_mode, score_indicator


def _indicator(key, change_pct=0.0, value=10.0, change_abs=0.0, quality="ok"):
    return {
        "indicator_key": key,
        "label": key,
        "value": value,
        "unit": "",
        "change_abs": change_abs,
        "change_pct": change_pct,
        "quality": quality,
        "source_name": "test",
        "source_url": "https://example.com",
        "as_of": "2026-01-01",
    }


def _mode_rows(**changes):
    defaults = {"gold": 0.1, "real_rate": -0.1, "dxy": -0.1, "sp500": 0.1, "vix": -0.1}
    defaults.update(changes)
    return {key: _indicator(key, change_pct=value) for key, value in defaults.items()}


def test_market_mode_priority_correlation_break_first():
    mode = detect_market_mode(_mode_rows(gold=1, real_rate=-1, dxy=1, sp500=-1, vix=1))
    assert mode["key"] == "correlation_break"


def test_market_modes():
    assert detect_market_mode(_mode_rows(gold=1, real_rate=-1, dxy=-1))["key"] == "normal_gold_tailwind"
    assert detect_market_mode(_mode_rows(real_rate=1, dxy=1, gold=-1))["key"] == "gold_headwind"
    assert detect_market_mode(_mode_rows(gold=1, real_rate=0, dxy=0, sp500=-1, vix=1))["key"] == "risk_off_gold_buying"
    assert detect_market_mode(_mode_rows(gold=-1, real_rate=-1, dxy=-1, sp500=1, vix=-1))["key"] == "neutral"


def test_risk_off_dollar_buying_uses_core_three_changes_only():
    mode = detect_market_mode(_mode_rows(gold=-1, dxy=1, vix=1, real_rate=None, sp500=None))
    assert mode["key"] == "risk_off_dollar_buying"
    assert mode["label"] == "リスクオフのドル買い優勢"


def test_risk_off_dollar_buying_requires_gold_dxy_vix_changes():
    assert detect_market_mode(_mode_rows(gold=-1, dxy=1, vix=None, real_rate=1))["key"] != "risk_off_dollar_buying"
    assert detect_market_mode(_mode_rows(gold=-1, dxy=None, vix=1, real_rate=1))["key"] != "risk_off_dollar_buying"
    assert detect_market_mode(_mode_rows(gold=None, dxy=1, vix=1, real_rate=1))["key"] != "risk_off_dollar_buying"


def test_risk_off_dollar_buying_precedes_gold_headwind():
    mode = detect_market_mode(_mode_rows(gold=-1, dxy=1, vix=1, real_rate=1, sp500=-1))
    assert mode["key"] == "risk_off_dollar_buying"


def test_correlation_break_remains_separate_from_risk_off_dollar_buying():
    mode = detect_market_mode(_mode_rows(gold=1, dxy=1, vix=1, real_rate=1, sp500=-1))
    assert mode["key"] == "correlation_break"


def test_missing_change_is_unknown_not_neutral():
    rows = _mode_rows()
    rows["dxy"]["change_pct"] = None
    assert detect_market_mode(rows)["key"] == "unknown"


@pytest.mark.parametrize(("value", "signal"), [(19.99, "normal"), (20, "warning"), (29.99, "warning"), (30, "stress")])
def test_vix_thresholds(value, signal):
    assert score_indicator(_indicator("vix", value=value))["signal"] == signal


def test_payload_is_schema_v2_without_news_keys():
    payload, indicators = build_dashboard_payload(
        [_indicator(key) for key in ("gold", "real_rate", "nominal_rate", "inflation_expectation", "dxy", "sp500", "vix")]
    )
    assert payload["schema_version"] == 3
    assert "data_freshness" in payload["summary"]
    assert len(indicators) == 7
    assert [item["indicator_key"] for item in indicators] == [
        "gold",
        "real_rate",
        "nominal_rate",
        "inflation_expectation",
        "dxy",
        "sp500",
        "vix",
    ]
    assert "economic_events" not in payload
    assert "geo_news" not in payload


def test_payload_adds_risk_off_dollar_buying_warning():
    rows = [_indicator(key) for key in ("gold", "real_rate", "nominal_rate", "inflation_expectation", "dxy", "sp500", "vix")]
    for row in rows:
        if row["indicator_key"] == "gold":
            row["change_pct"] = -1
        if row["indicator_key"] == "dxy":
            row["change_pct"] = 1
        if row["indicator_key"] == "vix":
            row["change_pct"] = 1
    payload, _indicators = build_dashboard_payload(rows)
    assert payload["summary"]["market_mode"]["key"] == "risk_off_dollar_buying"
    assert "リスクオフ下のドル買い優勢" in payload["summary"]["warning_signals"]


def test_market_mode_ignores_excluded_sp500_for_risk_off_gold_buying():
    rows = _mode_rows(gold=1, dxy=0, sp500=-1, vix=1)
    rows["sp500"]["used_in_market_mode"] = False
    assert detect_market_mode(rows)["key"] != "risk_off_gold_buying"


def test_risk_off_dollar_buying_works_without_sp500_when_core_is_usable():
    rows = _mode_rows(gold=-1, dxy=1, vix=1)
    rows["sp500"]["used_in_market_mode"] = False
    mode_rows = {key: row for key, row in rows.items() if row.get("used_in_market_mode", True)}
    assert detect_market_mode(mode_rows)["key"] == "risk_off_dollar_buying"
