"""Cấp / thu QUYỀN TRÊN THƯ MỤC — ghi vào `tab_doc_folder_access`.

Chỉ người mức **Quản lý** gọi được (gác ở `folder_access_controller.py` bằng
`folder_access_service.ensure_level(..., MANAGE)`). Cùng khuôn với
`document/access_service.grant/revoke`: có dòng còn sống thì SỬA dòng đó chứ
không thêm dòng mới; thu hồi là ĐÁNH DẤU, không xóa (G19, G20).
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .folder_access_model import DocFolderAccess
from .folder_constants import FOLDER_ACCESS_LEVEL_LABELS, FolderAccessLevel
from .folder_model import DocFolder

AUDIT_ENTITY = "doc_folder"


def grant(db: Session, folder: DocFolder, data, actor: int) -> DocFolderAccess:
    """`data` đã tự kiểm dải giá trị ở `FolderAccessGrantIn` (Pydantic). Dòng
    CẤM ép `level=PRIVATE` — cột đó vô nghĩa với cấm, đừng lưu số cũ gây hiểu
    lầm khi đọc lại (xem chú thích ở `folder_access_model.py`)."""
    from app.core.subject_match import EFFECT_ALLOW

    values = data.model_dump()
    if data.effect != EFFECT_ALLOW:
        values["level"] = int(FolderAccessLevel.PRIVATE)

    existing = (
        db.query(DocFolderAccess)
        .filter(DocFolderAccess.folder_id == folder.id,
               DocFolderAccess.subject_kind == data.subject_kind,
               DocFolderAccess.subject_id == data.subject_id,
               DocFolderAccess.effect == data.effect,
               DocFolderAccess.revoked_at.is_(None))
        .first()
    )
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
        existing.updated_by = actor
        row = existing
    else:
        row = DocFolderAccess(folder_id=folder.id, **values, created_by=actor, updated_by=actor)
        db.add(row)

    db.commit()
    db.refresh(row)
    record(db, actor, AUDIT_ENTITY, folder.id, "update",
          f"Cấp quyền {FOLDER_ACCESS_LEVEL_LABELS.get(values['level'], '')} trên thư mục "
          f"{folder.name}")
    return row


def revoke(db: Session, folder: DocFolder, access_id: int, reason: str, actor: int) -> DocFolderAccess:
    row = db.get(DocFolderAccess, access_id)
    if not row or row.folder_id != folder.id:
        raise HTTPException(404, "Không tìm thấy dòng chia sẻ")
    if row.revoked_at is not None:
        raise HTTPException(400, "Dòng này đã thu hồi rồi")

    row.revoked_at = datetime.now()
    row.revoked_by = actor
    row.revoke_reason = reason
    row.updated_by = actor
    db.commit()
    db.refresh(row)
    record(db, actor, AUDIT_ENTITY, folder.id, "update", f"Thu hồi quyền trên thư mục {folder.name}")
    return row


def list_direct(db: Session, folder_id: int) -> list[DocFolderAccess]:
    """Chỉ dòng khai TRỰC TIẾP trên thư mục này (không gồm tổ tiên) — dùng cho
    danh sách quản lý quyền. Xem `folder_access_view_service.list_effective`
    cho bản GỘP CẢ kế thừa (hiển thị ở trang chi tiết)."""
    return (
        db.query(DocFolderAccess)
        .filter(DocFolderAccess.folder_id == folder_id)
        .order_by(DocFolderAccess.revoked_at.isnot(None), DocFolderAccess.effect.desc(),
                 DocFolderAccess.id.desc())
        .all()
    )

