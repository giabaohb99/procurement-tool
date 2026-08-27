"""Tool HỘP VIỆC PHÊ DUYỆT cho Trợ lý AI — chỉ đọc, không ghi.

- `my_approval_tasks`: "tôi có phải duyệt gì không", "việc gì đang chờ tôi". Tái dùng
  ĐÚNG hàm của màn «Chờ tôi duyệt» (`task_service.viec_cua_toi`) — gồm cả việc được
  ủy quyền bấm thay — để chat và huy hiệu hộp việc không bao giờ đếm hai con số khác nhau.
- `my_requests_status`: "phiếu tôi trình đang tới đâu", "ai đang giữ phiếu của tôi",
  "văn bản của tôi bị trả lại vì sao". Đọc thẳng bảng phiên duyệt theo
  `started_by_employee_id` — chưa có màn nào của giao diện trả lời câu này, nên đây là
  chỗ duy nhất; phiếu đang chạy trả kèm bước hiện tại + TÊN người đang giữ.

Cả hai đều là DỮ LIỆU CỦA CHÍNH NGƯỜI HỎI nên không gác quyền gì ngoài đăng nhập —
y luật của endpoint `/api/approvals/my-tasks`: tài khoản chưa gắn hồ sơ nhân sự thì
trả rỗng kèm lời giải thích, không phải lỗi.
"""
from app.modules.approval import task_service
from app.modules.approval.instance_model import (INSTANCE_OPEN_STATUSES,
                                                 INSTANCE_STATUS_LABELS,
                                                 TASK_PENDING,
                                                 ApprovalInstance, ApprovalTask)
from app.modules.approval.serializer import _name_of
from app.modules.approval.task_notification import ENTITY_LABELS

from .base import ToolContext, ToolSpec

MAX_ROWS = 30

#  Đường dẫn CHI TIẾT bên frontend-v2 — để câu trả lời gắn được link Markdown mở đúng
#  phiếu. ⚠️ KHÔNG tái dùng `task_notification.ENTITY_LINKS`: bảng đó ghi đường KIỂU CŨ
#  (`/purchase-requests/{id}`) rồi nhờ `toAppPath()` của tầng thông báo dịch sang tiền tố
#  phân hệ — chat render Markdown thẳng, không đi qua tầng dịch đó, nên phải ghi đường
#  ĐẦY ĐỦ đúng `app-routes.ts` của v2.
_DETAIL_URLS = {
    "document": "/document/documents/{id}",
    "purchase_request": "/procurement/purchase-requests/{id}",
    "purchase_order": "/procurement/purchase-orders/{id}",
    "survey": "/procurement/surveys/{id}",
    "survey_request": "/procurement/survey-requests/{id}",
    "payment_request": "/finance/payment-requests/{id}",
}

#  Màn «Chờ tôi duyệt» — hiện chỉ Văn bản chạy bộ máy duyệt nên đích này phủ đủ (cùng
#  lý do với nút hộp việc trên thanh trên, xem `my-tasks-button.tsx`).
INBOX_URL = "/document/pending-approval"


def _detail_url(entity: str, entity_id: int) -> str:
    template = _DETAIL_URLS.get(entity, "")
    return template.format(id=entity_id) if template else ""


def _iso(value) -> str:
    return value.isoformat() if value else ""


def _limit(args: dict, default: int) -> int:
    limit = args.get("limit")
    return max(1, min(int(limit), MAX_ROWS)) if isinstance(limit, (int, float)) else default


_NO_EMPLOYEE_PROFILE = ("Tài khoản chưa gắn hồ sơ nhân sự nên không tham gia luồng phê duyệt "
                  "nào — liên hệ quản trị nếu điều này sai.")


# ── my_approval_tasks ───────────────────────────────────────────────────────────────────

def _run_my_approval_tasks(ctx: ToolContext, args: dict) -> dict:
    db, user = ctx.db, ctx.user
    if not getattr(user, "employee_id", None):
        return {"total": 0, "items": [], "note": _NO_EMPLOYEE_PROFILE}

    entity = str(args.get("entity") or "").strip()
    limit = _limit(args, default=20)

    rows = task_service.my_tasks(db, user.employee_id, entity)
    out = {
        "total": len(rows),
        "items": [{
            "entity": r["entity"],
            "entity_label": ENTITY_LABELS.get(r["entity"], r["entity"]),
            "code": r["entity_code"],
            "title": r["entity_title"],
            "step": r["node_name"],
            "submitted_by": r["started_by_name"],
            "due_at": _iso(r["due_at"]),
            "is_overdue": r["is_overdue"],
            #  Bấm THAY ai theo ủy quyền — rỗng nếu là việc của chính người hỏi.
            "on_behalf_of": r["on_behalf_of_name"],
            "url": _detail_url(r["entity"], r["entity_id"]),
        } for r in rows[:limit]],
        "inbox_url": INBOX_URL,
    }
    if len(rows) > limit:
        out["note"] = (f"Chỉ liệt kê {limit}/{len(rows)} việc tới hạn sớm nhất — "
                       "xem đủ ở màn «Chờ tôi duyệt» (inbox_url).")
    return out


MY_APPROVAL_TASKS_SPEC = ToolSpec(
    name="my_approval_tasks",
    description=(
        "Việc ĐANG CHỜ CHÍNH NGƯỜI HỎI phê duyệt (gồm cả việc được ủy quyền duyệt thay) — "
        "dùng cho câu 'tôi có phải duyệt gì không', 'việc gì đang chờ tôi', 'tôi còn nợ ai "
        "chữ ký nào'. Kết quả xếp việc gần hạn lên trước, kèm cờ quá hạn và đường dẫn `url` "
        "mở thẳng từng phiếu. Khác my_requests_status: tool này là phiếu NGƯỜI KHÁC trình "
        "đang chờ người hỏi ký; phiếu do chính người hỏi trình thì dùng my_requests_status."
    ),
    parameters={
        "type": "object",
        "properties": {
            "entity": {
                "type": "string",
                "description": ("Lọc theo loại chứng từ (tùy chọn), vd 'document' = văn bản. "
                                "Bỏ trống để lấy mọi loại."),
            },
            "limit": {"type": "integer",
                      "description": f"Số dòng tối đa, mặc định 20, trần {MAX_ROWS}."},
        },
    },
    handler=_run_my_approval_tasks,
)


# ── my_requests_status ──────────────────────────────────────────────────────────────────

def _run_my_requests_status(ctx: ToolContext, args: dict) -> dict:
    db, user = ctx.db, ctx.user
    if not getattr(user, "employee_id", None):
        return {"total": 0, "items": [], "note": _NO_EMPLOYEE_PROFILE}

    entity = str(args.get("entity") or "").strip()
    only_open = bool(args.get("only_open"))
    limit = _limit(args, default=10)

    query = (db.query(ApprovalInstance)
             .filter(ApprovalInstance.started_by_employee_id == user.employee_id))
    if entity:
        query = query.filter(ApprovalInstance.entity == entity)
    if only_open:
        query = query.filter(ApprovalInstance.status.in_(INSTANCE_OPEN_STATUSES))
    total = query.count()
    rows = query.order_by(ApprovalInstance.id.desc()).limit(limit).all()

    #  Phiếu đang chạy thì nói luôn ĐANG CHỜ AI — gom một truy vấn cho cả trang thay vì
    #  mỗi phiếu một câu.
    open_instances = [r.id for r in rows if r.status in INSTANCE_OPEN_STATUSES]
    pending_by_instance: dict[int, list[ApprovalTask]] = {}
    if open_instances:
        for task in (db.query(ApprovalTask)
                     .filter(ApprovalTask.instance_id.in_(open_instances),
                             ApprovalTask.status == TASK_PENDING)
                     .order_by(ApprovalTask.id.asc()).all()):
            pending_by_instance.setdefault(task.instance_id, []).append(task)

    items = []
    for r in rows:
        item = {
            "entity": r.entity,
            "entity_label": ENTITY_LABELS.get(r.entity, r.entity),
            "code": r.entity_code,
            "title": r.entity_title,
            "status": INSTANCE_STATUS_LABELS.get(r.status, str(r.status)),
            "submitted_at": _iso(r.started_at),
            "url": _detail_url(r.entity, r.entity_id),
        }
        waiting = pending_by_instance.get(r.id) or []
        if waiting:
            item["waiting_step"] = waiting[0].node_name
            item["waiting_on"] = [_name_of(db, t.assignee_employee_id) for t in waiting]
        if r.status not in INSTANCE_OPEN_STATUSES:
            item["finished_at"] = _iso(r.finished_at)
            if r.finish_reason:
                #  Lý do trả lại / từ chối — chính là câu trả lời cho "vì sao phiếu tôi
                #  bị trả", đừng bắt người hỏi mở dấu vết ra tìm.
                item["finish_reason"] = r.finish_reason
        items.append(item)

    out: dict = {"total": total, "items": items}
    if total > limit:
        out["note"] = f"Chỉ liệt kê {limit}/{total} phiếu mới trình gần nhất."
    if not total:
        out["note"] = ("Người hỏi chưa trình phiếu nào qua bộ máy phê duyệt"
                       + (f" (loại '{entity}')" if entity else "") + ".")
    return out


MY_REQUESTS_STATUS_SPEC = ToolSpec(
    name="my_requests_status",
    description=(
        "Trạng thái các phiếu / văn bản DO CHÍNH NGƯỜI HỎI TRÌNH duyệt — dùng cho câu "
        "'phiếu của tôi đang tới đâu', 'ai đang giữ văn bản tôi gửi', 'đơn của tôi được "
        "duyệt chưa', 'vì sao phiếu tôi bị trả lại'. Phiếu đang chạy trả kèm bước hiện "
        "tại (`waiting_step`) và tên người đang giữ (`waiting_on`); phiếu bị trả lại / "
        "từ chối có lý do trong `finish_reason`. Mỗi dòng kèm đường dẫn `url` mở thẳng "
        "phiếu. Khác my_approval_tasks: tool kia là việc chờ chính người hỏi KÝ."
    ),
    parameters={
        "type": "object",
        "properties": {
            "entity": {
                "type": "string",
                "description": ("Lọc theo loại chứng từ (tùy chọn), vd 'document' = văn bản. "
                                "Bỏ trống để lấy mọi loại."),
            },
            "only_open": {
                "type": "boolean",
                "description": ("true = chỉ phiếu CÒN ĐANG CHỜ duyệt; mặc định lấy cả phiếu "
                                "đã xong (đã duyệt / trả lại / từ chối / đã rút)."),
            },
            "limit": {"type": "integer",
                      "description": f"Số dòng tối đa, mặc định 10, trần {MAX_ROWS}."},
        },
    },
    handler=_run_my_requests_status,
)
