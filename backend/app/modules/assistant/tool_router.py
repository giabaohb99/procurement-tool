"""Nạp công cụ theo nhu cầu (ai-CR-161, phase 16.2).

Đo trên dev 10/10/2026: mỗi câu hỏi gửi kèm đủ 69 khai báo công cụ (~69.000 ký tự); một lượt trả lời web trung bình
~85.000 token vào. Ở đây chọn trước, KHÔNG gọi model: nhóm LÕI luôn gửi, cộng các nhóm nghiệp vụ mà câu hỏi chạm tới
(so chữ đã bỏ dấu), cộng nhóm của công cụ vừa dùng ở lượt trước (câu nối tiếp kiểu «xuất Excel», «còn NCC khác không»).

An toàn trước, rẻ sau:
- Không khớp nhóm nào → trả None = gửi ĐỦ như cũ.
- Đã lọc mà model thấy thiếu công cụ → model trả đúng chuỗi `NEED_MORE_TOOLS`, `assistant.service.ask` hỏi lại MỘT lần
  với đủ công cụ (xem `ROUTED_NOTE`).
- Thêm công cụ mới mà quên xếp nhóm → nó vào nhóm LÕI? Không: bài kiểm `test_assistant_tool_router.py` đỏ.
"""
from __future__ import annotations

import re

from app.modules.assistant.glossary import fold

NEED_MORE_TOOLS = "[CAN_THEM_CONG_CU]"
ROUTED_NOTE = (f"Bộ công cụ của lượt này đã được lọc theo câu hỏi. Nếu cần một công cụ KHÔNG có trong danh sách để trả "
               f"lời đúng, CHỈ trả lời đúng chuỗi {NEED_MORE_TOOLS} và không viết gì khác.")
#  ai-CR-183: gói tri thức cũng được lọc — nói rõ gói nào CHƯA nạp để model xin thêm thay vì bịa.
PACK_NOTE = ("Gói tri thức của lượt này cũng đã được lọc; các mảng CHƯA nạp: {titles}. Nếu câu hỏi thuộc một mảng đó, "
             f"CHỈ trả lời đúng chuỗi {NEED_MORE_TOOLS}.")

#  Nhóm lõi: nhẹ, dùng ở mọi loại câu.
CORE = frozenset({"search_docs", "glossary_lookup", "remember_fact", "forget_fact", "search_chat_history",
                  "report_missing_feature"})

#  (tên nhóm, công cụ, mẫu chữ ĐÃ BỎ DẤU). Một công cụ có thể nằm ở nhiều nhóm.
GROUPS: tuple[tuple[str, frozenset[str], str], ...] = (
    ("purchase", frozenset({
        "recent_purchase_orders", "recent_purchases", "my_procurement_requests", "procurement_doc_read",
        "pending_procurement_approvals", "purchase_report", "product_search", "product_best_price",
        "product_purchase_history", "supplier_search", "suppliers_for_product", "top_suppliers_by_purchase",
        "supplier_contracts", "contract_count_by_status", "contract_list_by_expiry", "analytics_query",
        #  ai-CR-173/174 (phase 23.4/23.5): giá + link trên web, chấm điểm NCC.
        "market_price_search", "supplier_scorecard"}),
     r"mua hang|don mua|dmh|\bpo\d*|ycmh|yeu cau mua|phieu mua|bao gia|ycbg|khao sat|\bncc\b|nha cung cap|san pham"
     r"|mat hang|\bgia\b|hop dong|nhap kho|thu mua|vat tu|dat hang|giao hang|tien do"
     r"|gia thi truong|tim gia|gia web|gia tren mang|link (mua|san pham)|ncc tot nhat|cham diem|danh gia ncc"
     r"|xep hang ncc|nha cung cap tot|nen mua( .{1,40})? cua ai|so ncc"),
    ("make_purchase", frozenset({"draft_purchase_request", "draft_survey_request"}),
     r"(len|tao|lap|soan|lam)( giup| giup anh| giup em)? (phieu|ycmh|ycbg|yeu cau|don)|can mua|dat mua|xin mua"
     r"|de xuat mua|phieu bao gia"),
    ("payable", frozenset({"payable_lookup", "payment_request_read", "draft_payment_request", "analytics_query"}),
     r"cong no|con no|tien no|no qua han|thanh toan|yctt|de nghi thanh toan|chi tien|hoa don|tra tien|chuyen khoan"
     r"|qua han"),
    ("approval", frozenset({"my_approval_tasks", "my_requests_status", "approval_flow_lookup",
                            "pending_procurement_approvals"}),
     r"duyet|phe duyet|trinh ky|luong duyet|cho ky"),
    ("leave", frozenset({"my_leave_summary", "draft_leave_request"}),
     r"nghi phep|\bphep\b|xin nghi|don nghi|nghi (thu|ngay|sang|chieu|ca)|\bnp\d+|quy phep|ngay nghi"),
    ("work", frozenset({"my_work_tasks", "draft_work_task", "draft_work_plan"}),
     r"\bviec\b|\btask\b|cong viec|du an|giao viec|han chot|deadline|viec hom nay|viec cua (toi|anh|em)|con gi|qua han"),
    ("ticket", frozenset({"my_tickets", "ticket_create"}),
     r"ho tro|ticket|bao loi|su co|\bit\b|may in|phieu ho tro"),
    ("edit", frozenset({"propose_document_update", "propose_document_delete", "procurement_doc_read"}),
     r"\bsua\b|\bdoi\b|chinh|\bxoa\b|bo dong|them .{1,40} vao|cap nhat|ly do"),
    ("account", frozenset({"propose_account_setup", "employee_lookup"}),
     r"tai khoan|vai tro|phan quyen|gan quyen|loai tru phong"),
    ("employee", frozenset({"employee_lookup"}),
     r"nhan vien|nhan su|so dien thoai|\bsdt\b|email|phong ban|truong phong|ai la|sinh nhat"),
    ("customs", frozenset({"customs_price_stats", "customs_buy_timing", "customs_market", "customs_legal_check"}),
     r"hai quan|to khai|nhap khau|gia nhap|\bhs\b|thi truong|thong quan|xuat khau|cif"),
    ("document", frozenset({"document_read", "document_search", "my_documents", "approval_flow_lookup"}),
     r"van ban|cong van|quyet dinh|to trinh|thong bao so|\bcv\d*|van thu|so cong van"),
    ("google", frozenset({"my_calendar_events", "create_calendar_event", "update_calendar_event",
                          "delete_calendar_event", "drive_read", "drive_search"}),
     r"\blich\b|cuoc hop|buoi hop|di hop|lich hop|\bhop (luc|vao|voi|ncc|chieu|sang)|\bhen\b|drive|google"),
    ("meeting", frozenset({"latest_meeting_report", "list_my_meetings", "rewrite_meeting_minutes",
                           "save_meeting_template"}),
     r"bien ban|recap|cuoc hop|buoi hop|mau bien ban"),
    ("group", frozenset({"list_my_groups", "read_group_messages", "read_group_file"}),
     r"\bnhom\b|group|zalo"),
    ("personal", frozenset({"add_personal_item", "list_personal_items", "mark_personal_item", "save_note",
                            "search_notes"}),
     r"chi tieu|\bchi \d|mua gi|ghi chu|viec rieng|\bnhac\b|di cho|danh sach mua|so nho|\bnho\b"),
    ("brief", frozenset({"manage_briefs"}), r"ban tin|diem bao|tin tuc|moi sang gui|hang ngay gui"),   # ai-CR-179 điểm báo
    #  ai-CR-178 (phase 23.1): nghiên cứu sâu nhiều nguồn, chạy nền, kết quả về chat riêng.
    ("research", frozenset({"deep_research"}),
     r"nghien cuu (sau|ky|ki|chi tiet|toan dien|day du|nhieu nguon)|bao cao nghien cuu|deep research"),
    ("export", frozenset({"export_excel_file", "export_report_file"}),
     r"xuat|excel|\bword\b|bao cao|tai ve|\bfile\b|\btep\b"),
    ("glossary", frozenset({"propose_glossary_term"}), r"thuat ngu|goi la|nghia la|viet tat"),
    ("analytics", frozenset({"analytics_query"}), r"thong ke|tong hop|bao nhieu|\btop\b|so sanh|xu huong"),
)
_COMPILED = tuple((name, tools, re.compile(pattern)) for name, tools, pattern in GROUPS)
ALL_GROUPED = frozenset().union(CORE, *(tools for _n, tools, _p in GROUPS))


def groups_for(text: str) -> list[str]:
    t = " " + fold(text or "") + " "
    return [name for name, _tools, rx in _COMPILED if rx.search(t)]


def groups_of_tools(names) -> list[str]:
    used = {str(n) for n in names or []}
    return [name for name, tools, _rx in _COMPILED if tools & used]


#  ai-CR-183: chủ đề GÓI TRI THỨC (`knowledge.PACK_TOPICS`) — theo nhóm công cụ đã chọn hoặc từ khóa riêng.
PACK_RULES: tuple[tuple[str, frozenset[str], str], ...] = (
    ("document", frozenset({"document"}), r"van ban|van thu|cong van|ban hanh|so ky hieu|luu tru|ho so luu"),
    ("work", frozenset({"work"}), r"du an|cong viec|\btask\b|kanban"),
    ("leave", frozenset({"leave"}), r"nghi phep|\bphep\b|quy phep|ngay nghi"),
    ("room", frozenset(), r"phong hop|dat phong|meeting room"),
    ("employee", frozenset({"employee", "account"}), r"ho so nhan su|chuc vu|ly lich|nhan su|hop dong lao dong|hdld"),
    ("factory", frozenset(), r"nha may|organic|qd\.ht|hd\.ht|he thong cong viec|cai tien|san xuat|\bxuong\b|ca lam|"
                              r"quy dinh he thong|giao thuc|tro ly ai nha may"),
)
_PACK_COMPILED = tuple((topic, groups, re.compile(rx)) for topic, groups, rx in PACK_RULES)


def pack_topics(message: str, picked_groups, recent_text: str = "") -> set[str] | None:
    """Chủ đề gói tri thức cho câu này. `picked_groups` None (gửi đủ công cụ) → None = nạp đủ gói. Có nhóm công cụ →
    chủ đề của các nhóm đó + chủ đề khớp từ khóa trong câu (và 2 câu người dùng gần nhất)."""
    if picked_groups is None:
        return None
    groups = set(picked_groups)
    t = " " + fold((message or "") + " " + (recent_text or "")) + " "
    return {topic for topic, g, rx in _PACK_COMPILED if (g & groups) or rx.search(t)}


def groups_selected(message: str, recent_tools=None) -> set[str]:
    return set(groups_for(message)) | set(groups_of_tools(recent_tools))


#  ai-CR-192: câu XÃ GIAO (chào, cảm ơn, ok…) — không cần công cụ nghiệp vụ lẫn gói tri thức; đo dev 16:27: «hello» nạp
#  đủ 73 công cụ + 7 gói = 56k token. So trên chữ đã bỏ dấu, chỉ khi CẢ câu là xã giao.
SMALLTALK = re.compile(r"^(?:(?:a+\s*)?l[oô]+|hello|hi|hey|chao(?: em| anh| chi| bot| ban| ca nha| lac lac| buoi sang| buoi chieu)?|"
                       r"cam on(?: em| anh| chi| nhe| nha| nhieu)*|thanks?|thank you|ok|oke|okay|tot|hay|duoc|good|bye|tam biet|"
                       r"ngu ngon|chuc .{0,30}|em oi|oi|test|ping)[\s.!?,~]*$")


def is_smalltalk(text: str) -> bool:
    return bool(SMALLTALK.match(" ".join(fold(text or "").split())))


RECENT_WINDOW_MIN = 15


def recent_tools(db, user_id: int) -> list[str]:
    """Công cụ của câu hỏi gần nhất (≤ 15 phút) của người này — câu nối tiếp («xuất Excel», «còn NCC khác không») cần
    lại đúng nhóm đó. Lấy từ sổ ý định (ai-CR-137). Hỏng thì [] — chỉ làm mất phần nối tiếp, không làm hỏng câu."""
    try:
        from datetime import timedelta

        from app.modules.agent_hub.model import AgentIntent
        from app.modules.agent_hub.timeutil import now_utc

        row = (db.query(AgentIntent).filter(AgentIntent.user_id == int(user_id or 0),
                                            AgentIntent.created_at >= now_utc() - timedelta(minutes=RECENT_WINDOW_MIN))
               .order_by(AgentIntent.id.desc()).first())
        return [str(t) for t in (row.tools or [])] if row is not None else []
    except Exception:  # noqa: BLE001
        return []


def select(message: str, recent_tools=None) -> set[str] | None:
    """Tên công cụ gửi kèm câu này; None = gửi đủ (không khớp nhóm nào — an toàn hơn đoán).

    ai-CR-183: không khớp nhóm nào nhưng người này VỪA dùng công cụ (≤ 15 phút) → câu nối tiếp («hạn là thứ 6 tuần
    sau, em tạo luôn nhé») đi với lõi + nhóm cũ, không gửi đủ 72 công cụ (đo 13/10: 9 → 72 giữa hai câu cùng một việc
    làm prompt phình và mất bộ đệm)."""
    picked = set(groups_for(message)) | set(groups_of_tools(recent_tools))
    if not picked:
        return None
    out = set(CORE)
    for name, tools, _rx in _COMPILED:
        if name in picked:
            out |= tools
    return out
