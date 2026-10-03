"""Quá trình công tác — finding LOW của code review 03/10/2026 (plan
`261003-0837-qua-trinh-lam-viec-nhan-su`). M1/M2/M3/M7 nằm ở
`test_qua_trinh_cong_tac_sua_loi_review.py`, H2 ở `..._gio_vn.py`.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.hr_work_history_codes import WorkEventType
from app.modules.audit.model import AuditLog
from app.modules.department.model import Department
from app.modules.employee import department_service as dept_svc
from app.modules.employee import work_history_apply_service as applysvc
from app.modules.employee import work_history_controller as whc
from app.modules.employee import work_history_service as whs
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.modules.employee.work_history_schema import WorkHistoryIn
from app.modules.employee.work_history_serializer import serialize_one

ACTOR = SimpleNamespace(id=1)


def _row(db, eid, event_type, from_date, **kw) -> EmployeeWorkHistory:
    row = EmployeeWorkHistory(employee_id=eid, event_type=int(event_type), from_date=from_date,
                              created_by=ACTOR.id, updated_by=ACTOR.id, **kw)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@pytest.fixture
def emp(db) -> Employee:
    e = Employee(code="RVLOW1", full_name="Người kiểm review low", is_active=True)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture
def dept(db) -> Department:
    d = Department(code="PRVLOW1", name="Phòng review low", is_active=True)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


# ══════════════════════════════════════════════════════════════════════════════
#  close_open_main chỉ nhận cho nhóm sự kiện CHÍNH
# ══════════════════════════════════════════════════════════════════════════════

def test_close_open_main_voi_loai_khac_thi_422(db, emp):
    with pytest.raises(HTTPException) as e:
        whs.create(db, emp.id, WorkHistoryIn(event_type=int(WorkEventType.OTHER),
                                             from_date=date(2025, 1, 1), close_open_main=True), ACTOR)
    assert e.value.status_code == 422


def test_close_open_main_voi_kiem_nhiem_thi_422(db, emp, dept):
    with pytest.raises(HTTPException) as e:
        whs.create(db, emp.id, WorkHistoryIn(
            event_type=int(WorkEventType.CONCURRENT), from_date=date(2025, 1, 1),
            department_id=dept.id, close_open_main=True), ACTOR)
    assert e.value.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
#  Gỡ kiêm nhiệm hết hạn: còn dòng KHÁC cùng phòng đang hiệu lực thì KHÔNG gỡ
# ══════════════════════════════════════════════════════════════════════════════

def test_kiem_nhiem_het_han_nhung_con_dong_khac_cung_phong_dang_hieu_luc_thi_khong_go(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    dept_id = world.dept["A.kt"]

    still_active = _row(world.db, world.emp["a3"], WorkEventType.CONCURRENT,
                        date.today() - timedelta(days=10), department_id=dept_id)
    applysvc.apply(world.db, still_active, a1.user, a1.profile())
    world.db.commit()
    assert dept_id in dept_svc.extra_departments_of(world.db, world.emp["a3"])

    expired = _row(world.db, world.emp["a3"], WorkEventType.CONCURRENT,
                   date.today() - timedelta(days=30),
                   to_date=date.today() - timedelta(days=1), department_id=dept_id)
    changes = applysvc.apply(world.db, expired, a1.user, a1.profile())

    assert changes == [], "còn dòng kiêm nhiệm KHÁC cùng phòng đang hiệu lực — không được gỡ"
    assert dept_id in dept_svc.extra_departments_of(world.db, world.emp["a3"])


# ══════════════════════════════════════════════════════════════════════════════
#  serialize_one: can_apply phải tính theo dòng chính MỚI NHẤT của nhân sự
# ══════════════════════════════════════════════════════════════════════════════

def test_serialize_one_tinh_can_apply_theo_dong_chinh_moi_nhat_cua_nhan_su(db, emp):
    newer = EmployeeWorkHistory(employee_id=emp.id, event_type=int(WorkEventType.TRANSFER),
                                from_date=date(2025, 6, 1), created_by=1, updated_by=1)
    older = EmployeeWorkHistory(employee_id=emp.id, event_type=int(WorkEventType.APPOINT),
                                from_date=date(2024, 1, 1), created_by=1, updated_by=1)
    db.add_all([newer, older])
    db.commit()
    db.refresh(newer)
    db.refresh(older)

    out = serialize_one(db, older)
    assert out["can_apply"] is False, "có dòng chính MỚI HƠN — chỉ áp được dòng chính mới nhất"


# ══════════════════════════════════════════════════════════════════════════════
#  applied_at phải CÙNG giao dịch với `update_employee` (không lệch sau rollback)
# ══════════════════════════════════════════════════════════════════════════════

def test_applied_at_cung_giao_dich_voi_update_employee_khong_lech_sau_rollback(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    pos = JobPosition(code="CV-REVIEWLOW", name="Trưởng phòng Review", is_active=True)
    world.db.add(pos)
    world.db.commit()
    world.db.refresh(pos)

    row = _row(world.db, world.emp["a3"], WorkEventType.APPOINT, date.today(), position_id=pos.id)
    applysvc.apply(world.db, row, a1.user, a1.profile())
    #  KHÔNG commit ở đây — mô phỏng một lỗi xảy ra GIỮA `apply()` và commit
    #  cuối của controller (vd `audit_record` hỏng). `update_employee` được gọi
    #  TỪ TRONG `apply()` đã tự commit — việc đó không rollback được.
    world.db.rollback()

    world.db.refresh(row)
    emp_after = world.db.get(Employee, world.emp["a3"])
    assert emp_after.position_id == pos.id, "update_employee đã tự commit — hồ sơ PHẢI đổi"
    assert row.applied_at is not None, ("applied_at phải CÙNG giao dịch với update_employee — "
                                        "không được None sau rollback")


# ══════════════════════════════════════════════════════════════════════════════
#  Audit xoá dòng phải ghi NỘI DUNG dòng, không chỉ số id
# ══════════════════════════════════════════════════════════════════════════════

def test_xoa_dong_ghi_audit_co_noi_dung_dong(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    row = _row(world.db, world.emp["a3"], WorkEventType.APPOINT, date(2025, 3, 1),
              decision_no="QD-REVIEWLOW-99")

    whc.delete_work_history(world.emp["a3"], row.id, world.db, a1.user)

    msgs = [r.message for r in world.db.query(AuditLog).filter(
        AuditLog.entity == "employee", AuditLog.entity_id == world.emp["a3"],
        AuditLog.action == "delete").all()]
    assert any("QD-REVIEWLOW-99" in m for m in msgs), "audit xoá phải ghi nội dung dòng"
