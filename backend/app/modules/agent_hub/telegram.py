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

from . import channels

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
    """Đủ cấu hình để chạy chưa. Thiếu một trong ba thì cả bộ máy nằm im.

    ai-CR-054: máy sửa mã tách rời KHÔNG giữ token bot — nó có `AGENT_RUNNER_NAME` và gửi tin vòng qua
    hàng đợi cho worker trên dev gửi hộ (`relaying()`), nên với nó «có token» = «có tên máy».
    """
    return bool(
        settings.AGENT_HUB_ENABLED
        and (settings.AGENT_TELEGRAM_BOT_TOKEN or relaying())
        and settings.AGENT_TELEGRAM_CHAT_ID
    )


def relaying() -> bool:
    """Tiến trình này là máy sửa mã không có token: mọi tin gửi đi phải đi vòng qua worker của bot."""
    return bool(settings.AGENT_RUNNER_NAME) and not settings.AGENT_TELEGRAM_BOT_TOKEN


def _relay(method: str, payload: dict) -> int:
    """Đẩy một lượt gọi Bot API sang worker của bot (hàng đợi mặc định). Không chờ kết quả: trả 0."""
    from app.core.celery_app import celery_app

    celery_app.send_task("agent.send_telegram", kwargs={"method": method, "payload": payload})
    return 0


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


FILE_URL = "https://api.telegram.org/file/bot{token}/{path}"
_BOT_USERNAME: dict[str, str] = {}


def get_bot_username() -> str:
    """Tên bot (không @): lấy từ `.env`, trống thì hỏi Telegram `getMe` một lần rồi nhớ (ai-CR-043).
    Hỏng thì trả rỗng — trang cá nhân chỉ mất nút mở thẳng bot, không hỏng gì khác."""
    name = (settings.AGENT_TELEGRAM_BOT_USERNAME or "").strip().lstrip("@")
    if name:
        return name
    if "name" not in _BOT_USERNAME:
        try:
            _BOT_USERNAME["name"] = str(_call("getMe", {}).get("username") or "")
        except TelegramError:
            return ""
    return _BOT_USERNAME["name"]


def download_file(file_id: str, *, max_bytes: int) -> tuple[bytes, str]:
    """Tải một tệp người dùng gửi (ai-CR-035). Trả (nội dung, đường dẫn phía Telegram).

    Lỗi KHÔNG được mang URL tải: URL chứa token của bot.
    ai-CR-111: «file_id» mang tiền tố `zlurl:` là đường tải của Zalo → tải bên `zalo`."""
    if file_id.startswith(channels.ZALO_FILE_PREFIX):
        from . import zalo

        return zalo.download(file_id[len(channels.ZALO_FILE_PREFIX):], max_bytes=max_bytes)
    info = _call("getFile", {"file_id": file_id})
    size = int(info.get("file_size") or 0)
    if size and size > max_bytes:
        raise TelegramError(f"tệp {size // (1024 * 1024)} MB, quá trần {max_bytes // (1024 * 1024)} MB")
    path = str(info.get("file_path") or "")
    if not path:
        raise TelegramError("Telegram không trả đường dẫn tệp")
    try:
        resp = requests.get(FILE_URL.format(token=settings.AGENT_TELEGRAM_BOT_TOKEN, path=path),
                            timeout=DOCUMENT_TIMEOUT)
    except requests.RequestException as e:
        raise TelegramError(f"tải tệp hỏng: {type(e).__name__}") from None
    if resp.status_code != 200:
        raise TelegramError(f"tải tệp trả {resp.status_code}")
    if len(resp.content) > max_bytes:
        raise TelegramError("tệp quá trần")
    return resp.content, path


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


#  ai-CR-071: gốc đầu tiên của các màn CHỈ có ở giao diện cũ `frontend/` (đóng băng, App.tsx). Chuông ERP còn lưu
#  đường dẫn kiểu cũ (`/purchase-orders/376`) nên phải về FRONTEND_URL; mọi đường khác (Trợ lý AI trả
#  `/procurement/purchase-orders/379`, `/hr/…`, `/finance/…`, `/support/…`) là màn ERP v2 → AGENT_ERP_URL.
#  Trước đây tất cả đi FRONTEND_URL nên link Trợ lý trên Telegram mở `devthumua/procurement/...` → trang trắng.
_V1_ROOTS = frozenset({
    "backups", "category-assignees", "contracts", "customs-prices", "documents", "import-batches", "inventory",
    "notifications", "payables", "payment-requests", "pr-lines-report", "purchase-orders", "purchase-progress",
    "purchase-requests", "reports", "roles", "settings", "suppliers", "survey-progress", "survey-report",
    "survey-requests", "surveys", "surveys-product", "surveys-supplier", "tickets", "users",
})


def absolute_url(path: str) -> str:
    """Đường dẫn tương đối trong ứng dụng -> tuyệt đối. Web tự nối gốc, Telegram thì không.
    Đường `/api/...` và màn ERP v2 → AGENT_ERP_URL; màn chỉ có ở bản cũ → FRONTEND_URL."""
    if not path.startswith("/"):
        return path
    root = path.lstrip("/").split("/", 1)[0].split("?", 1)[0]
    legacy = settings.FRONTEND_URL.rstrip("/")
    base = legacy if root in _V1_ROOTS else (settings.AGENT_ERP_URL or legacy).rstrip("/")
    return base + path


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
            #  ai-CR-105: + my_chat_member — bot được thêm vào / mời ra khỏi nhóm (ghi chủ nhóm).
            "allowed_updates": ["message", "callback_query", "my_chat_member"],
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
    if relaying():
        return
    if channels.is_zalo_account(chat_id):
        #  ai-CR-130: «đang soạn» trên Zalo + hẹn tin «em nhận tin rồi» nếu trả lời lâu.
        from . import zalo_account

        zalo_account.send_typing(chat_id)
        return
    if channels.is_zalo(chat_id):
        from . import zalo

        zalo.send_chat_action(chat_id, action)
        return
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


#  Đại ca chốt (ai-CR-121, nhắc lại 09/10/2026): KHÔNG để ngoặc «» trong tin bot gửi — khó đọc. Hàng trăm câu cũ trong
#  mã dùng «lệnh» để chỉ chữ cần nhắn; đổi tại MỘT cửa ra (mọi tin Telegram / Zalo đi qua `send` / `edit_text`) thành
#  chữ đậm, khỏi sửa từng câu và câu mới lỡ tay cũng không lọt. Không đụng phần trong <pre> / <code>.
_GUILLEMET = re.compile(r"«([^«»\n<>]{1,160})»")
_RAW_BLOCK = re.compile(r"(<pre>.*?</pre>|<code>.*?</code>)", re.DOTALL)


def polish(text: str) -> str:
    if not text or "«" not in text:
        return text
    parts = _RAW_BLOCK.split(text)
    for i in range(0, len(parts), 2):          # phần lẻ là khối <pre> / <code> — giữ nguyên
        parts[i] = _GUILLEMET.sub(r"<b>\1</b>", parts[i]).replace("«", "").replace("»", "")
    return "".join(parts)


def send(text: str, *, buttons: list[tuple[str, str]] | None = None,
         chat_id: str = "") -> int:
    """Gửi một tin. `buttons` là [(nhãn, mã hành động)]. Trả `message_id`, lỗi thì 0.

    Mã hành động đi thẳng vào `callback_data`, và Telegram chặn nó ở 64 byte —
    nên giữ dạng ngắn `<hành động>:<id task>`, đừng nhét JSON vào.
    ai-CR-111: chat Zalo (`zl:…`) rẽ sang `zalo.send` — nút bấm thành danh sách lựa chọn nhắn lại bằng chữ. Máy sửa mã
    (không token) vẫn gửi vòng qua worker như cũ; worker thấy tiền tố `zl:` thì gửi bằng Zalo.
    """
    text = polish(text)
    if channels.is_zalo_account(chat_id) and not relaying():
        from . import zalo_account

        return zalo_account.send(chat_id, text, buttons=buttons)
    if channels.is_zalo(chat_id) and not relaying():
        from . import zalo

        return zalo.send(chat_id, text, buttons=buttons)
    parts = split_long(text)
    first = 0
    for i, part in enumerate(parts):
        payload: dict = {
            "chat_id": chat_id or settings.AGENT_TELEGRAM_CHAT_ID,
            "text": part,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if buttons and i == len(parts) - 1:
            payload["reply_markup"] = {"inline_keyboard": [[_button(label, data)] for label, data in buttons]}
        if relaying():
            _relay("sendMessage", payload)
            continue
        mid = int(send_payload(payload).get("message_id") or 0)
        first = first or mid
    return first


#  ai-CR-115: tin dài cắt thành nhiều tin (trước đây cắt cụt ở MAX_TEXT, đại ca mất nửa sau bài phân tích báo cáo).
MAX_PARTS = 4


def split_long(text: str, limit: int = MAX_TEXT, max_parts: int = MAX_PARTS) -> list[str]:
    """Cắt theo đoạn trống → xuống dòng → khoảng trắng, không cắt giữa thẻ HTML và không cắt trong khối <pre>."""
    text = text or ""
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    rest = text
    while rest and len(parts) < max_parts - 1 and len(rest) > limit:
        cut = -1
        for sep in ("\n\n", "\n", " "):
            cut = rest.rfind(sep, 0, limit)
            if cut >= limit // 2:
                break
        if cut < limit // 2:
            cut = limit
        pre_open = rest.rfind("<pre>", 0, cut)
        if pre_open > rest.rfind("</pre>", 0, cut) and pre_open > 0:
            cut = pre_open                      # đừng tách đôi một khối mã
        lt, gt = rest.rfind("<", 0, cut), rest.rfind(">", 0, cut)
        if lt > gt:
            cut = lt                            # đừng tách đôi một thẻ
        parts.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    if rest:
        parts.append(_clip(rest))
    return [p for p in parts if p.strip()] or [_clip(text)]


_TAG = re.compile(r"<[^>]+>")


def send_payload(payload: dict) -> dict:
    """`sendMessage` với một lần lùi: Telegram chê HTML («can't parse entities» — thường do một cặp
    `<…>` trong chữ của model hay của kế hoạch) thì gửi lại bản chữ trơn, còn hơn im lặng (ai-CR-057:
    thẻ kế hoạch AI-0001 trên dev mất vì «<điều cần đổi>»)."""
    try:
        return _call("sendMessage", payload)
    except TelegramError as e:
        if "parse entities" not in str(e):
            raise
        plain = dict(payload)
        plain["text"] = html.unescape(_TAG.sub("", str(payload.get("text") or "")))
        plain.pop("parse_mode", None)
        return _call("sendMessage", plain)


def send_document(chat_id: str, filename: str, data: bytes, *, caption: str = "",
                  content_type: str = "") -> int:
    """Gửi một tệp (báo cáo Excel/Word do Trợ lý AI xuất) làm tệp đính kèm. Trả `message_id`.

    Web có nút «Tải báo cáo» gọi endpoint cần Bearer; Telegram không đăng nhập được vào
    ERP nên bot phải đọc byte từ kho rồi đẩy thẳng qua `sendDocument` (multipart).
    `caption` là HTML đã thoát, tối đa 1024 ký tự theo Telegram.
    """
    if channels.is_zalo_account(chat_id):
        from . import zalo_account

        return zalo_account.send_document(chat_id, filename, data, caption=caption)
    if channels.is_zalo(chat_id):
        from . import zalo

        return zalo.send_document(chat_id, filename, data, caption=caption)
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
    if not callback_id:
        return          # lệnh gõ bằng chữ (ai-CR-027) đi chung đường với nút nhưng không có nút nào
    try:
        _call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text[:200]})
    except TelegramError:
        pass


def edit_text(chat_id: str, message_id: int, text: str) -> bool:
    """Sửa chữ của một tin đã gửi (ai-CR-021: tin báo đang chạy cập nhật số phút mà không kêu
    chuông lần nữa). Trả False nếu hỏng — kể cả lỗi «message is not modified», không sao."""
    if not message_id or not channels.is_telegram(chat_id):
        return False                    # Zalo không cho sửa tin đã gửi
    try:
        _call("editMessageText", {
            "chat_id": chat_id, "message_id": message_id, "text": _clip(polish(text)),
            "parse_mode": "HTML", "disable_web_page_preview": True,
        })
        return True
    except TelegramError:
        return False


def clear_buttons(chat_id: str, message_id: int) -> None:
    """Gỡ hàng nút khỏi một tin đã gửi, sau khi đại ca bấm xong.

    Đây là chốt chống BẤM HAI LẦN, không phải chuyện thẩm mỹ: nút còn đó thì đại ca
    (hoặc một cú chạm nhầm) gửi lại đúng lệnh ấy lần nữa, và ở bậc 2 lần thứ hai đó
    là một lượt gọi bot code thật.
    """
    if not message_id or not channels.is_telegram(chat_id):
        return
    try:
        _call("editMessageReplyMarkup", {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": {"inline_keyboard": []},
        })
    except TelegramError:
        pass
