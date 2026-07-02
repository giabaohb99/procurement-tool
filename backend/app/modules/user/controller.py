from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import PasswordReset, RoleAssign, ScopeUpdate, UserOut, UserProvision

router = APIRouter(prefix="/api/users", tags=["user"])


@router.get("")
def list_users(
    search: str = "", pg: dict = Depends(pagination), db: Session = Depends(get_db),
    user=Depends(require("user", "read")),
):
    from app.modules.employee.model import Employee
    total, items = service.list_users(db, pg, search)
    out = []
    for u in items:
        d = UserOut.model_validate(u).model_dump()
        d["role_ids"] = service._role_ids(db, u.id)
        emp = db.get(Employee, u.employee_id) if u.employee_id else None
        d["full_name"] = (emp.full_name if emp else "") or u.email or ""
        d["department_name"] = (emp.department_name if emp else "") or ""
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
    service.reset_password(db, user_id, data.new_password, user.id)
    return success(None, "Đã đặt lại mật khẩu")


@router.put("/{user_id}/roles")
def assign_roles(
    user_id: int, data: RoleAssign, db: Session = Depends(get_db),
    user=Depends(require("user", "write")),
):
    service.assign_roles(db, user_id, data, user.id)
    return success(None, "Đã gán vai trò")


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), user=Depends(require("user", "read"))):
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    u = db.get(User, user_id)
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
    return success(service.get_user_scope(db, user_id, role_id))


@router.put("/{user_id}/roles/{role_id}/scope")
def set_scope(user_id: int, role_id: int, data: ScopeUpdate, db: Session = Depends(get_db),
              user=Depends(require("user", "write"))):
    service.set_user_scope(db, user_id, role_id, data, user.id)
    return success(None, "Đã lưu phạm vi")
