"""Giao diện chung cho mọi nhà cung cấp model + kiểu dữ liệu trao đổi."""
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


class ProviderError(Exception):
    """Lỗi ở tầng provider (chưa cấu hình, API trả lỗi, mạng...)."""


@dataclass
class ChatMessage:
    """Một lượt hội thoại. role: 'user' | 'assistant'. 'system' truyền riêng qua tham số."""

    role: str
    content: str


@dataclass
class ToolDef:
    """Khai báo TRUNG LẬP một tool loại A cho model gọi (function calling).

    `parameters` là JSON Schema (object) đúng chuẩn cả Claude (`input_schema`) lẫn Gemini
    (`functionDeclarations[].parameters`). Provider tự dịch sang định dạng nhà mình.
    """

    name: str
    description: str
    parameters: dict


# Hàm THỰC THI một tool: nhận (tên, tham số) -> trả dict JSON-hóa được. Tầng service truyền
# vào, đóng gói sẵn danh tính người hỏi (db + user) nên provider KHÔNG chạm DB/quyền.
ToolExecutor = Callable[[str, dict], dict[str, Any]]


@dataclass
class ChatResult:
    """Kết quả trả về đã CHUẨN HÓA giữa các nhà — app chỉ đọc các trường này."""

    text: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    # Token "suy nghĩ" (Gemini 2.5/3.x, Claude thinking) — tính giá như output, tách ra để soi chi phí.
    thinking_tokens: int = 0
    # Prompt caching: token GHI cache (đắt hơn input thường ~25%) và ĐỌC cache (rẻ ~90%).
    # Gói tri thức đứng yên -> lượt sau đọc lại từ cache, đây là chỗ tiết kiệm lớn nhất.
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    # Vết các tool đã gọi trong lượt này (để audit + hiển thị minh bạch): [{name, args, rows}].
    tool_calls: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


class Provider:
    """Lớp cơ sở. Mỗi nhà kế thừa và cài `ask` + `is_configured`."""

    name: str = "base"
    default_model: str = ""
    # Nhà này có hỗ trợ tool-calling (loại A) chưa. Bật ở lớp con khi đã cài `run_tools`.
    supports_tools: bool = False

    def is_configured(self) -> bool:
        """Đã có API key chưa."""
        raise NotImplementedError

    def ask(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        thinking: bool = False,
        cache_system: bool = False,
    ) -> ChatResult:
        """Gửi hội thoại, nhận một câu trả lời (không streaming ở Phase 1).

        thinking=False: cố gắng TẮT suy nghĩ để tiết kiệm (nhà nào hỗ trợ). Bật cho câu
        tư vấn quy trình (loại B), tắt cho tra cứu số liệu (loại A).

        cache_system=True: đánh dấu khối `system` (gói tri thức đứng yên) để nhà cung cấp
        cache lại — lượt sau chỉ trả tiền đọc cache. Claude cần cache_control tường minh;
        Gemini 2.5+ tự cache ngầm phần đầu nên cờ này chỉ có tác dụng ở Claude.
        """
        raise NotImplementedError

    def run_tools(
        self,
        messages: list[ChatMessage],
        *,
        tools: list[ToolDef],
        execute: ToolExecutor,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        thinking: bool = False,
        cache_system: bool = False,
        max_iters: int = 6,
    ) -> ChatResult:
        """Vòng lặp tool-calling (loại A): model chọn tool -> `execute` chạy dưới quyền người
        hỏi -> trả kết quả lại cho model -> lặp tới khi model chốt câu trả lời chữ.

        `max_iters` chặn vòng lặp vô hạn. Tổng token cộng dồn qua các vòng vào ChatResult.
        Nhà chưa cài thì `supports_tools=False` và service tự lùi về `ask` không tool.
        """
        raise NotImplementedError
