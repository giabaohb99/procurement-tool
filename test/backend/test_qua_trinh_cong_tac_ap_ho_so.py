"""Quá trình công tác — ÁP HỒ SƠ, MỘT GIAO DỊCH, KIÊM NHIỆM (phase 03).

Dựng người bằng `world` (`scope_factory.py`) để có sẵn hai pháp nhân × bốn
phòng và vai trò THẬT cấp qua `world.grant(...)`.
"""
import json
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.core.hr_work_history_codes import WorkEventType
from app.modules.employee import department_service as dept_svc
from app.modules.employee import work_history_apply_service as applysvc
from app.modules.employee import work_history_controller as whc
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.modules.employee.work_history_schema import WorkHistoryIn

ACTOR = 1


def _row(db, eid, event_type, from_date, **kw) -> EmployeeWorkHistory:
    row = EmployeeWorkHistory(employee_id=eid, event_type=int(event_type), from_date=from_date,
                              created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _position(db, name="Trưởng phòng KD") -> JobPosition:
    p = JobPosition(code=f"CV-{name[:8]}", name=name, is_active=True)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ══════════════════════════════════════════════════════════════════════════════
#  Bổ nhiệm — đổi chức vụ chính
# ══════════════════════════════════════════════════════════════════════════════

def test_bo_nhiem_hom_nay_ap_ho_so_doi_chuc_vu_va_ghi_audit(world):
    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    pos = _position(world.db, "Trưởng phòng KD")
    data = WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date.today(),
                         position_id=pos.id, apply_to_profile=True)

    body = json.loads(whc.create_work_history(world.emp["a3"], data, world.db, a1.user).body)
    assert body["data"]["applied_changes"]
    assert body["data"]["item"]["applied_at"] is not None

    emp = world.db.get(Employee, world.emp["a3"])
    assert emp.position_id == pos.id
    assert emp.position == "Trưởng phòng KD"

    from app.modules.audit.model import AuditLog
    msgs = [r.message for r in world.db.query(AuditLog).filter(
        AuditLog.entity == "employee", AuditLog.entity_id == world.emp["a3"]).all()]
    assert any("Áp vào hồ sơ" in m for m in msgs)


# ══════════════════════════════════════════════════════════════════════════════
#  Điều chuyển — pháp nhân / phòng ban
# ══════════════════════════════════════════════════════════════════════════════

def test_dieu_chuyen_sai_phap_nhan_ma_khong_doi_cty_thi_400_va_khong_luu(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    data = WorkHistoryIn(event_type=int(WorkEventType.TRANSFER), from_date=date.today(),
                         department_id=world.dept["B.kt"], apply_to_profile=True)
    with pytest.raises(HTTPException) as e:
        whc.create_work_history(world.emp["a3"], data, world.db, a1.user)
    assert e.value.status_code == 400
    #  Ở chạy thật, `core.database.get_db` rollback session khi có exception đi
    #  ngang — gọi tay ở đây vì test gọi thẳng controller, không qua dependency đó.
    world.db.rollback()
    assert world.db.query(EmployeeWorkHistory).filter(
        EmployeeWorkHistory.employee_id == world.emp["a3"]).count() == 0


def test_dieu_chuyen_kem_doi_phap_nhan_go_phong_cu(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    data = WorkHistoryIn(event_type=int(WorkEventType.TRANSFER), from_date=date.today(),
                         company_id=world.co["B"], department_id=world.dept["B.kt"],
                         apply_to_profile=True)
    whc.create_work_history(world.emp["a3"], data, world.db, a1.user)

    assert world.dept["A.mua"] not in dept_svc.departments_of(world.db, world.emp["a3"])
    emp = world.db.get(Employee, world.emp["a3"])
    assert emp.company_id == world.co["B"]
    assert emp.department_id == world.dept["B.kt"]


def test_l2_scope_company_dieu_chuyen_sang_cong_ty_khac_403_khong_luu(world):
    """L2 — phòng B.hc nằm ngoài tầm GÁN của `a1` (chỉ thấy phòng công ty A)."""
    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    data = WorkHistoryIn(event_type=int(WorkEventType.TRANSFER), from_date=date.today(),
                         department_id=world.dept["B.hc"], apply_to_profile=True)
    with pytest.raises(HTTPException) as e:
        whc.create_work_history(world.emp["a3"], data, world.db, a1.user)
    assert e.value.status_code == 403
    world.db.rollback()
    assert world.db.query(EmployeeWorkHistory).filter(
        EmployeeWorkHistory.employee_id == world.emp["a3"]).count() == 0


# ══════════════════════════════════════════════════════════════════════════════
#  Bốn chốt chung của việc ÁP
# ══════════════════════════════════════════════════════════════════════════════

def test_tu_ngay_mai_thi_400(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    data = WorkHistoryIn(event_type=int(WorkEventType.APPOINT),
                         from_date=date.today() + timedelta(days=1),
                         department_id=world.dept["A.kt"], apply_to_profile=True)
    with pytest.raises(HTTPException) as e:
        whc.create_work_history(world.emp["a3"], data, world.db, a1.user)
    assert e.value.status_code == 400


def test_dong_chinh_da_ket_thuc_thi_400(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    old = _row(world.db, world.emp["a3"], WorkEventType.APPOINT, date(2020, 1, 1),
              to_date=date(2020, 12, 31), department_id=world.dept["A.kt"])
    with pytest.raises(HTTPException) as e:
        whc.apply_work_history(world.emp["a3"], old.id, world.db, a1.user)
    assert e.value.status_code == 400


def test_dong_chinh_cu_hon_dong_chinh_khac_thi_400(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    _row(world.db, world.emp["a3"], WorkEventType.APPOINT, date(2024, 1, 1),
        department_id=world.dept["A.kt"])
    older = _row(world.db, world.emp["a3"], WorkEventType.TRANSFER, date(2023, 1, 1),
                department_id=world.dept["A.mua"])
    with pytest.raises(HTTPException) as e:
        whc.apply_work_history(world.emp["a3"], older.id, world.db, a1.user)
    assert e.value.status_code == 400


def test_loai_khac_khong_ap_duoc_thi_400(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    row = _row(world.db, world.emp["a3"], WorkEventType.OTHER, date(2024, 1, 1))
    with pytest.raises(HTTPException) as e:
        whc.apply_work_history(world.emp["a3"], row.id, world.db, a1.user)
    assert e.value.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
#  Kiêm nhiệm
# ══════════════════════════════════════════════════════════════════════════════

def test_kiem_nhiem_dang_hieu_luc_roi_sua_to_date_ve_hom_qua_thi_go(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    row = _row(world.db, world.emp["a3"], WorkEventType.CONCURRENT,
              date.today() - timedelta(days=10), department_id=world.dept["A.kt"])
    primary_before = world.db.get(Employee, world.emp["a3"]).department_id

    applysvc.apply(world.db, row, a1.user, a1.profile())
    world.db.commit()
    assert world.dept["A.kt"] in dept_svc.extra_departments_of(world.db, world.emp["a3"])

    row.to_date = date.today() - timedelta(days=1)
    world.db.commit()
    changes = applysvc.apply(world.db, row, a1.user, a1.profile())
    world.db.commit()

    assert changes, "đã kết thúc — phải gỡ, phải có thay đổi"
    assert world.dept["A.kt"] not in dept_svc.extra_departments_of(world.db, world.emp["a3"])
    assert world.db.get(Employee, world.emp["a3"]).department_id == primary_before


def test_kiem_nhiem_trung_phong_chinh_khong_nhan_doi(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    emp = world.db.get(Employee, world.emp["a3"])
    row = _row(world.db, world.emp["a3"], WorkEventType.CONCURRENT, date.today(),
              department_id=emp.department_id)

    changes = applysvc.apply(world.db, row, a1.user, a1.profile())
    assert changes == []
    assert emp.department_id not in dept_svc.extra_departments_of(world.db, world.emp["a3"])


# ══════════════════════════════════════════════════════════════════════════════
#  Idempotent (A5)
# ══════════════════════════════════════════════════════════════════════════════

def test_ap_lan_hai_khi_da_khop_thi_khong_doi_gi_nhung_khong_loi(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    pos = _position(world.db, "Nhân viên KD")
    row = _row(world.db, world.emp["a3"], WorkEventType.APPOINT, date.today(), position_id=pos.id)

    whc.apply_work_history(world.emp["a3"], row.id, world.db, a1.user)
    body2 = json.loads(whc.apply_work_history(world.emp["a3"], row.id, world.db, a1.user).body)
    assert body2["data"]["applied_changes"] == []
    assert body2["data"]["item"]["applied_at"] is not None
