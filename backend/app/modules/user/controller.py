from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core import privilege_escalation
from app.core.response import success
from app.core.scoping import get_perm_profile, get_scoped, scope_condition

from . import service
from .schema import ActiveUpdate, PasswordReset, RoleAssign, ScopeUpdate, UserOut, UserProvision

router = APIRouter(prefix="/api/users", tags=["user"])


def _block_out_of_scope(db, user_id: int, user, action: str):
    """Tài khoản #user_id phải nằm trong phạm vi của người đang thao tác — B-07.

    Danh sách tài khoản là màn nhạy nhất của hệ: các endpoint dưới đây đặt lại mật khẩu,
    gán vai trò, khóa và xóa tài khoản. Trước B-07 entity `user` không có trong
    `SCOPE_FIELDS` nên phạm vi vai trò bị bỏ qua sạch — hẹp tới đâu cũng đụng được mọi
    tài khoản. `tab_user` không có cột pháp nhân (chiều đó nằm ở hồ sơ nhân sự), nên
    `SCOPE_FIELDS["user"]` chỉ khai `self`: `own` = chính mình, `dept`/`company` = chặn.
    """
    from .model import User
    if get_scoped(db, User, "user", user_id, user, get_perm_profile(db, user), action) is None:
        from fastapi import HTTPException
        raise HTTPException(404, "Không tìm thấy tài khoản")


@router.get("")
def list_users(
    search: str = "", department: str = "", role_id: int = 0, sort: str = "", employee_id: int = 0,
    no_role: bool = False, orphan: bool = False,
    pg: dict = Depends(pagination), db: Session = Depends(get_db),
    user=Depends(require("user", "read")),
):
    from app.modules.employee.model import Employee
    from .model import User
    total, items = service.list_users(
        db, pg, search, department, role_id, sort, employee_id, no_role, orphan,
        scope_cond=scope_condition(User, "user", user, get_perm_profile(db, user)))
    out = []
    for u in items:
        d = UserOut.model_validate(u).model_dump()
        d["role_ids"] = service._role_ids(db, u.id)
        emp = db.get(Employee, u.employee_id) if u.employee_id else None
        d["full_name"] = (emp.full_name if emp else "") or u.email or ""
        d["department_name"] = (emp.department_name if emp else "") or ""
        d["code"] = emp.code if emp else ""          # mã nhân sự (rỗng nếu mồ côi)
        d["phone"] = (emp.phone if emp else "") or ""  # SĐT nhân sự — tìm & tự điền tài xế nội bộ
        # Email LIÊN HỆ của nhân sự (khác `email` = email ĐĂNG NHẬP của tài khoản, giữ nguyên).
        d["contact_email"] = (emp.email if emp else "") or ""
        d["avatar"] = u.avatar or ""                 # ảnh: cùng ảnh tài khoản đăng nhập
        d["is_orphan"] = emp is None      # không còn hồ sơ nhân sự -> tài khoản mồ côi
        out.append(d)
    return success({"total": total, "items": out})


@router.post("")
def provision_user(
    data: UserProvision, db: Session = Depends(get_db), user=Depends(require("user", "create"))
):
    u = service.provision_user(db, data, user.id)
    return success(UserOut.model_validate(u).model_dump(), "Đã cấp tài khoản", 201)


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int, data: PasswordReset, db: Session = Depends(get_db),
    user=Depends(require("user", "write")),
):
    _block_out_of_scope(db, user_id, user, "write")
    service.reset_password(db, user_id, data.new_password, user.id)
    return success(None, "Đã đặt lại mật khẩu")


@router.put("/{user_id}/roles")
def assign_roles(
    user_id: int, data: RoleAssign, db: Session = Depends(get_db),
    user=Depends(require("user", "write")),
):
    _block_out_of_scope(db, user_id, user, "write")
    #  Ba chốt chống tự nâng quyền — xem `core/privilege_escalation.py`. Không có
    #  chúng thì bất kỳ ai có `user.write` tự phong quản trị hệ thống bằng đúng
    #  một lần bấm trên chính trang của mình (dựng lại được 25/08/2026).
    privilege_escalation.block_edit_own_permissions(user_id, user)
    privilege_escalation.block_missing_roles(db, data.role_ids)
    privilege_escalation.block_role_escalation(db, user, data.role_ids)
    service.assign_roles(db, user_id, data, user.id)
    return success(None, "Đã gán vai trò")


@router.put("/{user_id}/active")
def set_active(
    user_id: int, data: ActiveUpdate, db: Session = Depends(get_db),
    user=Depends(require("user", "write")),
):
    _block_out_of_scope(db, user_id, user, "write")
    #  Tự khóa mình là tự đá mình ra khỏi hệ: đăng nhập lại không được, mà cửa mở
    #  khóa lại nằm sau đúng cái đăng nhập đó. Người khác gỡ hộ được — trừ khi
    #  người vừa bấm là quản trị duy nhất, lúc đó cả hệ mất đường vào.
    if user_id == user.id and not data.is_active:
        raise HTTPException(
            403, "Không tự khóa tài khoản của chính mình được — khóa xong bạn "
                 "không đăng nhập lại để mở ra được nữa.")
    service.set_active(db, user_id, data.is_active, user.id)
    return success(None, "Đã mở khóa tài khoản" if data.is_active else "Đã khóa tài khoản")


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), user=Depends(require("user", "delete"))):
    _block_out_of_scope(db, user_id, user, "delete")
    service.delete_user(db, user_id, user.id)
    return success(None, "Đã xóa tài khoản")


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), user=Depends(require("user", "read"))):
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    u = get_scoped(db, User, "user", user_id, user, get_perm_profile(db, user))
    if not u:
        from fastapi import HTTPException
        raise HTTPException(404, "Không tìm thấy tài khoản")
    d = UserOut.model_validate(u).model_dump()
    d["role_ids"] = service._role_ids(db, u.id)
    emp = db.get(Employee, u.employee_id) if u.employee_id else None
    d["full_name"] = (emp.full_name if emp else "") or u.email or ""
    d["department_name"] = (emp.department_name if emp else "") or ""
    return success(d)


@router.get("/{user_id}/roles/{role_id}/scope")
def get_scope(user_id: int, role_id: int, db: Session = Depends(get_db), user=Depends(require("user", "read"))):
    _block_out_of_scope(db, user_id, user, "read")
    return success(service.get_user_scope(db, user_id, role_id))


@router.put("/{user_id}/roles/{role_id}/scope")
def set_scope(user_id: int, role_id: int, data: ScopeUpdate, db: Session = Depends(get_db),
              user=Depends(require("user", "write"))):
    _block_out_of_scope(db, user_id, user, "write")
    #  Phạm vi dữ liệu cũng là quyền: tự đặt cho mình `all` là thấy toàn bộ hệ.
    privilege_escalation.block_edit_own_permissions(user_id, user)
    service.set_user_scope(db, user_id, role_id, data, user.id)
    return success(None, "Đã lưu phạm vi")
