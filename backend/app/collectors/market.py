from __future__ import annotations

from datetime import datetime
from urllib.parse import urlencode

from app.config import settings
from app.collectors.base import ProviderAdapter
from app.collectors.http import fetch_json
from app.schemas import NormalizedData, unknown_data


def _float_or_none(value: object) -> float | None:
    if value in (None, "", "."):
        return None
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except ValueError:
        return None


def _change(current: float | None, previous: float | None) -> tuple[float | None, float | None]:
    if current is None or previous in (None, 0):
        return None, None
    change_abs = current - previous
    return change_abs, (change_abs / previous) * 100


class FredSeriesAdapter(ProviderAdapter):
    endpoint = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, indicator_key: str, label: str, series_id: str, unit: str) -> None:
        self.indicator_key = indicator_key
        self.label = label
        self.series_id = series_id
        self.unit = unit
        self.source_url = f"https://fred.stlouisfed.org/series/{series_id}"
        self.provider_name = f"FRED {series_id}"

    def fetch(self) -> NormalizedData:
        if not settings.fred_api_key:
            raise RuntimeError("FRED_API_KEY is not set")
        params = urlencode(
            {
                "series_id": self.series_id,
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": "8",
            }
        )
        data = fetch_json(f"{self.endpoint}?{params}")
        values = [row for row in data.get("observations", []) if _float_or_none(row.get("value")) is not None]
        if not values:
            raise RuntimeError("No usable FRED observations")
        current = _float_or_none(values[0]["value"])
        previous = _float_or_none(values[1]["value"]) if len(values) > 1 else None
        change_abs, change_pct = _change(current, previous)
        return NormalizedData(
            indicator_key=self.indicator_key,
            label=self.label,
            value=current,
            unit=self.unit,
            as_of=values[0]["date"],
            source_name=self.provider_name,
            source_url=self.source_url,
            quality="ok",
            change_abs=change_abs,
            change_pct=change_pct,
        )


class AlphaVantageGoldAdapter(ProviderAdapter):
    provider_name = "Alpha Vantage"
    endpoint = "https://www.alphavantage.co/query"
    indicator_key = "gold"
    label = "GOLD価格"
    source_url = "https://www.alphavantage.co/documentation/#gold-silver"

    def _request(self, function: str, **extra: str) -> dict:
        params = urlencode({"function": function, "symbol": "XAU", "apikey": settings.alpha_vantage_api_key, **extra})
        data = fetch_json(f"{self.endpoint}?{params}")
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected Alpha Vantage {function} response")
        return data

    def fetch(self) -> NormalizedData:
        if not settings.alpha_vantage_api_key:
            raise RuntimeError("ALPHA_VANTAGE_API_KEY is not set")
        spot = self._request("GOLD_SILVER_SPOT")
        current = _float_or_none(spot.get("price") or spot.get("spot_price") or spot.get("value"))
        if current is None:
            raise RuntimeError("No gold spot price found")

        previous = None
        as_of = str(spot.get("timestamp") or spot.get("date") or datetime.utcnow().date().isoformat())[:10]
        try:
            history = self._request("GOLD_SILVER_HISTORY", interval="daily")
            rows = history.get("data") or history.get("history") or []
            if isinstance(rows, dict):
                rows = [{"date": date, **value} for date, value in rows.items() if isinstance(value, dict)]
            closes = [
                _float_or_none(row.get("close") or row.get("price") or row.get("value"))
                for row in rows
                if isinstance(row, dict)
            ]
            closes = [value for value in closes if value is not None]
            if closes:
                previous = closes[0] if closes[0] != current else (closes[1] if len(closes) > 1 else None)
        except Exception:
            previous = None

        change_abs, change_pct = _change(current, previous)
        return NormalizedData(
            indicator_key=self.indicator_key,
            label=self.label,
            value=current,
            unit="USD/oz",
            as_of=as_of,
            source_name=self.provider_name,
            source_url=self.source_url,
            quality="ok",
            change_abs=change_abs,
            change_pct=change_pct,
        )


class FmpQuoteAdapter(ProviderAdapter):
    provider_name = "Financial Modeling Prep"
    endpoint = "https://financialmodelingprep.com/stable/quote"
    source_url = "https://site.financialmodelingprep.com/developer/docs/stable/quote"

    def __init__(self, indicator_key: str, label: str, symbol: str, unit: str) -> None:
        self.indicator_key = indicator_key
        self.label = label
        self.symbol = symbol
        self.unit = unit

    def fetch(self) -> NormalizedData:
        if not settings.fmp_api_key:
            raise RuntimeError("FMP_API_KEY is not set")
        params = urlencode({"symbol": self.symbol, "apikey": settings.fmp_api_key})
        data = fetch_json(f"{self.endpoint}?{params}")
        row = data[0] if isinstance(data, list) and data else data
        if not isinstance(row, dict):
            raise RuntimeError(f"No quote found for {self.symbol}")
        value = _float_or_none(row.get("price") or row.get("close"))
        if value is None:
            raise RuntimeError(f"No quote found for {self.symbol}")
        return NormalizedData(
            indicator_key=self.indicator_key,
            label=self.label,
            value=value,
            unit=self.unit,
            as_of=str(row.get("date") or datetime.utcnow().date().isoformat())[:10],
            source_name=f"{self.provider_name} {self.symbol}",
            source_url=self.source_url,
            quality="ok",
            change_abs=_float_or_none(row.get("change")),
            change_pct=_float_or_none(row.get("changesPercentage")),
        )


def adapter_groups() -> dict[str, list[ProviderAdapter]]:
    return {
        "gold": [
            AlphaVantageGoldAdapter(),
            FmpQuoteAdapter("gold", "GOLD価格", "GCUSD", "USD/oz"),
        ],
        "real_rate": [FredSeriesAdapter("real_rate", "米10年実質金利", "DFII10", "%")],
        "nominal_rate": [FredSeriesAdapter("nominal_rate", "米10年名目金利", "DGS10", "%")],
        "inflation_expectation": [FredSeriesAdapter("inflation_expectation", "10年期待インフレ率", "T10YIE", "%")],
        "dxy": [
            FmpQuoteAdapter("dxy", "ドル指数 DXY", "DX-Y.NYB", ""),
            FredSeriesAdapter("dxy", "ドル指数 DXY（代替）", "DTWEXBGS", "index"),
        ],
        "sp500": [
            FmpQuoteAdapter("sp500", "S&P500", "^GSPC", ""),
            FredSeriesAdapter("sp500", "S&P500", "SP500", ""),
        ],
        "vix": [FredSeriesAdapter("vix", "VIX", "VIXCLS", "")],
    }


def collect_market_data(conn) -> list[NormalizedData]:
    results: list[NormalizedData] = []
    for indicator_key, adapters in adapter_groups().items():
        selected: NormalizedData | None = None
        for adapter in adapters:
            selected = adapter.safe_fetch(conn)
            if not selected.is_unknown:
                break
        if selected is None:
            selected = unknown_data(indicator_key, indicator_key, "未設定", "", "取得元が設定されていません。")
        results.append(selected)
    return results
