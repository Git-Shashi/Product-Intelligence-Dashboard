"""Mock trending keyword map per category."""

TRENDING_KEYWORDS: dict[str, list[str]] = {
    "shoes": ["running shoes", "lightweight shoes", "sports shoes for men", "casual footwear", "breathable shoes"],
    "footwear": ["running shoes", "lightweight shoes", "sports shoes", "casual footwear"],
    "dresses": ["women dress", "casual dress", "party wear dress", "floral dress", "summer dress"],
    "clothing": ["casual wear", "comfortable fit", "premium fabric", "everyday wear"],
    "apparel": ["casual wear", "comfortable fit", "trendy outfit", "fashion wear"],
    "bags": ["lightweight bag", "travel bag", "stylish handbag", "everyday bag", "durable bag"],
    "electronics": ["fast charging", "wireless", "premium quality", "high performance", "long battery life"],
    "home": ["home decor", "premium quality", "easy to use", "durable", "modern design"],
    "beauty": ["skin care", "natural ingredients", "dermatologist tested", "long lasting"],
    "sports": ["high performance", "gym wear", "workout gear", "comfortable fit", "durable"],
    "default": ["premium quality", "best value", "top rated", "highly durable"],
}


def get_keywords_for_category(category: str | None) -> list[str]:
    if not category:
        return TRENDING_KEYWORDS["default"]
    key = category.lower().strip()
    return TRENDING_KEYWORDS.get(key, TRENDING_KEYWORDS["default"])
