from fastapi import APIRouter, Depends, Request, BackgroundTasks, UploadFile, File, HTTPException
import uuid
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
from . import schema, service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _me_payload(db: Session, user) -> dict:
    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    return {
        "id": user.id,
        "email": user.email,
        "employee_id": user.employee_id,
        "full_name": emp.full_name if emp else user.email,
        "avatar": getattr(user, 'avatar', ''),
        "phone": emp.phone if emp else "",
        "department_name": emp.department_name if emp else "",
        "permissions": get_user_permissions(db, user),
    }


@router.post("/login")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login(request: Request, data: schema.LoginInput, db: Session = Depends(get_db)):
    user = service.authenticate(db, data.username, data.password)
    return success({
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "user": _me_payload(db, user),
    }, "Đăng nhập thành công")

@router.post("/google")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login_google(request: Request, data: schema.GoogleLoginInput, db: Session = Depends(get_db)):
    user = service.google_login(db, data.credential)
    return success({
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "user": _me_payload(db, user),
    }, "Đăng nhập Google thành công")


@router.post("/refresh")
def refresh(data: schema.RefreshInput, db: Session = Depends(get_db)):
    user_id = decode_token(data.refresh_token, "refresh")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        from fastapi import HTTPException
        raise HTTPException(401, "Tài khoản không hợp lệ")
    return success({"access_token": create_access_token(user.id)})


@router.get("/me")
def me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return success(_me_payload(db, user))

@router.post("/avatar")
def update_avatar(file: UploadFile = File(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.core.storage import upload_fileobj
    try:
        key = f"avatar/{user.id}/{uuid.uuid4().hex}_{file.filename}"
        url = upload_fileobj(file.file, key, file.content_type or "")
        user.avatar = url
        db.commit()
        return success({"avatar": url}, "Đã cập nhật ảnh đại diện")
    except Exception as e:
        raise HTTPException(400, f"Lỗi tải ảnh: {str(e)}")


@router.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(request: Request, data: schema.ForgotPasswordInput, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.is_active:
        return success(None, "Nếu email hợp lệ, hướng dẫn khôi phục mật khẩu đã được gửi.")
        
    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    full_name = emp.full_name if emp else user.email
    
    from app.core.auth import create_reset_token
    token = create_reset_token(user.id)
    
    frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:5173"
    reset_link = f"{frontend_url}/reset-password?token={token}"
    
    from app.modules.notification.service import send_password_reset_email
    send_password_reset_email(db, user.id, background_tasks, full_name, user.email, reset_link)
    
    return success(None, "Nếu email hợp lệ, hướng dẫn khôi phục mật khẩu đã được gửi.")

@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(request: Request, data: schema.ResetPasswordInput, db: Session = Depends(get_db)):
    from app.core.auth import hash_password
    try:
        user_id = decode_token(data.token, "reset_password")
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(400, "Token không hợp lệ hoặc đã hết hạn")
        
    user = db.get(User, user_id)
    if not user or not user.is_active:
        from fastapi import HTTPException
        raise HTTPException(400, "Tài khoản không tồn tại hoặc đã bị khóa")
        
    user.password_hash = hash_password(data.new_password)
    db.commit()
    
    return success(None, "Đặt lại mật khẩu thành công")
