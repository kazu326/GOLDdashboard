from app.collectors.base import ProviderAdapter


class BrokenAdapter(ProviderAdapter):
    provider_name = "broken"
    endpoint = "https://example.com"
    indicator_key = "gold"
    label = "GOLD価格"
    source_url = "https://example.com"

    def fetch(self):
        raise RuntimeError("boom")


def test_adapter_failure_returns_unknown():
    from app import db

    conn = db.connect(":memory:")
    try:
        db.init_db(conn)
        item = BrokenAdapter().safe_fetch(conn)
        assert item.quality == "unknown"
        assert item.value is None
    finally:
        conn.close()

