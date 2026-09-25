"""Người ký trên bản in — bao-CR-490 (đại ca chốt 25/09/2026).

Ba chứng từ thu mua (YCMH · YCBG · ĐMH) có thêm cột `approver_employee_id` = NHÂN SỰ thực bấm
Duyệt ở chặng trưởng phòng («Trưởng phòng phê duyệt»). Bản in nội bộ cho chọn ô ký hiện:
  · người duyệt (`approver_*`, tra theo cột này; phiếu cũ chưa có cột thì lùi về nhật ký), hay
  · trưởng phòng THEO HỒ SƠ phòng ban (`dept_head_*`, `Department.manager_id` của phòng lập).
Vì sao cần hai: người bấm Duyệt có thể là phó phòng / người được ủy quyền, còn giấy tờ nộp ra
ngoài lại cần đúng tên người đứng đầu phòng trên pháp lý. Mẫu thuế để trống ô ký, không đọc đây.
"""
from sqlalchemy.orm import Session


def employee_id_of_user(db: Session, user_id: int) -> int:
    from app.modules.user.model import User

    user = db.get(User, user_id) if user_id else None
    return int(user.employee_id or 0) if user else 0


def person_block(db: Session, employee_id: int) -> dict:
    """`{name, signature}` của một nhân sự; rỗng khi không có."""
    from app.core.audit import resolve_signature_by_employee
    from app.modules.employee.model import Employee

    emp = db.get(Employee, employee_id) if employee_id else None
    if not emp or not (emp.full_name or "").strip():
        return {"name": "", "signature": ""}
    return {"name": emp.full_name, "signature": resolve_signature_by_employee(db, emp.id)}


def department_head_block(db: Session, department_id: int) -> dict:
    """Trưởng phòng theo hồ sơ phòng ban (`Department.manager_id`) — `{employee_id, name, signature}`."""
    from app.modules.department.model import Department

    dept = db.get(Department, department_id) if department_id else None
    head_id = int(dept.manager_id or 0) if dept else 0
    return {"employee_id": head_id, **person_block(db, head_id)}


def stamp_approver(db: Session, doc, user_id: int) -> None:
    """Ghi nhân sự vừa bấm Duyệt vào `approver_employee_id` của chứng từ (không commit)."""
    doc.approver_employee_id = employee_id_of_user(db, user_id)


def approver_fields(db: Session, doc) -> dict:
    """Bộ khóa chung cho serializer ba chứng từ: id + tên người duyệt, tên trưởng phòng hồ sơ."""
    approver = person_block(db, int(getattr(doc, "approver_employee_id", 0) or 0))
    head = department_head_block(db, int(getattr(doc, "department_id", 0) or 0))
    return {
        "approver_employee_id": int(getattr(doc, "approver_employee_id", 0) or 0),
        "approver_employee_name": approver["name"],
        "dept_head_employee_id": head["employee_id"],
        "dept_head_name": head["name"],
        "dept_head_signature": head["signature"],
    }
