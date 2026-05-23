import shutil
import subprocess

from fastapi import APIRouter

router = APIRouter()


def _check_ocr() -> bool:
    if not shutil.which("tesseract"):
        return False
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_ffmpeg() -> bool:
    if not shutil.which("ffmpeg"):
        return False
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


@router.get("/health")
async def health():
    return {
        "ok": True,
        "ocr": _check_ocr(),
        "ffmpeg": _check_ffmpeg(),
    }
