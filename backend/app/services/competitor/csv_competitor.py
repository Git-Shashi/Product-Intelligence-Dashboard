"""
Parses competitor prices from an uploaded CSV.
Used for one-time ingestion via POST /competitor-prices/upload.
"""
import csv
import io
from datetime import datetime, timezone
from typing import Any

from app.services.competitor.competitor import CompetitorPriceData


def parse_csv(contents: bytes) -> list[tuple[str, CompetitorPriceData]]:
    """
    Returns list of (sku_id, CompetitorPriceData).
    Expected columns: sku_id, platform, competitor_url, competitor_price, currency
    """
    text = contents.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    results: list[tuple[str, CompetitorPriceData]] = []

    for row in reader:
        sku_id = str(row.get("sku_id", "")).strip()
        platform = str(row.get("platform", "")).strip()
        try:
            price = float(str(row.get("competitor_price", "0")).replace(",", ""))
        except ValueError:
            continue
        if not sku_id or not platform or price <= 0:
            continue

        results.append((
            sku_id,
            CompetitorPriceData(
                platform=platform,
                competitor_price=price,
                competitor_url=str(row.get("competitor_url", "")).strip(),
                currency=str(row.get("currency", "INR")).strip() or "INR",
            ),
        ))
    return results
