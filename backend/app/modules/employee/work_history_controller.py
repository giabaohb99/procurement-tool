"""API quá trình công tác — `prefix=/api/employees` (phase 02, hợp đồng khoá
cứng ở `phase-02-backend-api-ap-ho-so-dinh-kem.md`).

⚠️ `/me/work-history` PHẢI khai TRƯỚC `/{eid}/work-history`: FastAPI dò route
theo thứ tự khai trong CÙNG router, «me» rơi vào `eid: int` thì 422 chứ không
chạy hàm `GET /me/work-history`.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.database import get_db
from app.core.hr_work_history_codes import WORK_EVENT_TYPE_LABELS, WorkEventType
from app.core.response import success

from . import work_history_access, work_history_apply_service, work_history_service
from .work_history_serializer import serialize_list, serialize_one
from .work_history_schema import WorkHistoryIn, WorkHistoryUpdate

router = APIRouter(prefix="/api/employees", tags=["employee-work-history"])


def _audit_base_message(row) -> str:
    try:
        label = WORK_EVENT_TYPE_LABELS.get(WorkEventType(row.event_type), "")
    except ValueError:
        label = ""
    msg = label + (f" — {row.position_label}" if row.position_label else "")
    msg += f", từ {row.from_date.isoformat()}"
    if row.decision_no:
        msg += f", QĐ {row.decision_no}"
    return msg


def _audit_applied_message(row, applied_changes: list[str]) -> str:
    if row.event_type == int(WorkEventType.RESIGN):
        return f"Áp thôi việc từ dòng quá trình công tác: nghỉ việc từ {row.from_date.isoformat()}"
    return "Áp vào hồ sơ: " + "; ".join(applied_changes)


def _audit(db: Session, user, emp, row, *, base_action: str | None,
          applied_changes: list[str], closed: list[str]) -> None:
    if base_action:
        verb = "Thêm" if base_action == "create" else "Sửa"
        audit_record(db, user.id, "employee", emp.id, base_action,
                     f"{verb} quá trình công tác: {_audit_base_message(row)}", doc_code=emp.code or "")
    if applied_changes:
        audit_record(db, user.id, "employee", emp.id, "update",
                     _audit_applied_message(row, applied_changes), doc_code=emp.code or "")
    if closed:
        audit_record(db, user.id, "employee", emp.id, "update",
                     "Đóng dòng quá trình công tác cũ: " + "; ".join(closed), doc_code=emp.code or "")


@router.get("/me/work-history")
def my_work_history(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Chỉ đòi ĐĂNG NHẬP — id lấy từ `user.employee_id`, không nhận tham số.
    Chưa gắn hồ sơ (`employee_id = 0`) → `items: []`, không phải lỗi."""
    eid = int(getattr(user, "employee_id", 0) or 0)
    if not eid:
        return success({"items": [], "can_edit": False, "can_open_files": True})
    rows = work_history_service.list_rows(db, eid)
    return success({"items": serialize_list(db, rows), "can_edit": False, "can_open_files": True})


@router.get("/{eid}/work-history")
def list_work_history(eid: int, db: Session = Depends(get_db),
                      user=Depends(require("employee", "read"))):
    profile = get_perm_profile(db, user)
    work_history_access.employee_in_scope(db, eid, user, profile, "read")
    rows = work_history_service.list_rows(db, eid)
    return success({
        "items": serialize_list(db, rows),
        "can_edit": work_history_access.can_edit(db, user, profile, eid),
        "can_open_files": work_history_access.can_open_files(profile, eid),
    })


@router.post("/{eid}/work-history")
def create_work_history(eid: int, data: WorkHistoryIn, db: Session = Depends(get_db),
                        user=Depends(require("employee", "write"))):
    profile = get_perm_profile(db, user)
    emp = work_history_access.employee_in_scope(db, eid, user, profile, "write")
    work_history_access.block_self_write(db, user, eid)

    row, warnings, closed = work_history_service.create(db, eid, data, user)
    applied_changes = (work_history_apply_service.apply(db, row, user, profile)
                       if data.apply_to_profile else [])
    db.commit()
    db.refresh(row)
    _audit(db, user, emp, row, base_action="create", applied_changes=applied_changes, closed=closed)
    return success({"item": serialize_one(db, row), "warnings": warnings,
                    "applied_changes": applied_changes}, "Đã thêm quá trình công tác", 201)


@router.patch("/{eid}/work-history/{hid}")
def update_work_history(eid: int, hid: int, data: WorkHistoryUpdate, db: Session = Depends(get_db),
                        user=Depends(require("employee", "write"))):
    profile = get_perm_profile(db, user)
    emp = work_history_access.employee_in_scope(db, eid, user, profile, "write")
    work_history_access.block_self_write(db, user, eid)

    row, warnings, closed = work_history_service.update(db, eid, hid, data, user)
    applied_changes = (work_history_apply_service.apply(db, row, user, profile)
                       if data.apply_to_profile else [])
    db.commit()
    db.refresh(row)
    _audit(db, user, emp, row, base_action="update", applied_changes=applied_changes, closed=closed)
    return success({"item": serialize_one(db, row), "warnings": warnings,
                    "applied_changes": applied_changes}, "Đã cập nhật")


@router.delete("/{eid}/work-history/{hid}")
def delete_work_history(eid: int, hid: int, db: Session = Depends(get_db),
                        user=Depends(require("employee", "write"))):
    profile = get_perm_profile(db, user)
    emp = work_history_access.employee_in_scope(db, eid, user, profile, "write")
    work_history_access.block_self_write(db, user, eid)

    row = work_history_service.get_row_in_employee(db, eid, hid)
    work_history_access.block_delete_without_sensitive(db, user, row)
    base_message = _audit_base_message(row)

    work_history_service.delete(db, eid, hid, user)
    audit_record(db, user.id, "employee", emp.id, "delete",
                 f"Xóa dòng quá trình công tác: {base_message}", doc_code=emp.code or "")
    return success(None, "Đã xóa")


@router.post("/{eid}/work-history/{hid}/apply")
def apply_work_history(eid: int, hid: int, db: Session = Depends(get_db),
                       user=Depends(require("employee", "write"))):
    profile = get_perm_profile(db, user)
    emp = work_history_access.employee_in_scope(db, eid, user, profile, "write")
    work_history_access.block_self_write(db, user, eid)
    row = work_history_service.get_row_in_employee(db, eid, hid)

    applied_changes = work_history_apply_service.apply(db, row, user, profile)
    db.commit()
    db.refresh(row)
    _audit(db, user, emp, row, base_action=None, applied_changes=applied_changes, closed=[])
    return success({"item": serialize_one(db, row), "applied_changes": applied_changes},
                   "Đã áp vào hồ sơ")
