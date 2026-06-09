import base64
import mimetypes
import os
import uuid
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

from fastapi import HTTPException


SUPABASE_ENV_KEYS = (
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_STORAGE_BUCKET",
)


def has_supabase_storage_config() -> bool:
    return all(os.getenv(key) for key in SUPABASE_ENV_KEYS)


def get_storage_mode() -> str:
    configured_mode = (os.getenv("IMAGE_STORAGE_MODE") or "auto").strip().lower()
    if configured_mode in {"supabase", "local", "base64"}:
        return configured_mode

    if has_supabase_storage_config():
        return "supabase"
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


def upload_to_supabase_storage(contents: bytes, content_type: str, folder: str) -> str:
    supabase_url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET") or ""

    filename = f"{uuid.uuid4().hex}{guess_extension(content_type)}"
    object_path = f"{folder}/{filename}"
    upload_url = f"{supabase_url}/storage/v1/object/{bucket}/{object_path}"
    public_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{object_path}"

    request = urllib_request.Request(
        upload_url,
        data=contents,
        method="POST",
        headers={
            "Authorization": f"Bearer {service_role_key}",
            "apikey": service_role_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        },
    )

    try:
        with urllib_request.urlopen(request):
            return public_url
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(status_code=500, detail=f"图片上传失败：{detail or exc.reason}")
    except urllib_error.URLError as exc:
        raise HTTPException(status_code=500, detail=f"图片上传失败：{exc.reason}")


def store_image_asset(contents: bytes, content_type: str, folder: str = "species") -> str:
    mode = get_storage_mode()

    if mode == "supabase" and has_supabase_storage_config():
        return upload_to_supabase_storage(contents, content_type, folder)
    if mode == "local":
        return save_local_image(contents, content_type, folder)
    return build_data_uri(contents, content_type)
