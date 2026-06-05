from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


Status = str


@dataclass(frozen=True)
class NormalizedData:
    indicator_key: str
    label: str
    value: float | None
    unit: str
    as_of: str
    source_name: str
    source_url: str
    quality: str
    change_abs: float | None = None
    change_pct: float | None = None
    comment: str = ""

    @property
    def is_unknown(self) -> bool:
        return self.quality == "unknown" or self.value is None


def unknown_data(
    indicator_key: str,
    label: str,
    source_name: str,
    source_url: str,
    comment: str,
) -> NormalizedData:
    return NormalizedData(
        indicator_key=indicator_key,
        label=label,
        value=None,
        unit="",
        as_of=datetime.utcnow().date().isoformat(),
        source_name=source_name,
        source_url=source_url,
        quality="unknown",
        comment=comment,
    )


DashboardPayload = dict[str, Any]

