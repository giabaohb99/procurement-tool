"""Khung dựng cảnh cho test KIÊM NHIỆM hai loại dòng (duoc-CR-756) — dùng chung `test_kiem_nhiem_*_cr75[56].py`.

Thế giới mẫu (`scope_factory.build_world`) cộng thêm:
  * công ty C và phòng của nó `C.kt`;
  * phòng DÙNG CHUNG `SH` (`company_id = 0`) — ca khó nhất của phạm vi: cùng một id phòng ở công ty A, B, C;
  * `p` (= `a2`) chuyển sang (A, SH): người kiêm nhiệm CÔNG TY B trong các bài kiểm;
  * `hb` (B, SH) và `y1` (B, B.hc): người xem ở công ty B, `c1` (C, SH): người xem ở công ty C.

Mô hình đúng sau CR-756: dòng loại Phòng ban (`kn`) luôn ở công ty CHÍNH của người đó; dòng loại Công ty (`kc`) là
công ty KHÁC, không phòng. Tạo thẳng bằng model (qua service sẽ vướng chốt L1/L2 của người thao tác).
"""
from datetime import timedelta

from app.core.auth import perm_cache_clear
from app.core.hr_concurrent_codes import ConcurrentKind
from app.core.vn_time import vn_today
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.model import Employee
from app.modules.user.model import User
from scope_factory import Actor

TODAY = vn_today()
DAY = timedelta(days=1)


def add_employee(world, key: str, company_key: str, dept_key: str) -> None:
    db = world.db
    emp = Employee(code=key.upper(), full_name=f"Nhân sự {key}", company_id=world.co[company_key],
                   department_id=world.dept[dept_key], is_active=True)
    db.add(emp)
    db.flush()
    world.emp[key] = emp.id
    user = User(email=key, employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    world._actors[key] = Actor(world, key, user, emp)


def build_kn_world(world):
    """Dựng thêm công ty C, phòng SH / C.kt, người xem hb / y1 / c1 và chuyển a2 sang (A, SH)."""
    db = world.db
    company_c = Company(code="CTY_C", name="Công ty C", is_active=True)
    db.add(company_c)
    db.flush()
    world.co["C"] = company_c.id
    for key, code, company_id in (("SH", "SH_DC", 0), ("C.kt", "C_KT", company_c.id)):
        row = Department(code=code, name=f"Phòng {code}", company_id=company_id, is_active=True)
        db.add(row)
        db.flush()
        world.dept[key] = row.id
    world._actors["a2"].employee.department_id = world.dept["SH"]
    for key, company_key, dept_key in (("hb", "B", "SH"), ("y1", "B", "B.hc"), ("c1", "C", "SH")):
        add_employee(world, key, company_key, dept_key)
    db.commit()
    perm_cache_clear()
    return world


def kn(w, emp_key: str, dept_key: str, **kw) -> EmployeeConcurrent:
    """Dòng loại PHÒNG BAN: phòng của chính công ty chính của người đó. Mặc định đang hiệu lực + bật công tắc."""
    employee = w.db.get(Employee, w.emp[emp_key])
    row = EmployeeConcurrent(
        employee_id=employee.id, kind=int(ConcurrentKind.DEPARTMENT), department_id=w.dept[dept_key],
        company_id=employee.company_id, from_date=kw.pop("from_date", TODAY - 30 * DAY),
        position_label=kw.pop("position_label", ""), **kw)
    w.db.add(row)
    w.db.commit()
    perm_cache_clear()
    return row


def kc(w, emp_key: str, company_key: str, **kw) -> EmployeeConcurrent:
    """Dòng loại CÔNG TY: kiêm nhiệm cả công ty `company_key` (khác công ty chính), không phòng."""
    row = EmployeeConcurrent(
        employee_id=w.emp[emp_key], kind=int(ConcurrentKind.COMPANY), department_id=0, company_id=w.co[company_key],
        from_date=kw.pop("from_date", TODAY - 30 * DAY), position_label=kw.pop("position_label", ""), **kw)
    w.db.add(row)
    w.db.commit()
    perm_cache_clear()
    return row
