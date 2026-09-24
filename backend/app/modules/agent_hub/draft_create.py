"""Tạo THẬT chứng từ từ bản nháp của Trợ lý AI, sau khi người dùng xác nhận trong Telegram (ai-CR-046).

Trên web, tool «soạn nháp» của Trợ lý chỉ trả bản nháp; người dùng bấm nút mở form điền sẵn rồi tự
bấm Lưu. Telegram không mở được form, nên trước đây bot chỉ bảo «lên web». Nay bot tóm tắt bản nháp,
người dùng nhắn «tạo» là bot tạo đúng như nút Lưu của web:

  - kiểm lại quyền `create` của CHÍNH tài khoản đang dùng chat (không tin kết quả tool lúc soạn);
  - tự điền phần đầu phiếu từ hồ sơ nhân sự (người lập, chức vụ, phòng, pháp nhân, ngày) — việc mà
    form web làm ở phía trình duyệt;
  - gọi đúng hàm service mà đường API của web gọi, và làm nốt phần đường API tự làm (nhật ký thao
    tác cho đơn nghỉ, báo nhóm hỗ trợ cho phiếu hỗ trợ).

Phiếu tạo ra ở trạng thái NHÁP như bấm Lưu trên web; nhắn «tạo và gửi duyệt» thì gửi duyệt luôn
(ai-CR-047, `submit` ở cuối tệp).
⚠️ Đề nghị thanh toán KHÔNG tạo từ chat: dính tiền, một bản nháp có thể tách thành nhiều phiếu theo
NCC + pháp nhân, và phần kiểm phạm vi công nợ nằm ở đường API. Bot gửi link mở form web điền sẵn.
"""
from __future__ import annotations

from datetime import date, time

from sqlalchemy.orm import Session

from .timeutil import now_local

KIND_BY_TOOL = {
    "draft_leave_request": "leave",
    "ticket_create": "ticket",
    "draft_survey_request": "survey",
    "draft_purchase_request": "purchase",
    "draft_payment_request": "payment",
}
LABELS = {
    "leave": "đơn nghỉ phép",
    "ticket": "phiếu hỗ trợ",
    "survey": "yêu cầu báo giá (YCBG)",
    "purchase": "yêu cầu mua hàng (YCMH)",
    "payment": "đề nghị thanh toán",
}
ENTITIES = {
    "leave": "leave_request",
    "ticket": "ticket",
    "survey": "survey_request",
    "purchase": "purchase_request",
    "payment": "payment_request",
}
DETAIL_PATHS = {
    "leave": "/hr/leave-requests/{id}",
    "ticket": "/support/tickets/{id}",
    "survey": "/procurement/survey-requests/{id}",
    "purchase": "/procurement/purchase-requests/{id}",
}
SESSION_LABELS = {1: "cả ngày", 2: "buổi sáng", 3: "buổi chiều", 4: "theo giờ"}


class DraftError(ValueError):
    """Câu lỗi đọc được cho người dùng (thiếu quyền, thiếu dữ liệu, service từ chối)."""


def kind_of(tool_name: str) -> str:
    return KIND_BY_TOOL.get(tool_name or "", "")


def payment_link(draft: dict) -> str:
    """Đường dẫn form tạo đề nghị thanh toán điền sẵn — cùng khuôn nút «Tạo» của web (CR-025/CR-264)."""
    ids = [int(i) for i in (draft.get("payable_ids") or []) if str(i).isdigit() and int(i) > 0]
    offsets = [f"{int(k)}:{v}" for k, v in (draft.get("offsets") or {}).items()
               if str(k).isdigit() and isinstance(v, (int, float)) and v > 0]
    return (f"/finance/payment-requests/new?payables={','.join(map(str, ids))}"
            + (f"&offsets={','.join(offsets)}" if offsets else ""))


def summarize(kind: str, draft: dict) -> list[str]:
    """Vài dòng tóm tắt bản nháp để người dùng đọc trước khi nhắn «tạo»."""
    if kind == "leave":
        lines = draft.get("lines") or []
        types = ", ".join(f"{ln.get('leave_type') or 'loại #' + str(ln.get('leave_type_id'))}"
                          + (f" {ln.get('days')} ngày" if ln.get("days") else "") for ln in lines)
        span = draft.get("from_date", "")
        if draft.get("to_date") and draft.get("to_date") != span:
            span += f" → {draft.get('to_date')}"
        return [f"Ngày nghỉ: {span} ({SESSION_LABELS.get(draft.get('from_session'), '')}"
                + (f" → {SESSION_LABELS.get(draft.get('to_session'), '')}"
                   if draft.get("to_session") not in (None, draft.get("from_session")) else "") + ")",
                f"Loại: {types or 'chưa rõ'}", f"Lý do: {draft.get('reason') or '(trống)'}"]
    if kind == "ticket":
        return [f"Chủ đề: {draft.get('subject', '')}", f"Bộ phận: {draft.get('department') or '(trống)'}",
                f"Nội dung: {(draft.get('body') or '')[:300]}"]
    if kind in ("survey", "purchase"):
        items = draft.get("lines") or []
        out = [f"Mục đích: {draft.get('purpose') or '(trống)'}", f"{len(items)} dòng:"]
        for ln in items[:8]:
            name = ln.get("product_name") or ln.get("requirement_detail") or "?"
            qty = ln.get("qty", ln.get("request_qty", 0))
            unit = ln.get("unit", ln.get("uom", ""))
            out.append(f"- {name} × {qty:g} {unit}".rstrip() if isinstance(qty, (int, float)) else f"- {name}")
        if len(items) > 8:
            out.append(f"… và {len(items) - 8} dòng nữa")
        return out
    return []


def _check_permission(db: Session, user, kind: str) -> None:
    from app.core.auth import user_has_permission

    if not user_has_permission(db, user, ENTITIES[kind], "create"):
        raise DraftError(f"Tài khoản này không có quyền tạo {LABELS[kind]}.")


def _header(db: Session, user) -> dict:
    """Phần đầu phiếu mà form web tự điền từ người đang đăng nhập (createEmpty*Request)."""
    from app.modules.employee.model import Employee

    emp = db.get(Employee, user.employee_id) if getattr(user, "employee_id", 0) else None
    if emp is None:
        raise DraftError("Tài khoản này chưa gắn hồ sơ nhân sự nên không lập phiếu thay được.")
    return {"company_id": emp.company_id or 0, "requester": emp.full_name, "requester_id": emp.id,
            "requester_position": emp.position or "", "department_id": emp.department_id or 0,
            "department": emp.department_name or "", "request_date": now_local().date().isoformat()}


def _as_time(value) -> time | None:
    if not value:
        return None
    try:
        return time.fromisoformat(str(value))
    except ValueError:
        return None


def create(db: Session, user, kind: str, draft: dict) -> tuple[str, int]:
    """Tạo thật; trả (mã phiếu, id). Ném DraftError với câu đọc được khi không tạo được."""
    from fastapi import HTTPException

    if kind not in DETAIL_PATHS:
        raise DraftError(f"Loại {LABELS.get(kind, kind)} không tạo được từ chat.")
    _check_permission(db, user, kind)
    try:
        if kind == "leave":
            return _create_leave(db, user, draft)
        if kind == "ticket":
            return _create_ticket(db, user, draft)
        if kind == "survey":
            return _create_survey(db, user, draft)
        return _create_purchase(db, user, draft)
    except HTTPException as e:
        db.rollback()
        raise DraftError(str(e.detail)) from None
    except (ValueError, TypeError) as e:
        db.rollback()
        raise DraftError(f"Bản nháp chưa đủ dữ liệu: {str(e)[:300]}") from None


def _create_leave(db: Session, user, draft: dict) -> tuple[str, int]:
    from app.core.audit import record as audit_record
    from app.modules.leave import request_service
    from app.modules.leave.schema import LeaveLineItem, LeaveRequestCreate

    data = LeaveRequestCreate(
        lines=[LeaveLineItem(leave_type_id=int(ln.get("leave_type_id") or 0), days=float(ln.get("days") or 0))
               for ln in draft.get("lines") or []],
        from_date=date.fromisoformat(str(draft.get("from_date"))),
        to_date=date.fromisoformat(str(draft.get("to_date") or draft.get("from_date"))),
        from_session=int(draft.get("from_session") or 1), to_session=int(draft.get("to_session") or 1),
        from_time=_as_time(draft.get("from_time")), to_time=_as_time(draft.get("to_time")),
        reason=str(draft.get("reason") or "")[:1000], contact_phone=str(draft.get("contact_phone") or "")[:30],
    )
    obj = request_service.create(db, data, user)
    audit_record(db, user.id, "leave_request", obj.id, "create", f"Lập đơn nghỉ phép {obj.code} (qua Telegram)")
    return obj.code, obj.id


def _create_ticket(db: Session, user, draft: dict) -> tuple[str, int]:
    from app.core.auth import get_perm_profile
    from app.modules.ticket import service as ticket_service
    from app.modules.ticket.controller import _notify, _support_users
    from app.modules.ticket.schema import TicketCreate

    subject = str(draft.get("subject") or "").strip()
    if not subject:
        raise DraftError("Phiếu hỗ trợ chưa có chủ đề.")
    data = TicketCreate(subject=subject, department=str(draft.get("department") or ""),
                        priority=str(draft.get("priority") or "normal"), body=str(draft.get("body") or ""),
                        company_id=get_perm_profile(db, user).get("company_id") or 0)
    t = ticket_service.create_ticket(db, data, user.id, requester_emp_id=getattr(user, "employee_id", 0) or 0)
    #  Đường API của web báo nhóm hỗ trợ ngay sau khi tạo — thiếu bước này là không ai biết có phiếu.
    _notify(db, _support_users(db), f"{t.code} — Phiếu hỗ trợ mới", f"Có phiếu hỗ trợ mới: {t.subject}",
            f"/tickets/{t.id}", user.id, None, doc_code=t.code)
    return t.code, t.id


def _create_survey(db: Session, user, draft: dict) -> tuple[str, int]:
    from app.core.auth import get_perm_profile
    from app.modules.survey_request import service as sr_service
    from app.modules.survey_request.schema import SurveyRequestCreate, SurveyRequestLineIn

    keys = set(SurveyRequestLineIn.model_fields)
    header = _header(db, user)
    if draft.get("company_id"):
        header["company_id"] = int(draft["company_id"])
    lines = [SurveyRequestLineIn(**{k: v for k, v in ln.items() if k in keys}) for ln in draft.get("lines") or []]
    if not lines:
        raise DraftError("Yêu cầu báo giá chưa có dòng nào.")
    data = SurveyRequestCreate(**header, purpose=str(draft.get("purpose") or ""),
                               note=str(draft.get("note") or ""), lines=lines)
    s = sr_service.create_sr(db, data, user.id, user, get_perm_profile(db, user))
    return s.code, s.id


def _create_purchase(db: Session, user, draft: dict) -> tuple[str, int]:
    from app.core.auth import user_has_permission
    from app.modules.purchase_request import service as pr_service
    from app.modules.purchase_request.schema import PRCreate, PRItemIn

    keys = set(PRItemIn.model_fields)
    items = []
    for ln in draft.get("lines") or []:
        if not str(ln.get("product_name") or "").strip():
            raise DraftError("Có dòng chưa có tên hàng.")
        if not float(ln.get("qty") or 0) > 0:
            raise DraftError(f"Dòng «{ln.get('product_name')}» chưa có số lượng.")
        items.append(PRItemIn(**{k: v for k, v in ln.items() if k in keys}))
    if not items:
        raise DraftError("Yêu cầu mua hàng chưa có dòng nào.")
    header = _header(db, user)
    if draft.get("company_id"):
        header["company_id"] = int(draft["company_id"])
    data = PRCreate(**header, purpose=str(draft.get("purpose") or ""), note=str(draft.get("note") or ""),
                    need_date=str(draft.get("need_date") or ""), items=items)
    pr = pr_service.create_pr(db, data, user.id, user_has_permission(db, user, "supplier", "write"))
    return pr.code, pr.id


# ---------------------------------------------------------------------------
# Gửi duyệt ngay sau khi tạo — «tạo và gửi duyệt» (ai-CR-047)
# ---------------------------------------------------------------------------
#  Phiếu hỗ trợ không có bước duyệt (tạo là tới nhóm hỗ trợ) nên không nằm đây.
SUBMITTABLE = ("leave", "survey", "purchase")
#  Quyền mà đường API gửi duyệt của web đòi (`require(...)` ở controller).
_SUBMIT_ACTION = {"leave": "write", "survey": "read", "purchase": "read"}


def missing_for_submit(kind: str, draft: dict) -> str:
    """Luật «bắt buộc khi GỬI DUYỆT» mà web chỉ kiểm ở giao diện (`procurement/utils/required-fields.ts`):
    backend `submit_pr` / `submit_` không chặn gì, nên bot phải tự kiểm — không thì chat là cửa lách luật.
    Trả câu báo lỗi đầu tiên, rỗng nếu gửi được. Đơn nghỉ phép thì backend tự kiểm (quỹ phép, trùng ngày)."""
    if kind == "purchase":
        lines = [ln for ln in draft.get("lines") or [] if str(ln.get("product_name") or "").strip()]
        codes = [str(ln.get("product_code") or "").strip() for ln in lines if str(ln.get("product_code") or "").strip()]
        dup = sorted({c for c in codes if codes.count(c) > 1})
        if dup:
            return f"Mã hàng bị trùng: {', '.join(dup)}."
        for ln in lines:
            missing = [label for label, ok in (("Số lượng mua", float(ln.get("qty") or 0) > 0),
                                               ("Kho nhận", bool(str(ln.get("warehouse") or "").strip())),
                                               ("Ngày cần hàng", bool(str(ln.get("required_date") or "").strip())))
                       if not ok]
            if missing:
                return f"Sản phẩm «{ln.get('product_name')}» còn thiếu: {', '.join(missing)}."
    if kind == "survey":
        if not str(draft.get("purpose") or "").strip():
            return "Còn thiếu Mục đích khảo sát."
        for i, ln in enumerate(draft.get("lines") or [], 1):
            if not str(ln.get("item_group") or "").strip():
                return f"Dòng {i} còn thiếu: Phân loại."
    return ""


def submit(db: Session, user, kind: str, obj_id: int) -> None:
    """Gửi duyệt bằng ĐÚNG hàm của đường API web (trình bộ máy duyệt, giữ chỗ quỹ phép, chốt cờ đơn gấp,
    báo trưởng bộ phận…), chạy luôn các tác vụ nền nó xếp (email, đẩy thông báo). Ném DraftError."""
    from fastapi import BackgroundTasks, HTTPException

    from app.core.auth import user_has_permission

    if kind not in SUBMITTABLE:
        raise DraftError(f"{LABELS.get(kind, kind).capitalize()} không có bước gửi duyệt.")
    if not user_has_permission(db, user, ENTITIES[kind], _SUBMIT_ACTION[kind]):
        raise DraftError(f"Tài khoản này không có quyền gửi duyệt {LABELS[kind]}.")
    tasks = BackgroundTasks()
    try:
        if kind == "leave":
            from app.modules.leave import request_controller
            request_controller.submit_request(obj_id, db=db, user=user)
        elif kind == "survey":
            from app.modules.survey_request import controller as sr_controller
            sr_controller.submit_(obj_id, tasks, db=db, user=user)
        else:
            from app.modules.purchase_request import controller as pr_controller
            pr_controller.submit_pr(obj_id, tasks, db=db, user=user)
    except HTTPException as e:
        db.rollback()
        raise DraftError(str(e.detail)) from None
    for task in tasks.tasks:
        try:
            task.func(*task.args, **task.kwargs)
        except Exception:  # noqa: BLE001 — email / thông báo đẩy hỏng không làm hỏng phiếu đã gửi duyệt
            import logging
            logging.getLogger("app.agent_hub").exception("agent_hub: tác vụ nền sau gửi duyệt hỏng")
