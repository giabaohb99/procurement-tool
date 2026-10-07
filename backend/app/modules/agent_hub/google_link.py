"""NỐI GOOGLE CÁ NHÂN của từng người (ai-CR-064, M-06 của `doc/agent-hub/04`, phase 5).

Đại ca chốt 25/09/2026: Google CÁ NHÂN (không phải Workspace công ty). Mỗi người bấm «Nối Google» ở Trang cá
nhân → Khóa AI, đi qua màn đồng ý của Google (OAuth 2.0 authorization code), ERP giữ refresh token MÃ HÓA Fernet
(cùng khóa với cấu hình hệ thống). Tool Lịch / Drive chạy bằng token của CHÍNH người hỏi — trên web, Telegram và
cổng MCP đều vậy — nên bot chỉ thấy lịch và tệp của người đó, không thấy của ai khác.

Dùng lại OAuth client của đăng nhập Google (`GOOGLE_CLIENT_ID`, bao-CR-406) + thêm `GOOGLE_CLIENT_SECRET`; redirect
URI là `<AGENT_ERP_URL>/api/agent-hub/google/callback`, phải khai ở Google Cloud Console. Ứng dụng phải ở trạng thái
«In production» (không cần xác minh): để «Testing» thì Google thu hồi token sau 7 ngày.

Gỡ kết nối = thu hồi token phía Google + đóng dòng. Nghỉ việc đóng cùng phiên.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.config import settings

from .model import AgentGoogleLink

log = logging.getLogger("app.agent_hub.google")

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
CALENDAR_URL = "https://www.googleapis.com/calendar/v3"
DRIVE_URL = "https://www.googleapis.com/drive/v3"
TIMEOUT = 20
#  Lịch: đọc + tạo/sửa sự kiện. Drive: đọc mọi tệp của người đó (tìm, mở) + ghi tệp do ERP tạo (lưu báo cáo).
def client_id() -> str:
    """ai-CR-083: client riêng của Trợ lý nếu có, không thì client của đăng nhập Google (ai-CR-064)."""
    if settings.AGENT_GOOGLE_CLIENT_ID:
        return settings.AGENT_GOOGLE_CLIENT_ID
    return settings.GOOGLE_CLIENT_ID


def client_secret() -> str:
    #  Đi theo ĐÚNG client đang dùng: có client riêng thì phải dùng bí mật riêng, không trộn với bí mật cũ.
    if settings.AGENT_GOOGLE_CLIENT_ID:
        return settings.AGENT_GOOGLE_CLIENT_SECRET
    return settings.GOOGLE_CLIENT_SECRET


SCOPES = ("openid", "email",
          "https://www.googleapis.com/auth/calendar.events",
          "https://www.googleapis.com/auth/calendar.readonly",
          "https://www.googleapis.com/auth/drive.readonly",
          "https://www.googleapis.com/auth/drive.file")
STATE_TTL = 600


class GoogleError(Exception):
    """Lỗi đọc được cho người dùng (chưa nối, token hỏng, Google từ chối)."""


def is_configured() -> bool:
    return bool(client_id() and client_secret() and settings.AGENT_ERP_URL)


def redirect_uri() -> str:
    return settings.AGENT_ERP_URL.rstrip("/") + "/api/agent-hub/google/callback"


# ---------------------------------------------------------------------------
# state chống CSRF: user_id + hạn + HMAC(JWT_SECRET) — không cần bảng, không cần session
# ---------------------------------------------------------------------------
def _sign(payload: str) -> str:
    return hmac.new(settings.JWT_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def make_state(user_id: int) -> str:
    payload = f"{user_id}:{int(time.time()) + STATE_TTL}:{secrets.token_urlsafe(8)}"
    return f"{payload}:{_sign(payload)}"


def parse_state(state: str) -> int:
    """Trả user_id; state giả / hết hạn → 0."""
    try:
        uid, exp, nonce, sig = (state or "").split(":")
        payload = f"{uid}:{exp}:{nonce}"
        if not hmac.compare_digest(sig, _sign(payload)) or int(exp) < time.time():
            return 0
        return int(uid)
    except (ValueError, AttributeError):
        return 0


def authorize_url(user_id: int) -> str:
    if not is_configured():
        raise GoogleError("Chưa cấu hình AGENT_GOOGLE_CLIENT_ID / AGENT_GOOGLE_CLIENT_SECRET (hoặc GOOGLE_CLIENT_*) / AGENT_ERP_URL.")
    params = {"client_id": client_id(), "redirect_uri": redirect_uri(), "response_type": "code",
              "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent", "include_granted_scopes": "true",
              "state": make_state(user_id)}
    return f"{AUTH_URL}?{urlencode(params)}"


# ---------------------------------------------------------------------------
# Sổ liên kết
# ---------------------------------------------------------------------------
def get_link(db: Session, user_id: int) -> AgentGoogleLink | None:
    return db.scalar(select(AgentGoogleLink).where(AgentGoogleLink.user_id == user_id, AgentGoogleLink.revoked_at.is_(None))
                     .order_by(AgentGoogleLink.id.desc()).limit(1))


def _post_token(data: dict) -> dict:
    try:
        resp = requests.post(TOKEN_URL, data=data, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise GoogleError(f"Không gọi được Google: {e}") from e
    if resp.status_code != 200:
        raise GoogleError(f"Google từ chối ({resp.status_code}): {resp.text[:200]}")
    return resp.json()


def exchange_code(db: Session, user_id: int, code: str) -> AgentGoogleLink:
    """Đổi mã ủy quyền lấy token; lưu mã hóa; dòng cũ (nếu có) đóng."""
    tok = _post_token({"code": code, "client_id": client_id(), "client_secret": client_secret(),
                       "redirect_uri": redirect_uri(), "grant_type": "authorization_code"})
    refresh = str(tok.get("refresh_token") or "")
    access = str(tok.get("access_token") or "")
    if not refresh or not access:
        raise GoogleError("Google không cấp refresh token — thử «Nối lại» (màn đồng ý phải hiện ra đầy đủ).")
    email = ""
    try:
        info = requests.get(USERINFO_URL, headers={"Authorization": f"Bearer {access}"}, timeout=TIMEOUT)
        if info.status_code == 200:
            email = str(info.json().get("email") or "")
    except requests.RequestException:
        pass
    now = datetime.now()
    for old in db.scalars(select(AgentGoogleLink).where(AgentGoogleLink.user_id == user_id, AgentGoogleLink.revoked_at.is_(None))):
        old.revoked_at = now
    row = AgentGoogleLink(user_id=user_id, email=email[:255], scopes=str(tok.get("scope") or " ".join(SCOPES))[:500],
                          refresh_token_enc=app_settings.encrypt(refresh), access_token_enc=app_settings.encrypt(access),
                          access_expires_at=now + timedelta(seconds=int(tok.get("expires_in") or 3600) - 60),
                          created_by=user_id, updated_by=user_id)
    db.add(row)
    db.commit()
    return row


def access_token(db: Session, link: AgentGoogleLink) -> str:
    """Token còn hạn, hoặc làm mới bằng refresh token rồi lưu lại."""
    if link.access_expires_at and link.access_expires_at > datetime.now() + timedelta(seconds=30):
        cached = app_settings._decrypt(link.access_token_enc or "")
        if cached:
            return cached
    refresh = app_settings._decrypt(link.refresh_token_enc or "")
    if not refresh:
        raise GoogleError("Kết nối Google hỏng (không giải mã được token). Nối lại ở Trang cá nhân → Khóa AI.")
    try:
        tok = _post_token({"refresh_token": refresh, "client_id": client_id(),
                           "client_secret": client_secret(), "grant_type": "refresh_token"})
    except GoogleError as e:
        if "invalid_grant" in str(e):
            link.revoked_at = datetime.now()
            db.commit()
            raise GoogleError("Google đã thu hồi kết nối (đổi mật khẩu hoặc gỡ ứng dụng). Nối lại ở Trang cá nhân → Khóa AI.") from e
        raise
    access = str(tok.get("access_token") or "")
    link.access_token_enc = app_settings.encrypt(access)
    link.access_expires_at = datetime.now() + timedelta(seconds=int(tok.get("expires_in") or 3600) - 60)
    db.commit()
    return access


def revoke(db: Session, link: AgentGoogleLink) -> None:
    token = app_settings._decrypt(link.refresh_token_enc or "")
    if token:
        try:
            requests.post(REVOKE_URL, params={"token": token}, timeout=TIMEOUT)
        except requests.RequestException:
            pass
    link.revoked_at = datetime.now()
    db.commit()


def describe(db: Session, user_id: int) -> dict:
    link = get_link(db, user_id)
    return {"configured": is_configured(), "linked": link is not None, "email": link.email if link else "",
            "linked_at": link.created_at.isoformat(timespec="seconds") if link and link.created_at else None}


# ---------------------------------------------------------------------------
# Gọi Google API dưới token của một người
# ---------------------------------------------------------------------------
def api_get(db: Session, link: AgentGoogleLink, url: str, params: dict | None = None) -> dict:
    return _api(db, link, "GET", url, params=params)


def api_post(db: Session, link: AgentGoogleLink, url: str, body: dict) -> dict:
    return _api(db, link, "POST", url, body=body)


def api_patch(db: Session, link: AgentGoogleLink, url: str, body: dict) -> dict:
    """ai-CR-084: sửa một phần tài nguyên (dời giờ / đổi tên sự kiện) — không tạo mới."""
    return _api(db, link, "PATCH", url, body=body)


def api_delete(db: Session, link: AgentGoogleLink, url: str, params: dict | None = None) -> dict:
    """AI-0003: xóa một tài nguyên (hủy sự kiện lịch). Google trả 204 rỗng → `{}`."""
    return _api(db, link, "DELETE", url, params=params)


def _api(db: Session, link: AgentGoogleLink, method: str, url: str, *, params: dict | None = None, body: dict | None = None) -> dict:
    token = access_token(db, link)
    try:
        resp = requests.request(method, url, params=params, json=body, headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise GoogleError(f"Không gọi được Google: {e}") from e
    if resp.status_code == 401:
        link.access_expires_at = None            # ép làm mới lượt sau
        db.commit()
        raise GoogleError("Google từ chối token, thử lại sau vài giây.")
    if resp.status_code >= 400:
        raise GoogleError(f"Google trả lỗi {resp.status_code}: {resp.text[:200]}")
    if not resp.content:
        return {}
    try:
        return resp.json()
    except ValueError:
        return {"text": resp.text}


def export_text(db: Session, link: AgentGoogleLink, file_id: str, mime: str) -> str:
    """Nội dung chữ của một tệp Drive: Google Docs/Sheets xuất text/csv; tệp thường tải thẳng (chỉ text)."""
    token = access_token(db, link)
    if mime.startswith("application/vnd.google-apps."):
        target = "text/csv" if mime.endswith("spreadsheet") else "text/plain"
        resp = requests.get(f"{DRIVE_URL}/files/{file_id}/export", params={"mimeType": target},
                            headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
    else:
        resp = requests.get(f"{DRIVE_URL}/files/{file_id}", params={"alt": "media"},
                            headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
    if resp.status_code >= 400:
        raise GoogleError(f"Google trả lỗi {resp.status_code} khi mở tệp.")
    return resp.text[:20000]


_FOLDER_MIME = "application/vnd.google-apps.folder"
_FOLDER_CACHE: dict[tuple[int, str], str] = {}


def ensure_folder(db: Session, link: AgentGoogleLink, name: str) -> str:
    """Id thư mục `name` ở gốc Drive của người đó; chưa có thì tạo (ai-CR-112). Scope drive.file chỉ thấy thư mục do ERP
    tạo, nên thư mục cùng tên người dùng tự tạo tay không bị đụng. Hỏng thì trả "" (tệp lên gốc Drive)."""
    key = (int(link.id or 0), name)
    if key in _FOLDER_CACHE:
        return _FOLDER_CACHE[key]
    token = access_token(db, link)
    headers = {"Authorization": f"Bearer {token}"}
    safe = name.replace("\\", "\\\\").replace("'", "\\'")
    try:
        resp = requests.get("https://www.googleapis.com/drive/v3/files", headers=headers, timeout=20,
                            params={"q": f"name = '{safe}' and mimeType = '{_FOLDER_MIME}' and trashed = false",
                                    "fields": "files(id)", "pageSize": 1})
        found = (resp.json().get("files") or []) if resp.status_code < 400 else []
        if found:
            folder = str(found[0].get("id") or "")
        else:
            resp = requests.post("https://www.googleapis.com/drive/v3/files", headers=headers, timeout=20,
                                 params={"fields": "id"}, json={"name": name, "mimeType": _FOLDER_MIME})
            folder = str(resp.json().get("id") or "") if resp.status_code < 400 else ""
    except (requests.RequestException, ValueError):
        return ""
    if folder:
        _FOLDER_CACHE[key] = folder
    return folder


def upload_file(db: Session, link: AgentGoogleLink, filename: str, data: bytes, mime: str, *, parent: str = "") -> dict:
    """Đưa một tệp lên Drive của người đó (scope drive.file: chỉ tệp do ERP tạo). Trả {id, webViewLink}.
    `parent` = id thư mục (ai-CR-112); trống = gốc Drive."""
    token = access_token(db, link)
    meta = json.dumps({"name": filename, **({"parents": [parent]} if parent else {})}).encode()
    files = {"metadata": ("metadata", meta, "application/json; charset=UTF-8"), "file": (filename, data, mime)}
    resp = requests.post("https://www.googleapis.com/upload/drive/v3/files", params={"uploadType": "multipart", "fields": "id,webViewLink"},
                         headers={"Authorization": f"Bearer {token}"}, files=files, timeout=60)
    if resp.status_code >= 400:
        raise GoogleError(f"Google trả lỗi {resp.status_code} khi đưa tệp lên Drive.")
    return resp.json()
