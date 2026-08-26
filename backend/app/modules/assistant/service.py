"""Tầng dịch vụ Trợ lý AI — điều phối provider + routing theo loại câu hỏi.

- Phase 1: gọi model kèm GÓI TRI THỨC (AI-1) nhồi vào `system` + prompt caching.
- Phase 2: tool loại A. Khi có `db`+`user` và nhà cung cấp hỗ trợ, đưa danh sách tool cho
  model tự chọn gọi; tool chạy DƯỚI danh tính người hỏi (`tools.run_tool`) rồi trả số thật.

Routing quyết định: bật/tắt suy nghĩ + trần token + có mở tool hay không theo loại câu.
"""
from datetime import date

from app.core.config import settings

from . import tools as tool_layer
from .knowledge import build_system
from .provider import ChatMessage, get_provider

# kind câu hỏi -> cấu hình sinh. 'lookup' = loại A (tra cứu, rẻ, không cần suy nghĩ);
# 'advice' = loại B (tư vấn quy trình, cần suy nghĩ); 'general' = mặc định.
# `tools`: có mở lớp tool loại A cho model không. Loại B (advice) là hỏi văn bản -> chưa cần.
ROUTING: dict[str, dict] = {
    "lookup":  {"thinking": False, "max_tokens": 1024, "temperature": 0.2, "tools": True},
    "advice":  {"thinking": True,  "max_tokens": 2048, "temperature": 0.4, "tools": False},
    "general": {"thinking": False, "max_tokens": 1536, "temperature": 0.3, "tools": True},
}

# Hướng dẫn khi bật tool — bản đồ NĂNG LỰC + chiến lược gọi tool, để model tự chọn/kết hợp
# công cụ và biết nói gì khi câu hỏi nằm ngoài phạm vi (thay vì chỉ xin lỗi).
TOOL_GUIDE = """\
Bạn có bộ CÔNG CỤ tra dữ liệu thu mua thật (đã lọc theo quyền của người hỏi). Khi câu hỏi cần
số liệu, HÃY GỌI CÔNG CỤ thay vì đoán. Bộ công cụ trả lời được các nhóm câu:

- Hợp đồng NCC: còn hạn / hết hạn, đếm theo trạng thái, hợp đồng của một NCC cụ thể.
- Giá & lịch sử mua theo MÃ HÀNG: giá tốt nhất, lịch sử mua, các NCC từng bán mã đó.
- Tổng hợp toàn hệ: lần mua gần nhất, NCC mua nhiều nhất, đơn mua hàng (PO) gần nhất kèm giá
  trị, báo cáo chi tiêu (tổng, theo tháng, top mã hàng).
- Thống kê TÙY BIẾN (analytics_query): kết hợp CHỈ SỐ (chi tiêu / số lần mua / số lượng / đơn
  giá trung bình) theo CHIỀU (nhà cung cấp / mã hàng / tháng) trong một khoảng ngày, lọc theo
  NCC hoặc mã hàng. Dùng cho câu KHÔNG khớp các công cụ chuyên biệt ở trên, ví dụ "chi tiêu
  của NCC X theo từng tháng", "số lượng mã Y đã mua trong quý 1", "đơn giá trung bình mã Z".
- Tra danh mục: product_search / supplier_search để đổi MÔ TẢ sang mã.

Chiến lược gọi công cụ:
- Người hỏi mô tả sản phẩm/NCC bằng lời -> gọi product_search / supplier_search lấy mã TRƯỚC,
  rồi mới gọi công cụ cần mã. Được phép gọi NHIỀU công cụ nối tiếp trong một câu, cứ gọi tiếp
  đến khi đủ dữ liệu để trả lời.
- Câu có mốc thời gian ("năm nay", "quý 1", "tháng trước") -> tự quy ra ngày YYYY-MM-DD dựa
  vào ngày hôm nay ở trên rồi điền date_from/date_to.
- Kết quả rỗng hoặc bị từ chối (denied) -> nói thẳng là không có dữ liệu / không đủ quyền,
  KHÔNG bịa. Nếu câu hỏi nằm NGOÀI các nhóm trên, đừng chỉ xin lỗi: nêu ngắn gọn bạn tra được
  những gì (vài nhóm ở trên) để người hỏi hỏi lại đúng hướng.

Trả lời gọn, nêu con số cụ thể, ghi rõ nguồn là số liệu hệ thống."""


def _extra_system(tool_on: bool, caller: str | None) -> str | None:
    parts = []
    if tool_on:
        # Ngày hôm nay đặt TRƯỚC guide để model quy đổi "năm nay/quý 1/..." sang date_from/date_to.
        parts.append(f"Hôm nay là {date.today().isoformat()} (định dạng YYYY-MM-DD).")
        parts.append(TOOL_GUIDE)
    if caller:
        parts.append(caller)
    return "\n\n".join(parts) if parts else None


def ask(
    message: str,
    *,
    db=None,
    user=None,
    provider: str | None = None,
    model: str | None = None,
    kind: str = "general",
    system: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    """Hỏi một câu, trả về dict đã chuẩn hóa (dùng cho endpoint /chat).

    Có `db`+`user` (đi từ endpoint) thì mở lớp tool loại A; gọi trực tiếp không kèm ngữ cảnh
    người dùng (vd test provider) thì lùi về đường không tool.
    """
    cfg = ROUTING.get(kind, ROUTING["general"])
    prov = get_provider(provider)

    # Guard chi phí: câu tra cứu / mặc định có thể chạy model RẺ hơn (nếu admin khai
    # AI_LOOKUP_MODEL); câu tư vấn (advice) giữ model mặc định, thông minh hơn. Caller
    # chỉ định model tường minh thì tôn trọng, không đè.
    if model is None and settings.AI_LOOKUP_MODEL and kind in ("lookup", "general"):
        model = settings.AI_LOOKUP_MODEL

    tool_on = bool(cfg["tools"] and db is not None and user is not None and prov.supports_tools)

    # `system` của caller KHÔNG ghi đè định nghĩa/rào an toàn — chỉ chèn THÊM vào cuối.
    full_system = build_system(extra=_extra_system(tool_on, system))

    msgs: list[ChatMessage] = []
    for h in history or []:
        role = h.get("role")
        content = h.get("content", "")
        if role in ("user", "assistant") and content:
            msgs.append(ChatMessage(role=role, content=content))
    msgs.append(ChatMessage(role="user", content=message))

    common = {
        "model": model,
        "system": full_system,
        "max_tokens": cfg["max_tokens"],
        "temperature": cfg["temperature"],
        "thinking": cfg["thinking"],
        "cache_system": True,   # gói tri thức đứng yên -> cache prefix, lượt sau rẻ
    }

    if tool_on:
        result = prov.run_tools(
            msgs,
            tools=tool_layer.tool_defs(),
            execute=lambda name, args: tool_layer.run_tool(db, user, name, args),
            **common,
        )
    else:
        result = prov.ask(msgs, **common)

    return {
        "text": result.text,
        "provider": result.provider,
        "model": result.model,
        "kind": kind,
        "tool_calls": result.tool_calls,
        "usage": {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "thinking_tokens": result.thinking_tokens,
            "cache_write_tokens": result.cache_write_tokens,
            "cache_read_tokens": result.cache_read_tokens,
        },
    }
