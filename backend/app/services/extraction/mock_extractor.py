"""
Deterministic mock extractor. Seeded by sku_id so tests and demos are reproducible.
Returns a realistic product without needing any video/OCR.
"""
import hashlib

from app.services.extraction.extractor import ExtractedProduct

_MOCK_PRODUCTS = [
    {
        "product_title": "Demo Running Shoes Blue",
        "brand": "SportX",
        "category": "Shoes",
        "price": 2499.0,
        "mrp": 3299.0,
        "color": "Blue",
        "size": "UK 9",
        "material": "Mesh",
        "description": "Lightweight demo running shoes extracted from video. Breathable mesh upper with cushioned sole.",
    },
    {
        "product_title": "Demo Casual T-Shirt",
        "brand": "FashionCo",
        "category": "Apparel",
        "price": 699.0,
        "mrp": 999.0,
        "color": "White",
        "size": "L",
        "material": "Cotton",
        "description": "Comfortable demo cotton t-shirt extracted from video. Regular fit, machine washable.",
    },
    {
        "product_title": "Demo Smartwatch Black",
        "brand": "TechGear",
        "category": "Electronics",
        "price": 4999.0,
        "mrp": 6499.0,
        "color": "Black",
        "size": "One Size",
        "material": "Aluminum",
        "description": "Feature-rich demo smartwatch extracted from video. Heart rate monitor, GPS, 7-day battery.",
    },
    {
        "product_title": "Demo Leather Handbag",
        "brand": "LuxeBag",
        "category": "Bags",
        "price": 1899.0,
        "mrp": 2499.0,
        "color": "Brown",
        "size": "Medium",
        "material": "Leather",
        "description": "Elegant demo leather handbag extracted from video. Multiple compartments and durable stitching.",
    },
]


class MockExtractor:
    def extract(self, video_path: str, sku_id: str) -> ExtractedProduct:
        idx = int(hashlib.md5(sku_id.encode()).hexdigest(), 16) % len(_MOCK_PRODUCTS)
        template = _MOCK_PRODUCTS[idx]
        return ExtractedProduct(
            sku_id=sku_id,
            used_mock=True,
            raw_ocr_text="[mock — no OCR performed]",
            **template,
        )
