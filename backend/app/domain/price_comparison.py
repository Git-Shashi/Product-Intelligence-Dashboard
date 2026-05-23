"""
Pure functions for price comparison and alert rule evaluation.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PriceComparison:
    our_price: Optional[float]
    lowest_competitor: Optional[float]
    highest_competitor: Optional[float]
    average_competitor: Optional[float]
    price_gap: Optional[float]          # our_price - lowest_competitor
    percentage_diff: Optional[float]    # ((our - lowest) / lowest) * 100
    recommended_action: str


def compute_comparison(our_price: Optional[float], competitor_prices: list[float]) -> PriceComparison:
    if not competitor_prices:
        return PriceComparison(
            our_price=our_price,
            lowest_competitor=None,
            highest_competitor=None,
            average_competitor=None,
            price_gap=None,
            percentage_diff=None,
            recommended_action="No competitor prices available. Add competitor data to compare.",
        )

    lowest = min(competitor_prices)
    highest = max(competitor_prices)
    average = round(sum(competitor_prices) / len(competitor_prices), 2)

    if our_price is None or our_price <= 0:
        return PriceComparison(
            our_price=our_price,
            lowest_competitor=lowest,
            highest_competitor=highest,
            average_competitor=average,
            price_gap=None,
            percentage_diff=None,
            recommended_action="Set a valid price to enable comparison.",
        )

    gap = round(our_price - lowest, 2)
    pct = round((gap / lowest) * 100, 1) if lowest > 0 else 0.0

    if pct > 10:
        action = f"Reduce price by ₹{abs(gap):,.0f} to match lowest competitor (currently {pct:.1f}% higher)."
    elif pct > 0:
        action = f"Price is ₹{gap:,.0f} above the lowest competitor ({pct:.1f}%). Consider a small reduction."
    elif pct < -5:
        action = f"Price is {abs(pct):.1f}% below the lowest competitor — good competitive position."
    else:
        action = "Price is competitive. No action needed."

    return PriceComparison(
        our_price=our_price,
        lowest_competitor=lowest,
        highest_competitor=highest,
        average_competitor=average,
        price_gap=gap,
        percentage_diff=pct,
        recommended_action=action,
    )


def should_raise_price_alert(our_price: Optional[float], lowest_competitor: Optional[float]) -> bool:
    """HIGH alert: our price > 10% above lowest competitor."""
    if our_price is None or lowest_competitor is None or lowest_competitor <= 0:
        return False
    return our_price > lowest_competitor * 1.10


def is_significant_price_drop(old_price: float, new_price: float, threshold_pct: float = 5.0) -> bool:
    """MEDIUM alert: competitor price dropped by threshold_pct% or more."""
    if old_price <= 0:
        return False
    drop_pct = ((old_price - new_price) / old_price) * 100
    return drop_pct >= threshold_pct
