"""Dựng `effective_access` cho `GET /api/doc-folders/{id}` — TOÀN BỘ dòng ACL
áp dụng lên một thư mục: của chính nó + KẾ THỪA từ tổ tiên, kèm tên đối tượng
và tên thư mục nguồn (để giao diện ghi "kế thừa từ ‹thư mục›").

Tách khỏi `folder_access_grant_service.py` (CRUD ghi) và
`folder_access_service.py` (tính mức hiệu lực) để mỗi tệp một việc, dưới 200
dòng — chỉ nơi gọi (`folder_tree_service.get_detail`) mới quyết định có gắn
trường này vào response hay không (chỉ người mức Quản lý mới thấy).
"""
from sqlalchemy.orm import Session

from app.core.subject_match import EFFECT_LABELS, SUBJECT_LABELS

from .folder_access_model import DocFolderAccess
from .folder_constants import FOLDER_ACCESS_LEVEL_LABELS, FolderAccessLevel, FolderKind
from .folder_model import DocFolder


def _subject_names(db: Session, rows: list[DocFolderAccess]) -> dict[tuple[int, int], str]:
    """`{(subject_kind, subject_id): tên}` — MỘT lượt tra cho mỗi loại đối
    tượng, cùng lối `document/serializer.serialize_access`."""
    from app.core.subject_match import (SUBJECT_COMPANY, SUBJECT_DEPARTMENT,
                                        SUBJECT_EMPLOYEE, SUBJECT_ROLE)
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.role.model import Role

    by_kind = {
        SUBJECT_EMPLOYEE: (Employee, "full_name"),
        SUBJECT_DEPARTMENT: (Department, "name"),
        SUBJECT_COMPANY: (Company, "name"),
        SUBJECT_ROLE: (Role, "name"),
    }
    result: dict[tuple[int, int], str] = {}
    for kind, (model, field) in by_kind.items():
        ids = {r.subject_id for r in rows if r.subject_kind == kind}
        if not ids:
            continue
        for oid, name in db.query(model.id, getattr(model, field)).filter(model.id.in_(ids)).all():
            result[(kind, oid)] = name
    return result


def _folder_names(db: Session, folder_ids: set[int]) -> dict[int, str]:
    """Tên hiển thị của một nhóm thư mục — thư mục pháp nhân đọc tên từ
    `Company.name` (không lưu ở `DocFolder.name`), cùng luật với
    `folder_tree_service._label_of`."""
    if not folder_ids:
        return {}
    from app.modules.company.model import Company

    rows = (db.query(DocFolder.id, DocFolder.name, DocFolder.company_id, DocFolder.kind)
           .filter(DocFolder.id.in_(folder_ids)).all())
    company_ids = {r.company_id for r in rows if r.kind == int(FolderKind.COMPANY)}
    company_names = (dict(db.query(Company.id, Company.name).filter(Company.id.in_(company_ids)).all())
                     if company_ids else {})
    return {r.id: (r.name or company_names.get(r.company_id, "")) for r in rows}


def _row_dict(row: DocFolderAccess, target_folder_id: int, subject_names: dict,
             folder_names: dict) -> dict:
    return {
        "id": row.id,
        "folder_id": row.folder_id,
        "folder_name": folder_names.get(row.folder_id, ""),
        "is_inherited": row.folder_id != target_folder_id,
        "subject_kind": row.subject_kind,
        "subject_kind_label": SUBJECT_LABELS.get(row.subject_kind, ""),
        "subject_id": row.subject_id,
        "subject_name": subject_names.get((row.subject_kind, row.subject_id), ""),
        "effect": row.effect,
        "effect_label": EFFECT_LABELS.get(row.effect, ""),
        "level": row.level,
        "level_label": FOLDER_ACCESS_LEVEL_LABELS.get(row.level, ""),
        "valid_from": row.valid_from,
        "valid_to": row.valid_to,
        "reason": row.reason,
        "is_active": row.revoked_at is None,
        "revoked_at": row.revoked_at.isoformat() if row.revoked_at else "",
    }


def serialize_rows(db: Session, target_folder_id: int, rows: list[DocFolderAccess]) -> list[dict]:
    """Dùng chung cho GET `/access` (chỉ dòng TRỰC TIẾP, `folder_access_grant_service.list_direct`)
    và `effective_access` (dòng trực tiếp + kế thừa, `list_effective` dưới đây)."""
    if not rows:
        return []
    subject_names = _subject_names(db, rows)
    folder_names = _folder_names(db, {r.folder_id for r in rows})
    return [_row_dict(row, target_folder_id, subject_names, folder_names) for row in rows]


def list_effective(db: Session, folder: DocFolder) -> list[dict]:
    """ACL của `folder` VÀ mọi tổ tiên — đọc thẳng `path` vật hóa, MỘT truy
    vấn duy nhất."""
    chain_ids = [int(p) for p in (folder.path or "").strip("/").split("/") if p]
    if not chain_ids:
        return []

    rows = (
        db.query(DocFolderAccess)
        .filter(DocFolderAccess.folder_id.in_(chain_ids))
        .order_by(DocFolderAccess.revoked_at.isnot(None), DocFolderAccess.effect.desc(),
                 DocFolderAccess.id.desc())
        .all()
    )
    return serialize_rows(db, folder.id, rows)


def annotate_detail(db: Session, user, folder: DocFolder, node: dict) -> dict:
    """Gắn `my_level`/`effective_access` vào node chi tiết của `GET /{id}`
    (`folder_tree_service.get_detail`). `effective_access` CHỈ trả cho người
    mức Quản lý — người chỉ Xem/Đóng góp không cần biết toàn bộ danh sách ai
    khác đang có quyền trên thư mục này."""
    from .folder_access_service import my_level

    level = my_level(db, user, folder)
    node["my_level"] = level
    node["effective_access"] = list_effective(db, folder) if level >= int(FolderAccessLevel.MANAGE) else []
    return node
