from pydantic import BaseModel


class SeverityCount(BaseModel):
    HIGH: int = 0
    MEDIUM: int = 0
    LOW: int = 0


class QualitySummaryOut(BaseModel):
    total_products: int
    avg_quality_score: float
    issue_counts: SeverityCount
    weak_listings: int       # quality_score < 60
    missing_image_count: int
    invalid_price_count: int
    out_of_stock_count: int
