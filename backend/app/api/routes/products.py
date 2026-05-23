import csv
import io
import logging
import os

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.db.models import Job, JobStatus, JobType, ListingIssue, Product, ProductSource, Severity
from app.db.session import AsyncSessionLocal
from app.domain.enhance_title import generate_enhanced_title
from app.jobs.pipeline import _get_existing_skus, process_product_row
from app.jobs.runner import mark_completed, mark_failed, mark_partial, mark_running, update_progress
from app.schemas.job import JobCreated
from app.schemas.product import EnhancedTitleOut, ListingIssueOut, PriceComparisonOut, ProductOut, ProductUpdate

logger = logging.getLogger(__name__)
router = APIRouter(tags=["products"])

_WITH_ALL = [
    selectinload(Product.issues),
    selectinload(Product.competitor_prices),
    selectinload(Product.enhanced_titles),
]


async def _run_csv_job(job_id: int, contents: bytes) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(Job, job_id)
        if not job:
            return
        await mark_running(db, job)
        try:
            text = contents.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            total = len(rows)
            existing_skus = await _get_existing_skus(db)
            inserted = skipped = 0
            failed_rows: list[dict] = []

            for i, row in enumerate(rows):
                ok, err = await process_product_row(db, row, ProductSource.CSV, existing_skus)
                if ok:
                    inserted += 1
                else:
                    skipped += 1
                    failed_rows.append({"row": i + 2, "sku_id": row.get("sku_id", ""), "error": err})
                await update_progress(db, job, int((i + 1) / total * 90))

            summary = {"inserted": inserted, "skipped": skipped, "failed_rows": failed_rows}
            if failed_rows:
                await mark_partial(db, job, summary)
            else:
                await mark_completed(db, job, summary)
        except Exception as exc:
            logger.exception("CSV job %s failed", job_id)
            await mark_failed(db, job, str(exc))


@router.post("/upload-products-csv", response_model=JobCreated)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    job = Job(type=JobType.CSV_VALIDATION, status=JobStatus.PENDING)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    background_tasks.add_task(_run_csv_job, job.id, contents)
    return {"job_id": job.id}


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    severity: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Product).options(*_WITH_ALL).order_by(Product.id.desc())
    result = await db.execute(stmt)
    products = result.scalars().all()

    if severity:
        sev = Severity(severity.upper())
        products = [p for p in products if any(i.severity == sev for i in p.issues)]
    if category:
        products = [p for p in products if (p.category or "").lower() == category.lower()]
    return products


@router.get("/products/{sku_id}", response_model=ProductOut)
async def get_product(sku_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).options(*_WITH_ALL).where(Product.sku_id == sku_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/products/{sku_id}", response_model=ProductOut)
async def update_product(sku_id: str, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).options(*_WITH_ALL).where(Product.sku_id == sku_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    existing_skus = await _get_existing_skus(db)
    existing_skus.discard(sku_id)
    await process_product_row(
        db,
        {
            "sku_id": product.sku_id,
            "product_title": product.product_title,
            "description": product.description,
            "brand": product.brand,
            "category": product.category,
            "price": product.price,
            "mrp": product.mrp,
            "image_url": product.image_url,
            "availability": product.availability,
            "color": product.color,
            "size": product.size,
            "material": product.material,
        },
        product.source,
        existing_skus,
    )
    await db.refresh(product)
    return product


@router.get("/products/{sku_id}/issues", response_model=list[ListingIssueOut])
async def get_issues(sku_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.sku_id == sku_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    issues = await db.execute(select(ListingIssue).where(ListingIssue.product_id == product.id))
    return issues.scalars().all()


@router.post("/products/{sku_id}/enhance-title", response_model=EnhancedTitleOut)
async def enhance_title(sku_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).options(selectinload(Product.enhanced_titles)).where(Product.sku_id == sku_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    enhanced = await generate_enhanced_title(db, product)
    return enhanced
