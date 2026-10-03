"""ÁP một dòng quá trình công tác VÀO HỒ SƠ (A4/A5/A8).

⚠️ Đường ghi DUY NHẤT vào hồ sơ: `service.update_employee` (loại 1,2,3,5,6) /
`department_service.set_extra_departments` (loại 4). KHÔNG ghi thẳng
`Employee.position/department_id/status` — cấm đường ghi thứ ba.

⚠️ MỘT GIAO DỊCH: hàm `apply()` KHÔNG tự `commit`. Loại 1,2,3,5,6 ủy commit
cho `service.update_employee` (đã gồm dòng lịch sử + `applied_at` + hồ sơ +
khóa TK trong CÙNG một `db.commit()` của hàm đó); loại 4 (kiêm nhiệm) và
nhánh không-đổi-gì thì BÊN GỌI (controller) `commit`.
"""
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.hr_work_history_codes import POSITION_TRACK, WorkEventType
from app.core.vn_time import vn_today

from . import department_service
from . import service as employee_service
from .field_limits import check_resign_after_hire
from .model import Employee
from .schema import EmployeeUpdate
from .work_history_model import EmployeeWorkHistory
from .work_history_rules import apply_gate


def _company_label(db: Session, cid: int) -> str:
    if not cid:
        return "—"
    from app.modules.company.model import Company
    obj = db.get(Company, cid)
    return obj.name if obj else str(cid)


def _department_label(db: Session, did: int) -> str:
    if not did:
        return "—"
    from app.modules.department.model import Department
    obj = db.get(Department, did)
    return obj.name if obj else str(did)


def _apply_position_track(db: Session, emp: Employee, row: EmployeeWorkHistory,
                          actor, profile: dict) -> list[str]:
    """Loại 1,2,3,5 — đặt công ty/phòng/chức vụ CHÍNH, chỉ ô >0 và KHÁC hồ sơ."""
    diff: dict = {}
    changes: list[str] = []
    if row.company_id and row.company_id != (emp.company_id or 0):
        diff["company_id"] = row.company_id
        changes.append(f"Pháp nhân: {_company_label(db, emp.company_id)} → "
                       f"{_company_label(db, row.company_id)}")
    if row.department_id and row.department_id != (emp.department_id or 0):
        diff["department_id"] = row.department_id
        changes.append(f"Phòng ban: {_department_label(db, emp.department_id)} → "
                       f"{_department_label(db, row.department_id)}")
    if row.position_id and row.position_id != (emp.position_id or 0):
        diff["position_id"] = row.position_id
        changes.append(f"Chức vụ: {emp.position or '—'} → {row.position_label or '—'}")
    if not diff:
        return []

    if "department_id" in diff:
        #  L1 + L2 — Y HỆT `PATCH /employees/{id}` (CR-167): đổi phòng ban qua
        #  cửa này cũng đổi phạm vi dữ liệu, không được né hai chốt đó.
        department_service.block_edit_own_department(db, emp.id, actor)
        department_service.block_out_of_scope_departments(db, [diff["department_id"]], actor, profile)

    employee_service.update_employee(db, emp.id, EmployeeUpdate(**diff), actor.id)
    return changes


def _other_concurrent_still_in_effect(db: Session, eid: int, dept: int,
                                      exclude_id: int, today: date) -> bool:
    """Low (review 03/10/2026) — còn DÒNG KIÊM NHIỆM KHÁC, cùng phòng, đang
    hiệu lực không (loại trừ chính dòng đang xét). Dùng để KHÔNG gỡ phòng khi
    một dòng khác vẫn còn hợp lệ — gỡ lúc đó là cắt nhầm quyền của dòng kia."""
    return (db.query(EmployeeWorkHistory)
            .filter(EmployeeWorkHistory.employee_id == eid,
                    EmployeeWorkHistory.event_type == int(WorkEventType.CONCURRENT),
                    EmployeeWorkHistory.department_id == dept,
                    EmployeeWorkHistory.id != exclude_id,
                    or_(EmployeeWorkHistory.to_date.is_(None),
                        EmployeeWorkHistory.to_date >= today))
            .first() is not None)


def _apply_concurrent(db: Session, emp: Employee, row: EmployeeWorkHistory,
                      actor, profile: dict) -> list[str]:
    """Loại 4 — đang hiệu lực thì THÊM phòng kiêm nhiệm; đã kết thúc thì GỠ."""
    dept = row.department_id or 0
    if not dept or dept == (emp.department_id or 0):
        return []   # trùng phòng chính — không có gì để kiêm nhiệm thêm

    department_service.block_edit_own_department(db, emp.id, actor)
    department_service.block_out_of_scope_departments(db, [dept], actor, profile)

    existing = department_service.extra_departments_of(db, emp.id)
    today = vn_today()
    in_effect = row.to_date is None or row.to_date >= today
    if in_effect:
        if dept in existing:
            return []
        new_list, action = existing + [dept], "thêm"
    else:
        if dept not in existing:
            return []
        if _other_concurrent_still_in_effect(db, emp.id, dept, row.id, today):
            return []   # còn dòng kiêm nhiệm KHÁC cùng phòng đang hiệu lực — không gỡ
        new_list, action = [d for d in existing if d != dept], "gỡ"

    department_service.set_extra_departments(db, emp, new_list, actor.id)
    return [f"Kiêm nhiệm — {action} phòng «{_department_label(db, dept)}»"]


def _apply_resign(db: Session, emp: Employee, row: EmployeeWorkHistory, actor) -> list[str]:
    """Loại 6 — đúng đường nghỉ việc SẴN CÓ của tab «Chung» (Q2, bao-CR-400)."""
    try:
        check_resign_after_hire(emp.hire_date, row.from_date)
    except ValueError as e:
        raise HTTPException(400, str(e))

    diff: dict = {}
    changes: list[str] = []
    if (emp.status or "") != employee_service.STATUS_RESIGNED:
        diff["status"] = employee_service.STATUS_RESIGNED
        changes.append("Trạng thái: → Nghỉ việc")
    if emp.resign_date != row.from_date:
        diff["resign_date"] = row.from_date
        changes.append(f"Ngày nghỉ việc: → {row.from_date.isoformat()}")
    if not diff:
        return []

    employee_service.update_employee(db, emp.id, EmployeeUpdate(**diff), actor.id)
    return changes


def apply(db: Session, row: EmployeeWorkHistory, actor, profile: dict) -> list[str]:
    """Áp MỘT dòng — gọi từ POST/PATCH (`apply_to_profile=True`) và `/apply`.
    Idempotent (A5): khớp rồi thì trả `[]` nhưng vẫn cập nhật `applied_at`."""
    reason = apply_gate(db, row.employee_id, row, vn_today())
    if reason:
        raise HTTPException(400, reason)

    emp = db.get(Employee, row.employee_id)
    if emp is None:
        raise HTTPException(404, "Không tìm thấy nhân viên")

    #  GHI applied_at/applied_by TRƯỚC khi gọi nhánh áp (Low, review 03/10/2026):
    #  `employee_service.update_employee` (loại 1,2,3,5,6) tự COMMIT giữa chừng.
    #  Đặt hai cột này trước thì chúng đi CHUNG cú commit đó (cùng session) —
    #  không rơi vào khe hở giữa commit của `update_employee` và commit cuối của
    #  controller, nơi mà một lỗi ở giữa khiến hồ sơ đã đổi nhưng dòng lịch sử
    #  vẫn báo "chưa áp".
    row.applied_at = datetime.now()
    row.applied_by = actor.id

    et = WorkEventType(row.event_type)
    if et in POSITION_TRACK:
        changes = _apply_position_track(db, emp, row, actor, profile)
    elif et == WorkEventType.CONCURRENT:
        changes = _apply_concurrent(db, emp, row, actor, profile)
    elif et == WorkEventType.RESIGN:
        changes = _apply_resign(db, emp, row, actor)
    else:
        changes = []   # không tới đây — `apply_gate` đã chặn loại ngoài APPLICABLE

    return changes
