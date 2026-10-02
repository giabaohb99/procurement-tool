"""Đọc danh sách + CẤP/THU hàng loạt quyền XEM TỪNG BÁO CÁO.

Cùng khuôn `doc_catalog/folder_access_bulk_service.py` (CẤP: trùng chủ thể còn
hiệu lực cùng chiều → sửa; chủ thể không tồn tại → skip, không chặn cả lô;
MỘT giao dịch cho toàn lô) và `folder_access_grant_service.revoke` (THU HỒI:
đánh dấu, không xóa dòng).
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.report_keys import REPORT_META, ReportKey
from app.core.subject_match import (EFFECT_ALLOW, SUBJECT_COMPANY, SUBJECT_DEPARTMENT,
                                    SUBJECT_EMPLOYEE, SUBJECT_LABELS, SUBJECT_ROLE,
                                    subject_names)

from .model import ReportAccess
from .schema import ReportAccessGrantIn

AUDIT_ENTITY = "report_access"


def list_grants(db: Session) -> list[dict]:
    """13 mục theo ĐÚNG thứ tự khóa, mỗi mục kèm danh sách dòng CÒN SỐNG. Số
    truy vấn cố định: 1 (đọc dòng) + tối đa 4 (tra tên theo từng loại chủ thể,
    `subject_names`) — không phụ thuộc số dòng."""
    rows = (
        db.query(ReportAccess)
        .filter(ReportAccess.revoked_at.is_(None))
        .order_by(ReportAccess.report_key, ReportAccess.id)
        .all()
    )
    names = subject_names(db, rows)
    by_key: dict[int, list[dict]] = {}
    for row in rows:
        by_key.setdefault(row.report_key, []).append({
            "id": row.id,
            "subject_kind": row.subject_kind,
            "subject_kind_label": SUBJECT_LABELS.get(row.subject_kind, ""),
            "subject_id": row.subject_id,
            "subject_name": names.get((row.subject_kind, row.subject_id), ""),
            "effect": row.effect,
            "reason": row.reason,
            "valid_from": row.valid_from,
            "valid_to": row.valid_to,
            "created_at": row.created_at.isoformat() if row.created_at else "",
        })
    return [
        {
            "key": int(key),
            "label": REPORT_META[key][0],
            "group": REPORT_META[key][1],
            "grants": by_key.get(int(key), []),
        }
        for key in ReportKey
    ]


def _subject_exists(db: Session, subject_kind: int, subject_id: int) -> bool:
    """Chủ thể có thật trong danh mục tương ứng — gõ một id đã xóa/sai không
    được tạo ra ACL treo. Cùng logic `folder_access_bulk_service._subject_exists`."""
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.role.model import Role

    model = {
        SUBJECT_EMPLOYEE: Employee,
        SUBJECT_DEPARTMENT: Department,
        SUBJECT_COMPANY: Company,
        SUBJECT_ROLE: Role,
    }.get(subject_kind)
    if model is None:
        return False
    return db.query(model.id).filter(model.id == subject_id).first() is not None


def grant(db: Session, key: ReportKey, data: ReportAccessGrantIn, actor: int) -> dict:
    """`POST /{key}/grants` — CÙNG một chiều tác động cho cả danh sách chủ
    thể, MỘT giao dịch. Không chặn tự gán cho chính mình/vai trò mình: dòng
    CHO PHÉP ở đây chỉ mở `/summary`+`/summary/export` của ĐÚNG báo cáo này —
    quyền hành động (`require`) và phạm vi dữ liệu (`apply_scope`) của phân hệ
    gốc không đổi, nên gán rộng tay ở đây không mở rộng được dữ liệu ai xem."""
    #  Trùng chủ thể trong CÙNG một lượt gửi — giữ lần CUỐI (dict tự khử theo khóa).
    deduped: dict[tuple[int, int], None] = {}
    for subject in data.subjects:
        deduped[(subject.subject_kind, subject.subject_id)] = None

    created = updated = 0
    skipped: list[dict] = []
    touched: list[ReportAccess] = []
    for subject_kind, subject_id in deduped:
        if not _subject_exists(db, subject_kind, subject_id):
            skipped.append({"subject_kind": subject_kind, "subject_id": subject_id,
                            "reason": "Không tìm thấy đối tượng"})
            continue

        existing = (
            db.query(ReportAccess)
            .filter(ReportAccess.report_key == int(key),
                    ReportAccess.subject_kind == subject_kind,
                    ReportAccess.subject_id == subject_id,
                    ReportAccess.effect == data.effect,
                    ReportAccess.revoked_at.is_(None))
            .first()
        )
        if existing:
            existing.reason = data.reason
            existing.valid_from = data.valid_from
            existing.valid_to = data.valid_to
            existing.updated_by = actor
            touched.append(existing)
            updated += 1
        else:
            row = ReportAccess(
                report_key=int(key), subject_kind=subject_kind, subject_id=subject_id,
                effect=data.effect, reason=data.reason, valid_from=data.valid_from,
                valid_to=data.valid_to, created_by=actor, updated_by=actor)
            db.add(row)
            touched.append(row)
            created += 1

    #  MỘT commit cho toàn lô — một dòng lỗi giữa chừng không để lại phần đã ghi dở.
    db.commit()
    if created or updated:
        verb = "Cho phép" if data.effect == EFFECT_ALLOW else "Cấm"
        label = REPORT_META[key][0]
        record(db, actor, AUDIT_ENTITY, int(key), "update",
              f"{verb} xem «{label}» cho {created + updated} đối tượng")
    return {"created": created, "updated": updated, "skipped": skipped}


def revoke(db: Session, access_id: int, reason: str, actor: int) -> ReportAccess:
    """`DELETE /grants/{id}` — thu hồi là ĐÁNH DẤU, dòng ở lại bảng (G19, G20)."""
    row = db.get(ReportAccess, access_id)
    if not row:
        raise HTTPException(404, "Không tìm thấy dòng phân quyền báo cáo")
    if row.revoked_at is not None:
        raise HTTPException(400, "Dòng này đã thu hồi rồi")

    row.revoked_at = datetime.now()
    row.revoked_by = actor
    row.revoke_reason = reason
    row.updated_by = actor
    db.commit()
    db.refresh(row)
    label = REPORT_META[ReportKey(row.report_key)][0]
    record(db, actor, AUDIT_ENTITY, row.report_key, "update", f"Thu hồi quyền xem «{label}»")
    return row
