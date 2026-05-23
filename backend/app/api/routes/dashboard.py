from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models import ListingIssue, Product, Severity
from app.schemas.dashboard import QualitySummaryOut, SeverityCount

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/quality-summary", response_model=QualitySummaryOut)
async def quality_summary(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(Product))).scalar_one()
    avg_score = (await db.execute(select(func.avg(Product.quality_score)))).scalar_one() or 0.0
    weak = (await db.execute(select(func.count()).select_from(Product).where(Product.quality_score < 60))).scalar_one()
    missing_img = (await db.execute(
        select(func.count()).select_from(ListingIssue).where(ListingIssue.type == "MISSING_IMAGE")
    )).scalar_one()
    invalid_price = (await db.execute(
        select(func.count()).select_from(ListingIssue).where(ListingIssue.type == "INVALID_PRICE")
    )).scalar_one()
    out_of_stock = (await db.execute(
        select(func.count()).select_from(ListingIssue).where(ListingIssue.type == "OUT_OF_STOCK")
    )).scalar_one()

    high = (await db.execute(
        select(func.count()).select_from(ListingIssue).where(ListingIssue.severity == Severity.HIGH)
    )).scalar_one()
    medium = (await db.execute(
        select(func.count()).select_from(ListingIssue).where(ListingIssue.severity == Severity.MEDIUM)
    )).scalar_one()
    low = (await db.execute(
        select(func.count()).select_from(ListingIssue).where(ListingIssue.severity == Severity.LOW)
    )).scalar_one()

    return QualitySummaryOut(
        total_products=total,
        avg_quality_score=round(float(avg_score), 1),
        issue_counts=SeverityCount(HIGH=high, MEDIUM=medium, LOW=low),
        weak_listings=weak,
        missing_image_count=missing_img,
        invalid_price_count=invalid_price,
        out_of_stock_count=out_of_stock,
    )
