"""Lưu file đính kèm lên Cloudflare R2 (S3-compatible)."""
import boto3

from app.core.config import settings


import os
import shutil
from fastapi import HTTPException

def _eff(key: str):
    from app.core import app_settings
    return app_settings.get(key)


def _r2_ready() -> bool:
    """R2 chỉ 'sẵn sàng' khi có ĐỦ endpoint + access key + public_url.
    Thiếu public_url thì không thể sinh URL công khai hợp lệ → coi như chưa cấu hình
    và fallback lưu local (tránh lưu URL vỡ dạng '/file/...' làm file 'upload lên không hiện').
    Quyết định tập trung ở đây để upload/download/delete luôn đồng bộ cùng 1 nơi lưu."""
    endpoint = _eff("r2_endpoint")
    akey = _eff("r2_access_key_id")
    pub = (_eff("r2_public_url") or "").strip()
    return bool(endpoint and akey and pub)


def _client():
    if not _r2_ready():
        return None
    return boto3.client(
        "s3",
        endpoint_url=_eff("r2_endpoint"),
        aws_access_key_id=_eff("r2_access_key_id"),
        aws_secret_access_key=_eff("r2_secret_access_key"),
        region_name="auto",
    )


def upload_fileobj(fileobj, key: str, content_type: str = "") -> str:
    s3 = _client()
    if s3:
        s3.upload_fileobj(
            fileobj, _eff("r2_bucket"), key,
            ExtraArgs={"ContentType": content_type or "application/octet-stream"},
        )
        return f"{(_eff('r2_public_url') or '').rstrip('/')}/{key}"
    
    # Fallback local
    local_path = os.path.join("uploads", key)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        shutil.copyfileobj(fileobj, f)
    return f"/api/uploads/{key}"


def download_bytes(key: str) -> bytes:
    """Đọc lại nội dung file từ storage (R2 hoặc local) để tải/nén ZIP."""
    s3 = _client()
    if s3:
        obj = s3.get_object(Bucket=_eff("r2_bucket"), Key=key)
        return obj["Body"].read()
    local_path = os.path.join("uploads", key)
    if not os.path.exists(local_path):
        raise HTTPException(404, "File không tồn tại trên storage")
    with open(local_path, "rb") as f:
        return f.read()


def delete_key(key: str):
    s3 = _client()
    if s3:
        try:
            s3.delete_object(Bucket=_eff("r2_bucket"), Key=key)
        except Exception:
            pass
    else:
        local_path = os.path.join("uploads", key)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass
