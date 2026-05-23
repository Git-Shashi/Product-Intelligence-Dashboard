from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable


@dataclass
class ExtractedProduct:
    sku_id: str
    product_title: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    image_url: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    availability: bool = True
    raw_ocr_text: str = ""
    used_mock: bool = False


class ExtractionFailed(Exception):
    pass


@runtime_checkable
class VideoExtractor(Protocol):
    def extract(self, video_path: str, sku_id: str) -> ExtractedProduct:
        ...
