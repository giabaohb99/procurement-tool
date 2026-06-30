from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import verify_password
from app.modules.employee.model import Employee
from app.modules.user.model import User


def authenticate(db: Session, username: str, password: str) -> User:
    user = None
    if "@" in username:
        user = db.query(User).filter(User.email == username).first()
    else:
        emp = db.query(Employee).filter(Employee.code == username).first()
        if emp:
            user = db.query(User).filter(User.employee_id == emp.id).first()

    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Sai tài khoản hoặc mật khẩu")

    # Nhân viên phải đang active
    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    if emp and not emp.is_active:
        raise HTTPException(403, "Nhân viên đã ngừng hoạt động")
    return user
