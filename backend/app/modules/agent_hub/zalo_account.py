"""Zalo hướng B (ai-CR-122): MỘT tài khoản Zalo của công ty làm «bot» — đại ca chốt 08/10/2026.

Tài khoản thường (không phải bot chính thức) nên thấy TRỌN tin trong mọi nhóm nó có mặt. Phiên đăng nhập do tiến trình
Node `zalo-listener` (thư viện zca-js) giữ; tệp này chỉ nói chuyện với tiến trình đó qua HTTP nội bộ có chữ ký
(`core/agent_signature.py`, khóa AGENT_SERVICE_SECRET), không đụng tới Zalo trực tiếp.

  - Nhận: `GET /updates?offset=N&timeout=T` giữ kết nối chờ, trả các sự kiện có `id ≥ N` (như con trỏ Telegram). Bốn
    loại: `message` (tin riêng / tin nhóm), `group` (tên + danh sách thành viên một nhóm), `qr` (ảnh mã QR đăng nhập),
    `status` (đã đăng nhập / phiên văng).
  - Gửi: `POST /send {thread_id, thread_type: user|group, text, file?}` — tiến trình Node tự giãn nhịp gửi (giảm rủi ro
    Zalo khóa số). Tin cá nhân không có HTML: lõi soạn HTML kiểu Telegram, ở đây đổi ra chữ trơn.
  - Bot KHÔNG nói gì trong nhóm (đại ca chốt «chỉ trả lời riêng như hiện tại»): tin nhóm chỉ ghi lặng vào kho nhóm.

Quyền đọc một nhóm Zalo: tài khoản Zalo đã đăng nhập ERP (nhắn `/dangnhap <mã>` riêng cho tài khoản công ty) có tên
trong danh sách thành viên nhóm mà tiến trình Node báo về.
"""
from __future__ import annotations

import base64
import html
import json
import logging
import mimetypes
import re
from datetime import datetime
from urllib.parse import urlencode

import requests
from sqlalchemy.orm import Session

from app.core import agent_signature
from app.core.config import settings

from . import channels
from .telegram import TelegramError

log = logging.getLogger("app.agent_hub.zalo_account")

LONG_POLL_TIMEOUT = 25
HTTP_TIMEOUT = 15
SEND_TIMEOUT = 90               # tiến trình Node có thể đang giãn nhịp vài tin trước
#  Zalo cá nhân nhận tin khá dài, nhưng tin quá dài khó đọc trên điện thoại: cắt như kênh Zalo bot.
MAX_TEXT = 1900
MAX_PARTS = 5
MAX_FILE_BYTES = 20 * 1024 * 1024
MEMBERS_MAX = 5000              # nhóm Zalo tối đa ~1000 người; trần để một sự kiện giả không thổi phồng cột JSON

EV_MESSAGE = "message"
EV_GROUP = "group"
EV_QR = "qr"
EV_STATUS = "status"


class ZaloAccountError(TelegramError):
    """Lỗi khi nói chuyện với `zalo-listener`. Con của `TelegramError` để các chỗ bắt lỗi kênh trong lõi bắt luôn."""


def is_enabled() -> bool:
    return bool(settings.AGENT_HUB_ENABLED and settings.AGENT_ZALO_LISTENER_URL)


def _request(method: str, path: str, *, body: dict | None = None, timeout: int = HTTP_TIMEOUT) -> dict:
    base = (settings.AGENT_ZALO_LISTENER_URL or "").rstrip("/")
    if not base:
        raise ZaloAccountError("Chưa cấu hình AGENT_ZALO_LISTENER_URL")
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else b""
    sign_path = path.split("?", 1)[0]
    try:
        headers = agent_signature.sign_headers(method, sign_path, raw)
    except ValueError as e:
        raise ZaloAccountError(str(e)) from None
    if raw:
        headers["Content-Type"] = "application/json"
    try:
        resp = requests.request(method, base + path, data=raw or None, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        raise ZaloAccountError(f"Không gọi được zalo-listener: {type(e).__name__}") from None
    try:
        data = resp.json()
    except ValueError:
        raise ZaloAccountError(f"zalo-listener trả {resp.status_code}, không phải JSON") from None
    if resp.status_code >= 400 or not data.get("ok"):
        raise ZaloAccountError(f"zalo-listener từ chối ({resp.status_code}): {str(data.get('error') or '')[:200]}")
    return data


# ---------------------------------------------------------------------------
# Nhận
# ---------------------------------------------------------------------------
def fetch_updates(offset: int, *, timeout: int = LONG_POLL_TIMEOUT) -> list[dict]:
    q = urlencode({"offset": max(0, int(offset or 0)), "timeout": max(0, int(timeout))})
    data = _request("GET", f"/updates?{q}", timeout=timeout + HTTP_TIMEOUT)
    events = data.get("events")
    return [e for e in events if isinstance(e, dict)] if isinstance(events, list) else []


def _attachment(content) -> dict | None:
    """Tệp / ảnh / tin thoại trong một tin Zalo (zca-js để ở `content` dạng object có `href`)."""
    if not isinstance(content, dict):
        return None
    href = str(content.get("href") or content.get("url") or "")
    if not href.startswith("https://"):
        return None
    params = content.get("params")
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except ValueError:
            params = {}
    params = params if isinstance(params, dict) else {}
    return {"href": href, "title": str(content.get("title") or "")[:200],
            "size": int(str(params.get("fileSize") or 0)) if str(params.get("fileSize") or "0").isdigit() else 0,
            "ext": str(params.get("fileExt") or "").lower()[:10],
            "duration": int(params.get("duration") or 0) // 1000 if str(params.get("duration") or "0").isdigit() else 0}


_VOICE_TYPES = ("chat.voice",)
_PHOTO_TYPES = ("chat.photo", "webchat.photo")
_FILE_TYPES = ("share.file",)
_VIDEO_TYPES = ("chat.video.msg",)


def normalize(ev: dict) -> dict | None:
    """Sự kiện `message` của tiến trình Node → tin dạng Telegram mà `service.handle_message` đọc. None = bỏ qua.

    Tin chính tài khoản công ty gửi (`is_self`) bỏ qua. Id tin / id người gửi (chuỗi số của Zalo) đổi thành số ổn định
    cho các cột số; id gốc người gửi giữ ở `from.zalo_id`."""
    if ev.get("is_self"):
        return None
    group = str(ev.get("thread_type") or "user") == "group"
    tid = str(ev.get("thread_id") or "")
    chat_id = channels.zalo_group_chat(tid) if group else channels.zalo_user_chat(tid)
    uid = str(ev.get("from_uid") or "")
    if not chat_id or not uid:
        return None
    ts = int(ev.get("ts") or 0)
    out: dict = {
        "message_id": channels.number_of(ev.get("msg_id")),
        "date": ts // 1000 if ts > 10**11 else ts,
        #  Tên nhóm có thể chưa biết (tiến trình Node chưa quét xong): để trống thì kho nhóm KHÔNG đè tên đúng đã có.
        "chat": {"id": chat_id, "type": "group" if group else "private", "title": str(ev.get("thread_name") or "")},
        "from": {"id": channels.number_of(uid), "first_name": str(ev.get("from_name") or "").strip()[:120],
                 "zalo_id": uid},
        "channel": channels.ZALO_ACCOUNT,
    }
    content = ev.get("content")
    msg_type = str(ev.get("msg_type") or "")
    if isinstance(content, str):
        if not content.strip():
            return None
        out["text"] = content
        return out
    att = _attachment(content)
    if att is None:
        return None
    fid = channels.ZALO_FILE_PREFIX + att["href"]
    if msg_type in _PHOTO_TYPES:
        out["photo"] = [{"file_id": fid, "file_size": att["size"]}]
        desc = str((content or {}).get("description") or "") if isinstance(content, dict) else ""
        if desc:
            out["caption"] = desc
    elif msg_type in _VOICE_TYPES:
        out["voice"] = {"file_id": fid, "mime_type": "audio/aac", "duration": att["duration"]}
    elif msg_type in _VIDEO_TYPES:
        out["video"] = {"file_id": fid, "file_name": att["title"] or "video.mp4", "mime_type": "video/mp4",
                        "file_size": att["size"], "duration": att["duration"]}
    elif msg_type in _FILE_TYPES or att["title"]:
        name = att["title"] or f"tep.{att['ext'] or 'bin'}"
        #  Zalo không báo kiểu tệp: đoán theo đuôi để ghi âm / video gửi dạng tệp vẫn được nhận là cuộc họp.
        mime = mimetypes.guess_type(name)[0] or ""
        out["document"] = {"file_id": fid, "file_name": name, "mime_type": mime, "file_size": att["size"]}
    else:
        return None
    return out


def apply_group(db: Session, ev: dict):
    """Sự kiện `group`: tên + thành viên một nhóm (lúc tài khoản được thêm vào, khi có người vào / ra, và đợt quét định
    kỳ của tiến trình Node). `left` = tài khoản công ty đã rời / bị mời ra."""
    from . import chat_link, groups

    chat_id = channels.zalo_group_chat(ev.get("group_id"))
    if not chat_id:
        return None
    row = groups.get_group(db, chat_id)
    if row is None:
        if ev.get("left"):
            return None
        from .model import AgentGroup

        row = AgentGroup(chat_id=chat_id, title="nhóm Zalo", active=True, joined_at=datetime.now())
        db.add(row)
    if ev.get("name"):
        row.title = str(ev["name"])[:200]
    members = ev.get("member_ids")
    if isinstance(members, list):
        row.members = [str(m)[:40] for m in members[:MEMBERS_MAX] if str(m or "").strip()]
    if ev.get("left"):
        row.active = False
        row.left_at = datetime.now()
    else:
        row.active = True
        row.left_at = None
    adder = str(ev.get("added_by") or "")
    if adder and not row.owner_user_id:
        link = chat_link.get_active_link(db, channels.zalo_user_chat(adder))
        row.owner_tg_id = channels.number_of(adder)
        row.owner_user_id = int(link.user_id) if link is not None else 0
    db.flush()
    return row


# ---------------------------------------------------------------------------
# Gửi
# ---------------------------------------------------------------------------
_BLOCK_END = re.compile(r"</(p|li|div|pre|blockquote|h\d)>", re.I)
_LI = re.compile(r"<li[^>]*>", re.I)
_BR = re.compile(r"<br\s*/?>", re.I)
_TAG = re.compile(r"<[^>]+>")
_LINK = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)


def to_plain(text: str) -> str:
    """HTML kiểu Telegram → chữ trơn cho tin Zalo cá nhân: liên kết thành «chữ (địa chỉ)», bỏ thẻ, giữ xuống dòng."""

    def _link(m: re.Match) -> str:
        url, label = m.group(1), _TAG.sub("", m.group(2)).strip()
        return f"{label} ({html.unescape(url)})" if label and label != url else html.unescape(url)

    out = _LINK.sub(_link, text or "")
    out = _LI.sub("- ", _BR.sub("\n", out))
    out = _BLOCK_END.sub("\n", out)
    out = html.unescape(_TAG.sub("", out))
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def _button_lines(buttons: list[tuple[str, str]] | None) -> str:
    """Không có nút bấm: liệt kê lựa chọn để người dùng nhắn lại bằng chữ; nút liên kết thì in địa chỉ."""
    if not buttons:
        return ""
    lines = []
    for label, data in buttons:
        lines.append(f"- {label}: {data}" if str(data).startswith(("https://", "http://")) else f"- «{label}»")
    return "\n\nNhắn lại một trong các lựa chọn:\n" + "\n".join(lines)


def split_text(text: str, limit: int = MAX_TEXT) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    parts: list[str] = []
    rest = text
    while rest and len(parts) < MAX_PARTS:
        if len(rest) <= limit:
            parts.append(rest)
            rest = ""
            break
        cut = -1
        for sep in ("\n\n", "\n", " "):
            cut = rest.rfind(sep, 0, limit)
            if cut >= limit // 2:
                break
        if cut < limit // 2:
            cut = limit
        parts.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    if rest:
        parts[-1] = parts[-1] + "\n\n… (đã cắt bớt)"
    return parts


def _target(chat_id: str) -> tuple[str, str]:
    kind = "group" if str(chat_id).startswith(channels.ZALO_GROUP_PREFIX) else "user"
    return channels.raw_id(chat_id), kind


def send(chat_id: str, text: str, *, buttons: list[tuple[str, str]] | None = None) -> int:
    """Gửi chữ tới một chat Zalo của tài khoản công ty. Trả số dương khi gửi được, lỗi thì 0.

    Chặn cứng tin vào NHÓM: đại ca chốt bot chỉ trả lời riêng — lỡ một nhánh nào đó trong lõi định trả lời vào chat nhóm
    thì dừng ở đây."""
    if str(chat_id).startswith(channels.ZALO_GROUP_PREFIX):
        log.warning("agent_hub: chặn một tin định gửi vào nhóm Zalo %s (bot chỉ trả lời riêng)", chat_id)
        return 0
    tid, kind = _target(chat_id)
    first = 0
    for part in split_text(to_plain((text or "") + _button_lines(buttons))):
        try:
            res = _request("POST", "/send", body={"thread_id": tid, "thread_type": kind, "text": part},
                           timeout=SEND_TIMEOUT)
        except ZaloAccountError as e:
            log.warning("agent_hub: gửi Zalo (tài khoản công ty) hỏng: %s", e)
            return first
        first = first or channels.number_of(res.get("msg_id")) or 1
    return first


def send_document(chat_id: str, filename: str, data: bytes, *, caption: str = "") -> int:
    """Gửi tệp (báo cáo Word / Excel, biên bản họp) — tài khoản cá nhân gửi tệp được, khác bot chính thức."""
    if str(chat_id).startswith(channels.ZALO_GROUP_PREFIX):
        return 0
    if len(data or b"") > MAX_FILE_BYTES:
        return send(chat_id, f"Tệp {filename} nặng quá {MAX_FILE_BYTES // (1024 * 1024)} MB, Zalo không nhận. "
                             "Anh/chị lấy tệp qua Telegram hoặc Trợ lý AI trên web ERP.")
    tid, kind = _target(chat_id)
    body = {"thread_id": tid, "thread_type": kind, "text": to_plain(caption)[:MAX_TEXT],
            "file": {"name": str(filename or "tep")[:150], "b64": base64.b64encode(data or b"").decode("ascii")}}
    try:
        res = _request("POST", "/send", body=body, timeout=SEND_TIMEOUT)
    except ZaloAccountError as e:
        log.warning("agent_hub: gửi tệp Zalo (tài khoản công ty) hỏng: %s", e)
        return 0
    return channels.number_of(res.get("msg_id")) or 1


# ---------------------------------------------------------------------------
# Điều khiển phiên
# ---------------------------------------------------------------------------
def request_login() -> dict:
    """Xin tiến trình Node mở đăng nhập QR. Ảnh QR về sau qua sự kiện `qr`."""
    return _request("POST", "/login", body={})


def status() -> dict:
    """{state: connected|qr|down|idle, name, uid, groups, queued, since}."""
    return _request("GET", "/status")


def refresh_groups() -> dict:
    return _request("POST", "/groups/refresh", body={})
