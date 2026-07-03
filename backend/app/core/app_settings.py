"""Cấu hình hiệu lực (effective settings).
- Key thường: lưu DB (plaintext), DB ĐÈ .env.
- Key bí mật (SMTP password, R2 keys): lưu DB **đã mã hóa** (Fernet, khóa suy từ JWT_SECRET),
  API không bao giờ trả ngược giá trị (chỉ trạng thái đã cấu hình/chưa). .env là fallback.
Có cache in-process ngắn để tránh query mỗi lần.
"""
import base64
import hashlib
import time

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings as _env

# key DB → (kiểu, thuộc tính fallback .env) — sửa & hiển thị được
REGISTRY = {
    "email_enabled": ("bool", "EMAIL_ENABLED"),
    "smtp_host": ("str", "SMTP_HOST"),
    "smtp_port": ("int", "SMTP_PORT"),
    "smtp_from": ("str", "SMTP_FROM"),
    "smtp_user": ("str", "SMTP_USER"),
    "r2_endpoint": ("str", "R2_ENDPOINT"),
    "r2_bucket": ("str", "R2_BUCKET"),
    "r2_public_url": ("str", "R2_PUBLIC_URL"),
}

# key bí mật → thuộc tính fallback .env — NHẬP được nhưng không hiển thị lại
SECRETS = {
    "smtp_password": "SMTP_PASSWORD",
    "r2_access_key_id": "R2_ACCESS_KEY_ID",
    "r2_secret_access_key": "R2_SECRET_ACCESS_KEY",
}

_cache: dict = {}
_exp = 0.0
_TTL = 30.0


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(_env.JWT_SECRET.encode()).digest())
    return Fernet(key)


def encrypt(s: str) -> str:
    return _fernet().encrypt(s.encode()).decode()


def _decrypt(s: str) -> str:
    try:
        return _fernet().decrypt(s.encode()).decode()
    except (InvalidToken, Exception):
        return ""


def _load():
    global _cache, _exp
    from app.core.database import SessionLocal
    from app.modules.setting.model import Setting
    db = SessionLocal()
    try:
        _cache = {s.skey: s.svalue for s in db.query(Setting).all()}
    finally:
        db.close()
    _exp = time.time() + _TTL


def refresh():
    global _exp
    _exp = 0.0


def _cast(t: str, raw: str):
    if t == "bool":
        return str(raw).strip().lower() in ("1", "true", "yes", "on")
    if t == "int":
        try:
            return int(raw)
        except (ValueError, TypeError):
            return 0
    return raw


def get(key: str):
    """Giá trị hiệu lực: DB (nếu có) → .env. Secret được giải mã khi trả về (chỉ dùng nội bộ)."""
    if time.time() > _exp:
        _load()
    raw = _cache.get(key)
    if key in SECRETS:
        if raw not in (None, ""):
            dec = _decrypt(raw)
            if dec:
                return dec
        return getattr(_env, SECRETS[key], "")
    if key in REGISTRY:
        t, env_attr = REGISTRY[key]
        if raw not in (None, ""):
            return _cast(t, raw)
        return getattr(_env, env_attr)
    return getattr(_env, key.upper(), None)


def secret_configured(key: str) -> bool:
    if time.time() > _exp:
        _load()
    if _cache.get(key):
        return True
    return bool(getattr(_env, SECRETS.get(key, ""), ""))
