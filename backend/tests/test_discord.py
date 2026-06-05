from app.discord import build_discord_payload


def test_discord_payload_contains_summary():
    snapshot = {
        "summary": {
            "overall_label": "中立",
            "caution_level": "中",
            "important_event_summary": "公式カレンダーを確認",
        },
        "indicators": [
            {
                "label": "GOLD価格",
                "status_label": "要確認",
                "value_text": "要確認",
                "change_text": "前回比は要確認",
            }
        ],
    }
    payload = build_discord_payload(snapshot)
    assert payload["embeds"][0]["title"].startswith("GOLD環境認識")
    assert "GOLD価格" in payload["embeds"][0]["description"]

