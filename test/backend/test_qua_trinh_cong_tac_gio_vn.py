"""Quá trình công tác — GIỜ VIỆT NAM (H2, review backend 03/10/2026).

Container chạy UTC. Bốn chỗ (`apply_gate`, `apply()`, `_apply_concurrent`,
`serialize_list`) từng dùng thẳng `date.today()` — đọc NGÀY UTC, lệch với
NGÀY VIỆT NAM từ 00:00 đến 06:59 giờ VN (= 17:00-23:59 UTC hôm trước). Gộp về
`app.core.vn_time.vn_today()`, test ở đây khoá đồng hồ vào đúng khung giờ đó
để lỗi không còn phụ thuộc giờ thật lúc chạy bộ test.
"""
from datetime import date, datetime, time, timedelta

from app.core import vn_time
from app.core.hr_work_history_codes import WorkEventType
from app.modules.employee import department_service as dept_svc
from app.modules.employee import work_history_apply_service as applysvc
from app.modules.employee.model import Employee
from app.modules.employee.work_history_model import EmployeeWorkHistory

ACTOR = 1


def _row(db, eid, event_type, from_date, **kw) -> EmployeeWorkHistory:
    row = EmployeeWorkHistory(employee_id=eid, event_type=int(event_type), from_date=from_date,
                              created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _mock_vn_clock(monkeypatch, utc_value: datetime) -> None:
    """Khoá `vn_today()` vào một mốc UTC cố định — patch ĐÚNG MỘT chỗ
    (`app.core.vn_time.datetime`), đủ cho MỌI nơi gọi `vn_today()` bất kể nhập
    theo tên nào (`from ... import vn_today` vẫn chạy trong namespace của
    `vn_time` lúc gọi)."""
    class _FixedDatetime(datetime):
        @classmethod
        def utcnow(cls):
            return utc_value
    monkeypatch.setattr(vn_time, "datetime", _FixedDatetime)


def test_ap_duoc_dong_hom_nay_theo_gio_vn_du_utc_con_la_hom_truoc(world, monkeypatch):
    """06:30 sáng giờ VN = 23:30 UTC HÔM TRƯỚC. Dòng có `from_date` = hôm nay
    THEO GIỜ VN phải áp được ngay — lỗi cũ đọc ngày UTC (còn là hôm trước) nên
    từ chối nhầm «Chưa tới ngày hiệu lực»."""
    real_today = date.today()
    vn_today_fake = real_today + timedelta(days=1)   # "hôm nay" theo giờ VN lúc 06:30
    _mock_vn_clock(monkeypatch, datetime.combine(real_today, time(23, 30)))

    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    row = _row(world.db, world.emp["a3"], WorkEventType.APPOINT, vn_today_fake,
              department_id=world.dept["A.kt"])

    changes = applysvc.apply(world.db, row, a1.user, a1.profile())
    assert changes, "dòng hiệu lực từ HÔM NAY (giờ VN) phải áp được ngay, không bị chặn"


def test_kiem_nhiem_het_han_hom_qua_gio_vn_thi_go_du_utc_chua_qua_ngay(world, monkeypatch):
    """Cùng mốc 06:30 giờ VN. Một dòng kiêm nhiệm `to_date = hôm qua GIỜ VN`
    (= hôm nay theo UTC) phải bị coi là HẾT HẠN và gỡ khỏi phòng kiêm nhiệm —
    lỗi cũ còn thấy `to_date >= date.today()` (ngày UTC) nên giữ nhầm."""
    real_today = date.today()
    vn_today_fake = real_today + timedelta(days=1)
    _mock_vn_clock(monkeypatch, datetime.combine(real_today, time(23, 30)))

    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    emp = world.db.get(Employee, world.emp["a3"])
    dept_svc.set_extra_departments(world.db, emp, [world.dept["A.kt"]], ACTOR)
    world.db.commit()

    row = _row(world.db, world.emp["a3"], WorkEventType.CONCURRENT, real_today,
              to_date=real_today, department_id=world.dept["A.kt"])

    changes = applysvc.apply(world.db, row, a1.user, a1.profile())
    assert changes, "to_date = hôm qua GIỜ VN — phải coi là hết hạn, phải gỡ"
    assert vn_today_fake > row.to_date   # cho người đọc thấy rõ chiều lệch
    assert world.dept["A.kt"] not in dept_svc.extra_departments_of(world.db, world.emp["a3"])
