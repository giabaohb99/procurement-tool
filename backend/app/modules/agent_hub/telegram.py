"""Cầu nối Telegram — tự đi kéo tin, không webhook.

Vì sao đi kéo: hub chạy trên máy đại ca (QĐ-AI-4), không có địa chỉ công khai. Tự
kéo nên khỏi cần Cloudflare tunnel, khỏi webhook, và khỏi ký HMAC trên dữ liệu nút
bấm.

Tệp này CHỈ nói chuyện với Telegram — không đụng DB, không biết task là gì. Nhờ vậy
kiểm thử được bằng cách cắm một `requests` giả, và tầng luồng ở `service.py` không
phải bận tâm định dạng của Telegram.
"""
import html

import requests

from app.core.config import settings

BASE_URL = "https://api.telegram.org/bot{token}/{method}"

#  Telegram chặn tin quá 4096 ký tự bằng lỗi 400. Cắt ở 3900 để còn chỗ cho phần
#  đuôi báo đã cắt — thà đại ca đọc thiếu phần cuối còn hơn không nhận được gì.
MAX_TEXT = 3900
#  0 = HỎI RỒI VỀ NGAY, cố ý không giữ kết nối chờ.
#  Giữ kết nối (long-polling) tốn ít lượt gọi hơn, nhưng `celery-worker` ở local chạy
#  `-c 1`: một việc ngồi ôm kết nối 15 giây là chiếm luôn ô worker DUY NHẤT, và lượt
#  gọi Gemini của trạm phân loại phải xếp hàng sau nó. Đổi lại độ trễ bằng đúng nhịp
#  beat (10 giây) — chấp nhận được, vì trạm nào cũng đang chờ đại ca bấm nút.
POLL_TIMEOUT = 0
HTTP_TIMEOUT = 20


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


def _call(method: str, payload: dict, *, timeout: int = 30) -> dict:
    token = settings.AGENT_TELEGRAM_BOT_TOKEN
    if not token:
        raise TelegramError("Chưa cấu hình AGENT_TELEGRAM_BOT_TOKEN")
    url = BASE_URL.format(token=token, method=method)
    try:
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


def _clip(text: str) -> str:
    if len(text) <= MAX_TEXT:
        return text
    return text[:MAX_TEXT] + "\n\n… (đã cắt bớt, xem đầy đủ trong sổ)"


def fetch_updates(offset: int) -> list[dict]:
    """Kéo tin mới. `offset` = id update kế tiếp cần đọc.

    Trả [] khi hết giờ chờ mà không có gì — đó là trường hợp THƯỜNG, không phải lỗi.
    """
    result = _call(
        "getUpdates",
        {
            "offset": offset,
            "timeout": POLL_TIMEOUT,
            #  Chỉ xin hai loại mình xử. Không lọc thì mỗi lần ai đó vào/ra nhóm là
            #  một update rỗng làm con trỏ nhảy, không hại nhưng tốn lượt.
            "allowed_updates": ["message", "callback_query"],
        },
        timeout=HTTP_TIMEOUT,
    )
    return result if isinstance(result, list) else []


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
        payload["reply_markup"] = {
            "inline_keyboard": [
                [{"text": label, "callback_data": data}] for label, data in buttons
            ]
        }
    result = _call("sendMessage", payload)
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
