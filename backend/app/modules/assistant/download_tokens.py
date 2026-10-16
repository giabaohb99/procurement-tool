"""Đường tải tệp báo cáo DÙNG MỘT LẦN, ký HMAC, không cần đăng nhập web (ai-CR-207, lỗi 4 của cổng MCP).

Tool `export_report_file` / `export_excel_file` sinh tệp trong `assistant-report/`; đường tải thường
(`/api/assistant/files/{id}/download`) đòi JWT web nên ứng dụng AI ngoài (Claude Desktop qua MCP) không tải được. Tool
trả kèm `download_once_path` = `/api/assistant/files/dl/<mã>`:
- mã = `id.chủ.hết_hạn.nonce.chữ_ký`, chữ ký HMAC-SHA256 bằng `JWT_SECRET` → không sửa được id / chủ / hạn;
- hết hạn sau `TTL_SEC` (15 phút);
- dùng MỘT lần: lượt tải ghi audit (`assistant_file` · `export` · `nonce=…`), lượt sau cùng nonce bị từ chối.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from app.core.config import settings

TTL_SEC = 15 * 60
AUDIT_ENTITY = "assistant_file"
AUDIT_ACTION = "export"


def _sign(payload: str) -> str:
    return hmac.new(settings.JWT_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def make_token(file_id: int, user_id: int, *, ttl: int = TTL_SEC, now: float | None = None) -> str:
    exp = int((now or time.time()) + ttl)
    payload = f"{int(file_id)}.{int(user_id)}.{exp}.{secrets.token_hex(8)}"
    return f"{payload}.{_sign(payload)}"


def read_token(token: str, *, now: float | None = None) -> tuple[int, int, str] | None:
    """(file_id, user_id, nonce) nếu chữ ký đúng và còn hạn; không thì None."""
    parts = str(token or "").split(".")
    if len(parts) != 5 or not all(p.isalnum() for p in parts):
        return None
    payload, sig = ".".join(parts[:4]), parts[4]
    if not hmac.compare_digest(_sign(payload), sig):
        return None
    try:
        fid, uid, exp = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None
    if exp < (now or time.time()):
        return None
    return fid, uid, parts[3]


def once_path(file_id: int, user_id: int) -> str:
    return f"/api/assistant/files/dl/{make_token(file_id, user_id)}"
