"""Ép tải duoc-CR-680 trên MySQL THẬT: thời gian + số truy vấn khi mở bước «Người có quyền duyệt».

    docker compose cp plans/261023-1330-ep-tai-cr680/scripts/load-permission-approvers-cr680.py api:/tmp/l.py
    docker compose exec -T api env PYTHONPATH=/app python /tmp/l.py

Dựng N người giữ vai trò ST680 (phạm vi công ty, rải 3 pháp nhân) + 1 vai trò «tất cả», một phiếu đặt xe,
đo `resolve` lúc bộ đệm quyền LẠNH và NÓNG, và `holder_profiles`. Xong xóa sạch.
"""
import time

from sqlalchemy import event

import app.core.all_models  # noqa: F401
from app.core.auth import perm_cache_clear
from app.core.database import SessionLocal, engine
from app.modules.approval import permission_approvers as pa
from app.modules.employee.model import Employee
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole
from app.modules.vehicle_booking.model import VehicleBooking

PREFIX = "ST680-"
COUNT = {"n": 0}


@event.listens_for(engine, "before_cursor_execute")
def _count(*_a, **_k):
    COUNT["n"] += 1


def cleanup(db):
    roles = [r.id for r in db.query(Role).filter(Role.code.like(f"{PREFIX}%"))]
    emps = [e.id for e in db.query(Employee).filter(Employee.code.like(f"{PREFIX}%"))]
    users = [u.id for u in db.query(User).filter(User.employee_id.in_(emps))] if emps else []
    if users:
        db.query(UserRole).filter(UserRole.user_id.in_(users)).delete(False)
        db.query(User).filter(User.id.in_(users)).delete(False)
    if roles:
        db.query(Permission).filter(Permission.role_id.in_(roles)).delete(False)
        db.query(Role).filter(Role.id.in_(roles)).delete(False)
    if emps:
        db.query(Employee).filter(Employee.id.in_(emps)).delete(False)
    db.query(VehicleBooking).filter(VehicleBooking.code.like(f"{PREFIX}%")).delete(False)
    db.commit()
    perm_cache_clear()


def measure(label, fn):
    COUNT["n"] = 0
    t0 = time.perf_counter()
    out = fn()
    print(f"{label:<34} {(time.perf_counter() - t0) * 1000:8.1f} ms  {COUNT['n']:4d} truy vấn  -> {len(out)} người")
    return out


def run(n):
    db = SessionLocal()
    try:
        cleanup(db)
        company_role = Role(code=f"{PREFIX}company", name="ST680 điều phối công ty")
        all_role = Role(code=f"{PREFIX}all", name="ST680 điều phối tất cả")
        db.add_all([company_role, all_role])
        db.flush()
        db.add_all([Permission(role_id=company_role.id, entity="vehicle_booking", can_read=True,
                               can_approve=True, scope="company"),
                    Permission(role_id=all_role.id, entity="vehicle_booking", can_read=True,
                               can_approve=True, scope="all")])
        companies = [c for (c,) in db.query(Employee.company_id).filter(Employee.company_id > 0).distinct().limit(3)]
        for i in range(n):
            emp = Employee(code=f"{PREFIX}{i:03d}", full_name=f"Ep tai {i}", company_id=companies[i % len(companies)],
                           is_active=True)
            db.add(emp)
            db.flush()
            user = User(email=f"st680-{i}@local.test", employee_id=emp.id, is_active=True)
            db.add(user)
            db.flush()
            db.add(UserRole(user_id=user.id, role_id=all_role.id if i == 0 else company_role.id))
        booking = VehicleBooking(code=f"{PREFIX}XE", company_id=companies[0], department_id=0, created_by=0,
                                 purpose="ep tai")
        db.add(booking)
        db.commit()
        perm_cache_clear()
        subject = {"id": booking.id, "company_id": companies[0]}
        print(f"--- {n} người giữ quyền, {len(companies)} pháp nhân ---")
        cold = measure("resolve (bộ đệm quyền lạnh)", lambda: pa.resolve(db, "vehicle_booking", subject))
        warm = measure("resolve (bộ đệm quyền nóng)", lambda: pa.resolve(db, "vehicle_booking", subject))
        measure("holder_profiles", lambda: pa.holder_profiles(db, "vehicle_booking"))
        expected = 1 + len([i for i in range(1, n) if i % len(companies) == 0])
        print(f"đúng người: {len(cold) == len(warm) == expected} (mong {expected})")
    finally:
        cleanup(db)
        db.close()


if __name__ == "__main__":
    for n in (10, 60, 200):
        run(n)
