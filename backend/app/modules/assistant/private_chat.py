"""Cờ "cuộc trò chuyện RIÊNG của chính người hỏi" cho cả lượt xử lý (duoc-CR-757, luật lương).

Gắn bằng MÁY ở đúng chỗ đặt kênh AI (`agent_hub.service.handle_message`, cạnh `ai_channel_scope`), không bao giờ lấy từ
lời model hay tham số công cụ. Chế độ tách dịch vụ AI: `agent_hub.erp` gửi kèm header `PRIVATE_CHAT_HEADER`, cổng B
(`agent_gateway.controller`) chỉ đọc nó SAU khi chữ ký dịch vụ đúng — cùng khuôn header kênh AI (ai-CR-230).

Biến riêng, nhẹ (không kéo theo sổ công cụ) để cổng B / lớp gọi ERP nhập được mà không nạp cả `assistant.tools`.
"""
from contextlib import contextmanager
from contextvars import ContextVar, Token

from app.core.agent_signature import HEADER_PRIVATE_CHAT as PRIVATE_CHAT_HEADER  # noqa: F401 — nằm trong chuỗi ký cổng B

_private_chat: ContextVar[bool] = ContextVar("ai_private_chat", default=False)


def current_private_chat() -> bool:
    return bool(_private_chat.get())


def set_private_chat(flag: bool) -> Token:
    return _private_chat.set(bool(flag))


@contextmanager
def private_chat_scope(flag: bool):
    """Mọi công cụ chạy trong khối này biết lượt đang ở chat riêng (đã liên kết, không phải nhóm) hay không."""
    token = _private_chat.set(bool(flag))
    try:
        yield
    finally:
        _private_chat.reset(token)
