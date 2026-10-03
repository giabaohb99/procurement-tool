"""Quá trình công tác — VALIDATE, CẢNH BÁO, ĐÓNG DÒNG MỞ, TRẦN, BỘ MÃ (phase 03).

⚠️ SQLite không ép độ dài `VARCHAR` — kiểm `decision_no`/`note` ở TẦNG SCHEMA
(`pytest.raises(ValidationError)`), không ghi DB rồi khẳng định.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core import status_catalog
from app.core.hr_work_history_codes import WorkEventType
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee import work_history_service as whs
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.modules.employee.work_history_schema import WorkHistoryIn, WorkHistoryUpdate

ACTOR = SimpleNamespace(id=1)


# ══════════════════════════════════════════════════════════════════════════════
#  Tầng SCHEMA — 422
# ══════════════════════════════════════════════════════════════════════════════

def test_den_ngay_truoc_tu_ngay_thi_loi():
    with pytest.raises(ValidationError):
        WorkHistoryIn(event_type=int(WorkEventType.APPOINT),
                     from_date=date(2025, 5, 10), to_date=date(2025, 5, 1))


@pytest.mark.parametrize("year", [1899, 2201])
def test_nam_ngoai_dai_1900_2200_thi_loi(year):
    with pytest.raises(ValidationError):
        WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date(year, 1, 1))


@pytest.mark.parametrize("bad", [0, 7, 99])
def test_event_type_gia_tri_la_thi_loi(bad):
    with pytest.raises(ValidationError):
        WorkHistoryIn(event_type=bad, from_date=date(2025, 1, 1))


def test_khoa_la_bi_cam_forbid():
    with pytest.raises(ValidationError):
        WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date(2025, 1, 1),
                     status="resigned")


def test_decision_no_qua_50_ky_tu_thi_loi():
    with pytest.raises(ValidationError):
        WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date(2025, 1, 1),
                     decision_no="x" * 51)


def test_note_qua_500_ky_tu_thi_loi():
    with pytest.raises(ValidationError):
        WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date(2025, 1, 1),
                     note="y" * 501)


def test_update_cung_cam_khoa_la():
    with pytest.raises(ValidationError):
        WorkHistoryUpdate(status="resigned")


def test_update_den_ngay_truoc_tu_ngay_khi_ca_hai_cung_gui_thi_loi():
    with pytest.raises(ValidationError):
        WorkHistoryUpdate(from_date=date(2025, 5, 10), to_date=date(2025, 5, 1))


# ══════════════════════════════════════════════════════════════════════════════
#  Tầng SERVICE — 400
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def emp(db) -> Employee:
    e = Employee(code="KDL01", full_name="Người kiểm dữ liệu", is_active=True)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture
def dept(db) -> Department:
    d = Department(code="PKDL1", name="Phòng KDL 1", is_active=True)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def test_cong_ty_khong_ton_tai_thi_400(db, emp):
    data = WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date(2025, 1, 1),
                         company_id=999999, department_id=1)
    with pytest.raises(HTTPException) as e:
        whs.create(db, emp.id, data, ACTOR)
    assert e.value.status_code == 400


def test_phong_khong_ton_tai_thi_400(db, emp):
    data = WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date(2025, 1, 1),
                         department_id=999999)
    with pytest.raises(HTTPException) as e:
        whs.create(db, emp.id, data, ACTOR)
    assert e.value.status_code == 400


def test_chuc_vu_khong_ton_tai_thi_400(db, emp):
    data = WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date(2025, 1, 1),
                         position_id=999999)
    with pytest.raises(HTTPException) as e:
        whs.create(db, emp.id, data, ACTOR)
    assert e.value.status_code == 400


def test_phong_khong_thuoc_cong_ty_khai_thi_400(db, emp):
    cty_a = Company(code="KDL_CTA", name="Công ty A", is_active=True)
    cty_b = Company(code="KDL_CTB", name="Công ty B", is_active=True)
    db.add_all([cty_a, cty_b])
    db.flush()
    dept_b = Department(code="KDL_PB", name="Phòng B", company_id=cty_b.id, is_active=True)
    db.add(dept_b)
    db.commit()

    data = WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date(2025, 1, 1),
                         company_id=cty_a.id, department_id=dept_b.id)
    with pytest.raises(HTTPException) as e:
        whs.create(db, emp.id, data, ACTOR)
    assert e.value.status_code == 400


def test_chuc_vu_da_ngung_dung_van_ghi_duoc_vao_lich_su(db, emp):
    pos = JobPosition(code="KDL-CV", name="Chức vụ cũ", is_active=False)
    db.add(pos)
    db.commit()
    data = WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date(2025, 1, 1),
                         position_id=pos.id)
    row, _warnings, _closed = whs.create(db, emp.id, data, ACTOR)
    assert row.position_id == pos.id
    assert row.position_label == "Chức vụ cũ"


def test_kiem_nhiem_thieu_phong_thi_400(db, emp):
    data = WorkHistoryIn(event_type=int(WorkEventType.CONCURRENT), from_date=date(2025, 1, 1))
    with pytest.raises(HTTPException) as e:
        whs.create(db, emp.id, data, ACTOR)
    assert e.value.status_code == 400


def test_nhom_chinh_thieu_ca_phong_va_chuc_vu_thi_400(db, emp):
    data = WorkHistoryIn(event_type=int(WorkEventType.APPOINT), from_date=date(2025, 1, 1))
    with pytest.raises(HTTPException) as e:
        whs.create(db, emp.id, data, ACTOR)
    assert e.value.status_code == 400


def test_thoi_viec_khong_can_khai_gi_ca(db, emp):
    data = WorkHistoryIn(event_type=int(WorkEventType.RESIGN), from_date=date(2025, 1, 1))
    row, _w, _c = whs.create(db, emp.id, data, ACTOR)
    assert row.id


# ══════════════════════════════════════════════════════════════════════════════
#  Cảnh báo chồng lấn — #6
# ══════════════════════════════════════════════════════════════════════════════

def test_chong_lan_nhom_chinh_ra_canh_bao(db, emp, dept):
    whs.create(db, emp.id, WorkHistoryIn(event_type=int(WorkEventType.APPOINT),
                                         from_date=date(2025, 1, 1), department_id=dept.id), ACTOR)
    _row2, warnings, _closed = whs.create(db, emp.id, WorkHistoryIn(
        event_type=int(WorkEventType.TRANSFER), from_date=date(2025, 6, 1),
        department_id=dept.id), ACTOR)
    assert warnings, "dòng 2 bắt đầu khi dòng 1 (nhóm chính) chưa kết thúc — phải cảnh báo"


def test_kiem_nhiem_hai_phong_khac_nhau_cung_ngay_khong_canh_bao(db, emp, dept):
    dept2 = Department(code="PKDL2", name="Phòng KDL 2", is_active=True)
    db.add(dept2)
    db.commit()
    whs.create(db, emp.id, WorkHistoryIn(event_type=int(WorkEventType.CONCURRENT),
                                         from_date=date(2025, 1, 1), department_id=dept.id), ACTOR)
    _row2, warnings, _closed = whs.create(db, emp.id, WorkHistoryIn(
        event_type=int(WorkEventType.CONCURRENT), from_date=date(2025, 1, 1),
        department_id=dept2.id), ACTOR)
    assert warnings == []


# ══════════════════════════════════════════════════════════════════════════════
#  close_open_main — #7
# ══════════════════════════════════════════════════════════════════════════════

def test_close_open_main_dong_dung_dong_mo_cu_khong_dung_dong_moi_hon(db, emp, dept):
    old_row, _w1, _c1 = whs.create(db, emp.id, WorkHistoryIn(
        event_type=int(WorkEventType.APPOINT), from_date=date(2024, 1, 1), department_id=dept.id), ACTOR)
    newer_row, _w2, _c2 = whs.create(db, emp.id, WorkHistoryIn(
        event_type=int(WorkEventType.APPOINT), from_date=date(2026, 1, 1), department_id=dept.id), ACTOR)

    _row3, _w3, closed = whs.create(db, emp.id, WorkHistoryIn(
        event_type=int(WorkEventType.TRANSFER), from_date=date(2025, 1, 1), department_id=dept.id,
        close_open_main=True), ACTOR)
    db.commit()   # controller thật commit sau `create` — `refresh` dưới cần nó

    db.refresh(old_row)
    db.refresh(newer_row)
    assert old_row.to_date == date(2024, 12, 31)
    assert newer_row.to_date is None
    assert closed


# ══════════════════════════════════════════════════════════════════════════════
#  Trần 200 dòng/người — #5
# ══════════════════════════════════════════════════════════════════════════════

def test_dong_thu_201_thi_400(db, emp):
    for i in range(whs.MAX_ROWS):
        db.add(EmployeeWorkHistory(
            employee_id=emp.id, event_type=int(WorkEventType.OTHER),
            from_date=date(2000, 1, 1) + timedelta(days=i), created_by=ACTOR.id, updated_by=ACTOR.id))
    db.commit()

    with pytest.raises(HTTPException) as e:
        whs.create(db, emp.id, WorkHistoryIn(
            event_type=int(WorkEventType.OTHER), from_date=date(2020, 1, 1)), ACTOR)
    assert e.value.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
#  Bộ mã — #8
# ══════════════════════════════════════════════════════════════════════════════

def test_bo_ma_work_event_type_du_bay_ma_va_khop_enum():
    cs = status_catalog.get("work_event_type")
    assert len(cs.codes) == 7
    assert cs.values == frozenset(str(int(x)) for x in WorkEventType)
