from fastapi import APIRouter, Depends, Request, BackgroundTasks, UploadFile, File, HTTPException
import uuid
from sqlalchemy.orm import Session

from app.core.auth import (create_access_token, create_refresh_token,
                           decode_token, get_current_user, get_user_permissions,
                           hash_password, verify_password)
from app.core.audit import record as audit_record
from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.response import success
from app.modules.employee.model import Employee
from app.modules.user.model import User

from . import service
from . import schema, service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    """IP người gọi — ưu tiên X-Forwarded-For (đứng sau nginx/Cloudflare), fallback IP kết nối."""
    xff = request.headers.get("x-forwarded-for", "") if request else ""
    if xff:
        return xff.split(",")[0].strip()[:60]
    return (request.client.host if request and request.client else "")[:60]


def _me_payload(db: Session, user) -> dict:
    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    return {
        "id": user.id,
        "email": user.email,
        "employee_id": user.employee_id,
        "emp_code": emp.code if emp else "",
        "company_id": emp.company_id if emp else 0,
        "full_name": emp.full_name if emp else user.email,
        "avatar": getattr(user, 'avatar', ''),
        "signature": getattr(user, 'signature', ''),
        "phone": emp.phone if emp else "",
        "department_name": emp.department_name if emp else "",
        "role_name": emp.role_name if emp else "",
        "position": emp.position if emp else "",
        "permissions": get_user_permissions(db, user),
    }


@router.post("/login")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login(request: Request, data: schema.LoginInput, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    try:
        user = service.authenticate(db, data.username, data.password)
    except HTTPException as e:
        # Ghi log ĐĂNG NHẬP THẤT BẠI (chống tranh chấp/dò mật khẩu). entity_id=0 vì chưa xác định user.
        audit_record(db, 0, "auth", 0, "login_failed",
                     f"Đăng nhập thất bại: tài khoản '{data.username}' — {e.detail} (IP {ip})")
        raise
    audit_record(db, user.id, "auth", user.id, "login", f"Đăng nhập thành công (IP {ip})")
    return success({
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "user": _me_payload(db, user),
    }, "Đăng nhập thành công")

@router.post("/google")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login_google(request: Request, data: schema.GoogleLoginInput, db: Session = Depends(get_db)):
    user = service.google_login(db, data.credential)
    audit_record(db, user.id, "auth", user.id, "login", f"Đăng nhập Google (IP {_client_ip(request)})")
    return success({
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "user": _me_payload(db, user),
    }, "Đăng nhập Google thành công")


@router.post("/logout")
def logout(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Ghi log ĐĂNG XUẤT. JWT không có phiên phía server nên chỉ ghi nhận thao tác + xóa token ở client."""
    audit_record(db, user.id, "auth", user.id, "logout", f"Đăng xuất (IP {_client_ip(request)})")
    return success(None, "Đã đăng xuất")


@router.post("/refresh")
def refresh(data: schema.RefreshInput, db: Session = Depends(get_db)):
    user_id = decode_token(data.refresh_token, "refresh")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        from fastapi import HTTPException
        raise HTTPException(401, "Tài khoản không hợp lệ")
    # Trả kèm hồ sơ + phân quyền mới nhất (CR-028): client đằng nào cũng gọi refresh
    # mỗi khi access token hết hạn, gửi kèm ở đây thì không tốn thêm request nào,
    # mà đổi tên/gắn nhân sự/sửa quyền vẫn có hiệu lực không cần đăng xuất.
    return success({"access_token": create_access_token(user.id),
                    "user": _me_payload(db, user)})


@router.get("/me")
def me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return success(_me_payload(db, user))


@router.post("/change-password")
def change_password(data: dict, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Người dùng tự đổi mật khẩu (đang đăng nhập). Body: {old_password, new_password}."""
    old = (data.get("old_password") or "").strip()
    new = (data.get("new_password") or "").strip()
    if not verify_password(old, user.password_hash):
        raise HTTPException(400, "Mật khẩu hiện tại không đúng")
    if len(new) < 6:
        raise HTTPException(400, "Mật khẩu mới phải từ 6 ký tự trở lên")
    if verify_password(new, user.password_hash):
        raise HTTPException(400, "Mật khẩu mới không được trùng mật khẩu cũ")
    user.password_hash = hash_password(new)
    db.commit()
    return success(None, "Đã đổi mật khẩu thành công")

@router.post("/avatar")
def update_avatar(file: UploadFile = File(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.core.storage import env_prefix, safe_name, upload_fileobj
    try:
        key = f"{env_prefix()}/avatar/{user.id}/{uuid.uuid4().hex[:12]}-{safe_name(file.filename or 'avatar')}"
        url = upload_fileobj(file.file, key, file.content_type or "")
        user.avatar = url
        db.commit()
        return success({"avatar": url}, "Đã cập nhật ảnh đại diện")
    except Exception as e:
        raise HTTPException(400, f"Lỗi tải ảnh: {str(e)}")


@router.post("/signature")
def update_signature(file: UploadFile = File(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Tải ảnh chữ ký cá nhân (PNG nền trong là đẹp nhất). Mỗi lần tải ghi đè URL cũ."""
    from app.core.storage import env_prefix, safe_name, upload_fileobj
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, "Chữ ký phải là file ảnh (PNG, JPG…).")
    try:
        key = f"{env_prefix()}/signature/{user.id}/{uuid.uuid4().hex[:12]}-{safe_name(file.filename or 'signature')}"
        url = upload_fileobj(file.file, key, file.content_type or "")
        user.signature = url
        db.commit()
        audit_record(db, user.id, "user", user.id, "write", "Cập nhật ảnh chữ ký cá nhân")
        return success({"signature": url}, "Đã cập nhật chữ ký")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Lỗi tải ảnh chữ ký: {str(e)}")


@router.delete("/signature")
def delete_signature(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Gỡ chữ ký khỏi hồ sơ. Chỉ xóa liên kết, file trên storage giữ nguyên (không phá phiếu đã in)."""
    user.signature = ""
    db.commit()
    audit_record(db, user.id, "user", user.id, "write", "Gỡ ảnh chữ ký cá nhân")
    return success({"signature": ""}, "Đã gỡ chữ ký")


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
