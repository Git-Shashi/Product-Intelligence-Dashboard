"""
Real OCR extractor: ffmpeg frame grab → Pillow preprocessing → pytesseract → attribute parsing.
Raises ExtractionFailed if OCR yields nothing usable; caller should fall back to mock.
"""
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from app.services.extraction.extractor import ExtractionFailed, ExtractedProduct

logger = logging.getLogger(__name__)

# --- Known-value lists for keyword matching ---
_BRANDS = [
    "nike", "adidas", "puma", "reebok", "levi", "zara", "h&m", "hm", "mango",
    "casio", "samsung", "apple", "oneplus", "xiaomi", "boat", "sony", "lg",
    "lakme", "maybelline", "loreal", "himalaya", "biotique", "forest essentials",
    "wildcraft", "american tourister", "vip", "skybags", "fastrack", "titan",
    "woodland", "red tape", "bata", "liberty", "campus", "skechers", "crocs",
]

_CATEGORIES = {
    "shoes": "Shoes", "footwear": "Shoes", "sneakers": "Shoes", "boots": "Shoes",
    "sandals": "Shoes", "slippers": "Shoes", "heels": "Shoes",
    "dress": "Dresses", "gown": "Dresses", "skirt": "Dresses",
    "shirt": "Apparel", "t-shirt": "Apparel", "tshirt": "Apparel", "top": "Apparel",
    "jeans": "Apparel", "trousers": "Apparel", "kurta": "Apparel", "saree": "Apparel",
    "jacket": "Apparel", "hoodie": "Apparel", "sweater": "Apparel",
    "bag": "Bags", "handbag": "Bags", "backpack": "Bags", "wallet": "Bags",
    "watch": "Electronics", "smartwatch": "Electronics", "phone": "Electronics",
    "earphones": "Electronics", "headphones": "Electronics", "laptop": "Electronics",
    "cream": "Beauty", "serum": "Beauty", "moisturiser": "Beauty", "lipstick": "Beauty",
    "shampoo": "Beauty", "conditioner": "Beauty",
    "dumbbell": "Sports", "yoga": "Sports", "gym": "Sports",
}

_COLORS = [
    "black", "white", "red", "blue", "green", "yellow", "orange", "purple",
    "pink", "grey", "gray", "brown", "navy", "beige", "cream", "maroon",
    "olive", "teal", "cyan", "magenta", "gold", "silver",
]

_MATERIALS = [
    "cotton", "polyester", "nylon", "leather", "canvas", "mesh", "wool",
    "silk", "denim", "linen", "suede", "rubber", "foam", "metal", "aluminum",
    "stainless steel", "plastic", "resin", "fabric",
]

_SIZE_PATTERNS = [
    r"\b(XS|S|M|L|XL|XXL|XXXL)\b",
    r"\bUK\s*\d+(?:\.\d+)?\b",
    r"\bUS\s*\d+(?:\.\d+)?\b",
    r"\b\d+\s*(?:cm|mm|inch|inches|ft)\b",
]

_PRICE_PATTERNS = [
    r"(?:₹|Rs\.?|INR)\s*(\d[\d,]*(?:\.\d{1,2})?)",
    r"(\d[\d,]*(?:\.\d{1,2})?)\s*(?:₹|Rs\.?|INR)",
]

_MRP_PATTERN = r"MRP\s*:?\s*(?:₹|Rs\.?|INR)?\s*(\d[\d,]*(?:\.\d{1,2})?)"


def _find_ffmpeg() -> Optional[str]:
    path = shutil.which("ffmpeg")
    if path:
        return path
    for candidate in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"]:
        if os.path.isfile(candidate):
            return candidate
    return None


def _extract_frames(video_path: str, out_dir: str, fps: float = 0.5, max_frames: int = 20) -> list[str]:
    """Extract up to max_frames frames from the video at given fps."""
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise ExtractionFailed("ffmpeg not found")

    pattern = os.path.join(out_dir, "frame_%04d.png")
    cmd = [
        ffmpeg, "-i", video_path,
        "-vf", f"fps={fps}",
        "-frames:v", str(max_frames),
        "-q:v", "2",
        pattern,
        "-y", "-loglevel", "error",
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    if result.returncode != 0:
        raise ExtractionFailed(f"ffmpeg failed: {result.stderr.decode()[:200]}")

    return sorted(Path(out_dir).glob("frame_*.png"))


def _preprocess_frame(image_path: str):
    """Grayscale + threshold to improve OCR accuracy."""
    from PIL import Image, ImageFilter, ImageOps
    img = Image.open(image_path).convert("L")
    # Scale up if small
    w, h = img.size
    if w < 1200:
        img = img.resize((int(w * 1200 / w), int(h * 1200 / w)), Image.LANCZOS)
    img = ImageOps.autocontrast(img)
    return img


def _ocr_frames(frame_paths: list) -> str:
    """Run tesseract on each frame and combine the text."""
    import pytesseract
    texts: list[str] = []
    for path in frame_paths:
        try:
            img = _preprocess_frame(str(path))
            text = pytesseract.image_to_string(img, config="--psm 6")
            if text.strip():
                texts.append(text)
        except Exception as e:
            logger.debug("OCR failed on frame %s: %s", path, e)
    return "\n".join(texts)


def _parse_price(text: str) -> Optional[float]:
    for pattern in _PRICE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def _parse_mrp(text: str) -> Optional[float]:
    match = re.search(_MRP_PATTERN, text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _parse_brand(text: str) -> Optional[str]:
    lower = text.lower()
    for brand in _BRANDS:
        if brand in lower:
            return brand.title()
    return None


def _parse_category(text: str) -> Optional[str]:
    lower = text.lower()
    for keyword, category in _CATEGORIES.items():
        if keyword in lower:
            return category
    return None


def _parse_color(text: str) -> Optional[str]:
    lower = text.lower()
    for color in _COLORS:
        if re.search(rf"\b{color}\b", lower):
            return color.title()
    return None


def _parse_material(text: str) -> Optional[str]:
    lower = text.lower()
    for material in _MATERIALS:
        if re.search(rf"\b{material}\b", lower):
            return material.title()
    return None


def _parse_size(text: str) -> Optional[str]:
    for pattern in _SIZE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def _parse_title(text: str, brand: Optional[str], category: Optional[str]) -> Optional[str]:
    """Best-effort: pick the longest meaningful line."""
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 8]
    if not lines:
        return None
    # Prefer lines containing brand or category keywords
    scored = []
    for line in lines:
        score = len(line)
        if brand and brand.lower() in line.lower():
            score += 50
        if category and category.lower() in line.lower():
            score += 30
        # Penalise lines that look like noise (all caps, URLs, long numbers)
        if re.match(r"^[A-Z0-9\s\-\.]+$", line) and len(line) > 40:
            score -= 20
        if re.search(r"https?://", line):
            score -= 100
        scored.append((score, line))
    scored.sort(reverse=True)
    best = scored[0][1]
    return best[:200] if best else None


def _is_usable(product: ExtractedProduct) -> bool:
    """At least title or price must have been extracted."""
    return bool(product.product_title or product.price)


class OcrExtractor:
    def extract(self, video_path: str, sku_id: str) -> ExtractedProduct:
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                frames = _extract_frames(video_path, tmp_dir)
            except ExtractionFailed:
                raise
            except Exception as e:
                raise ExtractionFailed(f"Frame extraction error: {e}") from e

            if not frames:
                raise ExtractionFailed("No frames extracted from video")

            raw_text = _ocr_frames(frames)
            logger.info("OCR combined text length: %d chars from %d frames", len(raw_text), len(frames))

            if not raw_text.strip():
                raise ExtractionFailed("OCR produced no text")

            brand = _parse_brand(raw_text)
            category = _parse_category(raw_text)
            price = _parse_price(raw_text)
            mrp = _parse_mrp(raw_text)
            # If MRP not found separately, try treating second price occurrence as MRP
            if mrp is None and price is not None:
                prices_found = []
                for pattern in _PRICE_PATTERNS:
                    prices_found += [
                        float(m.replace(",", ""))
                        for m in re.findall(pattern, raw_text, re.IGNORECASE)
                        if m
                    ]
                prices_found = sorted(set(prices_found), reverse=True)
                if len(prices_found) >= 2:
                    mrp = prices_found[0]
                    price = prices_found[1]

            product = ExtractedProduct(
                sku_id=sku_id,
                product_title=_parse_title(raw_text, brand, category),
                brand=brand,
                category=category,
                price=price,
                mrp=mrp,
                color=_parse_color(raw_text),
                size=_parse_size(raw_text),
                material=_parse_material(raw_text),
                raw_ocr_text=raw_text[:2000],
                used_mock=False,
            )

            if not _is_usable(product):
                raise ExtractionFailed("OCR text not parseable into usable product fields")

            return product
