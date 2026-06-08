from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace

from app import db
from app.schemas import NormalizedData, unknown_data


class ProviderAdapter(ABC):
    provider_name: str
    endpoint: str
    indicator_key: str
    label: str
    source_url: str

    def safe_fetch(self, conn) -> NormalizedData:
        fetched_at = db.utc_now()
        try:
            item = self.fetch()
            db.log_fetch(conn, self.provider_name, self.endpoint, "ok", fetched_at=fetched_at)
            return replace(item, fetched_at=fetched_at)
        except Exception as exc:  # noqa: BLE001 - adapter boundary intentionally contains provider failures.
            db.log_fetch(conn, self.provider_name, self.endpoint, "error", str(exc), fetched_at=fetched_at)
            item = unknown_data(
                indicator_key=self.indicator_key,
                label=self.label,
                source_name=self.provider_name,
                source_url=self.source_url,
                comment="取得できませんでした。取得元を確認してください。",
            )
            return replace(item, fetched_at=fetched_at)

    @abstractmethod
    def fetch(self) -> NormalizedData:
        raise NotImplementedError
