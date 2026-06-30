from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import (create_access_token, create_refresh_token,
                           decode_token, get_current_user, get_user_permissions)
from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.response import success
from app.modules.employee.model import Employee
from app.modules.user.model import User

from . import service
from .schema import LoginInput, RefreshInput

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _me_payload(db: Session, user) -> dict:
    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    return {
        "id": user.id,
        "email": user.email,
        "employee_id": user.employee_id,
        "full_name": emp.full_name if emp else user.email,
        "permissions": get_user_permissions(db, user),
    }


@router.post("/login")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login(request: Request, data: LoginInput, db: Session = Depends(get_db)):
    user = service.authenticate(db, data.username, data.password)
    return success({
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "user": _me_payload(db, user),
    }, "Đăng nhập thành công")


@router.post("/refresh")
def refresh(data: RefreshInput, db: Session = Depends(get_db)):
    user_id = decode_token(data.refresh_token, "refresh")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        from fastapi import HTTPException
        raise HTTPException(401, "Tài khoản không hợp lệ")
    return success({"access_token": create_access_token(user.id)})


@router.get("/me")
def me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return success(_me_payload(db, user))
