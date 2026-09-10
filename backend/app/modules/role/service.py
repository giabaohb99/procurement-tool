from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import perm_cache_clear
from app.core.permissions import ACTIONS
from .model import Permission, Role
from .schema import PermissionUpdate, RoleCreate, RoleUpdate


def list_roles_query(db: Session):
    """Query thô để controller còn gắn thêm bộ lọc (apply_filters) trước khi .all()."""
    return db.query(Role).order_by(Role.id)


def list_roles(db: Session):
    return list_roles_query(db).all()


def get_role(db: Session, rid: int) -> Role:
    obj = db.get(Role, rid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy vai trò")
    return obj


def create_role(db: Session, data: RoleCreate, user_id: int) -> Role:
    if db.query(Role).filter(Role.code == data.code).first():
        raise HTTPException(400, "Mã vai trò đã tồn tại")
    obj = Role(code=data.code, name=data.name, description=data.description, created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, "role", obj.id, "create", f"Tạo vai trò {obj.name or obj.code}",
           doc_code=obj.code or "")
    return obj


def update_role(db: Session, rid: int, data: RoleUpdate, user_id: int) -> Role:
    obj = get_role(db, rid)
    changes = data.model_dump(exclude_unset=True)
    #  Kể tên ô vừa đổi. Không kèm giá trị cũ — đó là việc của `tab_change_log`
    #  (P4); chép sang đây là hai chỗ cùng giữ một sự thật rồi lệch nhau.
    for key, value in changes.items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, "role", rid, "update",
           f"Sửa vai trò {obj.name or obj.code}: " + ", ".join(sorted(changes)),
           doc_code=obj.code or "")
    return obj


def delete_role(db: Session, rid: int, user_id: int) -> None:
    obj = get_role(db, rid)
    # So sánh KHÔNG phân biệt hoa/thường: vai trò chuẩn trên DB có code là 'admin' (chữ thường),
    # danh sách chặn trước đây viết hoa nên không khớp -> vẫn xóa được vai trò quản trị hệ thống.
    if (obj.code or "").strip().upper() in ("ADMIN", "ADMINISTRATOR"):
        raise HTTPException(400, "Không được xóa vai trò mặc định của hệ thống")

    #  Đọc tên TRƯỚC khi xóa: sau `db.delete` + `commit` thì `obj` là bản ghi đã
    #  hết hạn, đụng vào thuộc tính nào cũng ném `ObjectDeletedError`.
    label, code = obj.name or obj.code, obj.code or ""

    db.query(Permission).filter(Permission.role_id == rid).delete()
    db.delete(obj)
    db.commit()
    record(db, user_id, "role", rid, "delete", f"Xóa vai trò {label}", doc_code=code)


def get_permissions(db: Session, rid: int):
    get_role(db, rid)
    return db.query(Permission).filter(Permission.role_id == rid).all()


#  ⚠️ CHỖ NÀY TỪNG KHÔNG CÓ MỘT DÒNG NHẬT KÝ NÀO (bao-CR-346).
#  `PUT /api/roles/{rid}/permissions` viết lại TOÀN BỘ ma trận quyền của một vai
#  trò — thao tác nguy hiểm nhất hệ thống, hơn cả xóa phiếu — mà cả phân hệ
#  `role/` lẫn `user/` không có lấy một lời gọi `record(...)`. Nghĩa là câu hỏi
#  *"ai đã cấp cho tài khoản này quyền duyệt đơn hàng, và lúc nào"* trước đây
#  không trả lời được bằng dữ liệu.
#  Ghi cả CÁI GÌ đổi chứ không chỉ "đã cập nhật phân quyền": bảng gửi lên có
#  ~55 dòng entity × 8 hành động, đọc lại nguyên bản chụp thì không ai thấy được
#  một ô vừa được tick thêm. Cái đáng đọc là **phần chênh**.
def _permission_matrix(perms) -> dict[str, set[str]]:
    """Danh sách dòng quyền -> `{entity: {hành động được phép}}`, để đem so."""
    return {p.entity: {a for a in ACTIONS if getattr(p, f"can_{a}", False)} for p in perms}


def _scope_map(perms) -> dict[str, str]:
    return {p.entity: (p.scope or "") for p in perms}


def describe_permission_change(before, after) -> str:
    """Câu tiếng Việt kể phần CHÊNH giữa hai ma trận quyền.

    Rỗng nghĩa là bấm Lưu nhưng không đổi gì — vẫn ghi một dòng nhật ký, vì
    *"người này có mở màn phân quyền ra và bấm Lưu"* cũng là dữ kiện.
    """
    old_matrix, new_matrix = _permission_matrix(before), _permission_matrix(after)
    old_scope, new_scope = _scope_map(before), _scope_map(after)

    granted, revoked, scoped = [], [], []
    for entity in sorted(set(old_matrix) | set(new_matrix)):
        was, now = old_matrix.get(entity, set()), new_matrix.get(entity, set())
        if now - was:
            granted.append(f"{entity}.{'/'.join(sorted(now - was))}")
        if was - now:
            revoked.append(f"{entity}.{'/'.join(sorted(was - now))}")
        old_s, new_s = old_scope.get(entity, ""), new_scope.get(entity, "")
        if entity in new_matrix and entity in old_matrix and old_s != new_s:
            scoped.append(f"{entity}: {old_s or 'trống'} -> {new_s or 'trống'}")

    parts = []
    if granted:
        parts.append("Cấp thêm " + ", ".join(granted))
    if revoked:
        parts.append("Thu hồi " + ", ".join(revoked))
    if scoped:
        parts.append("Đổi phạm vi " + "; ".join(scoped))
    return ". ".join(parts)


def set_permissions(db: Session, rid: int, data: PermissionUpdate, user_id: int):
    obj = get_role(db, rid)
    #  Chụp TRƯỚC khi xóa. `_permission_matrix` bóc ra dict thuần chứ không giữ
    #  đối tượng ORM: giữ đối tượng thì `delete()` ngay dưới làm chúng thành bản
    #  ghi đã xóa, và lúc đọc lại để so thì SQLAlchemy trả về rỗng.
    before = [SimpleNamespace(entity=p.entity, scope=p.scope,
                              **{f"can_{a}": getattr(p, f"can_{a}", False) for a in ACTIONS})
              for p in get_permissions(db, rid)]

    db.query(Permission).filter(Permission.role_id == rid).delete()
    for item in data.permissions:
        db.add(Permission(role_id=rid, created_by=user_id, updated_by=user_id, **item.model_dump()))
    db.commit()
    perm_cache_clear()  # quyền vừa đổi → nạp lại ở request sau

    after = get_permissions(db, rid)
    detail = describe_permission_change(before, after)
    record(db, user_id, "role", rid, "set_permissions",
           f"Phân quyền vai trò {obj.name or obj.code}"
           + (f": {detail}" if detail else " (bấm Lưu, không có ô nào đổi)"),
           doc_code=obj.code or "")
    return after
