"""Lưu file đính kèm lên Cloudflare R2 (S3-compatible)."""
import boto3

from app.core.config import settings


def _client():
    if not settings.R2_ENDPOINT or not settings.R2_ACCESS_KEY_ID:
        raise RuntimeError("Chưa cấu hình R2 (R2_ENDPOINT / R2_ACCESS_KEY_ID) trong .env")
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def upload_fileobj(fileobj, key: str, content_type: str = "") -> str:
    _client().upload_fileobj(
        fileobj, settings.R2_BUCKET, key,
        ExtraArgs={"ContentType": content_type or "application/octet-stream"},
    )
    return f"{settings.R2_PUBLIC_URL.rstrip('/')}/{key}"


def delete_key(key: str):
    try:
        _client().delete_object(Bucket=settings.R2_BUCKET, Key=key)
    except Exception:
        pass
