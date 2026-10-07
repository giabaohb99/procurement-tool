"""Tra tên theo lô cho serializer — mỗi loại MỘT truy vấn cho cả trang (không N+1)."""
from sqlalchemy.orm import Session


def names_map(db: Session, model, ids) -> dict[int, str]:
    ids = {int(i) for i in ids if i}
    if not ids:
        return {}
    return dict(db.query(model.id, model.name).filter(model.id.in_(ids)).all())


def user_names(db: Session, ids) -> dict[int, str]:
    """id tài khoản → họ tên nhân sự (không có hồ sơ thì lấy email)."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    ids = {int(i) for i in ids if i}
    if not ids:
        return {}
    rows = (db.query(User.id, User.email, Employee.full_name)
            .outerjoin(Employee, Employee.id == User.employee_id)
            .filter(User.id.in_(ids)).all())
    return {uid: (full_name or email or "") for uid, email, full_name in rows}
