from app.discord import build_discord_payload


def test_discord_payload_contains_mode_and_no_news_field():
    snapshot = {
        "summary": {
            "market_mode": {"key": "correlation_break", "label": "相関ブレイク警戒"},
            "primary_factor": "GOLD・DXY・VIXが同時上昇",
            "warning_signals": ["相関ブレイク"],
        },
        "indicators": [
            {"label": "GOLD価格", "signal_label": "GOLD追い風", "value_text": "$3,000", "change_text": "前日比 +1.00%"}
        ],
    }
    embed = build_discord_payload(snapshot)["embeds"][0]
    assert "相関ブレイク警戒" in embed["title"]
    assert "GOLD価格" in embed["description"]
    assert all(field["name"] != "重要イベント" for field in embed["fields"])
