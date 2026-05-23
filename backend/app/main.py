import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.alerts import router as alerts_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.products import router as products_router
from app.api.routes.video import router as video_router
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs(settings.upload_dir, exist_ok=True)

app = FastAPI(
    title="Product Intelligence Dashboard",
    description="API for extracting, validating, and monitoring e-commerce product listings.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(dashboard_router)
app.include_router(alerts_router)
app.include_router(products_router)
app.include_router(video_router)
