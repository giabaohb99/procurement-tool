"""API PHIẾU XIN NGHỈ BÙ — `/api/leave-comp-requests` (duoc-CR-715 C). Khuôn của `request_controller` (đơn nghỉ)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record, resolve_actor
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.base_controller import apply_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped
from app.modules.approval import steps_service, task_service
from app.modules.approval.self_approval_policy import ensure_not_self_approval
from app.modules.department.model import Department
from app.modules.employee.model import Employee

from . import comp_approval_bridge as bridge, comp_request_service as service
from .comp_request_model import LeaveCompRequest
from .comp_request_schema import LeaveCompRequestCreate, LeaveCompRequestUpdate
from .constants import LEAVE_COMP_STATUS_LABELS, LeaveCompStatus, label

router = APIRouter(prefix="/api/leave-comp-requests", tags=["leave"])
ENTITY = service.ENTITY


def _dump(obj: LeaveCompRequest, emps: dict[int, Employee], depts: dict[int, str] | None = None) -> dict:
    emp = emps.get(obj.employee_id)
    return {
        "id": obj.id, "code": obj.code, "company_id": obj.company_id, "department_id": obj.department_id,
        "department_name": (depts or {}).get(obj.department_id, ""),
        "employee_id": obj.employee_id, "employee_name": emp.full_name if emp else "",
        "employee_code": emp.code if emp else "",
        "work_date": obj.work_date, "days": obj.days, "reason": obj.reason or "",
        "status": obj.status, "status_label": label(LEAVE_COMP_STATUS_LABELS, obj.status),
        "approval_instance_id": obj.approval_instance_id or 0, "decided_at": obj.decided_at,
        "decision_note": obj.decision_note or "", "created_by": obj.created_by,
        "created_at": obj.created_at, "updated_at": obj.updated_at,
    }


def _emps(db: Session, objs) -> dict[int, Employee]:
    ids = {o.employee_id for o in objs if o.employee_id}
    return {e.id: e for e in db.query(Employee).filter(Employee.id.in_(ids)).all()} if ids else {}


def _dump_one(db: Session, obj: LeaveCompRequest) -> dict:
    dept = db.get(Department, obj.department_id) if obj.department_id else None
    return _dump(obj, _emps(db, [obj]), {obj.department_id: dept.name if dept else ""})


def _get_or_404(db: Session, rid: int, user, action: str = "read") -> LeaveCompRequest:
    obj = get_scoped(db, LeaveCompRequest, ENTITY, rid, user, get_perm_profile(db, user), action)
    #  Người ĐANG được giao ký đọc được phiếu dù phạm vi không với tới (như đơn nghỉ, CR-260) — chỉ cho `read`.
    if obj is None and action == "read" and bridge.can_read_request(db, rid, user):
        obj = db.get(LeaveCompRequest, rid)
    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy phiếu nghỉ bù")
    return obj


@router.get("")
def list_requests(request: Request, pg: dict = Depends(pagination), q: str | None = None,
                  db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Danh sách trong phạm vi người xem. Lọc: `status`, `employee_id`, `company_id`, `department_id`, `q` (mã / lý do / tên)."""
    query = db.query(LeaveCompRequest).filter(LeaveCompRequest.is_deleted.is_(False))
    query = apply_filters(query, LeaveCompRequest, request, service.FILTERABLE, {})
    if q and q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(LeaveCompRequest.code.like(like), LeaveCompRequest.reason.like(like),
                                 LeaveCompRequest.employee_id.in_(
                                     db.query(Employee.id).filter(Employee.full_name.like(like)))))
    query = apply_scope(query, LeaveCompRequest, ENTITY, user, get_perm_profile(db, user))
    query = apply_sort_from_request(query, LeaveCompRequest, request,
                                    default=(LeaveCompRequest.work_date.desc(), LeaveCompRequest.id.desc()))
    total = query.count()
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()
    emps = _emps(db, items)
    dept_ids = {i.department_id for i in items if i.department_id}
    depts = {d.id: d.name for d in db.query(Department).filter(Department.id.in_(dept_ids)).all()} if dept_ids else {}
    return success({"total": total, "items": [_dump(i, emps, depts) for i in items]})


@router.get("/to-approve")
def to_approve(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Phiếu ĐANG chờ chính tôi ký (kèm `task` = việc của tôi, `flow` = luồng duyệt). Đăng ký TRƯỚC `/{rid}`."""
    tasks = task_service.my_tasks(db, getattr(user, "employee_id", 0) or 0, ENTITY)
    ids = [t.get("entity_id") for t in tasks if t.get("entity_id")]
    rows = {o.id: o for o in db.query(LeaveCompRequest).filter(
        LeaveCompRequest.id.in_(ids), LeaveCompRequest.is_deleted.is_(False)).all()} if ids else {}
    emps = _emps(db, rows.values())
    flows = steps_service.steps_of_entities(db, ENTITY, list(rows)) if rows else {}
    items = []
    for task in tasks:
        obj = rows.get(task.get("entity_id"))
        if obj is None:
            continue
        data = _dump(obj, emps)
        data["task"], data["flow"] = task, flows.get(obj.id)
        items.append(data)
    return success({"total": len(items), "items": items})


@router.get("/{rid}")
def get_request(rid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Chi tiết. `approval_instance_id` > 0 → UI mở khối duyệt (`/api/approvals/of/leave_comp_request/{id}`)."""
    obj = _get_or_404(db, rid, user)
    data = _dump_one(db, obj)
    data["created_by_name"] = resolve_actor(db, obj.created_by)
    data["has_running_approval"] = bridge.running_instance(db, obj.id) is not None
    return success(data)


@router.post("")
def create_request(data: LeaveCompRequestCreate, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "create"))):
    obj = service.create(db, data, user)
    audit_record(db, user.id, ENTITY, obj.id, "create", f"Lập phiếu nghỉ bù {obj.code}")
    return success(_dump_one(db, obj), "Đã lưu phiếu nghỉ bù")


@router.patch("/{rid}")
def update_request(rid: int, data: LeaveCompRequestUpdate, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "write"))):
    obj = service.update(db, _get_or_404(db, rid, user, "write"), data, user)
    audit_record(db, user.id, ENTITY, obj.id, "update", f"Sửa phiếu nghỉ bù {obj.code}")
    return success(_dump_one(db, obj), "Đã cập nhật")


@router.delete("/{rid}")
def delete_request(rid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    obj = _get_or_404(db, rid, user, "delete")
    code = obj.code
    service.soft_delete(db, obj, user)
    audit_record(db, user.id, ENTITY, rid, "delete", f"Xóa phiếu nghỉ bù {code}")
    return success(None, "Đã xóa phiếu")


@router.post("/{rid}/submit")
def submit_request(rid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    """Gửi duyệt: kiểm TRƯỚC, trình bộ máy SAU. Cờ tắt / chưa có luồng → Chờ duyệt, duyệt thẳng bằng `/approve`."""
    obj = _get_or_404(db, rid, user, "write")
    service.prepare_submit(db, obj, user)       # chiếm phiếu (→ Chờ duyệt) trước khi đụng bộ máy duyệt
    instance_id = bridge.start_approval(db, obj, user)
    obj = service.mark_submitted(db, obj, user, instance_id)
    audit_record(db, user.id, ENTITY, obj.id, "update", f"Gửi duyệt phiếu nghỉ bù {obj.code}")
    return success(_dump_one(db, obj), "Đã gửi duyệt")


@router.post("/{rid}/approve")
def approve_request(rid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "approve"))):
    """Duyệt THẲNG — chỉ khi phiếu không chạy trong luồng nhiều bước."""
    obj = _get_or_404(db, rid, user, "approve")
    if obj.status != int(LeaveCompStatus.PENDING):
        raise HTTPException(400, "Chỉ duyệt được phiếu đang ở trạng thái Chờ duyệt")
    bridge.block_legacy_path(db, obj)
    ensure_not_self_approval(ENTITY, getattr(user, "employee_id", 0), obj.employee_id)   # luôn chặn với phiếu nghỉ bù
    bridge.approve_now(db, obj, user.id)
    db.commit()
    db.refresh(obj)
    audit_record(db, user.id, ENTITY, obj.id, "approve", f"Duyệt phiếu nghỉ bù {obj.code}")
    return success(_dump_one(db, obj), "Đã duyệt phiếu")


@router.post("/{rid}/reject")
def reject_request(rid: int, reason: str = Query("", max_length=500), db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "approve"))):
    """Từ chối THẲNG — cùng điều kiện với `/approve`."""
    obj = _get_or_404(db, rid, user, "approve")
    if obj.status != int(LeaveCompStatus.PENDING):
        raise HTTPException(400, "Chỉ từ chối được phiếu đang ở trạng thái Chờ duyệt")
    bridge.block_legacy_path(db, obj)
    service.claim(db, obj, (LeaveCompStatus.PENDING,), LeaveCompStatus.REJECTED, decision_note=(reason or "Bị từ chối")[:500],
                  decided_at=datetime.now(), updated_by=user.id)
    db.commit()
    db.refresh(obj)
    audit_record(db, user.id, ENTITY, obj.id, "update", f"Từ chối phiếu nghỉ bù {obj.code}")
    return success(_dump_one(db, obj), "Đã từ chối phiếu")


@router.post("/{rid}/cancel")
def cancel_request(rid: int, reason: str = Query("", max_length=500), db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "cancel"))):
    """Hủy: Nháp / Chờ duyệt / Trả về → Đã hủy (rút phiên duyệt trước); Đã duyệt → trừ lại nếu còn đủ, không thì 422."""
    obj = bridge.cancel_request(db, _get_or_404(db, rid, user, "cancel"), reason, user)
    audit_record(db, user.id, ENTITY, obj.id, "cancel", f"Hủy phiếu nghỉ bù {obj.code}")
    return success(_dump_one(db, obj), "Đã hủy phiếu")
