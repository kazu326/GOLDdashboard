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
    assert payload["schema_version"] == 2
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
