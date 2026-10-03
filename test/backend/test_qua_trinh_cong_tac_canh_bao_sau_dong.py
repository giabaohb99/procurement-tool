"""Quá trình công tác — lỗi phát hiện lúc kiểm tay bằng Chrome DevTools
03/10/2026 (plan `261003-0837-qua-trinh-lam-viec-nhan-su`): tạo dòng chính mới
với `close_open_main=true` khi có dòng chính đang mở sớm hơn vẫn trả cảnh báo
"Chồng lấn nhóm chính với dòng #..." cho ĐÚNG dòng mà lượt tạo này vừa đóng lại
(`to_date` đặt lùi một ngày trước `from_date` mới — không còn chồng lấn thật).

Nguyên nhân: `work_history_service.create/update` gọi `overlap_warnings` TRƯỚC
`close_open_main`, nên cảnh báo được tính trên dữ liệu CŨ (dòng kia còn
`to_date=None`). Sửa: tính cảnh báo SAU khi đóng, hoặc loại dòng sắp bị đóng
khỏi phép so — cả hai cách đều phải cho cùng kết quả: `close_open_main=True` ăn
HẾT cảnh báo chồng lấn với đúng dòng vừa đóng; `close_open_main=False` thì VẪN
phải cảnh báo (không được âm thầm nuốt cảnh báo thật)."""
from datetime import date
from types import SimpleNamespace

import pytest

from app.core.hr_work_history_codes import WorkEventType
from app.modules.department.model import Department
from app.modules.employee import work_history_service as whs
from app.modules.employee.model import Employee
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.modules.employee.work_history_schema import WorkHistoryIn, WorkHistoryUpdate

ACTOR = SimpleNamespace(id=1)


@pytest.fixture
def emp(db) -> Employee:
    e = Employee(code="CB01", full_name="Người kiểm cảnh báo", is_active=True)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture
def dept(db) -> Department:
    #  TRANSFER ∈ POSITION_TRACK — Validate #3 bắt ít nhất phòng hoặc chức vụ.
    d = Department(code="PCB01", name="Phòng kiểm cảnh báo", is_active=True)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def _open_main_row(db, eid: int, from_date: date) -> EmployeeWorkHistory:
    """Dòng chính ĐANG MỞ (`to_date=None`) — mồi cho `close_open_main`."""
    row = EmployeeWorkHistory(employee_id=eid, event_type=int(WorkEventType.HIRE),
                              from_date=from_date, created_by=ACTOR.id, updated_by=ACTOR.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_create_voi_close_open_main_true_khong_canh_bao_chong_lan_voi_dong_vua_dong(db, emp, dept):
    old = _open_main_row(db, emp.id, date(2026, 1, 1))

    _row, warnings, closed = whs.create(db, emp.id, WorkHistoryIn(
        event_type=int(WorkEventType.TRANSFER), from_date=date(2026, 4, 1),
        department_id=dept.id, close_open_main=True), ACTOR)

    assert len(closed) == 1, "close_open_main=True phải đóng đúng dòng #1 đang mở"
    assert not any(f"#{old.id}" in w for w in warnings), (
        f"dòng #{old.id} đã bị đóng ngày trước from_date mới (không còn chồng lấn thật) — "
        f"KHÔNG được còn trong cảnh báo chồng lấn. warnings={warnings}")


def test_create_voi_close_open_main_false_van_canh_bao_chong_lan(db, emp, dept):
    old = _open_main_row(db, emp.id, date(2026, 1, 1))

    _row, warnings, closed = whs.create(db, emp.id, WorkHistoryIn(
        event_type=int(WorkEventType.TRANSFER), from_date=date(2026, 4, 1),
        department_id=dept.id, close_open_main=False), ACTOR)

    assert closed == [], "close_open_main=False — không đóng dòng nào"
    assert any(f"#{old.id}" in w for w in warnings), (
        "close_open_main=False: dòng cũ VẪN đang mở, chồng lấn thật — phải cảnh báo")


def test_update_voi_close_open_main_true_khong_canh_bao_chong_lan_voi_dong_vua_dong(db, emp, dept):
    old = _open_main_row(db, emp.id, date(2026, 1, 1))
    editing = EmployeeWorkHistory(employee_id=emp.id, event_type=int(WorkEventType.TRANSFER),
                                  from_date=date(2026, 2, 1), department_id=dept.id,
                                  created_by=ACTOR.id, updated_by=ACTOR.id)
    db.add(editing)
    db.commit()
    db.refresh(editing)

    _row, warnings, closed = whs.update(db, emp.id, editing.id, WorkHistoryUpdate(
        from_date=date(2026, 4, 1), close_open_main=True), ACTOR)

    assert len(closed) == 1
    assert not any(f"#{old.id}" in w for w in warnings), (
        f"PATCH với close_open_main=True cũng phải tính cảnh báo SAU khi đóng dòng #{old.id}")
