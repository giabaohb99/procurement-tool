from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import hash_password, perm_cache_clear
from app.modules.employee.model import Employee

from .model import User, UserRole, UserScope
from .schema import RoleAssign, ScopeUpdate, UserProvision


# Vai trò mặc định của MỌI tài khoản mới (khách chốt): có tài khoản là có quyền 'Nhân sự'
# — tự tạo phiếu đề xuất / yêu cầu khảo sát của mình. Quyền khác vẫn phải gán tay.
DEFAULT_ROLE_CODE = "employee"

# Bảng KHÔNG tính là "dữ liệu nghiệp vụ" khi kiểm tra trước lúc xóa tài khoản:
# nhật ký giữ nguyên (lịch sử), còn thông báo/đăng ký push là của riêng tài khoản -> xóa theo.
_SKIP_REF_TABLES = {"tab_audit_log", "tab_user", "tab_user_role", "tab_user_scope",
                    "tab_notification", "tab_push_subscription"}


def _role_ids(db: Session, user_id: int) -> list[int]:
    return [ur.role_id for ur in db.query(UserRole).filter(UserRole.user_id == user_id).all()]


def default_role_ids(db: Session) -> list[int]:
    from app.modules.role.model import Role
    r = db.query(Role).filter(Role.code == DEFAULT_ROLE_CODE).first()
    return [r.id] if r else []


def orphan_user_ids(db: Session) -> list[int]:
    """Tài khoản MỒ CÔI = không gắn hồ sơ nhân sự, hoặc gắn vào hồ sơ đã bị xóa."""
    alive = {eid for (eid,) in db.query(Employee.id).all()}
    return [u.id for u in db.query(User).all()
            if not u.employee_id or u.employee_id not in alive]


def list_users(db: Session, pg: dict, search: str = "", department: str = "", role_id: int = 0,
               sort: str = "", employee_id: int = 0, no_role: bool = False, orphan: bool = False):
    query = db.query(User)
    if employee_id:   # tra CHÍNH XÁC tài khoản của 1 nhân sự (dùng cho nút "Phân quyền tài khoản")
        query = query.filter(User.employee_id == employee_id)
    if no_role:       # chưa được gán vai trò nào -> vào hệ thống nhưng chưa dùng được gì
        assigned = [uid for (uid,) in db.query(UserRole.user_id).distinct().all()]
        query = query.filter(User.id.notin_(assigned or [-1]))
    if orphan:        # mồ côi: không còn hồ sơ nhân sự
        query = query.filter(User.id.in_(orphan_user_ids(db) or [-1]))
    if search:
        like = f"%{search.strip()}%"
        emp_ids = [e.id for e in db.query(Employee).filter(
            (Employee.full_name.ilike(like)) | (Employee.code.ilike(like)) | (Employee.email.ilike(like))
        ).all()]
        cond = User.email.ilike(like)
        if emp_ids:
            cond = cond | User.employee_id.in_(emp_ids)
        query = query.filter(cond)
    if department:
        from app.modules.department.model import Department
        dep = db.query(Department).filter(Department.name == department).first()
        emp_ids = [e.id for e in db.query(Employee).filter(Employee.department_id == (dep.id if dep else -1)).all()]
        query = query.filter(User.employee_id.in_(emp_ids or [-1]))
    if role_id:
        uids = [ur.user_id for ur in db.query(UserRole).filter(UserRole.role_id == role_id).all()]
        query = query.filter(User.id.in_(uids or [-1]))
    total = query.count()
    if sort in ("name_asc", "name_desc"):
        query = query.outerjoin(Employee, User.employee_id == Employee.id)
        query = query.order_by(Employee.full_name.asc() if sort == "name_asc" else Employee.full_name.desc())
    else:
        query = query.order_by(User.id.desc())
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def provision_user(db: Session, data: UserProvision, actor_id: int) -> User:
    emp = db.get(Employee, data.employee_id)
    if not emp:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    if db.query(User).filter(User.employee_id == data.employee_id).first():
        raise HTTPException(400, "Nhân viên này đã có tài khoản")
    email = (data.email or emp.email or "").strip()
    # CR-023: 2 tài khoản đang hoạt động trùng email = đăng nhập nhập nhằng (cái nào cũng có thể
    # được chọn trước). Chặn ngay từ lúc tạo. Tài khoản đã khoá thì không tính.
    if email and db.query(User).filter(User.email == email, User.is_active.is_(True)).first():
        raise HTTPException(400, f"Email {email} đã được một tài khoản khác sử dụng")
    user = User(
        email=email,
        employee_id=data.employee_id,
        password_hash=hash_password(data.password),
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Không chọn vai trò nào -> mặc định 'Nhân sự' để tài khoản mới dùng được ngay
    assign_roles(db, user.id, RoleAssign(role_ids=data.role_ids or default_role_ids(db)), actor_id)
    return user


def user_data_refs(db: Session, user_id: int) -> list[str]:
    """Các bảng nghiệp vụ còn ghi nhận tài khoản này là người tạo — dùng để chặn xóa nhầm."""
    from app.core import all_models  # noqa: F401  (nạp đủ model)
    from app.core.base_model import Base

    out = []
    for mapper in Base.registry.mappers:
        table = mapper.local_table
        if table is None or table.name in _SKIP_REF_TABLES or "created_by" not in table.c:
            continue
        n = db.query(mapper.class_).filter(mapper.class_.created_by == user_id).count()
        if n:
            out.append(f"{table.name} ({n})")
    return sorted(out)


def delete_user(db: Session, user_id: int, actor_id: int) -> None:
    """Xóa hẳn tài khoản (dùng cho tài khoản mồ côi / tạo nhầm).

    Nhật ký thao tác GIỮ NGUYÊN — lịch sử không được sửa; chỗ nào hiển thị tên sẽ ghi "User #id".
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    if user_id == actor_id:
        raise HTTPException(400, "Không thể xóa tài khoản đang đăng nhập")

    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    if user.is_active and emp:
        raise HTTPException(400, f"Tài khoản đang hoạt động của nhân sự {emp.full_name} — "
                                 "hãy khóa tài khoản thay vì xóa.")

    from app.modules.role.model import Role
    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if admin_role and db.query(UserRole).filter(UserRole.user_id == user_id,
                                                UserRole.role_id == admin_role.id).first():
        others = db.query(UserRole).filter(UserRole.role_id == admin_role.id,
                                           UserRole.user_id != user_id).count()
        if others == 0:
            raise HTTPException(400, "Đây là tài khoản quản trị duy nhất, không thể xóa")

    refs = user_data_refs(db, user_id)
    if refs:
        raise HTTPException(400, "Tài khoản đã tạo dữ liệu trên hệ thống (" + ", ".join(refs[:5])
                                 + ") — hãy khóa tài khoản thay vì xóa.")

    from app.modules.notification.model import Notification
    from app.modules.push.model import PushSubscription

    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    db.query(UserScope).filter(UserScope.user_id == user_id).delete()
    db.query(Notification).filter(Notification.user_id == user_id).delete()
    db.query(PushSubscription).filter(PushSubscription.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    perm_cache_clear(user_id)


def reset_password(db: Session, user_id: int, new_password: str, actor_id: int) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    user.password_hash = hash_password(new_password)
    user.updated_by = actor_id
    db.commit()


def assign_roles(db: Session, user_id: int, data: RoleAssign, actor_id: int) -> None:
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    for rid in data.role_ids:
        db.add(UserRole(user_id=user_id, role_id=rid, created_by=actor_id, updated_by=actor_id))
    db.commit()
    perm_cache_clear(user_id)


def get_user_scope(db: Session, user_id: int, role_id: int) -> dict:
    out = {"companies": [], "departments": [], "employees": [],
           "exclude_companies": [], "exclude_departments": [], "exclude_employees": []}
    rows = db.query(UserScope).filter(UserScope.user_id == user_id, UserScope.role_id == role_id).all()
    for r in rows:
        v = int(r.value) if (r.value or "").isdigit() else r.value
        if r.dim == "company":
            out["exclude_companies" if r.is_exclude else "companies"].append(v)
        elif r.dim == "employee":
            out["exclude_employees" if r.is_exclude else "employees"].append(v)
        else:
            out["exclude_departments" if r.is_exclude else "departments"].append(r.value)
    return out


def set_user_scope(db: Session, user_id: int, role_id: int, data: ScopeUpdate, actor_id: int) -> None:
    db.query(UserScope).filter(UserScope.user_id == user_id, UserScope.role_id == role_id).delete()

    def add(dim, value, exc):
        db.add(UserScope(user_id=user_id, role_id=role_id, entity="", dim=dim, value=str(value),
                         is_exclude=exc, created_by=actor_id, updated_by=actor_id))
    for c in data.companies:
        add("company", c, False)
    for c in data.exclude_companies:
        add("company", c, True)
    for d in data.departments:
        add("department", d, False)
    for d in data.exclude_departments:
        add("department", d, True)
    for e in data.employees:
        add("employee", e, False)
    for e in data.exclude_employees:
        add("employee", e, True)
    db.commit()
    perm_cache_clear(user_id)


def set_active(db: Session, user_id: int, active: bool, actor_id: int) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    email = (user.email or "").strip()
    # CR-023: mở khoá lại mà email trùng một tài khoản đang hoạt động thì lại nhập nhằng đăng nhập
    if active and not user.is_active and email:
        dup = db.query(User).filter(User.email == email, User.id != user.id,
                                    User.is_active.is_(True)).first()
        if dup:
            raise HTTPException(400, f"Email {email} đang được tài khoản #{dup.id} sử dụng. "
                                     "Hãy sửa email trước khi mở khoá tài khoản này.")
    user.is_active = active
    user.updated_by = actor_id
    db.commit()
