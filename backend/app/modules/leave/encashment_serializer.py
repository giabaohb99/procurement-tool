"""DỰNG DỮ LIỆU TRẢ VỀ của phiếu thanh toán nghỉ phép (duoc-CR-719). Không bao giờ có số tiền trừ khi người xem được phép.

Số tiền của YCTT = lương ngày × số ngày nên chỉ lộ cho (a) chính nhân sự được thanh toán, (b) người đọc được YCTT đó
theo phạm vi + chốt D1a (`get_scoped(PaymentRequest, "payment_request")`). Người duyệt Nhân sự chỉ thấy trạng thái chi.
"""
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.scoping import get_scoped
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.employee.sensitive import is_self
from app.modules.payment_request import leave_encashment_payout as payout
from app.modules.payment_request.model import PaymentRequest

from .catalog_model import LeaveType
from .constants import (LEAVE_ENCASHMENT_REASON_LABELS, LEAVE_ENCASHMENT_STATUS_LABELS, LeaveEncashmentStatus as S,
                        label)
from .encashment_model import LeaveEncashment


def _lookups(db: Session, objs) -> tuple[dict, dict, dict]:
    emp_ids = {o.employee_id for o in objs if o.employee_id}
    type_ids = {o.leave_type_id for o in objs if o.leave_type_id}
    dept_ids = {o.department_id for o in objs if o.department_id}
    emps = {e.id: e for e in db.query(Employee).filter(Employee.id.in_(emp_ids)).all()} if emp_ids else {}
    types = {t.id: t.name for t in db.query(LeaveType).filter(LeaveType.id.in_(type_ids)).all()} if type_ids else {}
    depts = {d.id: d.name for d in db.query(Department).filter(Department.id.in_(dept_ids)).all()} if dept_ids else {}
    return emps, types, depts


def _payment_statuses(db: Session, objs) -> dict[int, tuple[str, str]]:
    """Trạng thái YCTT của các phiếu (một truy vấn, KHÔNG có số tiền): id -> (mã trạng thái, nhãn)."""
    from app.modules.payment_request import service as pay_service

    ids = {o.payment_request_id for o in objs if o.payment_request_id}
    if not ids:
        return {}
    rows = db.query(PaymentRequest.id, PaymentRequest.status).filter(
        PaymentRequest.id.in_(ids), PaymentRequest.is_deleted.is_(False)).all()
    return {i: (s, str(pay_service.STATUS_LABELS.get(s, s))) for i, s in rows}


def dump(obj: LeaveEncashment, emps: dict, types: dict, depts: dict, pay: dict | None = None) -> dict:
    emp = emps.get(obj.employee_id)
    pay_code, pay_label = (pay or {}).get(obj.payment_request_id, ("", ""))
    return {
        "id": obj.id, "code": obj.code, "company_id": obj.company_id, "department_id": obj.department_id,
        "department_name": depts.get(obj.department_id, ""),
        "employee_id": obj.employee_id, "employee_name": emp.full_name if emp else "",
        "employee_code": emp.code if emp else "",
        "leave_type_id": obj.leave_type_id, "leave_type_name": types.get(obj.leave_type_id, ""),
        "balance_year": obj.balance_year,
        "reason_kind": obj.reason_kind, "reason_kind_label": label(LEAVE_ENCASHMENT_REASON_LABELS, obj.reason_kind),
        "encashment_date": obj.encashment_date, "days": obj.days,
        "balance_snapshot": obj.balance_snapshot, "encashable_snapshot": obj.encashable_snapshot,
        "note": obj.note or "",
        "status": obj.status, "status_label": label(LEAVE_ENCASHMENT_STATUS_LABELS, obj.status),
        "approval_instance_id": obj.approval_instance_id or 0, "decided_at": obj.decided_at,
        "decision_note": obj.decision_note or "", "payment_request_id": obj.payment_request_id or 0,
        "payment_status": pay_code, "payment_status_label": pay_label,
        "created_by": obj.created_by, "created_at": obj.created_at, "updated_at": obj.updated_at,
    }


def dump_many(db: Session, objs) -> list[dict]:
    emps, types, depts = _lookups(db, objs)
    pay = _payment_statuses(db, objs)
    return [dump(o, emps, types, depts, pay) for o in objs]


def payment_block(db: Session, obj: LeaveEncashment, user) -> dict | None:
    """Khối `payment` của chi tiết: `{id, code, status, status_label, total}`; `total` = null khi người xem không được thấy."""
    state = payout.payout_state(db, obj.payment_request_id)
    if state is None:
        return None
    profile = get_perm_profile(db, user)
    visible = is_self(profile, obj.employee_id) or (
        get_scoped(db, PaymentRequest, "payment_request", state["id"], user, profile) is not None)
    if not visible:
        state = {**state, "total": None}
    return state


def cancel_block_message(state: dict) -> str:
    """Câu báo vì sao YCTT (đang ở `state`) chặn việc hủy phiếu thanh toán nghỉ phép."""
    if state["status"] == "paid":
        return f"YCTT {state['code']} đã chi tiền — không hủy được phiếu"
    return f"YCTT {state['code']} đang ở {state['status_label']} — kế toán từ chối YCTT trước"


def cancel_blocked_reason(db: Session, obj: LeaveEncashment) -> str:
    """Lý do KHÔNG hủy được (rỗng = hủy được) — để màn chi tiết tắt nút. Chỉ phiếu Đã duyệt mới có chốt này."""
    if obj.status != int(S.APPROVED):
        return ""
    state = payout.payout_state(db, obj.payment_request_id)
    return "" if payout.payout_allows_cancel(state) else cancel_block_message(state)
