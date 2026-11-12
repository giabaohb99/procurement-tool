"""Quyền trên KIÊM NHIỆM — cờ `can_edit` / `can_open_files` và gác TỆP quyết định (duoc-CR-755).

Không entity RBAC mới — tái dùng `employee` / `employee_sensitive`. Khác quá trình công tác
một điểm: L1 KHÔNG miễn cho quản trị (như `block_edit_own_department`) — không ai tự sửa kiêm
nhiệm của chính mình, kể cả tệp quyết định.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.scoping import get_scoped

from . import department_service, sensitive
from .concurrent_model import EmployeeConcurrent
from .model import Employee
from .work_history_access import check_file_read_scope, is_own_profile


def can_edit(db: Session, user, profile: dict, eid: int) -> bool:
    """Có `employee.write` đúng phạm vi trên hồ sơ VÀ không phải hồ sơ của chính mình (L1).

    Cờ cấp hồ sơ; việc gán từng cặp (phòng, công ty) còn qua L2 ở lúc ghi.
    """
    if is_own_profile(user, eid):
        return False
    return get_scoped(db, Employee, "employee", eid, user, profile, "write") is not None


def can_open_files(profile: dict, eid: int) -> bool:
    """= `can_read_sensitive` (đã gồm ngoại lệ chính chủ)."""
    return sensitive.can_read_sensitive(profile, eid)


def block_delete_without_sensitive(db: Session, user, row: EmployeeConcurrent) -> None:
    """Xóa dòng của NGƯỜI KHÁC kéo theo xóa tệp quyết định → phải có quyền MỞ tệp đó, không thì
    xóa dòng là đường vòng xóa tệp nhạy cảm mà chính mình không xem được."""
    from app.modules.attachment.model import FileLink

    has_file = db.query(FileLink.id).filter(
        FileLink.entity == "employee_concurrent", FileLink.entity_id == row.id).first() is not None
    if not has_file:
        return
    from app.core.auth import get_perm_profile
    if not sensitive.can_read_sensitive(get_perm_profile(db, user), row.employee_id):
        raise HTTPException(
            403, "Dòng này có tệp quyết định (nhạy cảm) đính kèm — cần quyền xem nhạy cảm "
                 "(employee_sensitive.read) để xóa")


def check_file(db: Session, user, entity: str, entity_id: int | None, mode: str) -> bool:
    """Gác riêng TỆP của dòng kiêm nhiệm — gọi ở đầu `attachment/controller._check`.

    Chỉ chạm khi `entity == "employee_concurrent"` VÀ đã có `entity_id` (tải tệp TẠM chưa gắn
    thì rơi về luồng thường). `True` = đã xét xong; `False` = chưa quyết, `_check` đi tiếp.
    """
    if entity != "employee_concurrent" or entity_id is None:
        return False

    row = db.get(EmployeeConcurrent, entity_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy dòng kiêm nhiệm")

    if is_own_profile(user, row.employee_id):
        if mode == "read":
            return True   # chính chủ luôn đọc được tệp của mình
        raise HTTPException(403, "Không tự gắn/gỡ tệp quyết định kiêm nhiệm của chính mình được")

    #  Dòng của NGƯỜI KHÁC: đọc hay ghi đều đòi thêm `employee_sensitive.read`.
    from app.core.auth import get_perm_profile
    profile = get_perm_profile(db, user)
    if not sensitive.can_read_sensitive(profile, row.employee_id):
        raise HTTPException(
            403, "Bạn không có quyền xem tệp quyết định (nhạy cảm) của hồ sơ nhân sự này")
    if mode != "read":
        #  Gắn/gỡ cần THẬT `employee.write` (nhánh chung của `_check` chấp nhận cả `create`,
        #  là quyền tạo hồ sơ mới — không phải quyền sửa hồ sơ người khác) + L2 theo cặp.
        if get_scoped(db, Employee, "employee", row.employee_id, user, profile, "write") is None:
            raise HTTPException(
                403, "Cần quyền sửa hồ sơ nhân sự (employee.write, đúng phạm vi) để gắn/gỡ "
                     "tệp quyết định của người khác")
        department_service.block_out_of_scope_pair(db, [(row.department_id, row.company_id)], profile)
        return True
    #  Đọc: tự xét phạm vi hồ sơ CÓ nhánh kiêm nhiệm (Q1) — luồng thường không biết nhánh đó.
    check_file_read_scope(db, user, profile, row.employee_id)
    return True
