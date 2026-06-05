from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    env_path = next(
        (path for path in (Path.cwd() / ".env", Path.cwd().parent / ".env") if path.exists()),
        None,
    )
    if env_path is None:
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./gold_dashboard.db")
    timezone: str = os.getenv("TIMEZONE", "Asia/Tokyo")
    dashboard_public_url: str = os.getenv("DASHBOARD_PUBLIC_URL", "http://localhost:3000")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    fred_api_key: str = os.getenv("FRED_API_KEY", "")
    alpha_vantage_api_key: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    fmp_api_key: str = os.getenv("FMP_API_KEY", "")
    discord_webhook_url: str = os.getenv("DISCORD_WEBHOOK_URL", "")

    @property
    def sqlite_path(self) -> str:
        if self.database_url.startswith("sqlite:///"):
            return self.database_url.removeprefix("sqlite:///")
        if self.database_url.startswith("sqlite://"):
            return self.database_url.removeprefix("sqlite://")
        return self.database_url


settings = Settings()
