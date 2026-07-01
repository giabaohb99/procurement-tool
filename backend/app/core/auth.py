"""Xác thực (JWT) + phân quyền (RBAC) dùng chung — giống AuthMiddleware."""
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    if not hashed:
        return False
    return pwd_context.verify(raw, hashed)


def _create_token(user_id: int, kind: str, minutes: int) -> str:
    payload = {
        "sub": str(user_id), "type": kind,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_access_token(user_id: int) -> str:
    return _create_token(user_id, "access", settings.ACCESS_EXPIRE_MIN)


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, "refresh", settings.REFRESH_EXPIRE_DAYS * 24 * 60)

def create_reset_token(user_id: int) -> str:
    return _create_token(user_id, "reset_password", 24 * 60)


def decode_token(token: str, expected_type: str) -> int:
    """Giải mã token, kiểm tra đúng loại (access/refresh). Trả user_id."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        if payload.get("type") != expected_type:
            raise HTTPException(401, "Sai loại token")
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(401, "Token không hợp lệ hoặc đã hết hạn")


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    from app.modules.user.model import User

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Thiếu token đăng nhập")
    user_id = decode_token(authorization.split(" ", 1)[1], "access")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "Tài khoản không tồn tại hoặc đã bị khóa")
    return user


def get_user_permissions(db: Session, user) -> dict:
    """Trả về map { entity: {action: bool, scope: str} } gộp từ các vai trò của user."""
    from app.modules.role.model import Permission
    from app.modules.user.model import UserRole
    from app.core.permissions import ACTIONS

    role_ids = [ur.role_id for ur in db.query(UserRole).filter(UserRole.user_id == user.id).all()]
    result: dict = {}
    if not role_ids:
        return result
    perms = db.query(Permission).filter(Permission.role_id.in_(role_ids)).all()
    for p in perms:
        cur = result.setdefault(p.entity, {a: False for a in ACTIONS})
        for a in ACTIONS:
            if getattr(p, f"can_{a}", False):
                cur[a] = True
        cur["scope"] = p.scope
    return result


def user_has_permission(db: Session, user, entity: str, action: str) -> bool:
    perms = get_user_permissions(db, user)
    return bool(perms.get(entity, {}).get(action, False))


def require(entity: str, action: str):
    """Dependency: chặn nếu user không có quyền `action` trên `entity`."""

    def dep(user=Depends(get_current_user), db: Session = Depends(get_db)):
        if not user_has_permission(db, user, entity, action):
            raise HTTPException(403, f"Không có quyền: {action} {entity}")
        return user

    return dep
