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
    old_email = (obj.email or "").strip()
    fields = data.model_dump(exclude_unset=True)
    for key, value in fields.items():
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
        _sync_user_role_from_employee(db, obj, new_role_name, user_id, old_role_name)

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


def _sync_user_role_from_employee(db: Session, emp: Employee, role_name: str,
                                  actor_id: int, old_role_name: str = "") -> None:
    """Đồng bộ vai trò "chính" (ô Vai trò ở màn Nhân sự) sang tài khoản đăng nhập — AN TOÀN:
    HOÁN ĐỔI vai trò cũ → vai trò mới, GIỮ NGUYÊN các vai trò khác đã gán tay (đa vai trò/phạm vi
    riêng ở màn Phân quyền, vd "Giá vốn nhà máy"). Không còn xóa sạch rồi gán đúng 1 vai trò.
    Bỏ qua nếu nhân sự chưa có tài khoản hoặc tên vai trò mới không khớp Role nào (nhãn tự do)."""
    from app.core.auth import perm_cache_clear
    from app.modules.role.model import Role
    from app.modules.user.model import User, UserRole

    user = db.query(User).filter(User.employee_id == emp.id).first()
    if not user:
        return
    new_role = db.query(Role).filter(Role.name == role_name).first()
    if not new_role:
        return  # nhãn tự do không map được Role → không đụng vai trò hiện có

    current = {ur.role_id for ur in db.query(UserRole).filter(UserRole.user_id == user.id).all()}
    changed = False

    # Gỡ vai trò "chính" CŨ (nếu có) để phản ánh việc đổi/hạ vai trò — KHÔNG đụng các vai trò khác.
    old_role = (db.query(Role).filter(Role.name == old_role_name).first()
                if (old_role_name or "").strip() else None)
    if old_role and old_role.id in current and old_role.id != new_role.id:
        db.query(UserRole).filter(
            UserRole.user_id == user.id, UserRole.role_id == old_role.id
        ).delete(synchronize_session=False)
        current.discard(old_role.id)
        changed = True

    # Đảm bảo có vai trò "chính" MỚI.
    if new_role.id not in current:
        db.add(UserRole(user_id=user.id, role_id=new_role.id,
                        created_by=actor_id, updated_by=actor_id))
        changed = True

    if changed:
        db.commit()
        perm_cache_clear(user.id)


def delete_employee(db: Session, eid: int, user_id: int) -> None:
    obj = get_employee(db, eid)
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, eid, "delete")
