"""
Seed the database with demo data so the deployed dashboard is populated on first boot.
Run: python seed.py
"""
import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.db.models import ProductSource
from app.jobs.pipeline import _get_existing_skus, process_product_row

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_PRODUCTS = [
    {
        "sku_id": "SHOE001",
        "product_title": "Nike Blue Running Shoes",
        "brand": "Nike",
        "category": "Shoes",
        "price": 3999,
        "mrp": 4999,
        "availability": True,
        "color": "Blue",
        "size": "UK 9",
        "material": "Mesh",
        "description": "Lightweight Nike running shoes with breathable mesh upper, cushioned sole, and durable rubber outsole. Perfect for daily runs and gym workouts.",
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
        "product_url": "https://www.flipkart.com/nike-blue-running-shoes/p/SHOE001",
    },
    {
        "sku_id": "DRESS001",
        "product_title": "Red Floral Dress",
        "brand": "Zara",
        "category": "Dresses",
        "price": 1799,
        "mrp": 2499,
        "availability": True,
        "color": "Red",
        "size": "M",
        "material": "Cotton",
        "description": "Elegant red floral dress from Zara. Lightweight cotton fabric, perfect for parties, dates, and casual outings. Available in multiple sizes.",
        "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400",
        "product_url": "https://www.flipkart.com/zara-red-dress/p/DRESS001",
    },
    {
        "sku_id": "BAG001",
        "product_title": "",
        "brand": "Puma",
        "category": "Bags",
        "price": None,
        "mrp": 1299,
        "availability": False,
        "color": "",
        "size": "",
        "material": "",
        "description": "",
        "image_url": "",
        "product_url": "",
    },
    {
        "sku_id": "TSHIRT001",
        "product_title": "Men Cotton Casual T-Shirt",
        "brand": "H&M",
        "category": "Apparel",
        "price": 599,
        "mrp": 799,
        "availability": True,
        "color": "Navy Blue",
        "size": "L",
        "material": "100% Cotton",
        "description": "Comfortable everyday cotton t-shirt for men. Soft fabric, breathable and machine washable.",
        "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
        "product_url": "https://www.flipkart.com/hm-tshirt/p/TSHIRT001",
    },
    {
        "sku_id": "WATCH001",
        "product_title": "Casio Digital Sports Watch",
        "brand": "Casio",
        "category": "Electronics",
        "price": 2200,
        "mrp": 2200,
        "availability": True,
        "color": "Black",
        "size": "One Size",
        "material": "Resin",
        "description": "Casio digital watch with stopwatch, alarm, and water resistance up to 50m. Durable resin case and strap.",
        "image_url": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400",
        "product_url": "https://www.flipkart.com/casio-watch/p/WATCH001",
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        existing = await _get_existing_skus(db)
        inserted = 0
        for row in SEED_PRODUCTS:
            if row["sku_id"] in existing:
                logger.info("Skipping existing SKU: %s", row["sku_id"])
                continue
            ok, err = await process_product_row(db, row, ProductSource.MANUAL, existing)
            if ok:
                inserted += 1
                logger.info("Seeded: %s", row["sku_id"])
            else:
                logger.warning("Failed to seed %s: %s", row["sku_id"], err)
        logger.info("Seed complete. Inserted %d products.", inserted)


if __name__ == "__main__":
    asyncio.run(seed())
