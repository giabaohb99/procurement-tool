"""Cầu nối Zalo Bot Platform — bot Zalo CHÍNH THỨC (ai-CR-111, hướng A ở `doc/agent-hub/12-de-xuat-tom-tat-nhom.md`).

Giống `telegram.py`: tự đi kéo tin (`getUpdates`, giữ kết nối chờ), không webhook — dev không cần mở cổng công khai.
Tệp này CHỈ nói chuyện với Zalo, không đụng DB. Tài liệu: https://bot.zapps.me/docs (đã đọc 07/10/2026).

  - Gọi: POST JSON tới `https://bot-api.zaloplatforms.com/bot<TOKEN>/<method>`.
  - Nhận: `getUpdates {timeout}` trả MỘT update `{event_name, message:{from, chat{id, chat_type}, text, photo, caption,
    voice_url?, message_id, date(ms)}}`; hết giờ chờ mà không có tin thì trả lỗi 408 — trường hợp THƯỜNG.
    `getUpdates` không chạy khi bot đã đặt webhook.
  - Gửi: `sendMessage {chat_id, text ≤ 2000, parse_mode: html}` — HTML chỉ nhận b / i / u / s / ul / li / p.
  - Không có nút bấm, không sửa tin đã gửi, không gửi tệp tài liệu: ba thứ đó lùi về chữ (xem từng hàm).
  - Trong nhóm (đang thử nghiệm), bot chính thức chỉ nhận tin trả lời bot hoặc tin nhắc tên bot.
"""
from __future__ import annotations

import html
import logging
import re
from urllib.parse import urlparse

import requests

from app.core.config import settings

from . import channels
from .telegram import TelegramError

log = logging.getLogger("app.agent_hub.zalo")

BASE_URL = "https://bot-api.zaloplatforms.com/bot{token}/{method}"
#  Zalo nhận 1–2000 ký tự một tin. Chừa chỗ cho dấu «(tiếp)».
MAX_TEXT = 1900
#  Một câu trả lời dài cắt tối đa bấy nhiêu tin — quá nữa thì cắt đuôi, đỡ dội cả chục tin vào máy người dùng.
MAX_PARTS = 5
LONG_POLL_TIMEOUT = 25
HTTP_TIMEOUT = 20
DOWNLOAD_TIMEOUT = 120
#  Đường tải ảnh / tin thoại Zalo gửi kèm phải nằm trên máy chủ của Zalo — kẻo một update giả mạo bắt bot đi tải
#  địa chỉ nội bộ.
FILE_HOSTS = ("zdn.vn", "zalo.me", "zadn.vn", "zaloapp.com", "zalo.vn", "zaloplatforms.com")
#  Đợt này chỉ nhận ba loại tin; còn lại (sticker, tin không hỗ trợ) bỏ qua lặng.
EVENT_TEXT = "message.text.received"
EVENT_IMAGE = "message.image.received"
EVENT_VOICE = "message.voice.received"


class ZaloError(TelegramError):
    """Lỗi khi nói chuyện với Zalo. Con của `TelegramError` để các chỗ đang bắt lỗi kênh trong lõi bắt luôn."""


def is_enabled() -> bool:
    return bool(settings.AGENT_HUB_ENABLED and settings.AGENT_ZALO_BOT_TOKEN)


def _call(method: str, payload: dict, *, timeout: int = 30) -> dict:
    token = settings.AGENT_ZALO_BOT_TOKEN
    if not token:
        raise ZaloError("Chưa cấu hình AGENT_ZALO_BOT_TOKEN")
    try:
        resp = requests.post(BASE_URL.format(token=token, method=method), json=payload, timeout=timeout)
    except requests.RequestException as e:
        #  Không đưa URL vào lỗi: URL chứa token.
        raise ZaloError(f"Lỗi gọi Zalo {method}: {type(e).__name__}") from None
    try:
        data = resp.json()
    except ValueError:
        raise ZaloError(f"Zalo {method} trả {resp.status_code}, không phải JSON") from None
    if not data.get("ok"):
        code = int(data.get("error_code") or resp.status_code or 0)
        if method == "getUpdates" and code == 408:
            return {}                       # hết giờ chờ, không có tin
        raise ZaloError(f"Zalo {method} từ chối ({code}): {str(data.get('description') or '')[:200]}")
    result = data.get("result")
    return result if isinstance(result, (dict, list)) else {}


# ---------------------------------------------------------------------------
# Nhận
# ---------------------------------------------------------------------------
def fetch_updates(*, timeout: int = LONG_POLL_TIMEOUT) -> list[dict]:
    """Kéo tin mới. Zalo không có con trỏ: tin đã trả là đã nhận. Trả [] khi hết giờ chờ."""
    result = _call("getUpdates", {"timeout": timeout}, timeout=timeout + HTTP_TIMEOUT)
    if isinstance(result, list):
        return [u for u in result if isinstance(u, dict)]
    return [result] if result else []


def normalize(update: dict) -> dict | None:
    """Update Zalo → tin dạng Telegram mà `service.handle_message` đọc. None = loại tin không xử.

    Mã chat mang tiền tố `zl:`; id tin và id người gửi (chuỗi phía Zalo) đổi thành số ổn định cho các cột số."""
    msg = update.get("message") if isinstance(update.get("message"), dict) else None
    if msg is None:
        return None
    event = str(update.get("event_name") or "")
    chat = msg.get("chat") or {}
    sender = msg.get("from") or {}
    chat_id = channels.zalo_chat(chat.get("id"))
    if not chat_id or sender.get("is_bot"):
        return None
    group = str(chat.get("chat_type") or "PRIVATE").upper() == "GROUP"
    name = str(sender.get("display_name") or "").strip()
    date_ms = int(msg.get("date") or 0)
    out: dict = {
        "message_id": channels.number_of(msg.get("message_id")),
        "date": date_ms // 1000 if date_ms > 10**11 else date_ms,
        "chat": {"id": chat_id, "type": "group" if group else "private", "title": str(chat.get("title") or "")
                 or ("nhóm Zalo" if group else "")},
        "from": {"id": channels.number_of(sender.get("id")), "first_name": name, "zalo_id": str(sender.get("id") or "")},
        "channel": channels.ZALO,
    }
    if event == EVENT_TEXT or (not event and msg.get("text")):
        out["text"] = str(msg.get("text") or "")
    elif event == EVENT_IMAGE:
        url = str(msg.get("photo") or msg.get("photo_url") or "")
        if not url:
            return None
        out["photo"] = [{"file_id": channels.ZALO_FILE_PREFIX + url, "file_size": 0}]
        if msg.get("caption"):
            out["caption"] = str(msg["caption"])
    elif event == EVENT_VOICE:
        url = str(msg.get("voice_url") or msg.get("url") or "")
        if not url:
            return None
        #  Zalo không báo độ dài tin thoại → coi là tin thoại ngắn (chép lời rồi trả lời như tin chữ).
        out["voice"] = {"file_id": channels.ZALO_FILE_PREFIX + url, "mime_type": "audio/aac", "duration": 0}
    else:
        return None
    return out


def _allowed_file_url(url: str) -> bool:
    u = urlparse(url)
    host = (u.hostname or "").lower()
    return u.scheme == "https" and any(host == h or host.endswith("." + h) for h in FILE_HOSTS)


def download(url: str, *, max_bytes: int) -> tuple[bytes, str]:
    """Tải ảnh / tin thoại Zalo gửi kèm. Trả (nội dung, đường dẫn) như `telegram.download_file`."""
    if not _allowed_file_url(url):
        raise ZaloError("đường tải tệp không thuộc Zalo")
    try:
        with requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True) as resp:
            if resp.status_code != 200:
                raise ZaloError(f"tải tệp trả {resp.status_code}")
            data = b""
            for chunk in resp.iter_content(256 * 1024):
                data += chunk
                if len(data) > max_bytes:
                    raise ZaloError("tệp quá trần")
    except requests.RequestException as e:
        raise ZaloError(f"tải tệp hỏng: {type(e).__name__}") from None
    return data, urlparse(url).path


# ---------------------------------------------------------------------------
# Gửi
# ---------------------------------------------------------------------------
_KEEP = {"b": "b", "strong": "b", "i": "i", "em": "i", "u": "u", "ins": "u", "s": "s", "strike": "s", "del": "s"}
_LINK = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)
_TAG = re.compile(r"</?([a-zA-Z0-9-]+)(?:\s[^>]*)?>")


def to_zalo_html(text: str) -> str:
    """HTML kiểu Telegram (lõi soạn sẵn) → HTML Zalo nhận được: giữ b / i / u / s; liên kết → «chữ (địa chỉ)»;
    code / pre / blockquote / span… bỏ thẻ, giữ chữ. Ký tự đã thoát (&lt; &amp;) giữ nguyên."""

    def _link(m: re.Match) -> str:
        url, label = m.group(1), m.group(2)
        plain = _TAG.sub("", label).strip()
        return f"{label} ({html.unescape(url)})" if plain and plain != url else html.unescape(url)

    out = _LINK.sub(_link, text or "")

    def _tag(m: re.Match) -> str:
        name = m.group(1).lower()
        keep = _KEEP.get(name)
        if not keep:
            return ""
        return f"</{keep}>" if m.group(0).startswith("</") else f"<{keep}>"

    return _TAG.sub(_tag, out)


def plain(text: str) -> str:
    return html.unescape(_TAG.sub("", text or ""))


def split_text(text: str, limit: int = MAX_TEXT) -> list[str]:
    """Cắt tin dài theo đoạn / dòng (Zalo chặn > 2000 ký tự). Không cắt giữa một thẻ HTML."""
    text = (text or "").strip()
    if len(text) <= limit:
        return [text] if text else []
    parts: list[str] = []
    rest = text
    while rest and len(parts) < MAX_PARTS:
        if len(rest) <= limit:
            parts.append(rest)
            rest = ""
            break
        cut = rest.rfind("\n\n", 0, limit)
        if cut < limit // 2:
            cut = rest.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = rest.rfind(" ", 0, limit)
        if cut < limit // 2:
            cut = limit
        #  Không để cắt rơi vào giữa «<b…>».
        lt, gt = rest.rfind("<", 0, cut), rest.rfind(">", 0, cut)
        if lt > gt:
            cut = lt
        parts.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    if rest:
        parts[-1] = parts[-1] + "\n\n… (đã cắt bớt)"
    return [_balance(p) for p in parts]


def _balance(part: str) -> str:
    """Đóng các thẻ b / i / u / s còn mở ở cuối một mẩu (mẩu sau mở lại thì Zalo vẫn hiển thị đúng phần chữ)."""
    for tag in ("b", "i", "u", "s"):
        opened = len(re.findall(f"<{tag}>", part)) - len(re.findall(f"</{tag}>", part))
        if opened > 0:
            part += f"</{tag}>" * opened
    return part


def _button_lines(buttons: list[tuple[str, str]] | None) -> str:
    """Zalo không có nút bấm: liệt kê lựa chọn để người dùng nhắn lại bằng chữ; nút liên kết thì in địa chỉ."""
    if not buttons:
        return ""
    lines = []
    for label, data in buttons:
        if str(data).startswith(("https://", "http://")):
            lines.append(f"- {html.escape(label)}: {data}")
        else:
            lines.append(f"- «{html.escape(label)}»")
    return "\n\nNhắn lại một trong các lựa chọn:\n" + "\n".join(lines)


def send(chat_id: str, text: str, *, buttons: list[tuple[str, str]] | None = None) -> int:
    """Gửi một tin (tự cắt nhiều mẩu nếu dài). Trả một số dương khi gửi được (Zalo trả id dạng chuỗi), lỗi thì 0."""
    target = channels.raw_id(chat_id)
    body = to_zalo_html((text or "") + _button_lines(buttons))
    first = 0
    for part in split_text(body):
        try:
            res = _call("sendMessage", {"chat_id": target, "text": part, "parse_mode": "html"})
        except ZaloError as e:
            if "từ chối" not in str(e):
                log.warning("agent_hub: gửi Zalo hỏng: %s", e)
                return first
            #  Zalo chê định dạng: gửi lại chữ trơn, còn hơn im lặng.
            try:
                res = _call("sendMessage", {"chat_id": target, "text": plain(part)[:2000]})
            except ZaloError as e2:
                log.warning("agent_hub: gửi Zalo hỏng: %s", e2)
                return first
        if not first:
            first = channels.number_of((res or {}).get("message_id")) or 1
    return first


def send_chat_action(chat_id: str, action: str = "typing") -> None:
    try:
        _call("sendChatAction", {"chat_id": channels.raw_id(chat_id), "action": "typing"}, timeout=5)
    except ZaloError:
        pass


def send_document(chat_id: str, filename: str, data: bytes, *, caption: str = "") -> int:
    """Zalo Bot chưa có API gửi tệp tài liệu (07/10/2026). Báo người dùng chỗ lấy tệp thay vì im lặng."""
    size_kb = max(1, len(data or b"") // 1024)
    note = (f"Em đã soạn xong tệp <b>{html.escape(filename)}</b> ({size_kb} KB) nhưng Zalo chưa cho bot gửi tệp. "
            "Anh/chị hỏi lại em trên bot Telegram để nhận tệp, hoặc dùng Trợ lý AI trên web ERP.")
    if caption:
        note = f"{caption}\n\n{note}"
    return send(chat_id, note)
