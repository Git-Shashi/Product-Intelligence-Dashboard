"""
Deterministic mock competitor prices.
Seeded by sku_id so results are reproducible across runs.
Simulates realistic variance: some platforms are cheaper, some more expensive.
URLs are real platform search pages using the product title so links actually resolve.
"""
import hashlib
from urllib.parse import quote_plus

from app.services.competitor.competitor import CompetitorPriceData


def _search_url(platform: str, query: str) -> str:
    q = quote_plus(query)
    urls = {
        "Amazon":    f"https://www.amazon.in/s?k={q}",
        "Myntra":    f"https://www.myntra.com/{q}",
        "Ajio":      f"https://www.ajio.com/search/?text={q}",
        "Meesho":    f"https://www.meesho.com/search?q={q}",
        "Tata Cliq": f"https://www.tatacliq.com/search/?searchCategory=all&text={q}",
    }
    return urls.get(platform, f"https://www.google.com/search?q={q}+buy+india")


_PLATFORMS = ["Amazon", "Myntra", "Ajio", "Meesho", "Tata Cliq"]

# Multipliers relative to our price — some undercut, some are higher
_MULTIPLIERS = [0.85, 0.92, 0.97, 1.03, 1.08]


class MockCompetitorService:
    def get_prices(self, sku_id: str, our_price: float | None, product_title: str = "") -> list[CompetitorPriceData]:
        base = our_price if our_price and our_price > 0 else 1000.0
        seed = int(hashlib.md5(sku_id.encode()).hexdigest(), 16)
        query = product_title.strip() if product_title.strip() else sku_id

        results: list[CompetitorPriceData] = []
        # Pick 3-4 platforms deterministically
        n_platforms = 3 + (seed % 2)
        indices = [(seed >> i) % len(_PLATFORMS) for i in range(n_platforms)]
        seen: set[int] = set()
        for idx in indices:
            if idx in seen:
                idx = (idx + 1) % len(_PLATFORMS)
            seen.add(idx)
            platform = _PLATFORMS[idx]
            multiplier = _MULTIPLIERS[(seed + idx) % len(_MULTIPLIERS)]
            price = round(base * multiplier, -1)  # round to nearest 10
            results.append(CompetitorPriceData(
                platform=platform,
                competitor_price=max(price, 1.0),
                competitor_url=_search_url(platform, query),
                currency="INR",
            ))
        return results
