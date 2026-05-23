from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EnhancedTitle, Product
from app.domain.keywords import get_keywords_for_category


def _build_attributes(product: Product) -> dict:
    attrs: dict[str, str] = {}
    if product.brand:
        attrs["brand"] = product.brand
    if product.color:
        attrs["color"] = product.color
    if product.size:
        attrs["size"] = product.size
    if product.material:
        attrs["material"] = product.material
    if product.category:
        attrs["category"] = product.category
    return attrs


def _build_enhanced_title(original: str, attrs: dict, keywords: list[str]) -> tuple[str, str]:
    """
    Builds an enhanced title by prepending brand, appending key attributes,
    and injecting the top trending keyword.
    """
    parts: list[str] = []

    brand = attrs.get("brand", "")
    color = attrs.get("color", "")
    material = attrs.get("material", "")
    category = attrs.get("category", "")

    # Start from original if it doesn't already contain the brand
    base = original.strip()
    if brand and brand.lower() not in base.lower():
        parts.append(brand)

    parts.append(base)

    extras: list[str] = []
    if color and color.lower() not in base.lower():
        extras.append(color)
    if material and material.lower() not in base.lower():
        extras.append(f"with {material} Material")

    if extras:
        parts.append(" ".join(extras))

    # Inject top keyword if not already present
    if keywords:
        top_kw = keywords[0]
        if top_kw.lower() not in " ".join(parts).lower():
            parts.append(f"| {top_kw.title()}")

    enhanced = " ".join(parts)

    reason_parts = ["Enhanced title"]
    if brand:
        reason_parts.append(f"includes brand '{brand}'")
    if color:
        reason_parts.append(f"highlights color '{color}'")
    if material:
        reason_parts.append(f"calls out material '{material}'")
    if keywords:
        reason_parts.append(f"adds trending keyword '{keywords[0]}'")

    reason = "; ".join(reason_parts) + "."
    return enhanced, reason


async def generate_enhanced_title(db: AsyncSession, product: Product) -> EnhancedTitle:
    original_title = product.product_title or product.sku_id
    attrs = _build_attributes(product)
    keywords = get_keywords_for_category(product.category)
    enhanced, reason = _build_enhanced_title(original_title, attrs, keywords)

    record = EnhancedTitle(
        product_id=product.id,
        original_title=original_title,
        attributes=attrs,
        keywords=keywords[:5],
        enhanced_title=enhanced,
        reason=reason,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
