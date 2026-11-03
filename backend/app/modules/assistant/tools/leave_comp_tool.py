"""Soạn nháp PHIẾU XIN NGHỈ BÙ cho Trợ lý web / bot / cổng MCP (duoc-CR-715 C, tool `draft_leave_comp_request`).

Khuôn draft_* + confirm_draft: tool chỉ SOẠN NHÁP và chạy trước đúng các chốt mà `comp_request_service.create` sẽ chạy
(loại nhận ngày bù đã khai, số ngày 0,5 / 1, ngày đi làm không ở tương lai, là ngày lễ / ngày nghỉ theo lịch, chưa có
phiếu khác) — KHÔNG ghi gì. Tạo thật ở `agent_hub/draft_create` (kind `leave_comp`) bằng ĐÚNG service của màn web, lúc
đó kiểm lại quyền create, quyền lập hộ, mọi chốt ngày.

Lập HỘ người khác (`employee` = mã nhân sự): chỉ người có `leave_comp_request.create` phạm vi rộng hơn "của mình" và
người đó nằm trong phạm vi khóa `employee` — cùng luật `request_service.ensure_can_create_for` của màn web. Mã không có
và mã ngoài phạm vi trả CÙNG một câu.

Phiếu nghỉ bù LUÔN chặn tự duyệt (`self_approval_policy.ALWAYS_STRICT_ENTITIES`) — tool không bao giờ đề xuất duyệt.
"""
from __future__ import annotations

from datetime import date

from . import confirm_fields
from .base import ToolContext, ToolSpec, denied

ENTITY = "leave_comp_request"
DETAIL_URL = "/hr/leave-comp-requests/{id}"
REASON_MAX = 1000
CODE_MAX = 30


def _iso(value) -> date | None:
    try:
        return date.fromisoformat(str(value or "").strip()[:10])
    except ValueError:
        return None


def _days(value) -> float | None:
    """0,5 / 1 (model hay gõ "nửa ngày", "0,5"); bỏ trống = 1 ngày như form."""
    raw = str(value if value is not None else "").strip().lower().replace(",", ".")
    if raw in ("", "1", "1.0", "ca ngay", "cả ngày"):
        return 1.0
    if raw in ("0.5", ".5", "nua ngay", "nửa ngày"):
        return 0.5
    return None


def _can_create_for_others(ctx: ToolContext) -> bool:
    """Có vai trò `leave_comp_request.create` phạm vi rộng hơn «của mình» (đúng điều kiện 1 của `ensure_can_create_for`)."""
    return any(g.get("perms", {}).get(ENTITY, {}).get("create")
               and g.get("perms", {}).get(ENTITY, {}).get("scope") != "own"
               for g in ctx.profile.get("grants", []))


def _resolve_taker(ctx: ToolContext, raw: str):
    """(nhân sự, lỗi). Bỏ trống = chính người hỏi. Mã lạ và mã ngoài phạm vi: cùng một câu (không lộ hồ sơ có tồn tại)."""
    from fastapi import HTTPException
    from sqlalchemy import func

    from app.core.scoping import apply_scope
    from app.modules.employee.model import Employee
    from app.modules.leave import request_service

    code = " ".join(str(raw or "").split())[:CODE_MAX]
    own_id = int(getattr(ctx.user, "employee_id", 0) or 0)
    if not code:
        if not own_id:
            return None, {"error": "Tài khoản của người hỏi chưa gắn hồ sơ nhân sự nên chưa xin nghỉ bù được — báo họ "
                                   "liên hệ phòng Nhân sự."}
        return ctx.db.get(Employee, own_id), None
    if not _can_create_for_others(ctx):
        return None, {"denied": True, "reason": "Bạn chỉ xin nghỉ bù được cho chính mình. Muốn lập hộ người khác thì "
                                                "cần vai trò có phạm vi rộng hơn \"của mình\"."}
    hidden = {"error": f"Không thấy nhân sự mã **{code}** trong phạm vi bạn được lập hộ — hỏi lại người dùng đúng mã "
                       "nhân sự."}
    emp = (apply_scope(ctx.db.query(Employee), Employee, "employee", ctx.user, ctx.profile)
           .filter(func.upper(Employee.code) == code.upper()).first())
    if emp is None:
        return None, hidden
    try:
        request_service.ensure_can_create_for(ctx.db, ctx.user, emp, ENTITY)
    except HTTPException:
        return None, hidden
    return emp, None


def _run(ctx: ToolContext, args: dict) -> dict:
    from fastapi import HTTPException

    from app.modules.leave import comp_request_service as service

    if not ctx.can(ENTITY, "create"):
        return denied("lập phiếu xin nghỉ bù (leave_comp_request.create)")
    user_text, asked = confirm_fields.take_context(args)
    work_date = _iso(args.get("work_date"))
    if args.get("work_date") and work_date is None:
        return {"error": "work_date phải dạng YYYY-MM-DD (ngày đã đi làm) — hỏi lại người dùng."}
    reason = " ".join(str(args.get("reason") or "").split())[:REASON_MAX]
    if reason and not confirm_fields.stated(user_text, reason) and "reason" not in asked:
        reason = ""             # đại ca 09/10: lý do người dùng chưa nói thì hỏi, không tự nghĩ ra
    #  Lý do là ô BẮT BUỘC khi gửi duyệt (`comp_request_service.prepare_submit`) nên luôn hỏi — kể cả lượt gọi thẳng
    #  không có lời người dùng (`take_context` coi mọi ô mặc định là đã hỏi); chỉ bỏ khi chính người dùng bảo bỏ qua.
    declined = {str(x).strip() for x in (args.get(confirm_fields.ASKED_ARG) or []) if str(x).strip()}
    missing = [{"field": f, "question": q} for f, q, ok, skip in (
        ("work_date", "Anh/chị đã đi làm vào ngày nào (ngày lễ hoặc ngày nghỉ theo lịch)?", work_date, asked),
        ("reason", "Hôm đó đi làm việc gì (lý do xin nghỉ bù)?", reason, declined)) if not ok and f not in skip]
    if missing:
        return confirm_fields.need(missing)
    if work_date is None:
        return {"error": "Thiếu ngày đi làm (work_date, YYYY-MM-DD) — không soạn được phiếu nghỉ bù."}
    days = _days(args.get("days"))
    if days is None:
        return {"error": "Số ngày nghỉ bù chỉ nhận 0,5 hoặc 1 ngày — hỏi lại người dùng."}

    emp, problem = _resolve_taker(ctx, args.get("employee"))
    if problem:
        return problem
    #  Đúng các chốt của `comp_request_service.create` — chỉ ĐỌC, báo sớm để khỏi xác nhận xong mới ăn câu chặn.
    try:
        comp_type = service.get_comp_type(ctx.db)
        service.check_days(days)
        service.check_work_date(ctx.db, emp, work_date)
    except HTTPException as exc:
        return {"error": f"{exc.detail} — báo người dùng nguyên câu này, chưa soạn phiếu.", "blocked": True}

    own = emp.id == int(getattr(ctx.user, "employee_id", 0) or 0)
    draft = {
        "kind": ENTITY,
        #  0 = chính người lập (như form); khác 0 chỉ khi lập hộ — service kiểm lại quyền lập hộ lúc tạo.
        "employee_id": 0 if own else emp.id,
        "employee_name": emp.full_name or "",
        "work_date": work_date.isoformat(),
        "days": days,
        "reason": reason or "",
    }
    return {
        "status": "ready",
        "total": 1,
        "kind": "leave_comp",
        "draft": draft,
        "comp_leave_type": comp_type.name,
        "note": (f"Duyệt xong, {days:g} ngày được cộng vào quỹ **{comp_type.name}** của "
                 f"{'anh/chị' if own else emp.full_name} (năm đi làm, hoặc năm nay nếu ngày đi làm thuộc năm ngoái) — "
                 "sau đó xin nghỉ bằng đơn nghỉ phép loại đó như mọi loại khác. Người đi làm KHÔNG tự duyệt được phiếu "
                 "nghỉ bù của chính mình."),
        "warnings": [] if reason else ["Chưa có lý do — lưu nháp được nhưng hệ chặn GỬI DUYỆT tới khi điền lý do."],
        "reminder": ("Phiếu CHƯA được tạo và CHƯA gửi duyệt. Tóm tắt (người đi làm, ngày đi làm, số ngày, lý do) rồi hỏi "
                     "người dùng; họ đồng ý thì xác nhận nháp với kind=leave_comp (submit=true để gửi duyệt luôn). Đừng "
                     "tự báo là đã tạo."),
    }


def my_comp_requests(db, employee_id: int, limit: int) -> list[dict]:
    """Phiếu nghỉ bù của CHÍNH một nhân sự (mới nhất trước) — cho `my_leave_summary`. Lọc cứng theo `employee_id`."""
    from app.modules.leave.comp_request_model import LeaveCompRequest
    from app.modules.leave.constants import LEAVE_COMP_STATUS_LABELS, label

    rows = (db.query(LeaveCompRequest)
            .filter(LeaveCompRequest.employee_id == employee_id, LeaveCompRequest.is_deleted.is_(False))
            .order_by(LeaveCompRequest.id.desc()).limit(limit).all())
    return [{"code": r.code, "work_date": r.work_date.isoformat() if r.work_date else "", "days": r.days,
             "status": r.status, "status_label": label(LEAVE_COMP_STATUS_LABELS, r.status),
             "reason": r.reason or "", "decision_note": r.decision_note or "",
             "url": DETAIL_URL.format(id=r.id)} for r in rows]


DRAFT_LEAVE_COMP_REQUEST_SPEC = ToolSpec(
    name="draft_leave_comp_request",
    description=("SOẠN NHÁP phiếu XIN NGHỈ BÙ: đã ĐI LÀM vào ngày lễ hoặc ngày nghỉ theo lịch (Chủ nhật…) thì xin nghỉ bù "
                 "('tôi đi trực kho Chủ nhật 25/10, xin nghỉ bù', 'làm lễ 2/9 xin bù nửa ngày'). Cần ngày đi làm "
                 "(work_date, YYYY-MM-DD, không ở tương lai, từ 01/01 năm ngoái) và lý do (đi làm việc gì); số ngày 0.5 "
                 "hoặc 1 (mặc định 1). Duyệt xong số ngày được CỘNG vào quỹ loại nghỉ bù — đây KHÔNG phải đơn nghỉ: muốn "
                 "nghỉ bằng ngày bù đã có thì dùng draft_leave_request với loại nghỉ bù. Lập hộ người khác thì truyền "
                 "employee = mã nhân sự (chỉ người có quyền lập hộ). Tool chưa ghi gì; người dùng đồng ý thì xác nhận nháp "
                 "(kind=leave_comp). Có `error` thì đọc nguyên câu cho người dùng."),
    parameters={"type": "object", "properties": {
        "work_date": {"type": "string", "description": "Ngày ĐÃ đi làm, YYYY-MM-DD. Người dùng nói tương đối (Chủ nhật "
                                                       "vừa rồi) thì tự quy ra theo hôm nay."},
        "days": {"type": "number", "description": "Số ngày nghỉ bù xin nhận: 1 (cả ngày, mặc định) hoặc "
                                                                   "0.5 (nửa ngày)."},
        "reason": {"type": "string", "description": "Đi làm việc gì — ĐÚNG lời người dùng. Chưa nói thì BỎ TRỐNG (tool "
                                                    "sẽ nhắc hỏi), không tự nghĩ ra."},
        "employee": {"type": "string", "description": "Mã nhân sự của người đi làm khi LẬP HỘ (Nhân sự / trưởng phòng). "
                                                      "Bỏ trống = chính người hỏi."},
        "asked_fields": confirm_fields.ASKED_PARAM}},
    handler=_run,
)
