from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.utils import generate_code

from .model import Employee
from .schema import EmployeeCreate, EmployeeUpdate

FILTERABLE = ["code", "full_name", "email", "is_active", "role_names", "department_id"]
ENTITY = "employee"


def list_employees(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(Employee.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def get_employee(db: Session, eid: int) -> Employee:
    obj = db.get(Employee, eid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    return obj


def create_employee(db: Session, data: EmployeeCreate, user_id: int) -> Employee:
    if not data.role_name:
        raise HTTPException(400, "Bắt buộc chọn vai trò cho nhân sự")
    if not data.code:
        data.code = generate_code(db, Employee, "NSU")
    elif db.query(Employee).filter(Employee.code == data.code).first():
        raise HTTPException(400, "Mã nhân viên đã tồn tại")
    obj = Employee(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create")
    return obj


def update_employee(db: Session, eid: int, data: EmployeeUpdate, user_id: int) -> Employee:
    obj = get_employee(db, eid)
    if data.role_name is not None and not data.role_name.strip():
        raise HTTPException(400, "Bắt buộc chọn vai trò cho nhân sự")
    old_role_name = (obj.role_name or "").strip()
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update")

    # Đồng bộ vai trò sang tài khoản đăng nhập (UserRole) KHI "Vai trò" ở màn Nhân sự thực sự ĐỔI.
    # Chỉ chạy khi role_name đổi (không đụng các lần sửa field khác) và nhân sự đã có tài khoản +
    # tên vai trò map được sang 1 Role → tránh ghi đè nhầm cấu hình đa vai trò/phạm vi đã gán tay.
    new_role_name = (obj.role_name or "").strip()
    if new_role_name and new_role_name != old_role_name:
        _sync_user_role_from_employee(db, obj, new_role_name, user_id)

    # Đồng bộ email sang tài khoản đăng nhập (User.email) để đăng nhập bằng email được.
    # RECONCILE mỗi lần lưu: nếu nhân sự có email mà tài khoản gắn với nó đang LỆCH (rỗng/khác)
    # thì khớp lại — KHÔNG phụ thuộc email có đổi trong lần lưu này hay không. Nhờ vậy vẫn vá được
    # các nhân sự đã nhập email TRƯỚC khi có bản này (User.email còn rỗng): chỉ cần lưu lại là khớp.
    _sync_user_email_from_employee(db, obj)
    return obj


def _sync_user_email_from_employee(db: Session, emp: Employee) -> None:
    """Khớp email đăng nhập (User.email) của tài khoản gắn với nhân sự = email hiện tại ở màn Nhân sự.
    Bỏ qua nếu nhân sự chưa có email (không xoá email đăng nhập đang có), chưa có tài khoản, đã khớp,
    hoặc email đã bị tài khoản KHÁC dùng (tránh 2 tài khoản trùng email → đăng nhập nhập nhằng)."""
    from app.modules.user.model import User

    new_email = (emp.email or "").strip()
    if not new_email:
        return
    user = db.query(User).filter(User.employee_id == emp.id).first()
    if not user or (user.email or "").strip() == new_email:
        return
    dup = db.query(User).filter(User.email == new_email, User.id != user.id).first()
    if dup:
        raise HTTPException(400, "Email này đã được một tài khoản khác sử dụng")
    user.email = new_email
    db.commit()


def _sync_user_role_from_employee(db: Session, emp: Employee, role_name: str, actor_id: int) -> None:
    """Set lại UserRole của tài khoản gắn với nhân sự = đúng 1 vai trò vừa chọn ở màn Nhân sự.
    Bỏ qua nếu nhân sự chưa có tài khoản (vai trò sẽ suy khi tạo tài khoản) hoặc tên vai trò
    không khớp Role nào (nhãn tự do)."""
    from app.modules.role.model import Role
    from app.modules.user.model import User
    from app.modules.user.schema import RoleAssign
    from app.modules.user.service import assign_roles

    user = db.query(User).filter(User.employee_id == emp.id).first()
    if not user:
        return
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        return
    assign_roles(db, user.id, RoleAssign(role_ids=[role.id]), actor_id)


def delete_employee(db: Session, eid: int, user_id: int) -> None:
    obj = get_employee(db, eid)
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, eid, "delete")
