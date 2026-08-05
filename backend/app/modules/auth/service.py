from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import verify_password
from app.modules.employee.model import Employee
from app.modules.user.model import User


def authenticate(db: Session, username: str, password: str) -> User:
    # CR-023: luôn ƯU TIÊN tài khoản đang hoạt động. Nếu có 2 tài khoản trùng email (một cái đã khoá
    # hoặc mồ côi do hồ sơ nhân sự bị xoá), bản cũ lấy `.first()` nên có thể vớ đúng cái đã khoá và
    # trả 401 cho người dùng thật.
    # 1. Thử tìm theo email trực tiếp trong User trước
    user = db.query(User).filter(User.email == username, User.is_active.is_(True)).first()

    # 2. Nếu không tìm thấy, thử tìm theo mã nhân viên
    if not user:
        emp = db.query(Employee).filter(Employee.code == username).first()
        if emp:
            user = (db.query(User).filter(User.employee_id == emp.id, User.is_active.is_(True)).first()
                    or db.query(User).filter(User.employee_id == emp.id).first())
        if not user:
            user = db.query(User).filter(User.email == username).first()

    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Sai tài khoản hoặc mật khẩu")

    # Nhân viên phải đang active
    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    if emp and not emp.is_active:
        raise HTTPException(403, "Nhân viên đã ngừng hoạt động")
    return user

def google_login(db: Session, credential: str) -> User:
    from google.oauth2 import id_token
    from google.auth.transport import requests
    from app.core.config import settings

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(500, "Chưa cấu hình GOOGLE_CLIENT_ID")

    try:
        idinfo = id_token.verify_oauth2_token(credential, requests.Request(), settings.GOOGLE_CLIENT_ID, clock_skew_in_seconds=60)
    except ValueError as e:
        print(f"Google Token error: {e}")
        raise HTTPException(401, f"Google Token không hợp lệ: {e}")

    email = idinfo.get("email")
    if not email:
        raise HTTPException(401, "Không lấy được email từ Google")

    # 1. Check if employee exists
    emp = db.query(Employee).filter(Employee.email == email).first()
    if not emp:
        raise HTTPException(403, "Email không hợp lệ, vui lòng liên hệ Admin để được hỗ trợ")

    if not emp.is_active:
        raise HTTPException(403, "Nhân sự đã ngừng hoạt động")

    # 2. Find user by employee_id — CR-023: ưu tiên tài khoản đang hoạt động (xem authenticate)
    user = (db.query(User).filter(User.employee_id == emp.id, User.is_active.is_(True)).first()
            or db.query(User).filter(User.employee_id == emp.id).first())
    if not user:
        user = (db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
                or db.query(User).filter(User.email == email).first())

    if user and not user.is_active:
        raise HTTPException(403, "Tài khoản đã bị khoá, vui lòng liên hệ Admin")

    # 3. Create user if not exists
    if not user:
        user = User(email=email, employee_id=emp.id, is_active=True, google_sub=idinfo.get("sub", ""), avatar=idinfo.get("picture", ""))
        db.add(user)
        db.flush()
        # CR-022: KHÔNG tự gán vai trò theo hồ sơ nhân sự nữa (ô đó nay là "Vị trí", chỉ là chữ).
        # Tài khoản mới đăng nhập lần đầu chưa có quyền gì — admin gán ở "Phân quyền tài khoản".
    else:
        if not user.google_sub:
            user.google_sub = idinfo.get("sub", "")
        if not user.avatar and idinfo.get("picture"):
            user.avatar = idinfo.get("picture", "")
            
    db.commit()
    return user
