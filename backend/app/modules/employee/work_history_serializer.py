"""Gộp `WorkHistoryOut` cho một DANH SÁCH — tên công ty/phòng ban + số tệp gom
MỖI LOẠI MỘT TRUY VẤN (hợp đồng API), không N+1 theo từng dòng."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.vn_time import vn_today

from .work_history_model import EmployeeWorkHistory
from .work_history_rules import compute_can_apply, compute_is_current
from .work_history_schema import WorkHistoryOut


def _names_map(db: Session, model, ids: set[int]) -> dict[int, str]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return dict(db.query(model.id, model.name).filter(model.id.in_(ids)).all())


def _file_counts(db: Session, ids: list[int]) -> dict[int, int]:
    from app.modules.attachment.model import FileLink

    if not ids:
        return {}
    rows = (db.query(FileLink.entity_id, func.count(FileLink.id))
            .filter(FileLink.entity == "employee_work_history", FileLink.entity_id.in_(ids))
            .group_by(FileLink.entity_id).all())
    return dict(rows)


def serialize_list(db: Session, rows: list[EmployeeWorkHistory]) -> list[dict]:
    from app.modules.company.model import Company
    from app.modules.department.model import Department

    today = vn_today()
    ids = [r.id for r in rows]
    company_names = _names_map(db, Company, {r.company_id for r in rows})
    department_names = _names_map(db, Department, {r.department_id for r in rows})
    file_counts = _file_counts(db, ids)
    can_apply_map = compute_can_apply(rows, today)
    is_current_map = compute_is_current(rows, today)

    out: list[dict] = []
    for r in rows:
        out.append(WorkHistoryOut(
            id=r.id, employee_id=r.employee_id, event_type=r.event_type,
            from_date=r.from_date, to_date=r.to_date, company_id=r.company_id,
            company_name=company_names.get(r.company_id, ""), department_id=r.department_id,
            department_name=department_names.get(r.department_id, ""),
            position_id=r.position_id, position_label=r.position_label,
            decision_no=r.decision_no, decision_date=r.decision_date, note=r.note,
            applied_at=r.applied_at, file_count=file_counts.get(r.id, 0),
            is_current=is_current_map.get(r.id, False), can_apply=can_apply_map.get(r.id, False),
        ).model_dump())
    return out


def serialize_one(db: Session, row: EmployeeWorkHistory) -> dict:
    """Trả ĐÚNG MỘT dòng — nhưng `can_apply` của nó phải tính trên TOÀN BỘ các
    dòng của nhân sự này (Low, review 03/10/2026): `compute_can_apply` cần biết
    dòng CHÍNH MỚI NHẤT để chốt «chỉ áp được dòng chính mới nhất» (#4 của
    `apply_gate`), mà gọi `serialize_list(db, [row])` với MỘT dòng duy nhất thì
    hàm đó chỉ thấy chính nó — luôn tự so với bản thân, chốt vô nghĩa.
    `is_current` cùng lý do (05/10/2026): cần biết có dòng chính mới hơn không."""
    siblings = (db.query(EmployeeWorkHistory)
               .filter(EmployeeWorkHistory.employee_id == row.employee_id).all())
    today = vn_today()
    out = serialize_list(db, [row])[0]
    out["can_apply"] = compute_can_apply(siblings, today).get(row.id, False)
    out["is_current"] = compute_is_current(siblings, today).get(row.id, False)
    return out
