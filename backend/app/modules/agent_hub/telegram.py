"""Cầu nối Telegram — tự đi kéo tin, không webhook.

Vì sao đi kéo: hub chạy trên máy đại ca (QĐ-AI-4), không có địa chỉ công khai. Tự
kéo nên khỏi cần Cloudflare tunnel, khỏi webhook, và khỏi ký HMAC trên dữ liệu nút
bấm.

Tệp này CHỈ nói chuyện với Telegram — không đụng DB, không biết task là gì. Nhờ vậy
kiểm thử được bằng cách cắm một `requests` giả, và tầng luồng ở `service.py` không
phải bận tâm định dạng của Telegram.
"""
import html
import re

import requests

from app.core.config import settings

BASE_URL = "https://api.telegram.org/bot{token}/{method}"

#  Telegram chặn tin quá 4096 ký tự bằng lỗi 400. Cắt ở 3900 để còn chỗ cho phần
#  đuôi báo đã cắt — thà đại ca đọc thiếu phần cuối còn hơn không nhận được gì.
MAX_TEXT = 3900
#  Hai nhịp kéo tin, chọn theo AI NGỒI KÉO:
#  - `POLL_TIMEOUT = 0` = hỏi rồi về ngay, cho vòng beat 10 giây chạy TRONG `celery-worker`
#    (`-c 1`): một việc ngồi ôm kết nối là chiếm luôn ô worker duy nhất.
#  - `LONG_POLL_TIMEOUT = 25` = giữ kết nối chờ tin, cho tiến trình `agent-poller` RIÊNG
#    (ai-CR-008): tin tới là về ngay, không tin thì Telegram mới thả sau 25 giây. Độ trễ
#    đại ca cảm thấy rơi từ "0-10 giây" xuống "gần như tức thì".
#  Telegram khuyên timeout dưới 30 để đi lọt mọi proxy.
POLL_TIMEOUT = 0
LONG_POLL_TIMEOUT = 25
#  Trần chờ HTTP CỘNG THÊM vào timeout kéo — phải lớn hơn timeout kéo, không thì `requests`
#  tự cắt trước khi Telegram kịp trả và mỗi lượt kéo dài là một lỗi giả.
HTTP_TIMEOUT = 20
#  Bot API nhận tệp gửi lên tối đa 50 MB. Báo cáo của Trợ lý AI cỡ vài trăm KB, nhưng chốt
#  ở đây để một tệp lạ không đi lên rồi ăn lỗi 413 khó đọc.
MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
#  Gửi tệp chờ lâu hơn gửi chữ: upload đi qua mạng nhà.
DOCUMENT_TIMEOUT = 120


class TelegramError(RuntimeError):
    """Lỗi khi nói chuyện với Telegram. Tách riêng để tầng trên nuốt gọn."""


def is_enabled() -> bool:
    """Đủ cấu hình để chạy chưa. Thiếu một trong ba thì cả bộ máy nằm im."""
    return bool(
        settings.AGENT_HUB_ENABLED
        and settings.AGENT_TELEGRAM_BOT_TOKEN
        and settings.AGENT_TELEGRAM_CHAT_ID
    )


def is_allowed_chat(chat_id) -> bool:
    """CHỈ chat_id khai trong `.env` được ra lệnh.

    Chưa khai thì trả False — chốt chặn, KHÔNG phải "cho tất cả". Đây là toàn bộ
    hàng rào của bậc 1: ai biết tên bot cũng nhắn được cho nó, nên hàm này là chỗ
    duy nhất phân biệt đại ca với người lạ.
    """
    allowed = (settings.AGENT_TELEGRAM_CHAT_ID or "").strip()
    return bool(allowed) and str(chat_id).strip() == allowed


def _call(method: str, payload: dict, *, timeout: int = 30, files: dict | None = None) -> dict:
    """Gọi một method của Bot API. Có `files` thì gửi multipart (tệp đính kèm), không thì JSON."""
    token = settings.AGENT_TELEGRAM_BOT_TOKEN
    if not token:
        raise TelegramError("Chưa cấu hình AGENT_TELEGRAM_BOT_TOKEN")
    url = BASE_URL.format(token=token, method=method)
    try:
        if files:
            resp = requests.post(url, data=payload, files=files, timeout=timeout)
        else:
            resp = requests.post(url, json=payload, timeout=timeout)
    except requests.RequestException as e:
        raise TelegramError(f"Lỗi gọi Telegram {method}: {e}") from e
    if resp.status_code != 200:
        raise TelegramError(f"Telegram {method} trả {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    if not data.get("ok"):
        raise TelegramError(f"Telegram {method} từ chối: {str(data)[:300]}")
    return data.get("result") or {}


def esc(text: str) -> str:
    """Thoát ký tự cho parse_mode=HTML.

    Dùng HTML chứ không dùng MarkdownV2: MarkdownV2 bắt thoát 18 ký tự, trong đó có
    dấu chấm và dấu gạch ngang — tức gần như câu tiếng Việt nào cũng làm Telegram trả
    400, và lỗi đó chỉ lộ ra lúc chạy thật.
    """
    return html.escape(str(text or ""), quote=False)


_MD_CODE_BLOCK = re.compile(r"```[^\n]*\n(.*?)```", re.S)
_MD_CODE = re.compile(r"`([^`\n]+)`")
_MD_LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")
_MD_BOLD = re.compile(r"\*\*(.+?)\*\*")
_MD_ITALIC_STAR = re.compile(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])")
_MD_ITALIC_UNDER = re.compile(r"(?<![\w/])_(?!\s)([^_\n]+?)(?<!\s)_(?![\w/])")
_MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
_MD_BULLET = re.compile(r"^(\s*)[-*+]\s+")
_MD_RULE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
_MD_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
#  Ô giữ chỗ cho đoạn đã thành thẻ HTML (code, link) để bước thoát HTML và bước
#  đậm/nghiêng phía sau không đụng vào chúng. Dùng ký tự NUL vì không có trong văn bản.
_SLOT = re.compile("\x00(\\d+)\x00")


def absolute_url(path: str) -> str:
    """Đường dẫn tương đối trong ứng dụng -> tuyệt đối. Web tự nối gốc, Telegram thì không."""
    if path.startswith("/"):
        return settings.FRONTEND_URL.rstrip("/") + path
    return path


def md_to_html(text: str) -> str:
    """Markdown của Trợ lý AI -> HTML rút gọn mà Telegram hiểu.

    Web render Markdown bằng react-markdown; Telegram thì in thô `**[X](/y)**` ra màn
    hình. Telegram chỉ có <b> <i> <code> <pre> <a>, không có bảng, tiêu đề, danh sách:
    tiêu đề thành chữ đậm, gạch đầu dòng thành `•`, bảng thành từng dòng, ô cách nhau
    bằng ` · `. Mọi chữ thường đều được thoát HTML — chỉ thẻ do chính hàm này sinh ra
    mới đi qua.
    """
    parts = _MD_CODE_BLOCK.split(text or "")
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            out.append(f"<pre>{html.escape(part.rstrip())}</pre>")
        else:
            lines = (_md_line(line) for line in part.split("\n"))
            out.append("\n".join(x for x in lines if x is not None))
    return "".join(out).strip()


def _md_line(line: str) -> str | None:
    #  Đường kẻ ngang và dòng `|---|---|` của bảng: bỏ hẳn, không để lại dòng trống.
    if _MD_RULE.match(line) or _MD_TABLE_SEP.match(line):
        return None
    m = _MD_HEADING.match(line)
    if m:
        return f"<b>{_md_inline(m.group(1))}</b>"
    stripped = line.strip()
    if stripped.startswith("|") and stripped.endswith("|"):
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        return " · ".join(_md_inline(c) for c in cells if c)
    if stripped.startswith(">"):
        line = stripped.lstrip("> ")
    line = _MD_BULLET.sub(r"\1• ", line)
    return _md_inline(line)


def _md_inline(line: str) -> str:
    slots: list[str] = []

    def keep(fragment: str) -> str:
        slots.append(fragment)
        return f"\x00{len(slots) - 1}\x00"

    line = _MD_CODE.sub(lambda m: keep(f"<code>{html.escape(m.group(1))}</code>"), line)
    line = _MD_LINK.sub(
        lambda m: keep(
            f'<a href="{html.escape(absolute_url(m.group(2)), quote=True)}">'
            f'{html.escape(m.group(1).replace("**", ""))}</a>'
        ),
        line,
    )
    line = html.escape(line, quote=False)
    line = _MD_BOLD.sub(r"<b>\1</b>", line)
    line = _MD_ITALIC_STAR.sub(r"<i>\1</i>", line)
    line = _MD_ITALIC_UNDER.sub(r"<i>\1</i>", line)
    return _SLOT.sub(lambda m: slots[int(m.group(1))], line)


def _clip(text: str) -> str:
    if len(text) <= MAX_TEXT:
        return text
    return text[:MAX_TEXT] + "\n\n… (đã cắt bớt, xem đầy đủ trong sổ)"


def fetch_updates(offset: int, *, timeout: int = POLL_TIMEOUT) -> list[dict]:
    """Kéo tin mới. `offset` = id update kế tiếp cần đọc, `timeout` = số giây Telegram
    được giữ kết nối chờ tin (0 = về ngay).

    Trả [] khi hết giờ chờ mà không có gì — đó là trường hợp THƯỜNG, không phải lỗi.
    """
    result = _call(
        "getUpdates",
        {
            "offset": offset,
            "timeout": timeout,
            #  Chỉ xin hai loại mình xử. Không lọc thì mỗi lần ai đó vào/ra nhóm là
            #  một update rỗng làm con trỏ nhảy, không hại nhưng tốn lượt.
            "allowed_updates": ["message", "callback_query"],
        },
        timeout=timeout + HTTP_TIMEOUT,
    )
    return result if isinstance(result, list) else []


def send_chat_action(chat_id: str = "", action: str = "typing") -> None:
    """Bật dòng "đang soạn tin..." trên máy đại ca trong ~5 giây.

    Gọi ngay khi nhận tin và gọi lại trước mỗi lượt gọi model dài: một câu hỏi qua trạm
    phân loại rồi qua Trợ lý AI mất 5-10 giây, mà không có dấu hiệu nào thì đại ca tưởng
    bot chết. Lỗi ở đây KHÔNG được làm hỏng luồng chính — nó chỉ là cái nhấp nháy.
    """
    try:
        _call("sendChatAction", {
            "chat_id": chat_id or settings.AGENT_TELEGRAM_CHAT_ID,
            "action": action,
        }, timeout=5)
    except TelegramError:
        pass


def _button(label: str, data: str) -> dict:
    """Nút bấm: mã hành động thì là `callback_data`; một URL (ai-CR-012, nút mở PR) thì là nút liên kết,
    bấm mở trình duyệt, không gọi về bot."""
    if data.startswith(("https://", "http://")):
        return {"text": label, "url": data}
    return {"text": label, "callback_data": data}


def send(text: str, *, buttons: list[tuple[str, str]] | None = None,
         chat_id: str = "") -> int:
    """Gửi một tin. `buttons` là [(nhãn, mã hành động)]. Trả `message_id`, lỗi thì 0.

    Mã hành động đi thẳng vào `callback_data`, và Telegram chặn nó ở 64 byte —
    nên giữ dạng ngắn `<hành động>:<id task>`, đừng nhét JSON vào.
    """
    payload: dict = {
        "chat_id": chat_id or settings.AGENT_TELEGRAM_CHAT_ID,
        "text": _clip(text),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": [[_button(label, data)] for label, data in buttons]}
    result = _call("sendMessage", payload)
    return int(result.get("message_id") or 0)


def send_document(chat_id: str, filename: str, data: bytes, *, caption: str = "",
                  content_type: str = "") -> int:
    """Gửi một tệp (báo cáo Excel/Word do Trợ lý AI xuất) làm tệp đính kèm. Trả `message_id`.

    Web có nút «Tải báo cáo» gọi endpoint cần Bearer; Telegram không đăng nhập được vào
    ERP nên bot phải đọc byte từ kho rồi đẩy thẳng qua `sendDocument` (multipart).
    `caption` là HTML đã thoát, tối đa 1024 ký tự theo Telegram.
    """
    if len(data) > MAX_DOCUMENT_BYTES:
        raise TelegramError(f"Tệp {filename} nặng {len(data)} byte, quá trần 50 MB của Telegram")
    payload = {"chat_id": chat_id or settings.AGENT_TELEGRAM_CHAT_ID}
    if caption:
        payload["caption"] = caption[:1024]
        payload["parse_mode"] = "HTML"
    result = _call(
        "sendDocument", payload, timeout=DOCUMENT_TIMEOUT,
        files={"document": (filename, data, content_type or "application/octet-stream")},
    )
    return int(result.get("message_id") or 0)


def answer_callback(callback_id: str, text: str = "") -> None:
    """Tắt cái đồng hồ quay trên nút vừa bấm.

    Không gọi thì Telegram để nút quay ~30 giây rồi báo lỗi trên máy đại ca, dù việc
    ở dưới đã chạy xong từ lâu. Lỗi ở đây KHÔNG được làm hỏng luồng chính — nó chỉ
    là cái nhấp nháy trên giao diện.
    """
    try:
        _call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text[:200]})
    except TelegramError:
        pass


def clear_buttons(chat_id: str, message_id: int) -> None:
    """Gỡ hàng nút khỏi một tin đã gửi, sau khi đại ca bấm xong.

    Đây là chốt chống BẤM HAI LẦN, không phải chuyện thẩm mỹ: nút còn đó thì đại ca
    (hoặc một cú chạm nhầm) gửi lại đúng lệnh ấy lần nữa, và ở bậc 2 lần thứ hai đó
    là một lượt gọi bot code thật.
    """
    if not message_id:
        return
    try:
        _call("editMessageReplyMarkup", {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": {"inline_keyboard": []},
        })
    except TelegramError:
        pass
