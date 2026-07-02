from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import hash_password, perm_cache_clear
from app.modules.employee.model import Employee

from .model import User, UserRole, UserScope
from .schema import RoleAssign, ScopeUpdate, UserProvision


def _role_ids(db: Session, user_id: int) -> list[int]:
    return [ur.role_id for ur in db.query(UserRole).filter(UserRole.user_id == user_id).all()]


def list_users(db: Session, pg: dict, search: str = ""):
    query = db.query(User)
    if search:
        like = f"%{search.strip()}%"
        emp_ids = [e.id for e in db.query(Employee).filter(
            (Employee.full_name.ilike(like)) | (Employee.code.ilike(like)) | (Employee.email.ilike(like))
        ).all()]
        cond = User.email.ilike(like)
        if emp_ids:
            cond = cond | User.employee_id.in_(emp_ids)
        query = query.filter(cond)
    total = query.count()
    items = query.order_by(User.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def provision_user(db: Session, data: UserProvision, actor_id: int) -> User:
    emp = db.get(Employee, data.employee_id)
    if not emp:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    if db.query(User).filter(User.employee_id == data.employee_id).first():
        raise HTTPException(400, "Nhân viên này đã có tài khoản")
    user = User(
        email=data.email or emp.email,
        employee_id=data.employee_id,
        password_hash=hash_password(data.password),
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    assign_roles(db, user.id, RoleAssign(role_ids=data.role_ids), actor_id)
    return user


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
    user.is_active = active
    user.updated_by = actor_id
    db.commit()
