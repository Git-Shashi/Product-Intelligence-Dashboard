import logging

from app.core.config import settings
from app.services.extraction.extractor import ExtractionFailed, ExtractedProduct
from app.services.extraction.mock_extractor import MockExtractor
from app.services.extraction.ocr_extractor import OcrExtractor

logger = logging.getLogger(__name__)

_mock = MockExtractor()
_ocr = OcrExtractor()


def extract(video_path: str, sku_id: str) -> ExtractedProduct:
    """
    Use OCR by default. Falls back to mock if:
    - EXTRACTION_PROVIDER=mock
    - OCR raises ExtractionFailed
    - Any unexpected exception
    """
    if settings.extraction_provider == "mock":
        logger.info("Extraction provider=mock, skipping OCR")
        return _mock.extract(video_path, sku_id)

    try:
        result = _ocr.extract(video_path, sku_id)
        logger.info("OCR extraction succeeded for %s (title=%s)", sku_id, result.product_title)
        return result
    except ExtractionFailed as e:
        logger.warning("OCR failed for %s (%s) — using mock extractor", sku_id, e)
        result = _mock.extract(video_path, sku_id)
        result.used_mock = True
        return result
    except Exception as e:
        logger.exception("Unexpected OCR error for %s — using mock extractor", sku_id)
        result = _mock.extract(video_path, sku_id)
        result.used_mock = True
        return result
