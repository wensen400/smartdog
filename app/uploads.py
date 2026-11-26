import uuid
from pathlib import Path

from fastapi import UploadFile

from .config import ALLOWED_IMAGE_EXT, MAX_IMAGE_SIZE, UPLOAD_DIR


async def save_image(file: UploadFile) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise ValueError("仅支持 png / jpg / jpeg / gif / webp 图片")

    data = await file.read()
    if len(data) > MAX_IMAGE_SIZE:
        raise ValueError("图片不能超过 5MB")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / filename).write_bytes(data)
    return f"/uploads/{filename}"
