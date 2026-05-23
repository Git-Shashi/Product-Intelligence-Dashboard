import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models import Alert, AlertStatus, CompetitorPrice, Job, JobStatus, JobType, Product, Severity
from app.db.session import AsyncSessionLocal
from app.domain.price_comparison import compute_comparison, is_significant_price_drop, should_raise_price_alert
from app.jobs.runner import mark_completed, mark_failed, mark_running, update_progress
from app.schemas.competitor import CompetitorRefreshOut, CompetitorUploadOut
from app.schemas.product import CompetitorPriceOut, PriceComparisonOut
from app.services.competitor.csv_competitor import parse_csv
from app.services.competitor.factory import get_competitor_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/competitor-prices", tags=["competitor"])
products_router = APIRouter(tags=["competitor"])


# ── helpers ──────────────────────────────────────────────────────────────────

async def _upsert_competitor_prices(
    db: AsyncSession,
    product: Product,
    price_data_list: list,
    check_drops: bool = False,
) -> list[str]:
    """
    Write new CompetitorPrice rows. If check_drops=True, compare against the
    most recent existing price per platform and raise MEDIUM alerts on drops.
    Returns list of alert messages raised.
    """
    alerts_raised: list[str] = []

    for pd in price_data_list:
        # Look up the most recent price for this platform
        result = await db.execute(
            select(CompetitorPrice)
            .where(
                CompetitorPrice.product_id == product.id,
                CompetitorPrice.platform == pd.platform,
            )
            .order_by(CompetitorPrice.last_checked_at.desc())
            .limit(1)
        )
        existing = result.scalar_one_or_none()

        if check_drops and existing:
            if is_significant_price_drop(existing.competitor_price, pd.competitor_price):
                drop_pct = ((existing.competitor_price - pd.competitor_price) / existing.competitor_price) * 100
                msg = (
                    f"[{product.sku_id}] {pd.platform} price dropped "
                    f"from ₹{existing.competitor_price:,.0f} to ₹{pd.competitor_price:,.0f} "
                    f"({drop_pct:.1f}% drop)."
                )
                db.add(Alert(
                    product_id=product.id,
                    type="COMPETITOR_PRICE_DROP",
                    severity=Severity.MEDIUM,
                    message=msg,
                    status=AlertStatus.OPEN,
                ))
                alerts_raised.append(msg)

        db.add(CompetitorPrice(
            product_id=product.id,
            platform=pd.platform,
            competitor_price=pd.competitor_price,
            competitor_url=pd.competitor_url,
            currency=pd.currency,
            last_checked_at=datetime.now(timezone.utc),
        ))

    return alerts_raised


async def _raise_price_alert_if_needed(db: AsyncSession, product: Product) -> None:
    """HIGH alert if our price is >10% above the lowest competitor."""
    result = await db.execute(
        select(CompetitorPrice).where(CompetitorPrice.product_id == product.id)
    )
    prices = [r.competitor_price for r in result.scalars().all()]
    if not prices:
        return

    comparison = compute_comparison(product.price, prices)
    if should_raise_price_alert(product.price, comparison.lowest_competitor):
        msg = (
            f"[{product.sku_id}] Our Flipkart price (₹{product.price:,.0f}) is "
            f"{comparison.percentage_diff:.1f}% higher than the lowest competitor "
            f"(₹{comparison.lowest_competitor:,.0f} on a competitor platform)."
        )
        # Only raise if no open alert of this type exists
        existing = await db.execute(
            select(Alert).where(
                Alert.product_id == product.id,
                Alert.type == "PRICE_TOO_HIGH",
                Alert.status == AlertStatus.OPEN,
            )
        )
        if not existing.scalar_one_or_none():
            db.add(Alert(
                product_id=product.id,
                type="PRICE_TOO_HIGH",
                severity=Severity.HIGH,
                message=msg,
                status=AlertStatus.OPEN,
            ))


# ── background job ────────────────────────────────────────────────────────────

async def _run_refresh_job(job_id: int) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(Job, job_id)
        if not job:
            return
        await mark_running(db, job)
        try:
            result = await db.execute(select(Product))
            products = result.scalars().all()
            service = get_competitor_service()
            total = len(products)
            refreshed = 0
            alerts_raised = 0

            for i, product in enumerate(products):
                price_data = service.get_prices(product.sku_id, product.price)
                new_alerts = await _upsert_competitor_prices(db, product, price_data, check_drops=True)
                alerts_raised += len(new_alerts)
                await _raise_price_alert_if_needed(db, product)
                refreshed += 1
                await update_progress(db, job, int((i + 1) / total * 90))

            await db.commit()
            await mark_completed(db, job, {"refreshed": refreshed, "alerts_raised": alerts_raised})
        except Exception as exc:
            logger.exception("Price refresh job %s failed", job_id)
            await mark_failed(db, job, str(exc))


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=CompetitorUploadOut)
async def upload_competitor_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    rows = parse_csv(contents)
    inserted = skipped = 0

    for sku_id, pd in rows:
        result = await db.execute(select(Product).where(Product.sku_id == sku_id))
        product = result.scalar_one_or_none()
        if not product:
            skipped += 1
            continue
        await _upsert_competitor_prices(db, product, [pd], check_drops=False)
        inserted += 1

    # Check price alerts for affected products
    affected_skus = {sku for sku, _ in rows}
    for sku_id in affected_skus:
        result = await db.execute(select(Product).where(Product.sku_id == sku_id))
        product = result.scalar_one_or_none()
        if product:
            await _raise_price_alert_if_needed(db, product)

    await db.commit()
    return {"inserted": inserted, "skipped": skipped}


@router.post("/refresh", response_model=CompetitorRefreshOut)
async def refresh_prices(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    job = Job(type=JobType.PRICE_REFRESH, status=JobStatus.PENDING)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    background_tasks.add_task(_run_refresh_job, job.id)
    return {"job_id": job.id}


@products_router.get("/products/{sku_id}/competitor-prices", response_model=PriceComparisonOut)
async def get_competitor_prices(sku_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.sku_id == sku_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    cp_result = await db.execute(
        select(CompetitorPrice)
        .where(CompetitorPrice.product_id == product.id)
        .order_by(CompetitorPrice.platform, CompetitorPrice.last_checked_at.desc())
    )
    all_rows = cp_result.scalars().all()

    # Deduplicate: keep latest per platform
    seen: dict[str, CompetitorPrice] = {}
    for row in all_rows:
        if row.platform not in seen:
            seen[row.platform] = row
    latest = list(seen.values())

    prices = [r.competitor_price for r in latest]
    comparison = compute_comparison(product.price, prices)

    return PriceComparisonOut(
        our_price=comparison.our_price,
        lowest_competitor=comparison.lowest_competitor,
        highest_competitor=comparison.highest_competitor,
        average_competitor=comparison.average_competitor,
        price_gap=comparison.price_gap,
        percentage_diff=comparison.percentage_diff,
        recommended_action=comparison.recommended_action,
        competitors=[CompetitorPriceOut.model_validate(r) for r in latest],
    )
