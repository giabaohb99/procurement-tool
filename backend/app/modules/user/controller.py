from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import PasswordReset, RoleAssign, UserOut, UserProvision

router = APIRouter(prefix="/api/users", tags=["user"])


@router.get("")
def list_users(
    pg: dict = Depends(pagination), db: Session = Depends(get_db),
    user=Depends(require("user", "read")),
):
    total, items = service.list_users(db, pg)
    out = []
    for u in items:
        d = UserOut.model_validate(u).model_dump()
        d["role_ids"] = service._role_ids(db, u.id)
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
