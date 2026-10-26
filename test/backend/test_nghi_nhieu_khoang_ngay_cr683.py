"""ĐƠN NGHỈ NHIỀU KHOẢNG NGÀY (duoc-CR-683) — phase 1: mô hình + nghiệp vụ.

Ví dụ của chủ sản phẩm: 27/10/2026 (T3) cả ngày + 03/11 (T3) chiều → 07/11 (T7) cả ngày,
lịch mặc định T2–T7 → ngày từng khoảng `[1, 4.5]`, tổng 5.5, đầu đơn 27/10 → 07/11.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.employee.model import Employee
from app.modules.leave import request_periods, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LR_PENDING, SESSION_AFTERNOON, SESSION_FULL
from app.modules.leave.period_spans import period_text, periods_by_request
from app.modules.leave.request_model import LeaveRequest, LeaveRequestPeriod
from app.modules.leave.schema import (LeavePeriodItem, LeaveRequestCreate,
                                      LeaveRequestUpdate)

D = date


def _setup(db):
    lt = LeaveType(code="annual", name="Phép năm", counts_balance=False)
    emp = Employee(code="NV001", full_name="Nguyễn Văn A", company_id=1, department_id=7)
    db.add_all([lt, emp])
    db.flush()
    return lt, emp, SimpleNamespace(id=1, employee_id=emp.id)


def _p(a, b, fs=SESSION_FULL, ts=SESSION_FULL):
    return LeavePeriodItem(from_date=a, to_date=b, from_session=fs, to_session=ts)


def _create(db, lt, user, periods, **kw):
    return request_service.create(db, LeaveRequestCreate(
        leave_type_id=lt.id, periods=periods, reason="Việc riêng", **kw), user)


def _rows(db, rid):
    return (db.query(LeaveRequestPeriod).filter_by(request_id=rid)
            .order_by(LeaveRequestPeriod.sort_order).all())


PRODUCT_OWNER = [_p(D(2026, 10, 27), D(2026, 10, 27)),
                 _p(D(2026, 11, 3), D(2026, 11, 7), SESSION_AFTERNOON, SESSION_FULL)]


def test_vi_du_chu_san_pham(db):
    lt, emp, user = _setup(db)
    obj = _create(db, lt, user, PRODUCT_OWNER)
    assert [r.days for r in _rows(db, obj.id)] == [1.0, 4.5]
    assert obj.total_days == 5.5
    assert (obj.from_date, obj.to_date) == (D(2026, 10, 27), D(2026, 11, 7))
    assert (obj.from_session, obj.to_session) == (SESSION_FULL, SESSION_FULL)


def test_payload_cu_ra_dung_mot_khoang(db):
    lt, emp, user = _setup(db)
    obj = request_service.create(db, LeaveRequestCreate(
        leave_type_id=lt.id, from_date=D(2026, 10, 27), to_date=D(2026, 10, 29),
        reason="x"), user)
    rows = _rows(db, obj.id)
    assert len(rows) == 1 and rows[0].days == obj.total_days == 3.0


def test_khong_co_periods_va_khong_co_ngay_la_422():
    with pytest.raises(ValidationError):
        LeaveRequestCreate(leave_type_id=1, reason="x")


def test_tran_20_khoang_va_dai_nam():
    many = [_p(D(2026, 1, i + 1), D(2026, 1, i + 1)) for i in range(21)]
    with pytest.raises(ValidationError):
        LeaveRequestCreate(leave_type_id=1, periods=many)
    with pytest.raises(ValidationError):
        _p(D(1999, 1, 1), D(1999, 1, 2))
    with pytest.raises(ValidationError):
        LeavePeriodItem(from_date=D(2026, 1, 1), to_date=D(2026, 1, 2), from_session=9)


@pytest.mark.parametrize("periods,needle", [
    ([_p(D(2026, 10, 27), D(2026, 10, 29)), _p(D(2026, 10, 29), D(2026, 10, 30))], "chồng ngày"),
    ([_p(D(2026, 10, 29), D(2026, 10, 27)), _p(D(2026, 11, 3), D(2026, 11, 4))], "Khoảng thứ 1"),
    ([_p(D(2026, 12, 29), D(2026, 12, 30)), _p(D(2027, 1, 5), D(2027, 1, 6))], "cùng một năm"),
    ([_p(D(2026, 10, 27), D(2026, 10, 27), 4, 4), _p(D(2026, 11, 3), D(2026, 11, 3))], "theo giờ"),
])
def test_khoang_sai_bi_chan(db, periods, needle):
    lt, emp, user = _setup(db)
    with pytest.raises(HTTPException) as e:
        _create(db, lt, user, periods)
    assert needle in e.value.detail


def test_vat_nam_422_va_mot_khoang_vat_nam_van_cho(db):
    lt, emp, user = _setup(db)
    with pytest.raises(HTTPException) as e:
        _create(db, lt, user, [_p(D(2026, 12, 29), D(2026, 12, 30)), _p(D(2027, 1, 5), D(2027, 1, 6))])
    assert e.value.status_code == 422
    obj = _create(db, lt, user, [_p(D(2026, 12, 30), D(2027, 1, 4))])
    assert len(_rows(db, obj.id)) == 1


def test_khoang_khong_co_ngay_lam_viec_bi_chan_ke_ca_khi_sua_de(db):
    lt, emp, user = _setup(db)
    sundays = [_p(D(2026, 11, 1), D(2026, 11, 1)), _p(D(2026, 11, 8), D(2026, 11, 8))]
    with pytest.raises(HTTPException) as e:
        _create(db, lt, user, sundays)
    assert "Khoảng thứ 1" in e.value.detail
    #  M2 (review CR-683): sửa đè số ngày KHÔNG mở được khoảng 0 ngày làm việc.
    with pytest.raises(HTTPException) as e2:
        _create(db, lt, user, sundays, total_days=2)
    assert e2.value.status_code == 400 and "Khoảng thứ 1" in e2.value.detail


def test_tran_check_lines_tinh_theo_ngay_lich_cua_khoang_khong_tinh_khe(db):
    lt, emp, user = _setup(db)
    # hai khoảng 1 ngày (tổng 2 ngày lịch), bao ngoài 8 ngày: gõ tay 5 phải bị chặn
    with pytest.raises(HTTPException) as e:
        _create(db, lt, user, [_p(D(2026, 10, 27), D(2026, 10, 27)),
                               _p(D(2026, 11, 3), D(2026, 11, 3))], total_days=5)
    assert "nhiều hơn" in e.value.detail


def test_chot_trung_ngay_theo_khoang_khe_khong_chan(db):
    lt, emp, user = _setup(db)
    first = _create(db, lt, user, PRODUCT_OWNER)
    first.status = LR_PENDING
    db.commit()
    in_gap = _create(db, lt, user, [_p(D(2026, 10, 29), D(2026, 10, 29))])
    assert request_periods.find_overlap(db, emp.id, request_periods.periods_of(db, in_gap)) is None
    hit = _create(db, lt, user, [_p(D(2026, 11, 4), D(2026, 11, 4))])
    with pytest.raises(HTTPException) as e:
        request_service.check_overlap(db, emp.id, D(2026, 11, 4), D(2026, 11, 4))
    assert first.code in e.value.detail and "trùng khoảng ngày" in e.value.detail
    with pytest.raises(HTTPException):
        request_periods.raise_if_overlap(db, emp.id, request_periods.periods_of(db, hit),
                                         exclude_id=hit.id)


def test_don_dung_tay_khong_co_dong_khoang_roi_ve_dau_don(db):
    lt, emp, user = _setup(db)
    raw = LeaveRequest(code="NP-X", employee_id=emp.id, leave_type_id=lt.id,
                       from_date=D(2026, 10, 27), to_date=D(2026, 10, 28), total_days=2,
                       status=LR_PENDING)
    db.add(raw)
    db.flush()
    got = periods_by_request(db, [raw.id])[raw.id]
    assert len(got) == 1 and got[0].to_date == D(2026, 10, 28) and got[0].id == 0
    assert request_periods.find_overlap(db, emp.id, [got[0]]) is not None


def test_sua_don_patch(db):
    lt, emp, user = _setup(db)
    obj = _create(db, lt, user, PRODUCT_OWNER)
    # vắng periods + có ô ngày trên đơn 2 khoảng → 400
    with pytest.raises(HTTPException) as e:
        request_service.update(db, obj, LeaveRequestUpdate(to_date=D(2026, 11, 8)), user)
    assert "2 khoảng ngày" in e.value.detail
    # vắng hết → giữ khoảng, tính lại ngày như cũ
    request_service.update(db, obj, LeaveRequestUpdate(reason="đổi lý do"), user)
    assert [r.days for r in _rows(db, obj.id)] == [1.0, 4.5] and obj.total_days == 5.5
    # có periods → ghi đè, đầu đơn tính lại
    request_service.update(db, obj, LeaveRequestUpdate(
        periods=[_p(D(2026, 10, 27), D(2026, 10, 28))]), user)
    assert len(_rows(db, obj.id)) == 1 and obj.total_days == 2.0
    assert obj.to_date == D(2026, 10, 28)
    # đơn 1 khoảng: sửa ô ngày như cũ
    request_service.update(db, obj, LeaveRequestUpdate(to_date=D(2026, 10, 29)), user)
    assert obj.total_days == 3.0 and _rows(db, obj.id)[0].to_date == D(2026, 10, 29)


def test_period_text():
    from app.modules.leave.period_spans import PeriodView
    got = period_text([PeriodView(D(2026, 10, 27), D(2026, 10, 27)),
                       PeriodView(D(2026, 11, 3), D(2026, 11, 7), SESSION_AFTERNOON, SESSION_FULL)])
    assert got == "27/10/2026 · 03/11 (chiều) → 07/11/2026"


# ── Phase 3 ── «Ai làm / ai nghỉ», hồ sơ làm việc ngày, tải việc: ngày KHE không phải ngày nghỉ ──

def _raw_two_period_leave(db, emp, d1, d2a, d2b, status=3):
    """Đơn dựng tay: đầu đơn là bao ngoài [d1, d2b], hai dòng khoảng [d1] và [d2a..d2b]."""
    req = LeaveRequest(code=f"NP-P3-{emp.id}-{d1:%m%d}", company_id=emp.company_id,
                       department_id=emp.department_id, employee_id=emp.id, leave_type_id=0,
                       from_date=d1, to_date=d2b, status=status)
    db.add(req)
    db.flush()
    db.add_all([
        LeaveRequestPeriod(request_id=req.id, from_date=d1, to_date=d1, sort_order=0, days=1),
        LeaveRequestPeriod(request_id=req.id, from_date=d2a, to_date=d2b, sort_order=1, days=3),
    ])
    db.flush()
    return req


def test_p3_roster_ngay_khe_trong_va_khoang_hai_bat_dau_buoi_chieu(db, cap_quyen):
    from app.core.scoping import get_perm_profile
    from app.modules.user.model import User
    from app.modules.work_schedule.roster_service import build_roster
    from lich_lam_viec_factory import make_world

    _, _, emp = make_world(db, "P3R")
    user = User(email="p3-roster@dego.vn", employee_id=0, is_active=True)
    db.add(user)
    db.commit()
    cap_quyen(user.id, "employee", scope="all", read=True)
    cap_quyen(user.id, "leave_request", scope="all", read=True)
    req = _raw_two_period_leave(db, emp, D(2026, 10, 27), D(2026, 11, 3), D(2026, 11, 6))
    second = (db.query(LeaveRequestPeriod).filter_by(request_id=req.id, sort_order=1).one())
    second.from_session = SESSION_AFTERNOON                       # 03/11 chỉ chiều
    db.commit()
    p = {"from_date": D(2026, 10, 26), "to_date": D(2026, 11, 8), "company_id": 0, "department_id": 0,
         "q": "", "page": 1, "page_size": 50}
    data = build_roster(db, user, get_perm_profile(db, user), p)
    row = next(i for i in data["items"] if i["employee_id"] == emp.id)
    cell = {str(c["date"]): c["leave"] for c in row["cells"]}
    assert cell["2026-10-27"] and cell["2026-10-27"]["morning"] and cell["2026-10-27"]["afternoon"]
    for gap in ("2026-10-28", "2026-10-29", "2026-10-30", "2026-11-02"):
        assert cell[gap] is None, gap
    assert (cell["2026-11-03"]["morning"], cell["2026-11-03"]["afternoon"]) == (False, True)
    assert cell["2026-11-04"]["morning"] and cell["2026-11-06"]["afternoon"]


def test_p3_roster_don_khong_co_dong_khoang_van_to_theo_dau_don(db, cap_quyen):
    from app.core.scoping import get_perm_profile
    from app.modules.user.model import User
    from app.modules.work_schedule.roster_leave import load_leaves
    from lich_lam_viec_factory import make_world

    _, _, emp = make_world(db, "P3N")
    user = User(email="p3-raw@dego.vn", employee_id=0, is_active=True)
    db.add(user)
    db.commit()
    cap_quyen(user.id, "leave_request", scope="all", read=True)
    db.add(LeaveRequest(code="NP-P3-RAW", company_id=emp.company_id, department_id=emp.department_id,
                        employee_id=emp.id, leave_type_id=0, from_date=D(2026, 10, 27),
                        to_date=D(2026, 10, 29), status=3))
    db.commit()
    p = {"from_date": D(2026, 10, 26), "to_date": D(2026, 11, 1)}
    got = load_leaves(db, user, get_perm_profile(db, user), [emp.id], p)
    assert [(s.from_date, s.to_date) for s, _ in got[emp.id]] == [(D(2026, 10, 27), D(2026, 10, 29))]


def test_p3_ho_so_ngay_trong_khe_leave_days_0_va_hai_dau_van_nghi(db, monkeypatch):
    from app.modules.usage_profile.daily_builder import aggregate_day
    from app.modules.usage_profile.model import UsageDaily
    from ho_so_lam_viec_factory import make_company, make_dept, make_person

    company = make_company(db)
    dept = make_dept(db, company)
    user, emp = make_person(db, "P3H", company, dept)
    _raw_two_period_leave(db, emp, D(2026, 1, 5), D(2026, 1, 8), D(2026, 1, 8))   # T2 + T5; khe T3, T4
    db.commit()
    monkeypatch.setattr("app.modules.usage_profile.daily_builder.vn_today", lambda: D(2026, 1, 20))
    got = {}
    for day in (D(2026, 1, 5), D(2026, 1, 6), D(2026, 1, 7), D(2026, 1, 8)):
        aggregate_day(db, day)
        got[day.day] = db.query(UsageDaily).filter_by(user_id=user.id, day=day).one().leave_days
    assert got == {5: 1.0, 6: 0.0, 7: 0.0, 8: 1.0}


def test_p3_tai_viec_khoang_khe_khong_dem_va_on_leave_today_sai(db):
    from app.modules.capability import workload_service as wl
    from app.modules.capability.workload_sources import leaves_in_window
    from lich_lam_viec_factory import make_world

    _, _, emp = make_world(db, "P3W")
    _raw_two_period_leave(db, emp, D(2026, 10, 27), D(2026, 11, 3), D(2026, 11, 7))
    db.commit()
    today = D(2026, 10, 29)
    got = leaves_in_window(db, [emp.id], today, D(2026, 11, 12))
    assert sorted((a, b) for _, a, b in got) == [(D(2026, 11, 3), D(2026, 11, 7))]
    on_today, days = wl._leave_numbers(got, today, 14)
    assert emp.id not in on_today and days[emp.id] == 5


# ── Phase 2 ── API (periods ở mọi bản dump, estimate-periods), giấy GNP, Trợ lý AI / agent_hub ──

def _body(resp):
    import json
    return json.loads(resp.body)["data"]


def _count_queries(db, fn):
    from sqlalchemy import event

    box = {"n": 0}
    engine = db.get_bind()

    def _hit(*_a, **_k):
        box["n"] += 1
    event.listen(engine, "before_cursor_execute", _hit)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", _hit)
    return box["n"]


def test_p2_dump_co_periods_va_nhan_buoi(db):
    from app.modules.leave import request_serializer as rs

    lt, emp, user = _setup(db)
    obj = _create(db, lt, user, PRODUCT_OWNER)
    data = rs.dump_request(obj, {}, {}, rs.lines_by_request(db, {obj.id}), rs.periods_for(db, {obj.id}))
    assert [p["days"] for p in data["periods"]] == [1.0, 4.5]
    assert data["periods"][1]["from_session"] == SESSION_AFTERNOON
    assert data["periods"][1]["from_session_label"] == "Buổi chiều"
    assert data["periods"][0]["to_session_label"] == "Cả ngày"
    assert set(data["periods"][0]) == {"id", "from_date", "from_session", "from_session_label", "to_date",
                                       "to_session", "to_session_label", "days", "sort_order"}
    assert (data["from_date"], data["to_date"]) == (D(2026, 10, 27), D(2026, 11, 7))


def test_p2_dump_khong_truyen_periods_thi_dung_tu_dau_don(db):
    from app.modules.leave import request_serializer as rs

    lt, emp, user = _setup(db)
    obj = _create(db, lt, user, PRODUCT_OWNER)
    data = rs.dump_request(obj, {}, {})
    assert len(data["periods"]) == 1 and data["periods"][0]["id"] == 0
    assert data["periods"][0]["to_date"] == D(2026, 11, 7)


def test_p2_so_truy_van_gom_periods_khong_doi_theo_so_don(db):
    from app.modules.leave import request_serializer as rs

    lt, emp, user = _setup(db)
    first = _create(db, lt, user, [_p(D(2026, 1, 5), D(2026, 1, 5))])
    one = _count_queries(db, lambda: rs.periods_for(db, {first.id}))
    ids = {first.id}
    for week in range(1, 7):      # thứ Hai và thứ Tư của mỗi tuần: đều là ngày làm việc
        mon = D(2026, 1, 5) + timedelta(days=7 * week)
        ids.add(_create(db, lt, user, [_p(mon, mon), _p(mon + timedelta(days=2), mon + timedelta(days=2))]).id)
    many = _count_queries(db, lambda: rs.periods_for(db, ids))
    assert one == many == 1


def test_p2_estimate_periods_vi_du_chu_san_pham(db):
    from app.modules.leave import request_controller as rc
    from app.modules.leave.schema import LeaveEstimateIn

    lt, emp, user = _setup(db)
    out = _body(rc.estimate_periods(LeaveEstimateIn(
        employee_id=emp.id, leave_type_id=lt.id, periods=PRODUCT_OWNER), db=db, user=user))
    assert [p["days"] for p in out["periods"]] == [1.0, 4.5]
    assert out["total_days"] == 5.5
    assert "schedule_name" in out


def test_p2_estimate_periods_loi_kiem_tra_nhu_khi_lap_don(db):
    from app.modules.leave import request_controller as rc
    from app.modules.leave.schema import LeaveEstimateIn

    lt, emp, user = _setup(db)
    chong = LeaveEstimateIn(employee_id=emp.id, leave_type_id=lt.id,
                            periods=[_p(D(2026, 10, 27), D(2026, 10, 29)), _p(D(2026, 10, 29), D(2026, 10, 30))])
    with pytest.raises(HTTPException) as err:
        rc.estimate_periods(chong, db=db, user=user)
    assert err.value.status_code == 400 and "chồng ngày" in err.value.detail
    vat_nam = LeaveEstimateIn(employee_id=emp.id, leave_type_id=lt.id,
                              periods=[_p(D(2026, 12, 30), D(2026, 12, 30)), _p(D(2027, 1, 4), D(2027, 1, 4))])
    with pytest.raises(HTTPException) as err:
        rc.estimate_periods(vat_nam, db=db, user=user)
    assert err.value.status_code == 422


def test_p2_estimate_days_cu_van_chay(db):
    from app.modules.leave import request_controller as rc

    lt, emp, user = _setup(db)
    out = _body(rc.estimate_days("2026-10-27", "2026-10-28", leave_type_id=lt.id, db=db, user=user))
    assert out["total_days"] == 2.0


def test_p2_gnp_metadata_nhan_leave_periods_chi_khi_tu_hai_khoang():
    from app.modules.document.type_metadata import _check_leave

    base = {"from_date": "2026-10-27", "to_date": "2026-11-07", "reason": "Việc riêng", "total_days": 5.5}
    periods = [{"from_date": "2026-10-27", "to_date": "2026-10-27", "from_session": "full",
                "to_session": "full", "days": 1},
               {"from_date": "2026-11-03", "to_date": "2026-11-07", "from_session": "afternoon",
                "to_session": "full", "days": 4.5}]
    got = _check_leave({**base, "leave_periods": periods}, 5)
    assert got["leave_periods"] == periods
    assert (got["from_date"], got["to_date"]) == ("2026-10-27", "2026-11-07")
    #  Một khoảng, phần tử hỏng, đến trước từ: đều bị bỏ -> metadata y hệt cũ.
    assert "leave_periods" not in _check_leave({**base, "leave_periods": periods[:1]}, 5)
    broken = [periods[0], "x", {"from_date": "rac", "to_date": "2026-11-01"},
              {"from_date": "2026-11-05", "to_date": "2026-11-01"}]
    assert "leave_periods" not in _check_leave({**base, "leave_periods": broken}, 5)
    assert "leave_periods" not in _check_leave(base, 5)
    many = [dict(periods[0], from_date=f"2026-01-{i:02d}", to_date=f"2026-01-{i:02d}") for i in range(1, 29)]
    assert len(_check_leave({**base, "leave_periods": many}, 5)["leave_periods"]) == 20


def test_p2_gnp_document_periods_tu_don_hai_khoang(db):
    from app.modules.leave import approval_bridge

    lt, emp, user = _setup(db)
    obj = _create(db, lt, user, PRODUCT_OWNER)
    got = approval_bridge._document_periods(db, obj)["leave_periods"]
    assert [(p["from_date"], p["from_session"], p["to_date"], p["days"]) for p in got] == [
        ("2026-10-27", "full", "2026-10-27", 1.0), ("2026-11-03", "afternoon", "2026-11-07", 4.5)]
    one = _create(db, lt, user, [_p(D(2026, 12, 1), D(2026, 12, 2))])
    assert approval_bridge._document_periods(db, one) == {}


def test_p2_hoan_tac_giu_nguyen_cac_khoang_khong_gop(db):
    from app.modules.assistant import change_service as cs

    lt, emp, user = _setup(db)
    obj = _create(db, lt, user, PRODUCT_OWNER)
    full = cs._leave_full(db, obj)
    assert [(p["from_date"], p["to_date"], p["from_session"]) for p in full["periods"]] == [
        ("2026-10-27", "2026-10-27", 1), ("2026-11-03", "2026-11-07", 3)]
    #  Đổi thành một khoảng liền (gộp), rồi hoàn tác -> phải về đúng hai khoảng.
    request_service.update(db, obj, LeaveRequestUpdate(periods=[_p(D(2026, 10, 27), D(2026, 11, 7))]), user)
    assert len(request_periods.periods_of(db, obj)) == 1
    cs._restore_leave(db, user, obj, full)
    db.refresh(obj)
    rows = _rows(db, obj.id)
    assert [(r.from_date, r.to_date, r.from_session, r.days) for r in rows] == [
        (D(2026, 10, 27), D(2026, 10, 27), 1, 1.0), (D(2026, 11, 3), D(2026, 11, 7), 3, 4.5)]
    assert obj.total_days == 5.5


def test_p2_hoan_tac_anh_cu_khong_co_periods_dung_mot_khoang(db):
    from app.modules.assistant import change_service as cs

    lt, emp, user = _setup(db)
    obj = _create(db, lt, user, [_p(D(2026, 10, 27), D(2026, 10, 28))])
    full = cs._leave_full(db, obj)
    full.pop("periods")
    request_service.update(db, obj, LeaveRequestUpdate(periods=[_p(D(2026, 11, 2), D(2026, 11, 3))]), user)
    cs._restore_leave(db, user, obj, full)
    assert [(r.from_date, r.to_date) for r in _rows(db, obj.id)] == [(D(2026, 10, 27), D(2026, 10, 28))]


def test_p2_update_tool_don_nhieu_khoang_tu_choi_from_to_nhung_nhan_periods(db):
    from app.modules.assistant.tools import update_tool as ut

    lt, emp, user = _setup(db)
    obj = _create(db, lt, user, PRODUCT_OWNER)
    fields, err = ut._clean_changes("leave_request", {"to_date": "2026-11-08"})
    assert err is None
    _, leave_error = ut._check_leave_change(db, obj, fields)
    assert leave_error and "periods" in leave_error and "2 khoảng" in leave_error
    #  Sửa lý do vẫn được.
    fields, _ = ut._clean_changes("leave_request", {"reason": "Lý do mới"})
    assert ut._check_leave_change(db, obj, fields)[1] is None
    #  Gửi cả hai kiểu -> từ chối.
    fields, err = ut._clean_changes("leave_request", {"to_date": "2026-11-08", "periods": [
        {"from_date": "2026-10-27", "to_date": "2026-10-27"}, {"from_date": "2026-11-03", "to_date": "2026-11-08"}]})
    assert "HOẶC" in ut._check_leave_change(db, obj, fields)[1]


def test_p2_update_tool_periods_de_xuat_va_ghi(db):
    from app.modules.assistant.tools import update_tool as ut

    lt, emp, user = _setup(db)
    obj = _create(db, lt, user, PRODUCT_OWNER)
    fields, err = ut._clean_changes("leave_request", {"periods": [
        {"from_date": "2026-11-03", "to_date": "2026-11-07", "from_session": "afternoon"},
        {"from_date": "2026-10-27", "to_date": "2026-10-28"}]})
    assert err is None
    shown, leave_error = ut._check_leave_change(db, obj, fields)
    assert leave_error is None
    assert shown["periods"].startswith("27/10/2026")           # đã sắp theo ngày
    assert ut._old_value(db, "leave_request", obj, "periods") == period_text(periods_by_request(db, [obj.id])[obj.id])
    #  Idempotent: token xác nhận chứa lại đúng hình đã làm sạch.
    again, err = ut._clean_changes("leave_request", {"periods": fields["periods"]})
    assert err is None and again["periods"] == fields["periods"]
    ut._update_leave(db, user, obj, fields)
    db.refresh(obj)
    assert [(r.from_date, r.to_date, r.from_session) for r in _rows(db, obj.id)] == [
        (D(2026, 10, 27), D(2026, 10, 28), 1), (D(2026, 11, 3), D(2026, 11, 7), 3)]
    assert obj.total_days == 6.5


def test_p2_update_tool_periods_hong_bi_tu_choi():
    from app.modules.assistant.tools import update_tool as ut

    assert ut._clean_changes("leave_request", {"periods": []})[1]
    assert ut._clean_changes("leave_request", {"periods": [{"from_date": "x", "to_date": "2026-01-01"}]})[1]
    assert ut._clean_changes("leave_request", {"periods": [
        {"from_date": "2026-01-01", "to_date": "2026-01-01", "from_session": "toi"}]})[1]
    assert ut._clean_changes("leave_request", {"periods": [
        {"from_date": "2026-01-01", "to_date": "2026-01-01"}] * 21})[1]


def _ctx_ai(db, seed, monkeypatch):
    from app.modules.assistant.tools.base import ToolContext
    from app.modules.user.model import User

    monkeypatch.setattr(ToolContext, "can", lambda self, entity, action="read": True)
    return ToolContext(db=db, user=db.get(User, seed.u_req_id))


def _loai_nghi(db):
    lt = LeaveType(code="annual", name="Phép năm", counts_balance=False, is_active=True)
    db.add(lt)
    db.flush()
    return lt


def test_p2_draft_tool_soan_nhieu_khoang(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave

    _loai_nghi(db)
    out = _run_leave(_ctx_ai(db, seed, monkeypatch), {
        "reason": "Việc riêng", "leave_type": "annual", "periods": [
            {"from_date": "2026-11-03", "to_date": "2026-11-07", "from_session": "afternoon"},
            {"from_date": "2026-10-27", "to_date": "2026-10-27"}]})
    assert out["status"] == "ready", out
    draft = out["draft"]
    assert (draft["from_date"], draft["to_date"]) == ("2026-10-27", "2026-11-07")
    assert [(p["from_date"], p["to_date"], p["from_session"], p["to_session"]) for p in draft["periods"]] == [
        ("2026-10-27", "2026-10-27", 1, 1), ("2026-11-03", "2026-11-07", 3, 1)]
    assert out["total_days"] == 5.5 and draft["lines"][0]["days"] == 5.5
    assert out["periods_text"] == "27/10/2026 · 03/11 (chiều) → 07/11/2026"


def test_p2_draft_tool_payload_cu_van_chay_va_co_periods_mot_phan_tu(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave

    _loai_nghi(db)
    out = _run_leave(_ctx_ai(db, seed, monkeypatch), {
        "from_date": "2026-10-27", "to_date": "2026-10-28", "reason": "Việc riêng", "leave_type": "annual"})
    assert out["status"] == "ready"
    assert out["draft"]["periods"] == [{"from_date": "2026-10-27", "to_date": "2026-10-28",
                                        "from_session": 1, "to_session": 1}]


def test_p2_draft_tool_khoang_chong_ngay_theo_gio_va_vat_nam_bi_chan(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave

    _loai_nghi(db)
    ctx = _ctx_ai(db, seed, monkeypatch)
    common = {"reason": "Việc riêng", "leave_type": "annual"}
    chong = _run_leave(ctx, {**common, "periods": [{"from_date": "2026-10-27", "to_date": "2026-10-29"},
                                                    {"from_date": "2026-10-29", "to_date": "2026-10-30"}]})
    assert "chồng ngày" in chong["error"]
    nam = _run_leave(ctx, {**common, "periods": [{"from_date": "2026-12-30", "to_date": "2026-12-30"},
                                                  {"from_date": "2027-01-04", "to_date": "2027-01-04"}]})
    assert "cùng một năm" in nam["error"]
    gio = _run_leave(ctx, {**common, "periods": [
        {"from_date": "2026-10-27", "to_date": "2026-10-27"}, {"from_date": "2026-11-03", "to_date": "2026-11-03"}],
        "from_session": "hourly"})
    assert gio["status"] == "ready"     # from_session ở gốc bị bỏ qua khi có periods
    sai = _run_leave(ctx, {**common, "periods": [{"from_date": "2026-10-27"}]})
    assert "error" in sai


def test_p2_draft_tool_canh_bao_trung_khong_bao_nham_ngay_khe(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave

    lt = _loai_nghi(db)
    other = LeaveRequest(code="NP-KHE", company_id=seed.company_id, department_id=seed.dept_id,
                         employee_id=seed.emp_req_id, leave_type_id=lt.id, from_date=D(2026, 10, 27),
                         to_date=D(2026, 11, 7), total_days=5.5, status=LR_PENDING)
    db.add(other)
    db.flush()
    db.add_all([LeaveRequestPeriod(request_id=other.id, from_date=D(2026, 10, 27), to_date=D(2026, 10, 27),
                                   sort_order=0, days=1),
                LeaveRequestPeriod(request_id=other.id, from_date=D(2026, 11, 3), to_date=D(2026, 11, 7),
                                   sort_order=1, days=4.5)])
    db.flush()
    ctx = _ctx_ai(db, seed, monkeypatch)
    khe = _run_leave(ctx, {"from_date": "2026-10-29", "to_date": "2026-10-30", "reason": "Việc riêng",
                           "leave_type": "annual"})
    assert not [w for w in khe["warnings"] if "NP-KHE" in w]
    trung = _run_leave(ctx, {"from_date": "2026-11-04", "to_date": "2026-11-04", "reason": "Việc riêng",
                             "leave_type": "annual"})
    warn = [w for w in trung["warnings"] if "NP-KHE" in w]
    assert warn and "27/10/2026 · 03/11 → 07/11/2026" in warn[0]


def test_p2_leave_tool_tra_periods(db, seed):
    from app.modules.assistant import tools as T
    from app.modules.user.model import User

    lt = _loai_nghi(db)
    req = LeaveRequest(code="NP-P2", company_id=seed.company_id, department_id=seed.dept_id,
                       employee_id=seed.emp_req_id, leave_type_id=lt.id, from_date=D(2026, 10, 27),
                       to_date=D(2026, 11, 7), total_days=5.5, status=LR_PENDING, created_by=seed.u_req_id)
    db.add(req)
    db.flush()
    db.add_all([LeaveRequestPeriod(request_id=req.id, from_date=D(2026, 10, 27), to_date=D(2026, 10, 27),
                                   sort_order=0, days=1),
                LeaveRequestPeriod(request_id=req.id, from_date=D(2026, 11, 3), from_session=SESSION_AFTERNOON,
                                   to_date=D(2026, 11, 7), sort_order=1, days=4.5)])
    db.commit()
    me = db.get(User, seed.u_req_id)
    from app.core.scoping import get_perm_profile  # noqa: F401
    import app.modules.assistant.tools.base as base
    orig = base.ToolContext.can
    base.ToolContext.can = lambda self, entity, action="read": True
    try:
        out = T.run_tool(db, me, "my_leave_summary", {})
    finally:
        base.ToolContext.can = orig
    row = next(r for r in out["requests"] if r["code"] == "NP-P2")
    assert len(row["periods"]) == 2 and row["periods"][1]["days"] == 4.5
    assert row["periods"][1]["from_session_label"] == "Buổi chiều"
    assert row["periods_text"] == "27/10/2026 · 03/11 (chiều) → 07/11/2026"
    assert "from_date_to_date" in out["glossary"]


def test_p2_agent_hub_tao_nhap_nhieu_khoang_va_tom_tat(db, seed):
    from app.modules.agent_hub import draft_create as dc

    lt = _loai_nghi(db)
    draft = {"lines": [{"leave_type_id": lt.id, "leave_type": "Phép năm", "days": 5.5}],
             "from_date": "2026-10-27", "to_date": "2026-11-07", "from_session": 1, "to_session": 1,
             "periods": [{"from_date": "2026-10-27", "to_date": "2026-10-27", "from_session": 1, "to_session": 1},
                         {"from_date": "2026-11-03", "to_date": "2026-11-07", "from_session": 3, "to_session": 1}],
             "reason": "Việc riêng"}
    assert any("2 khoảng" in line and "03/11 (chiều)" in line for line in dc.summarize("leave", draft))
    from app.modules.user.model import User
    me = db.get(User, seed.u_req_id)
    code, oid = dc._create_leave(db, me, draft)
    assert [(r.from_date, r.to_date, r.from_session, r.days) for r in _rows(db, oid)] == [
        (D(2026, 10, 27), D(2026, 10, 27), 1, 1.0), (D(2026, 11, 3), D(2026, 11, 7), 3, 4.5)]
    mine = [x for x in dc.list_mine(db, me) if x["kind"] == "leave"]
    assert mine[0]["title"].startswith("Nghỉ 27/10/2026 · 03/11 (chiều) → 07/11/2026")
    #  Ngày khe KHÔNG trùng; ngày trong khoảng thì trùng.
    khe = {"from_date": "2026-10-29", "to_date": "2026-10-30"}
    assert dc.same_days_leave(mine, khe) is None
    assert dc.same_days_leave(mine, {"from_date": "2026-11-05", "to_date": "2026-11-05"}) is not None


def test_p2_agent_hub_draft_cu_khong_co_periods_van_tao(db, seed):
    from app.modules.agent_hub import draft_create as dc
    from app.modules.user.model import User

    lt = _loai_nghi(db)
    me = db.get(User, seed.u_req_id)
    code, oid = dc._create_leave(db, me, {
        "lines": [{"leave_type_id": lt.id, "days": 2}], "from_date": "2026-10-27", "to_date": "2026-10-28",
        "reason": "Việc riêng"})
    assert len(_rows(db, oid)) == 1


# ── Phase 5 ── vòng đời đầy đủ: lập → gửi → duyệt/từ chối → hủy, sổ quỹ THEO DÒNG với 2 khoảng ──

def _quota_types(db):
    """Hai loại có sổ quỹ riêng — sổ lệch giữa các loại mới lộ ra khi đơn có nhiều khoảng."""
    annual = LeaveType(code="annual5", name="Phép năm", counts_balance=True, annual_quota_days=12.0)
    unpaid = LeaveType(code="unpaid5", name="Nghỉ không lương", counts_balance=True,
                       annual_quota_days=30.0)
    db.add_all([annual, unpaid])
    db.flush()
    return annual, unpaid


class _Inst:
    updated_by = 1
    finish_reason = ""


def _two_period_two_line(db):
    from app.modules.leave.schema import LeaveLineItem
    annual, unpaid = _quota_types(db)
    emp = Employee(code="NV005", full_name="Trần Thị B", company_id=1, department_id=7)
    db.add(emp)
    db.flush()
    user = SimpleNamespace(id=1, employee_id=emp.id)
    obj = request_service.create(db, LeaveRequestCreate(
        periods=PRODUCT_OWNER, reason="Việc riêng",
        lines=[LeaveLineItem(leave_type_id=annual.id, days=3.5),
               LeaveLineItem(leave_type_id=unpaid.id, days=2.0)]), user)
    return annual, unpaid, emp, user, obj


def _bal(db, emp, lt):
    from app.modules.leave import balance_service
    row = balance_service.get_balance(db, emp.id, 2026, lt.id)
    return (row.pending_days, row.used_days) if row else (0.0, 0.0)


def _submit5(db, obj, emp, user):
    employee = request_service.prepare_submit(db, obj, user)
    return request_service.mark_submitted(db, obj, employee, user)


def test_p5_tong_dong_chia_tren_hai_khoang_va_khoang_van_du_hai_dong(db):
    annual, unpaid, emp, user, obj = _two_period_two_line(db)
    assert obj.total_days == 5.5
    assert [r.days for r in _rows(db, obj.id)] == [1.0, 4.5]
    assert {l.leave_type_id: l.days for l in request_service.lines_of(db, obj.id)} == {
        annual.id: 3.5, unpaid.id: 2.0}


def test_p5_gui_duyet_giu_cho_theo_dong_khong_theo_khoang(db):
    from app.modules.leave.constants import LR_PENDING as PEND
    annual, unpaid, emp, user, obj = _two_period_two_line(db)
    _submit5(db, obj, emp, user)
    assert obj.status == PEND
    assert _bal(db, emp, annual) == (3.5, 0.0) and _bal(db, emp, unpaid) == (2.0, 0.0)


def test_p5_duyet_roi_huy_hoan_dung_tung_dong(db):
    from app.modules.leave import approval_bridge
    from app.modules.leave.constants import LR_APPROVED as APPR
    annual, unpaid, emp, user, obj = _two_period_two_line(db)
    _submit5(db, obj, emp, user)
    approval_bridge._on_approved(db, obj.id, _Inst())
    db.commit()
    assert obj.status == APPR
    assert _bal(db, emp, annual) == (0.0, 3.5) and _bal(db, emp, unpaid) == (0.0, 2.0)
    request_service.cancel(db, obj, "Đổi ý", emp.id)
    assert _bal(db, emp, annual) == (0.0, 0.0) and _bal(db, emp, unpaid) == (0.0, 0.0)
    assert len(_rows(db, obj.id)) == 2      # hủy đơn không đụng các khoảng


@pytest.mark.parametrize("hook", ["_on_rejected", "_on_returned", "_on_withdrawn"])
def test_p5_ba_ket_cuc_khong_duyet_tra_lai_quy_don_hai_khoang(db, hook):
    from app.modules.leave import approval_bridge
    annual, unpaid, emp, user, obj = _two_period_two_line(db)
    _submit5(db, obj, emp, user)
    getattr(approval_bridge, hook)(db, obj.id, _Inst())
    db.commit()
    assert _bal(db, emp, annual) == (0.0, 0.0) and _bal(db, emp, unpaid) == (0.0, 0.0)


def test_p5_huy_don_dang_cho_tra_lai_quy(db):
    annual, unpaid, emp, user, obj = _two_period_two_line(db)
    _submit5(db, obj, emp, user)
    request_service.cancel(db, obj, "Đổi ý", emp.id)
    assert _bal(db, emp, annual) == (0.0, 0.0) and _bal(db, emp, unpaid) == (0.0, 0.0)


def test_p5_gui_duyet_chan_khi_don_khac_cham_khoang_hai(db):
    """Đơn thứ hai nằm trong khe thì gửi được; chạm khoảng 2 thì chặn LÚC GỬI."""
    annual, unpaid, emp, user, obj = _two_period_two_line(db)
    _submit5(db, obj, emp, user)
    gap = _create(db, annual, user, [_p(D(2026, 10, 29), D(2026, 10, 29))])
    _submit5(db, gap, emp, user)       # khe: không chặn
    hit = _create(db, annual, user, [_p(D(2026, 11, 5), D(2026, 11, 5))])
    with pytest.raises(HTTPException) as e:
        _submit5(db, hit, emp, user)
    assert obj.code in e.value.detail


def test_p5_payload_cu_co_lines_khong_periods_van_chay_mot_khoang(db):
    from app.modules.leave.schema import LeaveLineItem
    annual, unpaid = _quota_types(db)
    emp = Employee(code="NV006", full_name="Lê C", company_id=1, department_id=7)
    db.add(emp)
    db.flush()
    user = SimpleNamespace(id=1, employee_id=emp.id)
    obj = request_service.create(db, LeaveRequestCreate(
        from_date=D(2026, 1, 5), to_date=D(2026, 1, 8), reason="Về quê",
        lines=[LeaveLineItem(leave_type_id=annual.id, days=3), LeaveLineItem(
            leave_type_id=unpaid.id, days=1)]), user)
    rows = _rows(db, obj.id)
    assert len(rows) == 1 and rows[0].days == obj.total_days == 4.0


def test_p5_vat_nam_422_qua_schema_service_va_message_tach_hai_don(db):
    lt, emp, user = _setup(db)
    with pytest.raises(HTTPException) as e:
        _create(db, lt, user, [_p(D(2026, 12, 29), D(2026, 12, 29)), _p(D(2027, 1, 5), D(2027, 1, 5))])
    assert e.value.status_code == 422 and "Tách thành hai đơn" in e.value.detail


# ── Review fixes ─────────────────────────────────────────────────────────────

def test_review_m2_khoang_chu_nhat_van_bi_chan_du_dong_co_so_sua_day(db):
    from app.modules.leave.schema import LeaveLineItem
    lt, emp, user = _setup(db)
    with pytest.raises(HTTPException) as e:
        _create(db, lt, user, [_p(D(2026, 10, 27), D(2026, 10, 27)), _p(D(2026, 11, 1), D(2026, 11, 1))],
                lines=[LeaveLineItem(leave_type_id=lt.id, days=1)])
    assert e.value.status_code == 400 and "Khoảng thứ 2 (01/11 → 01/11)" in e.value.detail


def test_review_m1_the_duyet_ai_hien_khoang_that_va_tong_ngay(db):
    from app.modules.assistant.tools.approval_action_tool import _summary
    lt, emp, user = _setup(db)
    obj = _create(db, lt, user, PRODUCT_OWNER)
    rows = {r["label"]: r["value"] for r in _summary(db, "leave_request", obj)}
    assert "Từ ngày" not in rows and "Đến ngày" not in rows
    assert rows["Số ngày"] == "5,5 ngày"
    assert rows["Thời gian nghỉ"] == period_text(request_periods.periods_of(db, obj))


def test_review_low_a_buoi_dang_so_khong_thanh_ca_ngay():
    from app.modules.assistant.tools.draft_tool import _session_code
    from app.modules.leave.constants import SESSION_MORNING
    assert [_session_code(v) for v in (1, "2", 3, "morning", None)] == [
        SESSION_FULL, SESSION_MORNING, SESSION_AFTERNOON, SESSION_MORNING, SESSION_FULL]
