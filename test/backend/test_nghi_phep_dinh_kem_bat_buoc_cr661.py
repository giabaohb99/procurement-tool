"""duoc-CR-661 (kh-HR1-2) — cờ «Bắt buộc đính kèm» của loại nghỉ phải được ép LÚC GỬI DUYỆT.

Trước CR này cờ `require_attachment` hiện trên form danh mục nhưng `request_service`
không đọc: Nghỉ ốm không kèm giấy vẫn gửi duyệt được. Chốt đặt ở `prepare_submit`
(không đặt lúc lưu nháp — tệp chỉ treo được vào đơn đã có id).
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.attachment.model import FileLink
from app.modules.employee.model import Employee
from app.modules.leave import request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.schema import LeaveLineItem, LeaveRequestCreate

MONDAY = date(2026, 1, 5)


def _type(db, code, name, **kw):
    kw.setdefault("counts_balance", True)
    kw.setdefault("annual_quota_days", 30.0)
    obj = LeaveType(code=code, name=name, **kw)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture
def world(db):
    emp = Employee(code="NV001", full_name="Nguyễn Văn A", company_id=1, department_id=7)
    db.add(emp)
    db.flush()
    return SimpleNamespace(
        user=SimpleNamespace(id=1, employee_id=emp.id),
        annual=_type(db, "annual", "Phép năm"),
        sick=_type(db, "sick", "Nghỉ ốm", require_attachment=True),
    )


def _draft(db, w, lines):
    return request_service.create(db, LeaveRequestCreate(
        lines=[LeaveLineItem(leave_type_id=lt.id, days=d) for lt, d in lines],
        from_date=MONDAY, to_date=MONDAY + timedelta(days=2), reason="Nghỉ"), w.user)


def _attach(db, obj, entity="leave_request"):
    db.add(FileLink(file_id=1, entity=entity, entity_id=obj.id, created_by=1, updated_by=1))
    db.flush()


def test_thieu_tep_bi_tu_choi_va_cau_neu_ten_loai(db, world):
    obj = _draft(db, world, [(world.sick, 3)])
    with pytest.raises(HTTPException) as exc:
        request_service.prepare_submit(db, obj, world.user)
    assert exc.value.status_code == 400
    assert "\"Nghỉ ốm\"" in exc.value.detail and "đính kèm" in exc.value.detail


def test_co_tep_thi_qua(db, world):
    obj = _draft(db, world, [(world.sick, 3)])
    _attach(db, obj)
    assert request_service.prepare_submit(db, obj, world.user) is not None


def test_loai_khong_bat_co_thi_qua_ma_khong_can_tep(db, world):
    obj = _draft(db, world, [(world.annual, 3)])
    assert request_service.prepare_submit(db, obj, world.user) is not None


def test_don_nhieu_loai_co_mot_loai_bat_co_thi_bi_chan(db, world):
    obj = _draft(db, world, [(world.annual, 2), (world.sick, 1)])
    with pytest.raises(HTTPException) as exc:
        request_service.prepare_submit(db, obj, world.user)
    assert "\"Nghỉ ốm\"" in exc.value.detail
    assert "«Phép năm»" not in exc.value.detail


def test_luu_nhap_khong_bi_chan(db, world):
    #  Chặn chỉ ở gửi duyệt: tạo nháp thiếu tệp phải thành công.
    assert _draft(db, world, [(world.sick, 3)]).id > 0


def test_tep_cua_don_khac_hoac_entity_khac_khong_tinh(db, world):
    obj = _draft(db, world, [(world.sick, 3)])
    db.add(FileLink(file_id=1, entity="leave_request", entity_id=obj.id + 999,
                    created_by=1, updated_by=1))
    _attach(db, obj, entity="purchase_request")
    with pytest.raises(HTTPException):
        request_service.prepare_submit(db, obj, world.user)
