import os
import shutil
import subprocess

from fastapi import APIRouter

router = APIRouter()

# Common binary locations that may not be in the server process PATH
_EXTRA_PATHS = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"]


def _find_bin(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for directory in _EXTRA_PATHS:
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _run_check(bin_path: str, args: list[str]) -> bool:
    try:
        result = subprocess.run([bin_path] + args, capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def _check_ocr() -> bool:
    path = _find_bin("tesseract")
    return bool(path and _run_check(path, ["--version"]))


def _check_ffmpeg() -> bool:
    path = _find_bin("ffmpeg")
    return bool(path and _run_check(path, ["-version"]))


@router.get("/health")
async def health():
    return {
        "ok": True,
        "ocr": _check_ocr(),
        "ffmpeg": _check_ffmpeg(),
    }
