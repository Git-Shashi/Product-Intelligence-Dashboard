"""
Core pipeline: validate a product dict and persist it (or update if SKU exists).
Used by CSV upload and video extraction jobs.
"""
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Alert, AlertStatus, Job, ListingIssue, Product, ProductSource, Severity
from app.validation.rules import run_all_rules
from app.validation.severity import compute_quality_score

logger = logging.getLogger(__name__)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() not in ("false", "0", "out_of_stock", "no", "")
    return bool(value)


def _parse_float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


async def _get_existing_skus(db: AsyncSession) -> set[str]:
    result = await db.execute(select(Product.sku_id))
    return {row[0] for row in result.fetchall()}


async def process_product_row(
    db: AsyncSession,
    row: dict[str, Any],
    source: ProductSource,
    existing_skus: set[str],
) -> tuple[bool, str]:
    """
    Upsert one product row. Returns (success, error_message).
    Duplicate SKU → update + re-validate instead of reject.
    """
    sku_id = str(row.get("sku_id", "")).strip()
    if not sku_id:
        return False, "Missing sku_id"

    price = _parse_float(row.get("price"))
    mrp = _parse_float(row.get("mrp"))
    availability = _parse_bool(row.get("availability", True))

    product_title = str(row.get("product_title", "")).strip() or None
    brand = str(row.get("brand", "")).strip() or None
    category = str(row.get("category", "")).strip() or None
    description = str(row.get("description", "")).strip() or None
    image_url = str(row.get("image_url", "")).strip() or None
    product_url = str(row.get("product_url", "")).strip() or None
    color = str(row.get("color", "")).strip() or None
    size = str(row.get("size", "")).strip() or None
    material = str(row.get("material", "")).strip() or None

    # Fetch or create product
    result = await db.execute(select(Product).where(Product.sku_id == sku_id))
    product = result.scalar_one_or_none()

    is_new = product is None
    if is_new:
        product = Product(sku_id=sku_id, source=source)
        db.add(product)

    product.product_title = product_title
    product.description = description
    product.brand = brand
    product.category = category
    product.price = price
    product.mrp = mrp
    product.image_url = image_url
    product_url and setattr(product, "product_url", product_url)
    product.availability = availability
    product.color = color
    product.size = size
    product.material = material
    product.source = source

    await db.flush()  # get product.id

    # Clear old issues and re-validate
    await db.execute(
        __import__("sqlalchemy", fromlist=["delete"]).delete(ListingIssue).where(
            ListingIssue.product_id == product.id
        )
    )

    issues = run_all_rules(
        sku_id=sku_id,
        product_title=product_title,
        description=description,
        brand=brand,
        category=category,
        price=price,
        mrp=mrp,
        image_url=image_url,
        availability=availability,
        color=color,
        size=size,
        material=material,
    )

    for issue_type, severity, message, suggested_fix in issues:
        db.add(ListingIssue(
            product_id=product.id,
            type=issue_type,
            severity=severity,
            message=message,
            suggested_fix=suggested_fix,
        ))

    product.quality_score = compute_quality_score([sev for _, sev, _, _ in issues])

    # Raise alerts for all issue severities on new products
    # On re-validation (edit/re-upload), only raise new HIGH alerts to avoid noise
    alert_severities = {Severity.HIGH, Severity.MEDIUM, Severity.LOW} if is_new else {Severity.HIGH}
    for issue_type, severity, message, _ in issues:
        if severity in alert_severities:
            db.add(Alert(
                product_id=product.id,
                type=issue_type,
                severity=severity,
                message=f"[{sku_id}] {message}",
                status=AlertStatus.OPEN,
            ))

    await db.commit()
    existing_skus.add(sku_id)
    return True, ""
