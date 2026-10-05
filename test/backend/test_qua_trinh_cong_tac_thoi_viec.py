"""Quá trình công tác — ÁP «THÔI VIỆC» qua ĐƯỜNG NGHỈ VIỆC SẴN CÓ (Q2, phase 03).

Chốt cốt lõi: áp dòng Thôi việc phải đi ĐÚNG đường `update_employee` mà tab
«Chung» đã dùng từ lâu (bao-CR-400) — khóa tài khoản, đá phiên, audit trên
entity `user`. Bài đầu tiên dưới đây chạy CẢ HAI đường trên hai hồ sơ khác
nhau rồi so kết quả, để chốt chắc «đi đúng đường sẵn có» chứ không phải một
đường ghi riêng trông giống.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.hr_work_history_codes import WorkEventType
from app.modules.audit.model import AuditLog
from app.modules.employee import service as employee_service
from app.modules.employee import work_history_apply_service as applysvc
from app.modules.employee import work_history_controller as whc
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeUpdate
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.modules.employee.work_history_schema import WorkHistoryIn
from app.modules.user.model import User

ACTOR_ID = 1


def _employee_with_user(db, code: str, hire_date=date(2020, 1, 1)) -> tuple[Employee, User]:
    emp = Employee(code=code, full_name=f"NV {code}", is_active=True, hire_date=hire_date,
                   status="official")
    db.add(emp)
    db.flush()
    user = User(email=code, employee_id=emp.id, password_hash="x", is_active=True, token_version=1)
    db.add(user)
    db.commit()
    return emp, user


def _row(db, eid, from_date, event_type=WorkEventType.RESIGN, **kw) -> EmployeeWorkHistory:
    row = EmployeeWorkHistory(employee_id=eid, event_type=int(event_type), from_date=from_date,
                              created_by=ACTOR_ID, updated_by=ACTOR_ID, **kw)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@pytest.fixture
def hr(db, cap_quyen) -> SimpleNamespace:
    """Người làm Nhân sự — `employee.write` phạm vi tất cả, không phải mục tiêu."""
    emp, user = _employee_with_user(db, "HR01")
    cap_quyen(user.id, "employee", scope="all", read=True, write=True)
    db.commit()
    return SimpleNamespace(db=db, user=user, employee=emp)


def _audit_actions(db, entity: str, entity_id: int) -> list[str]:
    return [r.action for r in db.query(AuditLog).filter(
        AuditLog.entity == entity, AuditLog.entity_id == entity_id).all()]


# ══════════════════════════════════════════════════════════════════════════════
#  Cùng kết quả với đường PATCH /employees/{id} sẵn có (Q2)
# ══════════════════════════════════════════════════════════════════════════════

def test_ap_thoi_viec_giong_het_duong_patch_san_co(db, hr):
    """Chạy hai đường trên hai hồ sơ riêng, so thẳng kết quả cuối."""
    via_history, user_history = _employee_with_user(db, "NV_LS")
    via_patch, user_patch = _employee_with_user(db, "NV_PT")
    today = date.today()

    row = _row(db, via_history.id, today)
    applysvc.apply(db, row, hr.user, {})
    db.commit()

    employee_service.update_employee(
        db, via_patch.id, EmployeeUpdate(status=employee_service.STATUS_RESIGNED,
                                         resign_date=today), ACTOR_ID)

    db.refresh(via_history)
    db.refresh(via_patch)
    db.refresh(user_history)
    db.refresh(user_patch)

    assert via_history.status == via_patch.status == employee_service.STATUS_RESIGNED
    assert via_history.resign_date == via_patch.resign_date == today
    assert user_history.is_active is False and user_patch.is_active is False
    assert user_history.token_version == user_patch.token_version == 2
    assert (_audit_actions(db, "user", user_history.id)
           == _audit_actions(db, "user", user_patch.id) == ["deactivate"])


# ══════════════════════════════════════════════════════════════════════════════
#  Các ca ngày
# ══════════════════════════════════════════════════════════════════════════════

def test_ngay_qua_khu_nhap_bu_resign_date_la_ngay_cua_dong(db, hr):
    target, user = _employee_with_user(db, "NV_BU")
    past = date.today() - timedelta(days=30)
    row = _row(db, target.id, past)

    applysvc.apply(db, row, hr.user, {})
    db.commit()
    db.refresh(target)
    db.refresh(user)

    assert target.resign_date == past
    assert user.is_active is False


def test_ngay_mai_400_khong_luu_khi_co_apply(db, hr):
    target, user = _employee_with_user(db, "NV_MAI")
    tomorrow = date.today() + timedelta(days=1)
    data = WorkHistoryIn(event_type=int(WorkEventType.RESIGN), from_date=tomorrow,
                         apply_to_profile=True)

    with pytest.raises(HTTPException) as e:
        whc.create_work_history(target.id, data, db, hr.user)
    assert e.value.status_code == 400
    db.rollback()

    db.refresh(target)
    db.refresh(user)
    assert target.status != employee_service.STATUS_RESIGNED
    assert user.is_active is True
    assert db.query(EmployeeWorkHistory).filter(
        EmployeeWorkHistory.employee_id == target.id).count() == 0


def test_ngay_mai_luu_khong_ap_thi_200_tai_khoan_nguyen(db, hr):
    target, user = _employee_with_user(db, "NV_MAI2")
    tomorrow = date.today() + timedelta(days=1)
    data = WorkHistoryIn(event_type=int(WorkEventType.RESIGN), from_date=tomorrow,
                         apply_to_profile=False)

    whc.create_work_history(target.id, data, db, hr.user)
    db.refresh(user)

    assert user.is_active is True
    assert db.query(EmployeeWorkHistory).filter(
        EmployeeWorkHistory.employee_id == target.id).count() == 1


def test_tu_ngay_truoc_hire_date_400_khong_luu(db, hr):
    target, user = _employee_with_user(db, "NV_SOM", hire_date=date(2025, 1, 1))
    data = WorkHistoryIn(event_type=int(WorkEventType.RESIGN), from_date=date(2024, 1, 1),
                         apply_to_profile=True)

    with pytest.raises(HTTPException) as e:
        whc.create_work_history(target.id, data, db, hr.user)
    assert e.value.status_code == 400
    db.rollback()

    db.refresh(user)
    assert user.is_active is True
    assert db.query(EmployeeWorkHistory).filter(
        EmployeeWorkHistory.employee_id == target.id).count() == 0


# ══════════════════════════════════════════════════════════════════════════════
#  Một giao dịch
# ══════════════════════════════════════════════════════════════════════════════

def test_mot_giao_dich_loi_trong_khoa_tai_khoan_khong_de_lai_gi(db, hr, monkeypatch):
    target, user = _employee_with_user(db, "NV_LOI")

    def _boom(*_a, **_kw):
        raise RuntimeError("ép lỗi để kiểm một giao dịch")
    monkeypatch.setattr(employee_service, "lock_linked_users", _boom)

    data = WorkHistoryIn(event_type=int(WorkEventType.RESIGN), from_date=date.today(),
                         apply_to_profile=True)
    with pytest.raises(RuntimeError):
        whc.create_work_history(target.id, data, db, hr.user)

    db.refresh(target)
    db.refresh(user)
    assert target.status != employee_service.STATUS_RESIGNED
    assert user.is_active is True
    assert db.query(EmployeeWorkHistory).filter(
        EmployeeWorkHistory.employee_id == target.id).count() == 0


# ══════════════════════════════════════════════════════════════════════════════
#  Hồ sơ đã nghỉ việc rồi
# ══════════════════════════════════════════════════════════════════════════════

def test_da_nghi_viec_roi_ap_dong_ngay_khac_chi_doi_resign_date(db, hr):
    target, user = _employee_with_user(db, "NV_DA_NGHI")
    target.status = employee_service.STATUS_RESIGNED
    target.resign_date = date.today() - timedelta(days=100)
    user.is_active = False
    db.commit()

    new_date = date.today() - timedelta(days=10)
    row = _row(db, target.id, new_date)
    changes = applysvc.apply(db, row, hr.user, {})
    db.commit()
    db.refresh(target)

    assert target.resign_date == new_date
    assert target.status == employee_service.STATUS_RESIGNED
    assert changes == [f"Ngày nghỉ việc: → {new_date.isoformat()}"]
    #  Không khóa lại — `has_left_company` chỉ bắt lúc CHUYỂN, không bắt lưu lại y nguyên.
    assert _audit_actions(db, "user", user.id) == []


def test_da_nghi_viec_roi_ap_dong_khop_het_thi_khong_doi_gi(db, hr):
    target, user = _employee_with_user(db, "NV_DA_NGHI2")
    resign_date = date.today() - timedelta(days=100)
    target.status = employee_service.STATUS_RESIGNED
    target.resign_date = resign_date
    user.is_active = False
    db.commit()

    row = _row(db, target.id, resign_date)
    changes = applysvc.apply(db, row, hr.user, {})
    assert changes == []


# ══════════════════════════════════════════════════════════════════════════════
#  Thôi việc là loại nhóm chính — bị chốt «dòng chính mới nhất»
# ══════════════════════════════════════════════════════════════════════════════

def test_thoi_viec_cu_hon_mot_dong_chinh_khac_400(db, hr):
    target, _user = _employee_with_user(db, "NV_REHIRE")
    _row(db, target.id, date.today(), event_type=WorkEventType.HIRE)
    resign_row = _row(db, target.id, date.today() - timedelta(days=60))

    with pytest.raises(HTTPException) as e:
        applysvc.apply(db, resign_row, hr.user, {})
    assert e.value.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
#  Q3 — tự áp cho chính mình
# ══════════════════════════════════════════════════════════════════════════════

def test_tu_ap_thoi_viec_cho_chinh_minh_403(db, cap_quyen):
    emp, user = _employee_with_user(db, "TU_AP")
    cap_quyen(user.id, "employee", scope="all", read=True, write=True)
    row = _row(db, emp.id, date.today())

    with pytest.raises(HTTPException) as e:
        whc.apply_work_history(emp.id, row.id, db, user)
    assert e.value.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
#  Idempotent — áp lần hai
# ══════════════════════════════════════════════════════════════════════════════

def test_ap_lan_hai_khi_da_khop_thi_applied_changes_rong(db, hr):
    target, user = _employee_with_user(db, "NV_LAN2")
    row = _row(db, target.id, date.today())

    whc.apply_work_history(target.id, row.id, db, hr.user)
    import json
    body2 = json.loads(whc.apply_work_history(target.id, row.id, db, hr.user).body)
    assert body2["data"]["applied_changes"] == []
