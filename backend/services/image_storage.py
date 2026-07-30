import base64
import mimetypes
import os
import uuid
from pathlib import Path

def get_storage_mode() -> str:
    configured_mode = (os.getenv("IMAGE_STORAGE_MODE") or "auto").strip().lower()
    if configured_mode in {"local", "base64"}:
        return configured_mode

    if os.getenv("VERCEL"):
        return "base64"
    return "local"

def get_uploads_dir() -> Path:
    raw_path = os.getenv("UPLOADS_DIR")
    if raw_path:
        return Path(raw_path)
    return Path(__file__).resolve().parents[2] / "uploads"

def build_data_uri(contents: bytes, content_type: str) -> str:
    base64_data = base64.b64encode(contents).decode("utf-8")
    return f"data:{content_type};base64,{base64_data}"

def guess_extension(content_type: str) -> str:
    extension = mimetypes.guess_extension(content_type) or ".bin"
    if extension == ".jpe":
        return ".jpg"
    return extension

def save_local_image(contents: bytes, content_type: str, folder: str) -> str:
    uploads_dir = get_uploads_dir()
    target_dir = uploads_dir / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{guess_extension(content_type)}"
    file_path = target_dir / filename
    file_path.write_bytes(contents)
    return f"/uploads/{folder}/{filename}"

def store_image_asset(contents: bytes, content_type: str, folder: str = "species") -> str:
    mode = get_storage_mode()

    if mode == "local":
        return save_local_image(contents, content_type, folder)
    return build_data_uri(contents, content_type)
