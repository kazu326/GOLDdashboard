from __future__ import annotations

import csv
import io
from datetime import datetime
from urllib.parse import urlencode
from xml.etree import ElementTree

from app.config import settings
from app.collectors.base import ProviderAdapter
from app.collectors.http import fetch_json, fetch_text
from app.schemas import NormalizedData, unknown_data


def _float_or_none(value: object) -> float | None:
    if value in (None, "", "."):
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def _change(current: float | None, previous: float | None) -> tuple[float | None, float | None]:
    if current is None or previous in (None, 0):
        return None, None
    change_abs = current - previous
    return change_abs, (change_abs / previous) * 100


class FredSeriesAdapter(ProviderAdapter):
    def __init__(self, indicator_key: str, label: str, series_id: str, unit: str, source_url: str) -> None:
        self.indicator_key = indicator_key
        self.label = label
        self.series_id = series_id
        self.unit = unit
        self.source_url = source_url
        self.provider_name = f"FRED {series_id}"
        self.endpoint = "https://api.stlouisfed.org/fred/series/observations"

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


class TreasuryTenYearAdapter(ProviderAdapter):
    provider_name = "U.S. Treasury"
    endpoint = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve"
    indicator_key = "us10y"
    label = "米10年金利"
    source_url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates"

    def fetch(self) -> NormalizedData:
        text = fetch_text(self.endpoint)
        root = ElementTree.fromstring(text)
        entries = []
        for props in root.findall(".//{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties"):
            row = {child.tag.split("}")[-1]: child.text for child in props}
            value = _float_or_none(row.get("BC_10YEAR") or row.get("NEW_DATE_10_YR"))
            date = row.get("NEW_DATE") or row.get("QUOTE_DATE") or row.get("Id")
            if value is not None and date:
                entries.append((date[:10], value))
        if not entries:
            raise RuntimeError("No 10-year yield found in Treasury XML")
        current_date, current = entries[-1]
        previous = entries[-2][1] if len(entries) > 1 else None
        change_abs, change_pct = _change(current, previous)
        return NormalizedData(
            indicator_key=self.indicator_key,
            label=self.label,
            value=current,
            unit="%",
            as_of=current_date,
            source_name=self.provider_name,
            source_url=self.source_url,
            quality="ok",
            change_abs=change_abs,
            change_pct=change_pct,
        )


class CboeVixAdapter(ProviderAdapter):
    provider_name = "Cboe"
    endpoint = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
    indicator_key = "vix"
    label = "VIX"
    source_url = "https://www.cboe.com/tradable_products/vix/vix_historical_data/"

    def fetch(self) -> NormalizedData:
        text = fetch_text(self.endpoint)
        rows = list(csv.DictReader(io.StringIO(text)))
        usable = [row for row in rows if _float_or_none(row.get("CLOSE")) is not None]
        if not usable:
            raise RuntimeError("No VIX close values found")
        current_row = usable[-1]
        previous_row = usable[-2] if len(usable) > 1 else {}
        current = _float_or_none(current_row.get("CLOSE"))
        previous = _float_or_none(previous_row.get("CLOSE"))
        change_abs, change_pct = _change(current, previous)
        return NormalizedData(
            indicator_key=self.indicator_key,
            label=self.label,
            value=current,
            unit="",
            as_of=current_row.get("DATE", datetime.utcnow().date().isoformat()),
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
    source_url = "https://www.alphavantage.co/documentation/"

    def fetch(self) -> NormalizedData:
        if not settings.alpha_vantage_api_key:
            raise RuntimeError("ALPHA_VANTAGE_API_KEY is not set")
        params = urlencode(
            {
                "function": "GOLD_SILVER_SPOT",
                "symbol": "XAU",
                "apikey": settings.alpha_vantage_api_key,
            }
        )
        data = fetch_json(f"{self.endpoint}?{params}")
        value = _float_or_none(data.get("price") or data.get("spot_price") or data.get("value"))
        if value is None:
            raise RuntimeError("No gold spot price found")
        return NormalizedData(
            indicator_key=self.indicator_key,
            label=self.label,
            value=value,
            unit="USD/oz",
            as_of=str(data.get("timestamp") or datetime.utcnow().date().isoformat())[:10],
            source_name=self.provider_name,
            source_url=self.source_url,
            quality="ok",
        )


class FmpQuoteAdapter(ProviderAdapter):
    provider_name = "Financial Modeling Prep"
    endpoint = "https://financialmodelingprep.com/stable/quote"
    source_url = "https://site.financialmodelingprep.com/developer/docs/quickstart"

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
        value = _float_or_none(row.get("price") or row.get("close"))
        change_abs = _float_or_none(row.get("change"))
        change_pct = _float_or_none(row.get("changesPercentage"))
        if value is None:
            raise RuntimeError(f"No quote found for {self.symbol}")
        return NormalizedData(
            indicator_key=self.indicator_key,
            label=self.label,
            value=value,
            unit=self.unit,
            as_of=datetime.utcnow().date().isoformat(),
            source_name=f"{self.provider_name} {self.symbol}",
            source_url=self.source_url,
            quality="ok",
            change_abs=change_abs,
            change_pct=change_pct,
        )


def adapter_groups() -> dict[str, list[ProviderAdapter]]:
    return {
        "us10y": [
            TreasuryTenYearAdapter(),
            FredSeriesAdapter("us10y", "米10年金利", "DGS10", "%", "https://fred.stlouisfed.org/series/DGS10"),
        ],
        "dollar_index": [
            FmpQuoteAdapter("dollar_index", "ドル指数", "DX-Y.NYB", ""),
            FredSeriesAdapter(
                "dollar_index",
                "代替ドル指数",
                "DTWEXBGS",
                "index",
                "https://fred.stlouisfed.org/series/DTWEXBGS",
            ),
        ],
        "vix": [
            CboeVixAdapter(),
            FredSeriesAdapter("vix", "VIX", "VIXCLS", "", "https://fred.stlouisfed.org/series/VIXCLS"),
        ],
        "gold": [
            AlphaVantageGoldAdapter(),
            FmpQuoteAdapter("gold", "GOLD価格", "GCUSD", "USD/oz"),
        ],
        "sp500": [
            FredSeriesAdapter("sp500", "S&P500", "SP500", "", "https://fred.stlouisfed.org/series/SP500"),
            FmpQuoteAdapter("sp500", "S&P500", "^GSPC", ""),
        ],
    }


def collect_market_data(conn) -> list[NormalizedData]:
    results: list[NormalizedData] = []
    for indicator_key, adapters in adapter_groups().items():
        selected: NormalizedData | None = None
        for adapter in adapters:
            item = adapter.safe_fetch(conn)
            if not item.is_unknown:
                selected = item
                break
            selected = item
        if selected is None:
            selected = unknown_data(
                indicator_key=indicator_key,
                label=indicator_key,
                source_name="未設定",
                source_url="",
                comment="取得元が設定されていません。",
            )
        results.append(selected)
    return results

