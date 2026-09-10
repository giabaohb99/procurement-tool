from fastapi import APIRouter, Depends, Request, BackgroundTasks, UploadFile, File, HTTPException
import uuid
from sqlalchemy.orm import Session

from app.core.auth import (SESSION_EXPIRED_MESSAGE, create_access_token, create_refresh_token,
                           decode_token, decode_token_claims, get_current_user,
                           get_user_permissions, hash_password, verify_password)
from app.core.audit import record as audit_record
from app.core.client_ip import get_client_ip
from app.core.config import settings
from app.core.database import get_db
from app.core.device_fingerprint import MAX_USER_AGENT
from app.core.limiter import limiter
from app.core.request_context import get_context
from app.core.response import success
from app.modules.employee.model import Employee
from app.modules.login_session.constants import LoginMethod, RevokeReason
from app.modules.login_session.model import LoginSession
from app.modules.login_session.service import (mark_refreshed, revoke_session,
                                               revoke_user_sessions, start_session)
from app.modules.user.model import User, UserRole
from app.modules.user_preference.service import get_preferences

from . import service
from . import schema, service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    """IP người gọi. bao-CR-313: bản cũ lấy phần tử ĐẦU của X-Forwarded-For — phần
    client tự đặt được — nên dòng `login_failed` ghi IP giả. Nay dùng chung một hàm
    với limiter (`core/client_ip.py`, ưu tiên `CF-Connecting-IP`)."""
    return get_client_ip(request) if request else ""


def _user_agent(request: Request) -> str:
    return (request.headers.get("user-agent") or "")[:MAX_USER_AGENT] if request else ""


def _bind_session(session_id: int) -> None:
    """Gắn phiên vừa mở/vừa tra vào ngữ cảnh lượt gọi (bao-CR-360).

    Bốn đường trong tệp này (`/login`, `/google`, `/refresh`) là **đường công
    khai** — không đi qua `get_current_user`, nên không ai điền `ctx.session_id`
    hộ. Thiếu dòng này thì chính dấu vết `login` — dòng quan trọng nhất của cả
    phiên — lại là dòng duy nhất không biết nó thuộc phiên nào.
    """
    ctx = get_context()
    if ctx:
        ctx.session_id = int(session_id)


def _open_session(db: Session, request: Request, user, login_method: int) -> LoginSession:
    """Mở phiên + gắn ngữ cảnh, dùng chung cho đăng nhập mật khẩu và Google."""
    session = start_session(db, user, ip=_client_ip(request),
                            user_agent=_user_agent(request), login_method=login_method)
    _bind_session(session.id)
    return session


def _me_payload(db: Session, user) -> dict:
    emp = db.get(Employee, user.employee_id) if user.employee_id else None

    #  Vai trò THẬT nằm ở tab_user_role (CR-022 đã bỏ cột tab_employee.role_name),
    #  nên phải join ra TÊN — trước đây trả cột chết luôn rỗng nên hồ sơ hiện
    #  "Chưa cập nhật".
    role_ids = sorted(
        row[0] for row in db.query(UserRole.role_id).filter(UserRole.user_id == user.id).all())
    role_names: list[str] = []
    if role_ids:
        from app.modules.role.model import Role
        role_names = [r[0] for r in db.query(Role.name)
                      .filter(Role.id.in_(role_ids)).order_by(Role.name).all()]

    #  Vị này có hồ sơ TÀI XẾ (tab_driver.user_id) hay không — để mở đúng mục
    #  "Chuyến của tôi" (Đặt xe) cho tài xế mà không phải join lại ở FE. Điều phối
    #  viên nhận ra qua quyền `vehicle_booking.approve`, nên chỉ cần cờ này cho lái xe.
    from app.modules.vehicle_booking.model import Driver
    is_driver = db.query(Driver.id).filter(Driver.user_id == user.id).first() is not None

    #  Kiêm nhiệm = các phòng PHỤ (is_primary=False) của nhân sự — tái dùng
    #  tab_employee_department, hiển thị dưới Vị trí/Chức vụ ở Trang cá nhân.
    kiem_nhiem: list[str] = []
    if emp:
        from app.modules.department.model import Department
        from app.modules.employee.department_model import EmployeeDepartment
        extra_ids = [row[0] for row in db.query(EmployeeDepartment.department_id).filter(
            EmployeeDepartment.employee_id == emp.id,
            EmployeeDepartment.is_primary.is_(False)).all()]
        if extra_ids:
            kiem_nhiem = [r[0] for r in db.query(Department.name)
                          .filter(Department.id.in_(extra_ids)).order_by(Department.name).all()]

    return {
        "id": user.id,
        "email": user.email,
        "employee_id": user.employee_id,
        "emp_code": emp.code if emp else "",
        "company_id": emp.company_id if emp else 0,
        "company_name": emp.company_name if emp else "",
        "full_name": emp.full_name if emp else user.email,
        "avatar": getattr(user, 'avatar', ''),
        "signature": getattr(user, 'signature', ''),
        "notify_email": bool(getattr(user, 'notify_email', True)),
        "phone": emp.phone if emp else "",
        #  CẢ id lẫn tên: màn Tạo văn bản tự điền ô «Phòng chủ trì» theo phòng
        #  của người đang đăng nhập, mà dò theo TÊN thì sai — một tên phòng có
        #  mặt ở nhiều pháp nhân (xem `department/service.py`).
        "department_id": emp.department_id if emp else 0,
        "department_name": emp.department_name if emp else "",
        #  role_name giữ cho tương thích cũ = nối tên các vai trò thật.
        "role_name": ", ".join(role_names),
        "role_names": role_names,
        "position": emp.position if emp else "",
        "kiem_nhiem": kiem_nhiem,
        #  Có hồ sơ tài xế không — FE dùng để hiện mục "Chuyến của tôi" cho lái xe.
        "is_driver": is_driver,
        #  Vai trò ĐANG GIỮ, không phải quyền. Màn Phân quyền cần nó để khóa ma
        #  trận của chính vai trò mình đang giữ — backend đã chặn cửa đó
        #  (`privilege_escalation`), nhưng để người dùng tick thoải mái rồi mới
        #  ăn 403 lúc bấm Lưu thì họ tưởng hệ hỏng, không tưởng là có luật.
        "role_ids": role_ids,
        "permissions": get_user_permissions(db, user),
        #  Tuỳ chọn hiển thị cá nhân (hiện có: bảng màu giao diện). Gửi kèm ở đây
        #  chứ không để client gọi thêm một vòng: nó cần NGAY ở khung hình đầu
        #  tiên, gọi sau thì người dùng thấy màu mặc định lóe lên rồi mới nhảy
        #  sang màu họ chọn. `refresh` cũng đi qua payload này nên đổi bảng màu ở
        #  máy khác là lần làm mới token kế tiếp đã đồng bộ.
        "preferences": get_preferences(db, user.id),
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
    session = _open_session(db, request, user, LoginMethod.PASSWORD)
    audit_record(db, user.id, "auth", user.id, "login",
                 f"Đăng nhập thành công (IP {ip}) — {session.device_label}")
    return success({
        "access_token": create_access_token(user.id, session.token_id, session.token_version),
        "refresh_token": create_refresh_token(user.id, session.token_id, session.token_version),
        "user": _me_payload(db, user),
    }, "Đăng nhập thành công")

@router.post("/google")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login_google(request: Request, data: schema.GoogleLoginInput, db: Session = Depends(get_db)):
    user = service.google_login(db, data.credential)
    session = _open_session(db, request, user, LoginMethod.GOOGLE)
    audit_record(db, user.id, "auth", user.id, "login",
                 f"Đăng nhập Google (IP {_client_ip(request)}) — {session.device_label}")
    return success({
        "access_token": create_access_token(user.id, session.token_id, session.token_version),
        "refresh_token": create_refresh_token(user.id, session.token_id, session.token_version),
        "user": _me_payload(db, user),
    }, "Đăng nhập Google thành công")


@router.post("/logout")
def logout(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Đăng xuất — bao-CR-360 khiến việc này **có hiệu lực thật** (đóng BM-002).

    Trước đây đây chỉ là một dòng nhật ký: JWT không có phiên phía máy chủ nên
    vé vẫn sống tới lúc hết hạn, và người mượn máy người khác bấm *Đăng xuất*
    rồi bỏ đi thực ra chưa đăng xuất. Nay phiên bị đánh dấu thu hồi, vé của
    riêng thiết bị này chết ngay; các thiết bị khác không bị đụng tới.
    """
    ctx = get_context()
    session = db.get(LoginSession, ctx.session_id) if (ctx and ctx.session_id) else None
    if session:
        revoke_session(db, session, RevokeReason.SELF_LOGOUT, user.id)
    audit_record(db, user.id, "auth", user.id, "logout", f"Đăng xuất (IP {_client_ip(request)})")
    return success(None, "Đã đăng xuất")


@router.post("/refresh")
def refresh(request: Request, data: schema.RefreshInput, db: Session = Depends(get_db)):
    #  bao-CR-313 / BM-003: trước đây gia hạn KHÔNG ghi dấu vết và không lấy IP — refresh
    #  token bị cắp tự gia hạn im lặng suốt 7 ngày, không dòng nào để mà thấy. Nay mỗi
    #  lần gia hạn (thành công lẫn thất bại) là một dòng `auth` kèm IP, đọc cùng chỗ với
    #  `login` / `login_failed`.
    ip = _client_ip(request)
    try:
        claims = decode_token_claims(data.refresh_token, "refresh")
    except HTTPException as e:
        audit_record(db, 0, "auth", 0, "refresh_failed",
                     f"Gia hạn phiên thất bại: {e.detail} (IP {ip})")
        raise
    user_id = int(claims["sub"])
    user = db.get(User, user_id)
    if not user or not user.is_active:
        audit_record(db, user_id, "auth", user_id, "refresh_failed",
                     f"Gia hạn phiên thất bại: tài khoản không tồn tại hoặc đã bị khóa (IP {ip})")
        raise HTTPException(401, "Tài khoản không hợp lệ")

    #  bao-CR-360: gia hạn cũng phải qua cửa phiên, không thì thu hồi vô nghĩa —
    #  vé truy cập chết sau 30 phút nhưng refresh token vẫn tự đẻ vé mới suốt 7
    #  ngày. Ở đây KHÔNG dùng `resolve_session`: hàm đó có đệm 60 giây, mà cửa
    #  duy nhất giữ được refresh token bị cắp thì không nên có độ trễ nào.
    token_id = str(claims.get("jti") or "")
    session = (db.query(LoginSession).filter(LoginSession.token_id == token_id).first()
               if token_id else None)
    if (not session or session.revoked_at is not None or session.user_id != user.id
            or int(claims.get("ver") or 0) != int(user.token_version or 1)):
        audit_record(db, user.id, "auth", user.id, "refresh_failed",
                     f"Gia hạn phiên thất bại: phiên đã kết thúc (IP {ip})")
        raise HTTPException(401, SESSION_EXPIRED_MESSAGE)
    _bind_session(session.id)

    #  Đổi IP giữa phiên là dấu hiệu đáng xem — có thể chỉ là đổi wifi sang 4G,
    #  cũng có thể là vé đã sang tay. Vẫn cho gia hạn (chặn thì người đi tàu
    #  đăng nhập lại mười lần một ngày), nhưng để lại dòng đọc được.
    if session.last_seen_ip and session.last_seen_ip != ip:
        audit_record(db, user.id, "auth", user.id, "refresh_ip_changed",
                     f"Phiên gia hạn từ IP khác: {session.last_seen_ip} -> {ip}")
    #  QĐ-A: gia hạn THÀNH CÔNG không còn đẻ dòng nhật ký (46.000 dòng rác mỗi
    #  năm, không dòng nào ai đọc). Thay bằng hai cột đếm trên chính dòng phiên;
    #  thất bại và đổi IP thì vẫn ghi như cũ.
    mark_refreshed(db, session.id, ip)
    # Trả kèm hồ sơ + phân quyền mới nhất (CR-028): client đằng nào cũng gọi refresh
    # mỗi khi access token hết hạn, gửi kèm ở đây thì không tốn thêm request nào,
    # mà đổi tên/gắn nhân sự/sửa quyền vẫn có hiệu lực không cần đăng xuất.
    return success({"access_token": create_access_token(user.id, session.token_id,
                                                        session.token_version),
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
    #  bao-CR-360: đổi mật khẩu thì cắt mọi thiết bị KHÁC — nếu ai đó đang mượn
    #  phiên của mình thì đây chính là động tác người dùng làm để đuổi họ ra.
    #
    #  ⚠️ Cố ý KHÔNG tăng `token_version` (khác bản thiết kế §5 viết ban đầu):
    #  tăng là giết cả vé đang cầm, tức bấm «Đổi mật khẩu» xong bị đá ra màn
    #  đăng nhập. Giữ phiên hiện tại sống nên chấp nhận độ trễ tối đa 60 giây
    #  của đệm tra phiên ở các tiến trình uvicorn khác.
    ctx = get_context()
    revoke_user_sessions(db, user.id, RevokeReason.PASSWORD_CHANGED, user.id,
                         except_session_id=(ctx.session_id if ctx else 0) or 0)
    return success(None, "Đã đổi mật khẩu thành công")

@router.put("/notify-email")
def set_my_notify_email(data: schema.NotifyEmailInput, user=Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """Người dùng tự bật/tắt email thông báo luồng duyệt của chính mình (bao-CR-349).

    Tắt rồi thì mọi việc cần duyệt chỉ còn thấy ở chuông trong app và thông báo đẩy —
    giao diện phải nói rõ điều đó trước khi người ta tắt."""
    user.notify_email = data.notify_email
    db.commit()
    audit_record(db, user.id, "user", user.id, "write",
                 "Tự bật email thông báo" if data.notify_email else "Tự tắt email thông báo")
    return success({"notify_email": data.notify_email},
                   "Đã bật email thông báo" if data.notify_email else "Đã tắt email thông báo")


@router.post("/avatar")
def update_avatar(file: UploadFile = File(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.modules.user.service import set_user_avatar
    try:
        url = set_user_avatar(db, user, fileobj=file.file, filename=file.filename or "avatar",
                              content_type=file.content_type or "", actor_id=user.id)
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

    #  bao-CR-360: khác đổi mật khẩu, ở đây KHÔNG chừa phiên nào — người đi
    #  đường này thường là người vừa mất quyền kiểm soát tài khoản, và cái họ
    #  cần chính là đá sạch mọi thiết bị đang đăng nhập. `force_relogin` tăng
    #  `token_version` nên hiệu lực tức thì, không qua đệm.
    from app.modules.login_session.service import force_relogin
    force_relogin(db, user, RevokeReason.PASSWORD_CHANGED, user.id)

    return success(None, "Đặt lại mật khẩu thành công")
