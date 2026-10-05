"""Quyền trên QUÁ TRÌNH CÔNG TÁC — tự sửa (Q3), cờ `can_edit`/`can_open_files`
(A9), gác tệp QĐ (Q4). Không entity RBAC mới — tái dùng `employee`/`employee_sensitive`.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.privilege_escalation import is_system_admin
from app.core.scoping import get_scoped

from . import sensitive
from .model import Employee
from .work_history_model import EmployeeWorkHistory


def employee_in_scope(db: Session, eid: int, user, profile: dict, action: str = "read") -> Employee:
    """Hồ sơ nằm trong phạm vi — khuôn `employee.controller._employee_in_scope`,
    tách riêng ở đây vì phase này không sửa `employee/controller.py` (ngoài
    phạm vi «File Ownership»)."""
    obj = get_scoped(db, Employee, "employee", eid, user, profile, action)
    if obj is None:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    return obj


def is_own_profile(user, eid: int) -> bool:
    mine = int(getattr(user, "employee_id", 0) or 0)
    return bool(mine) and mine == int(eid)


def block_self_write(db: Session, user, eid: int) -> None:
    """Q3 — chặn HR tự ghi/sửa/xóa/áp quá trình công tác của chính mình, trừ
    quản trị hệ thống. Gọi ở MỌI cửa ghi của work-history (tệp đính kèm có
    chốt riêng ở `check_file` dưới)."""
    if is_own_profile(user, eid) and not is_system_admin(db, user.id):
        raise HTTPException(
            403, "Không tự ghi/sửa quá trình công tác của chính mình được — "
                 "nhờ một quản trị khác thao tác.")


def can_edit(db: Session, user, profile: dict, eid: int) -> bool:
    """Cờ `can_edit` (A9): có `employee.write` phạm vi write trên hồ sơ, VÀ
    (không phải hồ sơ của chính mình HOẶC là quản trị hệ thống)."""
    if get_scoped(db, Employee, "employee", eid, user, profile, "write") is None:
        return False
    if is_own_profile(user, eid) and not is_system_admin(db, user.id):
        return False
    return True


def can_open_files(profile: dict, eid: int) -> bool:
    """Cờ `can_open_files` (A9) = `can_read_sensitive` (đã gồm ngoại lệ chính chủ)."""
    return sensitive.can_read_sensitive(profile, eid)


def block_delete_without_sensitive(db: Session, user, row: EmployeeWorkHistory) -> None:
    """M2 (review 03/10/2026) — xoá một DÒNG của NGƯỜI KHÁC kéo theo xoá TỆP QĐ
    đính kèm (`work_history_service.delete` gọi `delete_attachments_for`). Mở
    tệp đó cần thêm `employee_sensitive.read` (Q4/`check_file`) — thiếu chốt
    này, một người có `employee.write` nhưng KHÔNG có `employee_sensitive.read`
    vẫn xoá được dòng, và tệp biến mất theo: một đường vòng xoá tệp nhạy cảm mà
    chính người đó không có quyền MỞ. Chính chủ không bị chặn (Q3 — tự xoá dòng
    của mình đã chặn ở `block_self_write` từ trước, trừ quản trị)."""
    if is_own_profile(user, row.employee_id):
        return
    from app.modules.attachment.model import FileLink
    has_file = db.query(FileLink).filter(
        FileLink.entity == "employee_work_history", FileLink.entity_id == row.id).first() is not None
    if not has_file:
        return
    from app.core.auth import get_perm_profile
    if not sensitive.can_read_sensitive(get_perm_profile(db, user), row.employee_id):
        raise HTTPException(
            403, "Dòng này có tệp quyết định (nhạy cảm) đính kèm — cần quyền xem nhạy cảm "
                 "(employee_sensitive.read) để xoá")


def check_file(db: Session, user, entity: str, entity_id: int | None, mode: str) -> bool:
    """Gác riêng TỆP của dòng quá trình công tác (Q4) — gọi ở ĐẦU
    `attachment/controller._check`. Chỉ chạm khi `entity == "employee_work_history"`
    VÀ đã có `entity_id` (tải file TẠM chưa gắn thì bỏ qua, rơi về luồng
    thường như mọi entity khác).

    Trả `True` = ĐÃ XÉT XONG, `_check` trả ngay (chính chủ ĐỌC tệp của mình,
    không cần `employee.read`). Trả `False` = chưa quyết, `_check` tiếp tục
    luồng thường (`employee.read`/`write` + `ensure_in_scope`). Có thể ném
    403/404 thẳng khi đã đủ dữ kiện để từ chối.
    """
    if entity != "employee_work_history" or entity_id is None:
        return False

    row = db.get(EmployeeWorkHistory, entity_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy dòng quá trình công tác")

    if is_own_profile(user, row.employee_id):
        if mode == "read":
            return True   # chính chủ luôn đọc được tệp của mình (Q4)
        if not is_system_admin(db, user.id):
            raise HTTPException(
                403, "Không tự gắn/gỡ tệp quyết định vào quá trình công tác của chính mình được")
        return False   # quản trị — rơi về luồng thường (employee.write + phạm vi)

    #  Dòng của NGƯỜI KHÁC: đọc hay ghi đều đòi thêm `employee_sensitive.read`
    #  — không cho gỡ/gắn tệp mà chính mình không được xem.
    from app.core.auth import get_perm_profile
    profile = get_perm_profile(db, user)
    if not sensitive.can_read_sensitive(profile, row.employee_id):
        raise HTTPException(
            403, "Bạn không có quyền xem tệp quyết định (nhạy cảm) của hồ sơ nhân sự này")
    if mode != "read":
        #  M3 (review 03/10/2026) — gắn/gỡ tệp QĐ của NGƯỜI KHÁC phải có thật
        #  `employee.write` (kèm phạm vi). Nhánh CHUNG của `_check` chấp nhận
        #  `write HOẶC create` (đúng cho entity cha bình thường), nhưng `create`
        #  là quyền TẠO một hồ sơ MỚI — không phải quyền sửa hồ sơ người khác
        #  đang có. Thiếu chốt này, một vai trò chỉ có `employee.create` +
        #  `employee_sensitive.read` vẫn gắn/gỡ được tệp QĐ của bất kỳ ai.
        if get_scoped(db, Employee, "employee", row.employee_id, user, profile, "write") is None:
            raise HTTPException(
                403, "Cần quyền sửa hồ sơ nhân sự (employee.write, đúng phạm vi) để gắn/gỡ "
                     "tệp quyết định của người khác")
        return True   # đã đủ sensitive + write — khỏi rơi về nhánh chung (vốn chấp nhận cả create)
    return False   # đọc — rơi về luồng thường (employee.read + phạm vi)
