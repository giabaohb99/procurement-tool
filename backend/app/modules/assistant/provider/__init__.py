"""Lớp provider model cho Trợ lý AI — che nhà cung cấp phía sau một giao diện chung.

Phase 0: hai adapter Claude + Gemini (gọi REST bằng `requests`). App KHÔNG gọi thẳng
SDK/nhà nào; luôn qua `get_provider()`. Sau này thêm nhà mới (vd model mở tự nhúng docker)
chỉ là thêm một adapter đăng ký vào `_REGISTRY`.
"""
from app.core.config import settings

from .base import (
    ChatMessage,
    ChatResult,
    Provider,
    ProviderError,
    ToolDef,
    ToolExecutor,
)
from .claude import ClaudeProvider
from .gemini import GeminiProvider

# Đăng ký một thực thể mỗi nhà (không giữ trạng thái nên dùng chung an toàn).
_REGISTRY: dict[str, Provider] = {
    ClaudeProvider.name: ClaudeProvider(),
    GeminiProvider.name: GeminiProvider(),
}


def get_provider(name: str | None = None) -> Provider:
    """Lấy provider theo tên; None = nhà mặc định (config). Ưu tiên nhà đã cấu hình key."""
    if name:
        p = _REGISTRY.get(name)
        if not p:
            raise ProviderError(f"Không có nhà cung cấp '{name}'")
        return p
    # Không chỉ định: dùng mặc định nếu đã cấu hình, không thì nhà đầu tiên có key.
    default = _REGISTRY.get(settings.AI_DEFAULT_PROVIDER)
    if default and default.is_configured():
        return default
    for p in _REGISTRY.values():
        if p.is_configured():
            return p
    raise ProviderError("Chưa cấu hình API key cho nhà cung cấp AI nào (.env)")


def configured_providers() -> list[dict]:
    """Danh sách nhà + model mặc định + đã có key chưa (cho endpoint /providers)."""
    return [
        {"name": p.name, "default_model": p.default_model, "configured": p.is_configured()}
        for p in _REGISTRY.values()
    ]


__all__ = [
    "ChatMessage",
    "ChatResult",
    "Provider",
    "ProviderError",
    "ToolDef",
    "ToolExecutor",
    "get_provider",
    "configured_providers",
]
