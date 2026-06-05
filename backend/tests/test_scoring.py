from app.scoring.engine import score_indicator


def test_us10y_rising_is_attention():
    row = {
        "indicator_key": "us10y",
        "label": "米10年金利",
        "value": 4.5,
        "unit": "%",
        "change_abs": 0.06,
        "change_pct": 1.3,
        "quality": "ok",
        "source_name": "test",
        "source_url": "https://example.com",
        "as_of": "2026-01-01",
        "comment": "",
    }
    assert score_indicator(row)["status"] == "red"


def test_unknown_stays_unknown():
    row = {
        "indicator_key": "gold",
        "label": "GOLD価格",
        "value": None,
        "unit": "",
        "change_abs": None,
        "change_pct": None,
        "quality": "unknown",
        "source_name": "test",
        "source_url": "https://example.com",
        "as_of": "2026-01-01",
        "comment": "",
    }
    scored = score_indicator(row)
    assert scored["status"] == "unknown"
    assert scored["value_text"] == "要確認"

