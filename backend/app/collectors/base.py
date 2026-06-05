from __future__ import annotations

from abc import ABC, abstractmethod

from app import db
from app.schemas import NormalizedData, unknown_data


class ProviderAdapter(ABC):
    provider_name: str
    endpoint: str
    indicator_key: str
    label: str
    source_url: str

    def safe_fetch(self, conn) -> NormalizedData:
        try:
            item = self.fetch()
            db.log_fetch(conn, self.provider_name, self.endpoint, "ok")
            return item
        except Exception as exc:  # noqa: BLE001 - adapter boundary intentionally contains provider failures.
            db.log_fetch(conn, self.provider_name, self.endpoint, "error", str(exc))
            return unknown_data(
                indicator_key=self.indicator_key,
                label=self.label,
                source_name=self.provider_name,
                source_url=self.source_url,
                comment="取得できませんでした。原典を確認してください。",
            )

    @abstractmethod
    def fetch(self) -> NormalizedData:
        raise NotImplementedError

