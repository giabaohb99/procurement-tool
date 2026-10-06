"""Bốn tool SỔ GHI NHỚ CÁ NHÂN (ai-CR-095, nhóm C-02) — bộ nhớ riêng của NGƯỜI ĐANG HỎI, không phải dữ liệu ERP.

  - `remember_fact` (ghi lõi) : một dòng ngắn, ổn định về chính họ — ở đâu, gia đình, sở thích, cách muốn được trả lời,
                                 điều đã chốt. Trợ lý TỰ gọi khi nghe được, rồi báo một dòng «Em ghi nhớ: …».
  - `forget_fact`   (xóa lõi) : người dùng bảo quên / nói điều cũ sai.
  - `save_note`     (ghi kho) : nội dung dài — ghi chú dự án, danh bạ, đoạn văn họ dán, tóm tắt một buổi trao đổi.
  - `search_notes`  (đọc kho) : tìm trong ghi chú của chính họ.

`user_id` luôn là `ctx.user.id` — model KHÔNG có tham số chọn người, nên không với sang sổ người khác được
(bài canh `test_so_nho_tool_khong_lan_nguoi_khac`). Không ghi bí mật: `personal_memory.is_secret`.
"""
from __future__ import annotations

from app.modules.agent_hub import personal_memory as pm

from .base import ToolContext, ToolSpec


def _uid(ctx: ToolContext) -> int:
    return int(getattr(ctx.user, "id", 0) or 0)


def _remember_fact(ctx: ToolContext, args: dict) -> dict:
    out = pm.remember(ctx.db, _uid(ctx), str(args.get("text") or ""), str(args.get("section") or ""))
    if out.get("ok"):
        ctx.db.commit()
    return out


def _forget_fact(ctx: ToolContext, args: dict) -> dict:
    removed = pm.forget(ctx.db, _uid(ctx), str(args.get("text") or ""))
    if removed:
        ctx.db.commit()
    return {"ok": bool(removed), "removed": removed,
            "message": "đã quên" if removed else "không thấy dòng nào khớp trong sổ"}


def _save_note(ctx: ToolContext, args: dict) -> dict:
    out = pm.add_note(ctx.db, _uid(ctx), str(args.get("title") or ""), str(args.get("text") or ""))
    if out.get("ok"):
        ctx.db.commit()
    return out


def _search_notes(ctx: ToolContext, args: dict) -> dict:
    hits = pm.search_notes(ctx.db, _uid(ctx), str(args.get("query") or ""))
    return {"count": len(hits), "notes": hits}


REMEMBER_FACT_SPEC = ToolSpec(
    name="remember_fact",
    description=("GHI MỘT DÒNG vào sổ ghi nhớ RIÊNG của người đang hỏi (không phải dữ liệu ERP). Gọi khi họ nói một điều ỔN "
                 "ĐỊNH về chính mình: ở đâu / hay đi đâu, gia đình, sở thích, khẩu vị, cách muốn bạn trả lời (ngắn, không hỏi "
                 "lại…), điều đã chốt — hoặc khi họ bảo «nhớ …». Mỗi lần ghi, câu trả lời phải có dòng «Em ghi nhớ: …» để "
                 "họ «quên» nếu sai. KHÔNG ghi chuyện nhất thời (hôm nay mệt), KHÔNG ghi mật khẩu / khóa / số thẻ. "
                 "`section`: ban_than · so_thich · cach_lam_viec · da_chot (bỏ trống thì tự xếp)."),
    parameters={"type": "object", "properties": {
        "text": {"type": "string", "description": "Một dòng ngắn, ngôi thứ ba hoặc trung tính, vd «ở Cần Thơ, Ninh Kiều»."},
        "section": {"type": "string", "enum": list(pm.SECTION_KEYS)}},
        "required": ["text"]},
    handler=_remember_fact,
)
FORGET_FACT_SPEC = ToolSpec(
    name="forget_fact",
    description=("XÓA dòng trong sổ ghi nhớ riêng của người đang hỏi có chứa cụm `text` — khi họ bảo «quên …» hoặc nói điều "
                 "đã ghi không còn đúng (đổi chỗ ở, đổi ý)."),
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    handler=_forget_fact,
)
SAVE_NOTE_SPEC = ToolSpec(
    name="save_note",
    description=("LƯU một ghi chú DÀI vào kho riêng của người đang hỏi: ghi chú dự án, danh bạ, đoạn văn họ dán, điều họ "
                 "bảo «lưu lại», hay bản tóm tắt một buổi trao đổi dài. Không phải dữ liệu ERP, không ai khác đọc được. "
                 "Dòng ngắn về bản thân thì dùng remember_fact."),
    parameters={"type": "object", "properties": {
        "title": {"type": "string", "description": "Tiêu đề ngắn (≤ 60 ký tự)."},
        "text": {"type": "string"}},
        "required": ["text"]},
    handler=_save_note,
)
SEARCH_NOTES_SPEC = ToolSpec(
    name="search_notes",
    description=("TÌM trong kho ghi chú riêng của người đang hỏi («hôm trước anh có ghi gì về…», «tìm ghi chú về X»). Các "
                 "ghi chú liên quan nhất đã được nạp sẵn vào ngữ cảnh; gọi thêm khi cần tìm chủ đề khác."),
    parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    handler=_search_notes,
)
PERSONAL_SPECS = [REMEMBER_FACT_SPEC, FORGET_FACT_SPEC, SAVE_NOTE_SPEC, SEARCH_NOTES_SPEC]
