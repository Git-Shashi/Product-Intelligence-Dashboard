"""
Pure validation functions. Each returns (issue_type, severity, message, suggested_fix) or None.
Quality score formula: start at 100, subtract HIGH=20, MEDIUM=10, LOW=3, floor at 0.
"""
import re
from typing import Optional
from urllib.parse import urlparse

from app.db.models import Severity

IssueResult = tuple[str, Severity, str, Optional[str]]


def check_missing_title(title: Optional[str]) -> Optional[IssueResult]:
    if not title or not title.strip():
        return ("MISSING_TITLE", Severity.HIGH, "Product title is missing.", "Add a clear product title.")
    return None


def check_short_title(title: Optional[str]) -> Optional[IssueResult]:
    if not title:
        return None
    stripped = title.strip()
    if len(stripped) < 15 or len(stripped.split()) < 3:
        return (
            "SHORT_TITLE",
            Severity.MEDIUM,
            f"Title is too short: '{stripped}'.",
            "Add brand, product type, color, gender, or material to the title.",
        )
    return None


def check_missing_brand(brand: Optional[str]) -> Optional[IssueResult]:
    if not brand or not brand.strip():
        return ("MISSING_BRAND", Severity.MEDIUM, "Brand is missing.", "Add brand if known, or mark as 'Unbranded'.")
    return None


def check_invalid_price(price: Optional[float]) -> Optional[IssueResult]:
    if price is None or price <= 0:
        return ("INVALID_PRICE", Severity.HIGH, "Price is missing or invalid (must be > 0).", "Set a positive numeric price.")
    return None


def check_mrp_lower_than_price(price: Optional[float], mrp: Optional[float]) -> Optional[IssueResult]:
    if price is not None and mrp is not None and mrp < price:
        return (
            "MRP_BELOW_PRICE",
            Severity.HIGH,
            f"MRP ({mrp}) is lower than selling price ({price}).",
            "Correct MRP or selling price — MRP must be ≥ price.",
        )
    return None


def check_missing_image(image_url: Optional[str]) -> Optional[IssueResult]:
    if not image_url or not image_url.strip():
        return ("MISSING_IMAGE", Severity.HIGH, "Product image URL is missing.", "Add at least one product image URL.")
    return None


def check_broken_image_url(image_url: Optional[str]) -> Optional[IssueResult]:
    if not image_url:
        return None
    try:
        result = urlparse(image_url.strip())
        if result.scheme not in ("http", "https") or not result.netloc:
            return (
                "BROKEN_IMAGE_URL",
                Severity.MEDIUM,
                f"Image URL does not appear to be a valid HTTP/HTTPS URL: '{image_url}'.",
                "Replace with an accessible image URL starting with http:// or https://.",
            )
    except Exception:
        return (
            "BROKEN_IMAGE_URL",
            Severity.MEDIUM,
            "Image URL could not be parsed.",
            "Replace with a valid image URL.",
        )
    return None


def check_weak_description(description: Optional[str]) -> Optional[IssueResult]:
    if not description or len(description.strip()) < 50:
        return (
            "WEAK_DESCRIPTION",
            Severity.LOW,
            "Description is too short or missing (< 50 characters).",
            "Add more product details, attributes, and use-cases in the description.",
        )
    return None


def check_missing_attributes(
    color: Optional[str],
    size: Optional[str],
    material: Optional[str],
    category: Optional[str],
) -> Optional[IssueResult]:
    missing = [f for f, v in [("color", color), ("size", size), ("material", material), ("category", category)] if not v or not str(v).strip()]
    if len(missing) >= 2:
        return (
            "MISSING_ATTRIBUTES",
            Severity.MEDIUM,
            f"Important attributes are missing: {', '.join(missing)}.",
            "Add color, size, material, and category to improve listing quality.",
        )
    return None


def check_out_of_stock(availability: bool) -> Optional[IssueResult]:
    if not availability:
        return (
            "OUT_OF_STOCK",
            Severity.LOW,
            "Product is out of stock.",
            "Restock or mark the product separately. Notify the operations team.",
        )
    return None


def run_all_rules(
    sku_id: str,
    product_title: Optional[str],
    description: Optional[str],
    brand: Optional[str],
    category: Optional[str],
    price: Optional[float],
    mrp: Optional[float],
    image_url: Optional[str],
    availability: bool,
    color: Optional[str],
    size: Optional[str],
    material: Optional[str],
    existing_sku_ids: Optional[set[str]] = None,
) -> list[IssueResult]:
    issues: list[IssueResult] = []

    for result in [
        check_missing_title(product_title),
        check_short_title(product_title),
        check_missing_brand(brand),
        check_invalid_price(price),
        check_mrp_lower_than_price(price, mrp),
        check_missing_image(image_url),
        check_broken_image_url(image_url),
        check_weak_description(description),
        check_missing_attributes(color, size, material, category),
        check_out_of_stock(availability),
    ]:
        if result:
            issues.append(result)

    return issues
