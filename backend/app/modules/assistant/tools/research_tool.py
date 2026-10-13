"""Tool NGHIÊN CỨU SÂU của Trợ lý (ai-CR-178, phase 23.1) — để người dùng web cũng gọi được.

Việc chạy NỀN vài phút (lập câu con → tìm + đọc nhiều trang → viết báo cáo → Word + Drive) nên tool chỉ KHỞI ĐỘNG và trả
về ngay; kết quả về CHAT RIÊNG (Telegram / Zalo) đã đăng nhập ERP của chính người hỏi — giống `latest_meeting_report`.
Không đọc dữ liệu ERP nào (nguồn là web công khai), không có tham số chọn người; chưa có chat riêng thì chỉ dẫn cách
đăng nhập chat với bot.

Ở chế độ tách dịch vụ (`AGENT_MODE=service`) tool này phải chạy ở dịch vụ AI: thêm `"research_tool"` vào
`agent_hub/erp.LOCAL_TOOL_MODULES` (tệp đó không nằm trong phạm vi sửa của ai-CR-178 — ghi trong báo cáo).
"""
from __future__ import annotations

from .base import ToolContext, ToolSpec


def _deep_research(ctx: ToolContext, args: dict) -> dict:
    from app.modules.agent_hub import deep_research, meeting_drive, user_keys

    question = " ".join(str(args.get("question") or "").split())
    if len(question) < 4:
        return {"error": "cần chủ đề nghiên cứu rõ ràng, ví dụ 'giá thép xây dựng quý 4 2026 và dự báo'"}
    uid = int(getattr(ctx.user, "id", 0) or 0)
    chat = meeting_drive.private_chat(ctx.db, uid)
    if not chat:
        return {"error": ("nghiên cứu sâu chạy nền vài phút và gửi kết quả (bản rút gọn + tệp Word + Drive) vào chat riêng "
                          "Telegram / Zalo đã đăng nhập ERP của bạn. Hãy nhắn riêng với bot, gõ /dangnhap <mã ở Trang cá "
                          "nhân>, rồi nhắn 'nghiên cứu sâu: <chủ đề>'.")}
    with user_keys.for_chat(ctx.db, chat):
        out = deep_research.start(ctx.db, chat, uid, deep_research.KIND_WEB, question)
    if out.get("status") == deep_research.ST_WAITING:
        msg = (f"Chi phí ước tính khoảng {out.get('usd', 0):.2f} USD nên bot đã gửi thẻ hỏi vào chat riêng; trả lời 'ok' "
               "ở đó để chạy.")
    elif out.get("status") == deep_research.ST_QUEUED:
        msg = "Đã bắt đầu nghiên cứu sâu; vài phút nữa kết quả (bản rút gọn + Word) về chat riêng đã đăng nhập của bạn."
    else:
        msg = "Chưa khởi động được nghiên cứu; xem tin bot gửi trong chat riêng."
    return {"started": out.get("status") in (deep_research.ST_QUEUED, deep_research.ST_WAITING), **out, "message": msg}


DEEP_RESEARCH_SPEC = ToolSpec(
    name="deep_research",
    description=(
        "NGHIÊN CỨU SÂU một chủ đề trên web (nhiều bước): bot tự lập 3–6 câu tìm con, tìm và đọc nhiều trang công khai, "
        "viết báo cáo có cấu trúc (tóm tắt · phát hiện chính trích nguồn [n] · chỗ mâu thuẫn · kết luận và khuyến nghị · "
        "danh mục nguồn) kèm tệp Word, lưu Drive. Gọi khi người dùng nói 'nghiên cứu sâu / nghiên cứu kỹ / báo cáo nghiên "
        "cứu về …', 'tìm hiểu toàn diện …'. KHÔNG dùng cho câu hỏi tra nhanh một con số (dùng trả lời thường). Việc chạy "
        "NỀN vài phút và kết quả về CHAT RIÊNG Telegram / Zalo của người hỏi — tool chỉ khởi động; khi trả lời hãy nói rõ "
        "`message` (đã bắt đầu / cần trả lời ok trong chat / cần đăng nhập chat với bot)."),
    parameters={"type": "object", "properties": {
        "question": {"type": "string", "description": "Chủ đề / câu hỏi nghiên cứu đầy đủ, ví dụ 'giá thép xây dựng quý 4 "
                                                       "2026 tại Việt Nam và dự báo'."},
    }, "required": ["question"]},
    handler=_deep_research,
)

RESEARCH_SPECS = (DEEP_RESEARCH_SPEC,)
