"""Lưu file đính kèm lên Cloudflare R2 (S3-compatible)."""
import boto3

from app.core.config import settings


import os
import shutil
from fastapi import HTTPException

def _client():
    if not settings.R2_ENDPOINT or not settings.R2_ACCESS_KEY_ID:
        return None
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def upload_fileobj(fileobj, key: str, content_type: str = "") -> str:
    s3 = _client()
    if s3:
        s3.upload_fileobj(
            fileobj, settings.R2_BUCKET, key,
            ExtraArgs={"ContentType": content_type or "application/octet-stream"},
        )
        return f"{settings.R2_PUBLIC_URL.rstrip('/')}/{key}"
    
    # Fallback local
    local_path = os.path.join("uploads", key)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        shutil.copyfileobj(fileobj, f)
    return f"/api/uploads/{key}"


def delete_key(key: str):
    s3 = _client()
    if s3:
        try:
            s3.delete_object(Bucket=settings.R2_BUCKET, Key=key)
        except Exception:
            pass
    else:
        local_path = os.path.join("uploads", key)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass
