"""Gộp `ConcurrentOut` cho một DANH SÁCH — tên công ty / phòng ban + số tệp gom MỖI LOẠI
MỘT truy vấn (không N+1). Trạng thái dẫn xuất tính từ ngày + `vn_today()`."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.hr_concurrent_codes import (CONCURRENT_KIND_LABELS, CONCURRENT_STATUS_LABELS, ConcurrentKind,
                                          get_concurrent_status)
from app.core.vn_time import vn_today

from .concurrent_model import EmployeeConcurrent
from .concurrent_schema import ConcurrentOut


def _names_map(db: Session, model, ids: set[int]) -> dict[int, str]:
    ids = {i for i in ids if i}
    return dict(db.query(model.id, model.name).filter(model.id.in_(ids)).all()) if ids else {}


def _file_counts(db: Session, ids: list[int]) -> dict[int, int]:
    from app.modules.attachment.model import FileLink

    if not ids:
        return {}
    rows = (db.query(FileLink.entity_id, func.count(FileLink.id))
            .filter(FileLink.entity == "employee_concurrent", FileLink.entity_id.in_(ids))
            .group_by(FileLink.entity_id).all())
    return dict(rows)


def serialize_list(db: Session, rows: list[EmployeeConcurrent]) -> list[dict]:
    from app.modules.company.model import Company
    from app.modules.department.model import Department

    today = vn_today()
    company_names = _names_map(db, Company, {r.company_id for r in rows})
    department_names = _names_map(db, Department, {r.department_id for r in rows})
    file_counts = _file_counts(db, [r.id for r in rows])

    out: list[dict] = []
    for r in rows:
        status = get_concurrent_status(r.from_date, r.to_date, today)
        kind = ConcurrentKind(r.kind or ConcurrentKind.DEPARTMENT)
        out.append(ConcurrentOut(
            id=r.id, employee_id=r.employee_id, kind=int(kind), kind_label=CONCURRENT_KIND_LABELS[kind],
            company_id=r.company_id,
            company_name=company_names.get(r.company_id, ""), department_id=r.department_id,
            department_name=department_names.get(r.department_id, ""), position_id=r.position_id or 0,
            position_label=r.position_label or "", from_date=r.from_date, to_date=r.to_date,
            decision_no=r.decision_no or "", decision_date=r.decision_date, note=r.note or "",
            counts_scope=bool(r.counts_scope), work_history_id=r.work_history_id or 0,
            status=int(status), status_label=CONCURRENT_STATUS_LABELS[status],
            file_count=file_counts.get(r.id, 0),
        ).model_dump(mode="json"))
    return out


def serialize_one(db: Session, row: EmployeeConcurrent) -> dict:
    return serialize_list(db, [row])[0]
