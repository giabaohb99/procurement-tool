from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.utils import generate_code

from .model import Employee
from .schema import EmployeeCreate, EmployeeUpdate

FILTERABLE = ["code", "full_name", "email", "is_active", "position", "role_names", "department_id"]
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
    old_email = (obj.email or "").strip()
    fields = data.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update")

    # CR-022: hồ sơ nhân sự KHÔNG còn cấp quyền cho tài khoản đăng nhập. Ô ở màn Nhân sự nay là
    # "Vị trí / Chức vụ" (`position`) — chỉ là chữ để hiển thị/in phiếu. Quyền thật của tài khoản
    # chỉ gán ở màn "Phân quyền tài khoản" (tab_user_role), không có đường đồng bộ ngầm nào nữa.

    # Đồng bộ email sang tài khoản đăng nhập (User.email) để đăng nhập bằng email được.
    # CHỈ khớp trong 2 trường hợp an toàn (tránh ghi đè "handle đăng nhập" như admin/TESTREQ mà
    # ai đó cố tình đặt khác email nhân sự):
    #   (a) User.email đang RỖNG → điền email nhân sự (đúng ca bug: tạo TK khi chưa có email, sau đó
    #       thêm email vào nhân sự — kể cả email đã nhập TRƯỚC bản vá, lần lưu sau tự khớp);
    #   (b) admin THỰC SỰ đổi field email trong lần lưu này (old != new) → đẩy email mới sang.
    email_changed = "email" in fields and (obj.email or "").strip() != old_email
    _sync_user_email_from_employee(db, obj, email_changed)
    return obj


def _sync_user_email_from_employee(db: Session, emp: Employee, email_changed: bool) -> None:
    """Khớp email đăng nhập (User.email) = email nhân sự khi tài khoản đang RỖNG email, hoặc khi admin
    vừa đổi email ở lần lưu này. Bỏ qua nếu nhân sự chưa có email (không xoá email đăng nhập đang có),
    hoặc email đã bị tài khoản KHÁC dùng (tránh 2 tài khoản trùng email → đăng nhập nhập nhằng)."""
    from app.modules.user.model import User

    new_email = (emp.email or "").strip()
    if not new_email:
        return
    user = db.query(User).filter(User.employee_id == emp.id).first()
    if not user:
        return
    cur = (user.email or "").strip()
    if cur == new_email:
        return
    if cur and not email_changed:
        return  # giữ nguyên handle/email khác khi admin không chủ động đổi email
    dup = db.query(User).filter(User.email == new_email, User.id != user.id).first()
    if dup:
        raise HTTPException(400, "Email này đã được một tài khoản khác sử dụng")
    user.email = new_email
    db.commit()


def delete_employee(db: Session, eid: int, user_id: int) -> None:
    obj = get_employee(db, eid)
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, eid, "delete")
