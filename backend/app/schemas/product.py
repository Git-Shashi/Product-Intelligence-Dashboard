from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.db.models import AlertStatus, ProductSource, Severity


class ListingIssueOut(BaseModel):
    id: int
    type: str
    severity: Severity
    message: str
    suggested_fix: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompetitorPriceOut(BaseModel):
    id: int
    platform: str
    competitor_url: Optional[str] = None
    competitor_price: float
    currency: str
    last_checked_at: datetime

    model_config = {"from_attributes": True}


class EnhancedTitleOut(BaseModel):
    id: int
    original_title: str
    attributes: dict
    keywords: list
    enhanced_title: str
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    sku_id: str
    product_title: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    availability: bool = True
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None


class ProductOut(ProductBase):
    id: int
    source: ProductSource
    quality_score: int
    created_at: datetime
    updated_at: datetime
    issues: list[ListingIssueOut] = []
    competitor_prices: list[CompetitorPriceOut] = []
    enhanced_titles: list[EnhancedTitleOut] = []

    model_config = {"from_attributes": True}


class ProductUpdate(BaseModel):
    product_title: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    availability: Optional[bool] = None
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None


class PriceComparisonOut(BaseModel):
    our_price: Optional[float]
    lowest_competitor: Optional[float]
    highest_competitor: Optional[float]
    average_competitor: Optional[float]
    price_gap: Optional[float]
    percentage_diff: Optional[float]
    recommended_action: str
    competitors: list[CompetitorPriceOut] = []
