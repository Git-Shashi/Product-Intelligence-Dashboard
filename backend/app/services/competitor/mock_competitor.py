"""
Deterministic mock competitor prices.
Seeded by sku_id so results are reproducible across runs.
Simulates realistic variance: some platforms are cheaper, some more expensive.
"""
import hashlib

from app.services.competitor.competitor import CompetitorPriceData

_PLATFORMS = [
    ("Amazon", "https://amazon.in/dp/{sku}"),
    ("Myntra", "https://myntra.com/p/{sku}"),
    ("Ajio", "https://ajio.com/p/{sku}"),
    ("Meesho", "https://meesho.com/p/{sku}"),
    ("Tata Cliq", "https://tatacliq.com/p/{sku}"),
]

# Multipliers relative to our price — some undercut, some are higher
_MULTIPLIERS = [0.85, 0.92, 0.97, 1.03, 1.08]


class MockCompetitorService:
    def get_prices(self, sku_id: str, our_price: float | None) -> list[CompetitorPriceData]:
        base = our_price if our_price and our_price > 0 else 1000.0
        seed = int(hashlib.md5(sku_id.encode()).hexdigest(), 16)

        results: list[CompetitorPriceData] = []
        # Pick 3-4 platforms deterministically
        n_platforms = 3 + (seed % 2)
        indices = [(seed >> i) % len(_PLATFORMS) for i in range(n_platforms)]
        seen = set()
        for idx in indices:
            if idx in seen:
                idx = (idx + 1) % len(_PLATFORMS)
            seen.add(idx)
            platform, url_template = _PLATFORMS[idx]
            multiplier = _MULTIPLIERS[(seed + idx) % len(_MULTIPLIERS)]
            price = round(base * multiplier, -1)  # round to nearest 10
            results.append(CompetitorPriceData(
                platform=platform,
                competitor_price=max(price, 1.0),
                competitor_url=url_template.format(sku=sku_id),
                currency="INR",
            ))
        return results
