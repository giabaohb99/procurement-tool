"""Lưu file đính kèm lên Cloudflare R2 (S3-compatible)."""
import boto3

from app.core.config import settings


import os
import shutil
from fastapi import HTTPException

def _eff(key: str):
    from app.core import app_settings
    return app_settings.get(key)


def _client():
    endpoint = _eff("r2_endpoint")
    akey = _eff("r2_access_key_id")
    skey = _eff("r2_secret_access_key")
    if not endpoint or not akey:
        return None
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=akey,
        aws_secret_access_key=skey,
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
