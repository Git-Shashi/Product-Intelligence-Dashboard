import logging
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.db.models import Job, JobStatus, JobType, ProductSource
from app.db.session import AsyncSessionLocal
from app.domain.enhance_title import generate_enhanced_title
from app.jobs.pipeline import _get_existing_skus, process_product_row
from app.jobs.runner import mark_completed, mark_failed, mark_running, update_progress
from app.schemas.job import JobCreated
from app.services.extraction.factory import extract

logger = logging.getLogger(__name__)
router = APIRouter(tags=["video"])

ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm", "video/mpeg"}


async def _run_video_job(job_id: int, video_path: str, sku_id: str, enhance: bool) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(Job, job_id)
        if not job:
            return
        await mark_running(db, job)
        try:
            await update_progress(db, job, 10)

            # Extract product data (real OCR or mock fallback)
            extracted = extract(video_path, sku_id)
            await update_progress(db, job, 50)

            existing_skus = await _get_existing_skus(db)
            row = {
                "sku_id": extracted.sku_id,
                "product_title": extracted.product_title,
                "description": extracted.description,
                "brand": extracted.brand,
                "category": extracted.category,
                "price": extracted.price,
                "mrp": extracted.mrp,
                "image_url": extracted.image_url,
                "availability": extracted.availability,
                "color": extracted.color,
                "size": extracted.size,
                "material": extracted.material,
            }
            ok, err = await process_product_row(db, row, ProductSource.VIDEO, existing_skus)
            if not ok:
                await mark_failed(db, job, err)
                return

            await update_progress(db, job, 80)

            summary: dict = {
                "sku_id": sku_id,
                "used_mock": extracted.used_mock,
                "fields_extracted": [
                    f for f, v in {
                        "title": extracted.product_title,
                        "brand": extracted.brand,
                        "category": extracted.category,
                        "price": extracted.price,
                        "color": extracted.color,
                    }.items() if v
                ],
            }

            # Optionally run title enhancement
            if enhance:
                from sqlalchemy import select
                from app.db.models import Product
                from sqlalchemy.orm import selectinload
                result = await db.execute(
                    select(Product)
                    .options(selectinload(Product.enhanced_titles))
                    .where(Product.sku_id == sku_id)
                )
                product = result.scalar_one_or_none()
                if product:
                    enhanced = await generate_enhanced_title(db, product)
                    summary["enhanced_title"] = enhanced.enhanced_title

            await mark_completed(db, job, summary)
        except Exception as exc:
            logger.exception("Video job %s failed", job_id)
            await mark_failed(db, job, str(exc))
        finally:
            # Clean up temp file
            try:
                os.remove(video_path)
            except OSError:
                pass


@router.post("/upload-video", response_model=JobCreated)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enhance_title: bool = Form(False),
    sku_id: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type and file.content_type not in ALLOWED_VIDEO_TYPES:
        # Be lenient — some clients send wrong MIME for .mp4
        if not (file.filename or "").lower().endswith((".mp4", ".mov", ".avi", ".webm", ".mpeg")):
            raise HTTPException(status_code=400, detail="Unsupported file type. Upload an MP4, MOV, AVI, or WebM video.")

    # Save to temp file
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    tmp_path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}{ext}")
    os.makedirs(settings.upload_dir, exist_ok=True)

    contents = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(contents)

    # Generate SKU if not provided
    if not sku_id.strip():
        sku_id = f"VID-{uuid.uuid4().hex[:8].upper()}"

    job = Job(type=JobType.VIDEO_EXTRACTION, status=JobStatus.PENDING)
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(_run_video_job, job.id, tmp_path, sku_id.strip(), enhance_title)
    return {"job_id": job.id}
