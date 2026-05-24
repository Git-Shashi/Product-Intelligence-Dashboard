from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class CompetitorPriceData:
    platform: str
    competitor_price: float
    competitor_url: str = ""
    currency: str = "INR"


@runtime_checkable
class CompetitorService(Protocol):
    def get_prices(self, sku_id: str, our_price: float | None, product_title: str = "") -> list[CompetitorPriceData]:
        ...
