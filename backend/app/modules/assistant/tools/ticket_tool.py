"""Tool phiếu hỗ trợ (CR-218): `ticket_create` (soạn nháp — KHÔNG ghi DB) + `my_tickets`.

`ticket_create` theo đúng khuôn draft_tool: trợ lý chỉ gom thông tin thành BẢN ĐỀ XUẤT,
giao diện chat hiện nút mở form tạo phiếu hỗ trợ đã điền sẵn — người dùng rà lại rồi tự
bấm Gửi. `my_tickets` trả các phiếu CHÍNH người hỏi đứng tên (created_by = tài khoản hỏi,
hoặc requester_id = hồ sơ nhân sự của họ) — không cần scope vì điều kiện chủ sở hữu đã
chặt hơn mọi scope.
"""
from sqlalchemy import or_

from app.modules.ticket.model import Ticket
from app.modules.ticket.service import PRIORITIES, PRIORITY_LABELS, STATUS_LABELS, STATUSES

from .base import ToolContext, ToolSpec
from .draft_tool import _clean_text

#  Nhóm tiếp nhận — chép ĐÚNG danh sách của form tạo phiếu (create-ticket-dialog.tsx);
#  đây là nhãn tự do trong DB, danh sách chỉ để model chọn đúng chữ với form.
_DEPARTMENTS = ("Hệ thống / CNTT", "Thu mua / Cung ứng", "Kế toán / Tài chính",
                "Nhân sự / Hành chính", "Sản xuất / Kho", "Khác")

_CREATE_PARAMS = {
    "type": "object",
    "properties": {
        "subject": {"type": "string",
                    "description": "Tiêu đề phiếu hỗ trợ — bắt buộc, nêu ngắn gọn vấn đề."},
        "body": {"type": "string",
                 "description": "Mô tả chi tiết vấn đề / lỗi gặp phải — bắt buộc."},
        "department": {
            "type": "string",
            "enum": list(_DEPARTMENTS),
            "description": "Nhóm tiếp nhận — chọn theo nội dung vấn đề; không rõ thì bỏ "
                           "trống (mặc định Hệ thống / CNTT).",
        },
        "priority": {
            "type": "string",
            "enum": list(PRIORITIES),
            "description": "Mức ưu tiên: low | normal | high | urgent. Chỉ đặt high/urgent "
                           "khi người dùng nói việc gấp; mặc định normal.",
        },
    },
    "required": ["subject", "body"],
}

_CREATE_DESC = (
    "SOẠN SẴN dữ liệu cho PHIẾU HỖ TRỢ nội bộ từ vấn đề người dùng mô tả (lỗi hệ thống, "
    "hỏi nghiệp vụ, xin cấp quyền...). KHÔNG tạo phiếu — chỉ chuẩn bị bản đề xuất; giao "
    "diện sẽ hiện nút mở form tạo phiếu hỗ trợ đã điền sẵn để người dùng rà lại và tự bấm "
    "Gửi. Gọi khi người dùng muốn báo lỗi / cần hỗ trợ và đã mô tả được vấn đề; thiếu chi "
    "tiết thì hỏi gộp MỘT lượt (hiện tượng, màn hình nào, mã phiếu liên quan nếu có) rồi "
    "mới gọi. Đủ thông tin thì PHẢI gọi ngay trong lượt trả lời — nút 'Tạo phiếu hỗ trợ' "
    "chỉ xuất hiện khi tool được gọi. Sau khi gọi, báo người dùng bấm nút đó để mở form — "
    "nhấn mạnh phiếu CHƯA được tạo."
)


def _run_create(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("ticket", "create"):
        return {"denied": True,
                "reason": "Bạn không có quyền tạo phiếu hỗ trợ (ticket.create)."}

    subject = _clean_text(args.get("subject"), 255)
    body = _clean_text(args.get("body"), 4000)
    if not subject or not body:
        return {"error": "Thiếu subject hoặc body — hỏi người dùng bổ sung rồi gọi lại."}

    department = _clean_text(args.get("department"), 255)
    if department not in _DEPARTMENTS:
        department = _DEPARTMENTS[0]
    priority = _clean_text(args.get("priority"), 20)
    if priority not in PRIORITIES:
        priority = "normal"

    return {
        "status": "ready",
        "total": 1,
        "draft": {
            #  `kind` để giao diện chat phân biệt với bản nháp YCBG/YCMH/nghỉ phép.
            "kind": "ticket",
            "subject": subject,
            "department": department,
            "priority": priority,
            "body": body,
        },
        "priority_label": PRIORITY_LABELS.get(priority, priority),
        "reminder": "Phiếu CHƯA được tạo. Hãy tóm tắt bản đề xuất (tiêu đề, nhóm tiếp nhận, "
                    "mức ưu tiên) và mời người dùng bấm nút 'Tạo phiếu hỗ trợ' dưới câu "
                    "trả lời để mở form đã điền sẵn — họ rà lại rồi tự bấm Gửi.",
    }


TICKET_CREATE_SPEC = ToolSpec(
    name="ticket_create",
    description=_CREATE_DESC,
    parameters=_CREATE_PARAMS,
    handler=_run_create,
)


# ── Phiếu hỗ trợ CỦA TÔI ─────────────────────────────────────────────────────────────────

MAX_ROWS = 30

_MINE_PARAMS = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": list(STATUSES),
            "description": "Lọc theo trạng thái: open (Mới) | in_progress (Đang xử lý) | "
                           "answered (Đã trả lời) | closed (Đã đóng). Bỏ trống = tất cả.",
        },
        "limit": {"type": "integer",
                  "description": f"Số phiếu tối đa (mặc định 10, trần {MAX_ROWS})."},
    },
}

_MINE_DESC = (
    "Danh sách phiếu hỗ trợ do CHÍNH người hỏi gửi, mới nhất trước — kèm trạng thái, nhóm "
    "tiếp nhận và đường dẫn mở chi tiết. Gọi khi người dùng hỏi 'phiếu hỗ trợ của tôi tới "
    "đâu rồi', 'ticket tôi gửi đã được trả lời chưa'... Khi trả lời, kèm `url` dạng link "
    "để người dùng bấm mở phiếu."
)


def _run_mine(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("ticket", "read"):
        return {"denied": True,
                "reason": "Bạn không có quyền xem phiếu hỗ trợ (ticket.read)."}

    limit = args.get("limit")
    limit = max(1, min(int(limit), MAX_ROWS)) if isinstance(limit, (int, float)) else 10

    #  Chính chủ theo CẢ HAI cột: created_by (tài khoản tạo) + requester_id (hồ sơ nhân sự)
    #  — cùng khuôn với my_procurement_requests, phòng phiếu do người khác tạo hộ.
    owner_conds = [Ticket.created_by == ctx.user.id]
    emp_id = getattr(ctx.user, "employee_id", 0) or 0
    if emp_id:
        owner_conds.append(Ticket.requester_id == emp_id)
    q = ctx.db.query(Ticket).filter(or_(*owner_conds))

    status = str(args.get("status") or "").strip()
    if status in STATUSES:
        q = q.filter(Ticket.status == status)

    rows = q.order_by(Ticket.id.desc()).limit(limit).all()
    items = [{
        "code": t.code,
        "subject": t.subject,
        "department": t.department,
        "priority": t.priority,
        "priority_label": PRIORITY_LABELS.get(t.priority, t.priority),
        "status": t.status,
        "status_label": STATUS_LABELS.get(t.status, t.status),
        "created_at": t.created_at.isoformat() if t.created_at else "",
        "url": f"/support/tickets/{t.id}",
    } for t in rows]
    return {"items": items, "total": len(items)}


MY_TICKETS_SPEC = ToolSpec(
    name="my_tickets",
    description=_MINE_DESC,
    parameters=_MINE_PARAMS,
    handler=_run_mine,
)
