"""Bước duyệt khai người duyệt THEO VAI TRÒ phải tra ra được người.

Lỗi có từ ngày dựng bộ máy duyệt (fda76b43): `approver_resolver._by_role` nhập
`UserRole` từ `app.modules.role.model`, trong khi lớp đó nằm ở
`app.modules.user.model`. Mọi bước khai «theo vai trò» nổ ImportError đúng lúc
luồng mở bước đó, nên người bấm duyệt bước trước nhận lỗi 500. Bắt được khi thử
luồng Đặt xe hai bước trên local ngày 03/10/2026.
"""
from types import SimpleNamespace

from app.modules.approval.approver_resolver import resolve
from app.modules.approval.flow_model import APPROVER_ROLE
from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole


def _person(db, code: str, active: bool = True) -> tuple[Employee, User]:
    emp = Employee(code=code, full_name=f"Nhân sự {code}", is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"{code.lower()}@dego.test", employee_id=emp.id, is_active=active)
    db.add(user)
    db.flush()
    return emp, user


def test_buoc_theo_vai_tro_tra_ra_nhan_su_dang_hoat_dong(db):
    role = Role(code="booking_manager", name="Quản lý điều phối")
    db.add(role)
    db.flush()
    manager, manager_user = _person(db, "QL01")
    _, locked_user = _person(db, "QL02", active=False)
    _person(db, "NV01")
    for user in (manager_user, locked_user):
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()

    node = SimpleNamespace(approver_kind=APPROVER_ROLE, approver_ref="booking_manager")

    assert resolve(db, node, {}, None) == [manager.id]


def test_vai_tro_khong_ai_giu_thi_tra_rong(db):
    db.add(Role(code="seal_director", name="Giám đốc duyệt dấu"))
    db.flush()
    node = SimpleNamespace(approver_kind=APPROVER_ROLE, approver_ref="seal_director")

    assert resolve(db, node, {}, None) == []
