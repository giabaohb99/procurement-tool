"""Chốt phạm vi dữ liệu dùng chung cho Mẫu HĐ và HĐLĐ (2 lớp: `require()` ở route + file này).

Luật chung của repo: lấy MỘT dòng theo id PHẢI qua `get_scoped`, không `db.get` — nếu không thì
gõ id vào URL là bỏ qua phạm vi. Ngoài phạm vi trả 404 như id không tồn tại.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.scoping import apply_scope, get_scoped


def has_perm(profile: dict, entity: str, action: str) -> bool:
    """Vai trò của người này có `action` trên `entity` (không xét phạm vi)."""
    return bool(((profile or {}).get("perms_union") or {}).get(entity, {}).get(action, False))


def get_or_404_scoped(db: Session, model, entity: str, oid: int, user, profile: dict,
                      action: str = "read", message: str = "Không tìm thấy", lock: bool = False):
    """`lock=True` (đường GHI): sau khi qua chốt phạm vi, khóa dòng `FOR UPDATE` và nạp lại giá trị
    mới nhất — hai người chuyển trạng thái / sửa / xóa cùng lúc thì người sau chờ rồi đọc trạng thái
    SAU lệnh của người trước (không đè nhau). SQLite (test) bỏ qua FOR UPDATE, đường code vẫn chạy."""
    obj = get_scoped(db, model, entity, oid, user, profile, action)
    if obj is None:
        raise HTTPException(404, message)
    if lock:
        obj = (db.query(model).filter(model.id == oid).with_for_update()
               .populate_existing().first())
        if obj is None:   # vừa bị người khác xóa trong lúc chờ khóa
            raise HTTPException(404, message)
    return obj


def ensure_created_in_scope(db: Session, model, entity: str, row, user, profile: dict,
                            message: str) -> None:
    """Dòng MỚI phải nằm trong phạm vi `create` của người tạo.

    Dòng chưa có thì `get_scoped` không hỏi được ⇒ `flush()` để có id rồi hỏi lại; không thấy →
    rollback toàn bộ + 403. Nơi gọi phải `db.add(row)` trước và set `created_by`.
    """
    db.flush()
    if get_scoped(db, model, entity, row.id, user, profile, "create") is None:
        db.rollback()
        raise HTTPException(403, message)


def can_create_for(db: Session, model, entity: str, row, user, profile: dict) -> bool:
    """Hỏi trước «nếu lập dòng `row` thì có nằm trong phạm vi `create` không» — KHÔNG ghi gì.

    Dùng cho ô chọn mẫu theo nhân sự: phải cùng luật với lúc lập thật (`ensure_created_in_scope`),
    nên dựng dòng tạm trong SAVEPOINT, hỏi `get_scoped` rồi hủy savepoint.
    """
    savepoint = db.begin_nested()
    try:
        db.add(row)
        db.flush()
        return get_scoped(db, model, entity, row.id, user, profile, "create") is not None
    finally:
        savepoint.rollback()


def ids_allowed(db: Session, model, entity: str, ids: list[int], user, profile: dict,
                action: str) -> set[int]:
    """Trong `ids`, những dòng người này làm được `action` — MỘT truy vấn cho cả trang
    (cờ `can_*` của danh sách; không gọi `get_scoped` từng dòng)."""
    if not ids or not has_perm(profile, entity, action):
        return set()
    q = apply_scope(db.query(model.id).filter(model.id.in_(ids)), model, entity, user, profile, action)
    return {i for (i,) in q.all()}
