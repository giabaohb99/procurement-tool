"""Bộ mã «DÙNG AI» cho nhóm chỉ số 3.8 (duoc-CR-655, D0d) — số đã cấp KHÔNG ĐỔI, KHÔNG TÁI DÙNG.

Kênh AI (`AI_CHANNEL_*`) do ai-CR-230 cấp ở `logging_codes.py` (cột `tab_ai_usage_daily.channel` và
`tab_audit_log.ai_channel`); tệp này CHỈ đăng ký bộ mã đó vào `status_catalog` để giao diện nhận bản TS sinh ra,
và thêm bộ «ứng dụng AI» để giá trị chỉ số `ai_main_client` là số (R2). Không đổi tệp của ai-CR-230.

Thuần stdlib (cùng `usage_codes.py`): `code_sets.py` phải nạp được khi chạy `scripts/gen_status_ts.py`.
"""
from enum import IntEnum

from app.core.logging_codes import AI_CHANNEL_LABELS, AI_CHANNEL_NONE
from app.core.status_catalog import Code, CodeSet, register


class AiClient(IntEnum):
    """Ứng dụng AI ngoài nối qua cổng MCP, suy từ `clientInfo.name` (tên sản phẩm, không phải chữ người gõ)."""

    CLAUDE = 1
    CHATGPT = 2
    OTHER = 9


AI_CLIENT_LABELS = {AiClient.CLAUDE: "Claude", AiClient.CHATGPT: "ChatGPT", AiClient.OTHER: "Ứng dụng AI khác"}


def ai_client_code(name: str) -> int:
    n = (name or "").lower()
    if "claude" in n:
        return int(AiClient.CLAUDE)
    if "chatgpt" in n or "openai" in n:
        return int(AiClient.CHATGPT)
    return int(AiClient.OTHER)


#  0 = «tự làm» không phải một kênh để chọn → bỏ khỏi bộ mã hiển thị.
AI_CHANNEL_SET = register(CodeSet(
    "ai_channel", "Kênh dùng AI",
    [Code(str(k), v, sort_order=k) for k, v in AI_CHANNEL_LABELS.items() if k != AI_CHANNEL_NONE]))
AI_CLIENT_SET = register(CodeSet(
    "ai_client", "Ứng dụng AI",
    [Code(str(int(k)), v, sort_order=int(k), key=k.name) for k, v in AI_CLIENT_LABELS.items()]))
