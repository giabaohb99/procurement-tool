"""Cấp QUYỀN TRÊN THƯ MỤC hàng loạt + đổi mức tại chỗ — hộp «Chia sẻ» kiểu
Drive (phase 10B, đặc tả §C, duoc-CR-476 bổ sung).

Tách khỏi `folder_access_grant_service.py` (CRUD đơn lẻ) để mỗi tệp dưới 200
dòng — gọi qua `folder_access_controller.py`, cùng luật quyền Quản lý với
đường đơn lẻ (gác ở controller bằng `ensure_level(..., MANAGE)` trước khi vào
đây, không lặp lại ở tầng service).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .folder_access_grant_service import AUDIT_ENTITY
from .folder_access_model import DocFolderAccess
from .folder_access_schema import FolderAccessBulkGrantIn
from .folder_constants import FOLDER_ACCESS_LEVEL_LABELS, FolderAccessLevel
from .folder_model import DocFolder


def _subject_exists(db: Session, subject_kind: int, subject_id: int) -> bool:
    """Chủ thể có thật trong danh mục tương ứng hay không — CHỈ dùng cho
    `grant_bulk`: cấp hàng loạt gõ tay/dán nhiều dễ lẫn một id đã xóa hoặc gõ
    sai, khác đường ĐƠN LẺ (`grant`, người dùng chọn từ ô select nên luôn hợp
    lệ) — đường HÀNG LOẠT phải tự soát trước khi ghi để khỏi tạo ACL treo trên
    một chủ thể không tồn tại."""
    from app.core.subject_match import (SUBJECT_COMPANY, SUBJECT_DEPARTMENT,
                                        SUBJECT_EMPLOYEE, SUBJECT_ROLE)
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


def grant_bulk(db: Session, folder: DocFolder, data: FolderAccessBulkGrantIn, actor: int) -> dict:
    """`POST /{folder_id}/access/bulk` — CÙNG một mức + một chiều tác động cho
    CẢ danh sách chủ thể, MỘT giao dịch (một `db.commit()` cho toàn lô, khác
    `grant()` đơn lẻ commit riêng từng lần gọi).

    Trùng chủ thể trong CHÍNH payload này (dán nhầm hai lần) → giữ dòng CUỐI,
    không tạo/sửa hai lần. Trùng với dòng CÒN HIỆU LỰC đã có trong DB (cùng
    `subject_kind`/`subject_id`/`effect`) → SỬA dòng đó (như `grant()`), tính
    vào `updated`. Chủ thể không tồn tại → góp vào `skipped`, không chặn cả lô.
    """
    from app.core.subject_match import EFFECT_ALLOW

    level = data.level if data.effect == EFFECT_ALLOW else int(FolderAccessLevel.PRIVATE)

    #  Trùng CHỦ THỂ trong CÙNG một lượt gửi — giữ dòng CUỐI (dict tự khử theo khóa).
    deduped: dict[tuple[int, int], None] = {}
    for subject in data.subjects:
        deduped[(subject.subject_kind, subject.subject_id)] = None

    created = 0
    updated = 0
    skipped: list[dict] = []
    touched_rows: list[DocFolderAccess] = []

    for subject_kind, subject_id in deduped:
        if not _subject_exists(db, subject_kind, subject_id):
            skipped.append({
                "subject": {"subject_kind": subject_kind, "subject_id": subject_id},
                "reason": "Không tìm thấy đối tượng",
            })
            continue

        existing = (
            db.query(DocFolderAccess)
            .filter(DocFolderAccess.folder_id == folder.id,
                   DocFolderAccess.subject_kind == subject_kind,
                   DocFolderAccess.subject_id == subject_id,
                   DocFolderAccess.effect == data.effect,
                   DocFolderAccess.revoked_at.is_(None))
            .first()
        )
        if existing:
            existing.level = level
            existing.valid_from = data.valid_from
            existing.valid_to = data.valid_to
            existing.reason = data.reason
            existing.updated_by = actor
            touched_rows.append(existing)
            updated += 1
        else:
            row = DocFolderAccess(
                folder_id=folder.id, subject_kind=subject_kind, subject_id=subject_id,
                effect=data.effect, level=level, valid_from=data.valid_from,
                valid_to=data.valid_to, reason=data.reason,
                created_by=actor, updated_by=actor)
            db.add(row)
            touched_rows.append(row)
            created += 1

    #  MỘT commit cho toàn lô — đúng "một giao dịch" của đặc tả, khác vòng lặp
    #  gọi `grant()` N lần (N commit rời, một dòng lỗi giữa chừng để lại phần
    #  đã ghi dở).
    db.commit()
    for row in touched_rows:
        db.refresh(row)
        record(db, actor, AUDIT_ENTITY, folder.id, "update",
              f"Cấp quyền hàng loạt {FOLDER_ACCESS_LEVEL_LABELS.get(row.level, '')} trên thư "
              f"mục {folder.name}")

    return {"created": created, "updated": updated, "skipped": skipped}


def update_level(db: Session, folder: DocFolder, access_id: int, level: int,
                 actor: int) -> DocFolderAccess:
    """`PATCH /{folder_id}/access/{access_id}` — đổi MỨC tại chỗ (dòng «Người
    có quyền» của hộp «Chia sẻ», menu thả xuống). Chỉ áp cho dòng CHO PHÉP còn
    hiệu lực, đúng thư mục này — dòng CẤM không có mức để đổi (luôn `PRIVATE`,
    xem `folder_access_model.py`); dòng kế thừa/đã thu hồi phải sửa ở đúng thư
    mục nguồn hoặc cấp lại, không sửa được qua cửa này."""
    from app.core.subject_match import EFFECT_ALLOW

    row = db.get(DocFolderAccess, access_id)
    if not row or row.folder_id != folder.id:
        raise HTTPException(404, "Không tìm thấy dòng chia sẻ")
    if row.revoked_at is not None:
        raise HTTPException(400, "Dòng này đã thu hồi rồi")
    if row.effect != EFFECT_ALLOW:
        raise HTTPException(400, "Dòng không cho phép không có mức quyền để đổi")

    row.level = level
    row.updated_by = actor
    db.commit()
    db.refresh(row)
    record(db, actor, AUDIT_ENTITY, folder.id, "update",
          f"Đổi mức quyền thành {FOLDER_ACCESS_LEVEL_LABELS.get(level, '')} trên thư mục "
          f"{folder.name}")
    return row
