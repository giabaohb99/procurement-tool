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
    until = None
    if str(args.get("until") or "").strip():
        until = pm.resolve_until(str(args.get("until")))
        if until is None:
            return {"ok": False, "message": "ngày hết hạn không đọc được, dùng dạng YYYY-MM-DD"}
    out = pm.remember(ctx.db, _uid(ctx), str(args.get("text") or ""), str(args.get("section") or ""), until=until)
    if out.get("ok"):
        ctx.db.commit()
    return out


def _forget_fact(ctx: ToolContext, args: dict) -> dict:
    removed = pm.forget(ctx.db, _uid(ctx), str(args.get("text") or ""))
    ctx.db.commit()             # ai-CR-137: cả khi lõi không có dòng nào, điều tự rút đang đếm vẫn thành bia mộ
    return {"ok": bool(removed), "removed": removed,
            "message": "đã quên" if removed else "không thấy dòng nào khớp trong sổ"}


def _save_note(ctx: ToolContext, args: dict) -> dict:
    out = pm.add_note(ctx.db, _uid(ctx), str(args.get("title") or ""), str(args.get("text") or ""))
    if out.get("ok"):
        ctx.db.commit()
    return out


def _search_chat_history(ctx: ToolContext, args: dict) -> dict:
    hits = pm.search_history(ctx.db, _uid(ctx), str(args.get("query") or ""), int(args.get("days") or 30))
    return {"count": len(hits), "messages": hits}


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
        "section": {"type": "string", "enum": list(pm.SECTION_KEYS)},
        "until": {"type": "string", "description": ("Ngày hết hạn YYYY-MM-DD cho điều TẠM THỜI («tuần này anh ở Đà Nẵng», "
                                                    "«tháng này ăn kiêng»). Bỏ trống = nhớ lâu dài.")}},
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
SEARCH_CHAT_HISTORY_SPEC = ToolSpec(
    name="search_chat_history",
    description=("TÌM LẠI HỘI THOẠI CŨ của chính người đang hỏi với bot («hôm trước anh hỏi gì về NCC X», «tuần trước mình "
                 "bàn giá thép thế nào»). Trả các tin cũ khớp từ khóa kèm ngày giờ. Dùng cùng search_notes (kho có bản tóm "
                 "tắt từng buổi). `days` mặc định 30, tối đa 180."),
    parameters={"type": "object", "properties": {"query": {"type": "string"},
                                                 "days": {"type": "integer", "minimum": 1, "maximum": 180}},
                "required": ["query"]},
    handler=_search_chat_history,
)
# ── Thẻ cá nhân (ai-CR-103, C-05): lịch trình / chi tiêu / mua sắm — dữ liệu riêng, không phải ERP ─────────────
def _kind(args: dict):
    from app.modules.agent_hub import personal_items as pi

    return pi.KIND_BY_NAME.get(str(args.get("kind") or "").strip())


def _add_personal_item(ctx: ToolContext, args: dict) -> dict:
    from app.modules.agent_hub import personal_items as pi

    kind = _kind(args)
    if kind is None:
        return {"ok": False, "message": "kind phải là lich_trinh · chi_tieu · mua_sam"}
    when = None
    if str(args.get("when") or "").strip():
        when = pi.parse_when(str(args.get("when")))
        if when is None:
            return {"ok": False, "message": "giờ không đọc được, dùng dạng YYYY-MM-DD HH:MM"}
    try:
        amount = int(float(args.get("amount") or 0))
    except (TypeError, ValueError):
        amount = 0
    out = pi.add(ctx.db, _uid(ctx), kind, str(args.get("title") or ""), amount=amount,
                 category=str(args.get("category") or ""), when=when, note=str(args.get("note") or ""))
    if out.get("ok"):
        ctx.db.commit()
    return out


def _list_personal_items(ctx: ToolContext, args: dict) -> dict:
    from app.modules.agent_hub import personal_items as pi

    kind = _kind(args)
    if kind is None:
        return {"error": "kind phải là lich_trinh · chi_tieu · mua_sam"}
    return pi.list_items(ctx.db, _uid(ctx), kind, period=str(args.get("period") or ""),
                         include_done=bool(args.get("include_done")))


def _mark_personal_item(ctx: ToolContext, args: dict) -> dict:
    from app.modules.agent_hub import personal_items as pi

    status = pi.ItemStatus.CANCELLED if str(args.get("status") or "") == "bo" else pi.ItemStatus.DONE
    out = pi.mark(ctx.db, _uid(ctx), item_id=int(args.get("id") or 0), title=str(args.get("title") or ""),
                  kind=_kind(args), status=status)
    if out.get("ok"):
        ctx.db.commit()
    return out


_KIND_PARAM = {"type": "string", "enum": ["lich_trinh", "chi_tieu", "mua_sam"]}
ADD_PERSONAL_ITEM_SPEC = ToolSpec(
    name="add_personal_item",
    description=("GHI vào THẺ CÁ NHÂN của người đang hỏi (dữ liệu riêng, không phải ERP): `lich_trinh` = việc / hẹn riêng "
                 "(kèm `when` nếu có giờ); `chi_tieu` = một khoản đã chi (`amount` đồng, `category` như ăn uống, đi lại, "
                 "nhà cửa…); `mua_sam` = món cần mua. Ví dụ «trưa nay ăn 45k» → chi_tieu 45000 ăn uống; «mua sữa với trứng» → "
                 "hai món mua_sam. Ghi xong báo một dòng."),
    parameters={"type": "object", "properties": {
        "kind": _KIND_PARAM, "title": {"type": "string"},
        "amount": {"type": "number", "description": "Số tiền đồng (chỉ chi_tieu). «45k» = 45000, «1tr2» = 1200000."},
        "category": {"type": "string"},
        "when": {"type": "string", "description": "YYYY-MM-DD HH:MM giờ Việt Nam (lịch trình), hoặc lúc chi."},
        "note": {"type": "string"}},
        "required": ["kind", "title"]},
    handler=_add_personal_item,
)
LIST_PERSONAL_ITEMS_SPEC = ToolSpec(
    name="list_personal_items",
    description=("XEM THẺ CÁ NHÂN: lịch trình riêng, chi tiêu (kèm tổng và theo nhóm), danh sách cần mua. `period` hom_nay · "
                 "tuan_nay · thang_nay · tat_ca (chi tiêu mặc định tháng này)."),
    parameters={"type": "object", "properties": {
        "kind": _KIND_PARAM, "period": {"type": "string", "enum": ["hom_nay", "tuan_nay", "thang_nay", "tat_ca"]},
        "include_done": {"type": "boolean"}},
        "required": ["kind"]},
    handler=_list_personal_items,
)
MARK_PERSONAL_ITEM_SPEC = ToolSpec(
    name="mark_personal_item",
    description=("ĐÁNH DẤU một món trong thẻ cá nhân là XONG («mua sữa rồi», «xong việc đón con») hoặc BỎ (`status` = bo). Theo "
                 "`id` hoặc `title` (khớp đúng một món đang mở; khớp nhiều thì hỏi lại kèm lựa chọn)."),
    parameters={"type": "object", "properties": {
        "id": {"type": "integer"}, "title": {"type": "string"}, "kind": _KIND_PARAM,
        "status": {"type": "string", "enum": ["xong", "bo"]}}},
    handler=_mark_personal_item,
)
PERSONAL_SPECS = [REMEMBER_FACT_SPEC, FORGET_FACT_SPEC, SAVE_NOTE_SPEC, SEARCH_NOTES_SPEC, SEARCH_CHAT_HISTORY_SPEC,
                  ADD_PERSONAL_ITEM_SPEC, LIST_PERSONAL_ITEMS_SPEC, MARK_PERSONAL_ITEM_SPEC]
