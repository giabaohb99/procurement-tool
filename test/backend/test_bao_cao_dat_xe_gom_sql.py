"""Chứng minh TƯƠNG ĐƯƠNG của bản GOM Ở SQL (`vehicle_booking/report_grouped_fetch.py` +
`report_turnaround_sql.py`) với bản per-row CŨ (review hiệu năng 01/10/2026 — xem
`frontend-v2/plans/reports/fullstack-developer-261001-1103-load-test-8-bao-cao-moi.md` §2:
105 lượt hỏi IN(...) chia lô của `turnaround_hours()` chiếm 70% thời gian ở mốc 3 năm/50k
phiếu, mục tiêu <1s/<20MB/≤10 câu lệnh cùng quy mô).

Bản CŨ không còn trong mã nguồn (đã thay hẳn), nên tệp này GIỮ LẠI một bản sao `_legacy_*`
Y HỆT per-row logic trước khi sửa (đọc trực tiếp từ nội dung tệp cũ, chỉ đổi tiền tố tên hàm)
làm ĐỐI CHỨNG ĐỘC LẬP — vẫn dùng `app.modules.approval.report_turnaround.turnaround_hours`
thật (tệp đó KHÔNG đổi) nên phép so sánh không tự lừa chính nó. Hai bản cùng chạy qua CÙNG
một khung `report_aggregate.build_report()` (không đổi), chỉ khác `fetch`/`ReportSpec`.

Ba nhóm bài kiểm:
  1. `test_gom_sql_ra_dung_y_het_ban_cu` — ma trận (kỳ so sánh × group_by) trên một bộ dữ
     liệu phong phú (nhiều trạng thái/loại/công ty/phòng ban/xe/tài xế/người yêu cầu, phiếu
     gửi lại duyệt — ĐÃ KẾT THÚC hai lần, phiên chỉ ĐANG CHẠY, phiên thiếu mốc, nháp, xóa mềm).
  2. `test_dat_xe_resubmit_lay_phien_moi_nhat_khong_phai_phien_dau` — kiểm TAY (không qua đối
     chứng) rằng JOIN `MAX(id)` chọn đúng phiên KẾT THÚC MỚI NHẤT, không phải phiên đầu.
  3. `test_benchmark_gom_sql_o_quy_mo_50k` — đo thời gian/bộ nhớ/số câu lệnh ở quy mô ~50k
     phiếu/3 năm NGAY TRONG DB SQLite của pytest (không thay cho đo MySQL thật — xem docstring
     bài đó).
"""
from __future__ import annotations

import time
import tracemalloc
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import event, insert
from starlette.datastructures import QueryParams

from app.core.auth import get_perm_profile
from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_period import parse_period, range_filter, to_local_date
from app.core.scoping import apply_scope
from app.modules.approval.instance_model import (INSTANCE_APPROVED, INSTANCE_REJECTED,
                                                 INSTANCE_RUNNING, ApprovalInstance)
from app.modules.approval.report_turnaround import turnaround_hours
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.report.procurement_summary_rows import valid_company_id
from app.modules.vehicle_booking import model as vm
from app.modules.vehicle_booking import report_controller as veh_rc
from app.modules.vehicle_booking.schema import VehicleBookingCreate
from app.modules.vehicle_booking.service import create_booking

# ══════════════════════════════════════════════════════════════════════════════
#  ĐỐI CHỨNG: bản per-row CŨ, chép nguyên — KHÔNG sửa khi sửa bản mới ở trên.
# ══════════════════════════════════════════════════════════════════════════════

_BAD_STATUSES = (vm.BK_REJECTED, vm.BK_CANCELLED)

_LEGACY_FETCH_COLUMNS = (
    vm.VehicleBooking.id, vm.VehicleBooking.start_time, vm.VehicleBooking.status,
    vm.VehicleBooking.request_type, vm.VehicleBooking.company_id, vm.VehicleBooking.department_id,
    vm.VehicleBooking.assigned_vehicle_id, vm.VehicleBooking.assigned_driver_id,
    vm.VehicleBooking.requester_id, vm.VehicleBooking.requester,
    vm.VehicleBooking.distance_km, vm.VehicleBooking.cost, vm.VehicleBooking.passenger_count,
)


def _legacy_id_name_map(db, id_col, name_col, ids):
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return dict(db.query(id_col, name_col).filter(id_col.in_(ids)).all())


def _legacy_decorate(db, rows, group_by=None):
    companies = (_legacy_id_name_map(db, Company.id, Company.name, {r.company_id for r in rows})
                if group_by == "company" else {})
    depts = (_legacy_id_name_map(db, Department.id, Department.name,
                                 {r.department_id for r in rows}) if group_by == "department" else {})
    vehicles = {}
    if group_by == "vehicle":
        ids = {r.assigned_vehicle_id for r in rows if r.assigned_vehicle_id}
        if ids:
            vehicles = {v.id: (f"{v.license_plate} — {v.model}" if v.model else v.license_plate)
                       for v in db.query(vm.Vehicle).filter(vm.Vehicle.id.in_(ids)).all()}
    drivers = (_legacy_id_name_map(db, vm.Driver.id, vm.Driver.name,
                                   {r.assigned_driver_id for r in rows}) if group_by == "driver" else {})
    hours = turnaround_hours(db, "vehicle_booking", [r.id for r in rows])

    out = []
    for r in rows:
        out.append({
            "start_time": r.start_time, "status": r.status, "request_type": r.request_type,
            "company_id": r.company_id, "company_name": companies.get(r.company_id, ""),
            "department_id": r.department_id, "department_name": depts.get(r.department_id, ""),
            "vehicle_id": r.assigned_vehicle_id,
            "vehicle_label": vehicles.get(r.assigned_vehicle_id, ""),
            "driver_id": r.assigned_driver_id, "driver_label": drivers.get(r.assigned_driver_id, ""),
            "requester_id": r.requester_id, "requester": r.requester or "",
            "distance_km": r.distance_km or 0, "cost": r.cost or 0,
            "passenger_count": r.passenger_count or 0,
            "approval_hours": hours.get(r.id),
        })
    return out


def _legacy_build_spec() -> ReportSpec:
    metrics = [
        MetricSpec("requests", "Yêu cầu", kind="int", value_of=lambda r: 1),
        MetricSpec("completed", "Chuyến hoàn thành", kind="int",
                  value_of=lambda r: 1 if r["status"] == vm.BK_COMPLETED else 0),
        MetricSpec("rejected_cancelled", "Từ chối + hủy", kind="int", helper=True,
                  value_of=lambda r: 1 if r["status"] in _BAD_STATUSES else 0),
        MetricSpec("distance_km", "Tổng km", kind="int",
                  value_of=lambda r: round(r["distance_km"] or 0)),
        MetricSpec("cost", "Chi phí", kind="money", value_of=lambda r: r["cost"]),
        MetricSpec("passengers", "Hành khách", kind="int", value_of=lambda r: r["passenger_count"]),
        MetricSpec("approval_hours_sum", "Tổng giờ duyệt", kind="hours", helper=True,
                  value_of=lambda r: r["approval_hours"] if r["approval_hours"] is not None else 0),
        MetricSpec("approval_hours_count", "Số phiếu có giờ duyệt", kind="int", helper=True,
                  value_of=lambda r: 1 if r["approval_hours"] is not None else 0),
    ]
    derived = [
        DerivedSpec("reject_cancel_rate", "Tỷ lệ từ chối + hủy", num="rejected_cancelled",
                   den="requests", kind="percent", good="down"),
        DerivedSpec("avg_approval_hours", "Thời gian duyệt TB", num="approval_hours_sum",
                   den="approval_hours_count", kind="hours", good="down", scale=1),
    ]
    dimensions = {
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r["company_id"], r["company_name"])] if r["company_id"] else [])),
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r["department_id"], r["department_name"])] if r["department_id"] else [])),
        "request_type": DimensionSpec("request_type", "Loại yêu cầu", key_of=lambda r: (
            [(r["request_type"], vm.REQUEST_TYPE_LABELS.get(r["request_type"], ""))])),
        "status": DimensionSpec("status", "Trạng thái", key_of=lambda r: (
            [(r["status"], vm.BOOKING_STATUS_LABELS.get(r["status"], ""))])),
        "vehicle": DimensionSpec("vehicle", "Xe", key_of=lambda r: (
            [(r["vehicle_id"], r["vehicle_label"])] if r["vehicle_id"] else [])),
        "driver": DimensionSpec("driver", "Tài xế", key_of=lambda r: (
            [(r["driver_id"], r["driver_label"])] if r["driver_id"] else [])),
        "requester": DimensionSpec("requester", "Người yêu cầu", key_of=lambda r: (
            [(r["requester_id"], r["requester"])] if r["requester_id"] else [])),
    }
    breakdowns = {"status": dimensions["status"], "request_type": dimensions["request_type"]}
    return ReportSpec(date_of=lambda r: to_local_date(r["start_time"]), metrics=metrics,
                      derived=derived, dimensions=dimensions, breakdowns=breakdowns)


def _legacy_fetch_builder(db, user, prof, group_by, company_id):
    def fetch(d_from, d_to):
        q = (db.query(vm.VehicleBooking)
             .filter(vm.VehicleBooking.is_deleted == False,  # noqa: E712
                     vm.VehicleBooking.status != vm.BK_DRAFT))
        q = apply_scope(q, vm.VehicleBooking, "vehicle_booking", user, prof)
        if company_id is not None:
            q = q.filter(vm.VehicleBooking.company_id == company_id)
        q = q.filter(range_filter(vm.VehicleBooking.start_time, "str", d_from, d_to))
        rows = q.with_entities(*_LEGACY_FETCH_COLUMNS).all()
        return _legacy_decorate(db, rows, group_by)
    return fetch


def _legacy_result(db, user, params: dict) -> dict:
    prof = get_perm_profile(db, user)
    period = parse_period(QueryParams([(k, str(v)) for k, v in params.items()]))
    group_by = params.get("group_by") or None
    cid = valid_company_id(params.get("company_id"))
    return build_report(_legacy_fetch_builder(db, user, prof, group_by, cid),
                        _legacy_build_spec(), period, group_by=group_by)


# ══════════════════════════════════════════════════════════════════════════════
#  Hạ tầng dùng chung
# ══════════════════════════════════════════════════════════════════════════════

def _req(**params) -> SimpleNamespace:
    return SimpleNamespace(query_params=QueryParams([(k, str(v)) for k, v in params.items()]))


def _unwrap(resp) -> dict:
    import json
    return json.loads(resp.body)["data"]


def _new_result(db, user, params: dict) -> dict:
    return _unwrap(veh_rc.booking_summary(_req(**params), db, user))


def _count_queries(db, fn):
    counted: list[str] = []

    def _on_exec(conn, cursor, statement, *args):
        counted.append(statement)

    event.listen(db.get_bind(), "before_cursor_execute", _on_exec)
    try:
        result = fn()
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", _on_exec)
    return result, counted


def _actor(db, *, uid: int, code: str, dept: int, company: int) -> SimpleNamespace:
    emp = Employee(code=code, full_name=code, email=f"{code}@dego.vn",
                   department_id=dept, company_id=company)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=uid, employee_id=emp.id, email=f"{code}@dego.vn")


def _instance(db, booking_id: int, status: int, started, finished) -> None:
    db.add(ApprovalInstance(entity="vehicle_booking", entity_id=booking_id, flow_id=1,
                            status=status, started_at=started, finished_at=finished))
    db.flush()


def _params(compare: str, group_by: str | None, **extra) -> dict:
    p = {"preset": "custom", "date_from": CUR_FROM.isoformat(), "date_to": CUR_TO.isoformat(),
         "compare": compare}
    if group_by:
        p["group_by"] = group_by
    p.update(extra)
    return p


# ══════════════════════════════════════════════════════════════════════════════
#  Bộ dữ liệu phong phú (nhỏ, dùng cho ma trận tương đương)
# ══════════════════════════════════════════════════════════════════════════════

CUR_FROM, CUR_TO = date(2025, 2, 1), date(2025, 8, 15)
CTY1, CTY2 = 7001, 7002
DEPT1, DEPT2 = 7101, 7102


def _build_world(db, compare_mode: str) -> SimpleNamespace:
    """Dựng phiếu CHO MỌI `compare_mode` giống nhau ở cửa sổ HIỆN TẠI; chỉ thêm phiếu ở cửa
    sổ SO SÁNH khi `compare_mode != "none"` — biên của cửa sổ đó đọc từ CHÍNH `parse_period`
    (không tự tính tay) để không lệch mép do tính nhầm lịch/năm nhuận."""
    actor1 = _actor(db, uid=9001, code="RQ1", dept=DEPT1, company=CTY1)
    actor2 = _actor(db, uid=9002, code="RQ2", dept=DEPT2, company=CTY2)
    actor3 = _actor(db, uid=9003, code="RQ3", dept=DEPT1, company=CTY1)

    veh1, veh2 = vm.Vehicle(license_plate="51A-999.99", model="Fortuner"), vm.Vehicle(
        license_plate="51B-888.88", model="")
    drv1, drv2 = vm.Driver(name="Tài xế X"), vm.Driver(name="Tài xế Y")
    db.add_all([veh1, veh2, drv1, drv2])
    db.flush()

    bookings: dict[str, vm.VehicleBooking] = {}

    def mk(key, actor, *, when, status, rtype=vm.TYPE_CAR, km=0.0, cost=0, pax=1,
          veh=None, drv=None, dept=None, deleted=False, submit=True):
        data = VehicleBookingCreate(request_type=rtype, purpose="Kiểm thử", start_location="VP",
                                    end_location="Kho", start_time=f"{when}T08:00",
                                    end_time=f"{when}T08:00", passenger_count=pax)
        b = create_booking(db, data, actor, submit=submit)
        if status is not None:
            b.status = status
        b.distance_km, b.cost, b.passenger_count = km, cost, pax
        if veh is not None:
            b.assigned_vehicle_id = veh
        if drv is not None:
            b.assigned_driver_id = drv
        if dept is not None:
            b.department_id = dept
        b.is_deleted = deleted
        db.flush()
        bookings[key] = b
        return b

    #  ---- Cửa sổ HIỆN TẠI — giống nhau ở MỌI `compare_mode` ----
    mk("c1", actor1, when="2025-02-05", status=vm.BK_APPROVED, km=12.3, cost=150000, pax=3,
       veh=veh1.id, drv=drv1.id)
    mk("c2", actor2, when="2025-02-05", status=vm.BK_COMPLETED, rtype=vm.TYPE_DELIVERY,
       km=45.7, cost=300000, pax=1, veh=veh2.id, drv=drv2.id, dept=0)   # phòng CHƯA GẮN
    mk("c3", actor3, when="2025-03-10", status=vm.BK_REJECTED, km=8.4, cost=50000, pax=2)
    mk("c4", actor1, when="2025-03-10", status=vm.BK_CANCELLED, rtype=vm.TYPE_DELIVERY,
       km=0.0, cost=0, pax=1)
    mk("c5", actor2, when="2025-04-20", status=vm.BK_DISPATCHED, km=100.9, cost=800000, pax=4,
       veh=veh1.id)
    mk("c6", actor3, when="2025-05-01", status=vm.BK_PENDING, km=33.3, cost=120000, pax=2,
       drv=drv1.id)
    mk("c7", actor1, when="2025-06-15", status=vm.BK_RETURNED, rtype=vm.TYPE_DELIVERY,
       km=7.6, cost=20000, pax=1)
    mk("c8", actor2, when="2025-07-01", status=vm.BK_COMPLETED, km=19.2, cost=90000, pax=2,
       veh=veh2.id, drv=drv1.id)
    mk("c_draft", actor1, when="2025-07-02", status=None, submit=False)        # BK_DRAFT, loại
    mk("c_deleted", actor1, when="2025-07-03", status=vm.BK_APPROVED, deleted=True)  # xóa mềm, loại

    b_resubmit = mk("c_resubmit", actor2, when="2025-07-20", status=vm.BK_APPROVED,
                    km=5.0, cost=10000, pax=1)
    _instance(db, b_resubmit.id, INSTANCE_REJECTED,
             datetime(2025, 7, 20, 8, 0), datetime(2025, 7, 20, 9, 0))      # 1h — BỊ GHI ĐÈ
    _instance(db, b_resubmit.id, INSTANCE_APPROVED,
             datetime(2025, 7, 21, 8, 0), datetime(2025, 7, 21, 13, 0))     # 5h — THẮNG (id sau)

    b_running = mk("c_running", actor1, when="2025-07-25", status=vm.BK_APPROVED, km=2.0)
    _instance(db, b_running.id, INSTANCE_RUNNING, datetime(2025, 7, 25, 8, 0), None)

    b_missing = mk("c_missing_start", actor2, when="2025-07-28", status=vm.BK_APPROVED, km=3.0)
    _instance(db, b_missing.id, INSTANCE_APPROVED, None, datetime(2025, 7, 28, 10, 0))

    b_rej_turn = mk("c_rejected_turn", actor3, when="2025-08-01", status=vm.BK_REJECTED, km=1.5)
    _instance(db, b_rej_turn.id, INSTANCE_REJECTED,
             datetime(2025, 8, 1, 8, 0), datetime(2025, 8, 1, 8, 30))       # 0.5h

    b_simple = mk("c_simple_turn", actor2, when="2025-08-10", status=vm.BK_APPROVED, km=4.0,
                 cost=70000, pax=2, veh=veh2.id, drv=drv2.id)
    _instance(db, b_simple.id, INSTANCE_APPROVED,
             datetime(2025, 8, 10, 8, 0), datetime(2025, 8, 10, 9, 15))     # 1.25h

    mk("c9", actor3, when="2025-08-15", status=vm.BK_APPROVED, rtype=vm.TYPE_DELIVERY,
       km=0.0, cost=0, pax=1)

    mk("out_of_range", actor1, when="2023-01-01", status=vm.BK_APPROVED, km=999, cost=999)

    #  ---- Cửa sổ SO SÁNH — biên lấy từ `parse_period`, chỉ dựng khi có so sánh ----
    if compare_mode != "none":
        p = parse_period(QueryParams([("preset", "custom"), ("date_from", CUR_FROM.isoformat()),
                                      ("date_to", CUR_TO.isoformat()), ("compare", compare_mode)]))
        cf, ct = p.compare_from, p.compare_to
        mid = cf + (ct - cf) // 2
        mk(f"cmp1_{compare_mode}", actor1, when=(cf + timedelta(days=1)).isoformat(),
           status=vm.BK_APPROVED, km=10.0, cost=40000, pax=2, veh=veh1.id)
        mk(f"cmp2_{compare_mode}", actor2, when=mid.isoformat(), status=vm.BK_COMPLETED,
           rtype=vm.TYPE_DELIVERY, km=20.0, cost=60000, pax=1, drv=drv2.id)
        mk(f"cmp3_{compare_mode}", actor3, when=(ct - timedelta(days=1)).isoformat(),
           status=vm.BK_REJECTED, km=5.0, cost=0, pax=1)
        b_cmp_turn = mk(f"cmp_turn_{compare_mode}", actor1, when=mid.isoformat(),
                       status=vm.BK_APPROVED, km=2.0)
        _instance(db, b_cmp_turn.id, INSTANCE_APPROVED,
                 datetime.combine(mid, datetime.min.time()).replace(hour=8),
                 datetime.combine(mid, datetime.min.time()).replace(hour=10))

    db.commit()
    return SimpleNamespace(bookings=bookings, cty1=CTY1, cty2=CTY2, veh1=veh1.id, veh2=veh2.id,
                           drv1=drv1.id, drv2=drv2.id)


# ══════════════════════════════════════════════════════════════════════════════
#  1. Ma trận tương đương
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("group_by", [None, "status", "request_type", "company",
                                       "department", "vehicle", "driver", "requester"])
@pytest.mark.parametrize("compare", ["none", "previous", "year"])
def test_gom_sql_ra_dung_y_het_ban_cu(db, cap_quyen, compare, group_by):
    admin = _actor(db, uid=9999, code="ADMDX", dept=DEPT1, company=CTY1)
    cap_quyen(9999, "vehicle_booking", scope="all", read=True)
    _build_world(db, compare)

    params = _params(compare, group_by)
    legacy = _legacy_result(db, admin, dict(params))
    new = _new_result(db, admin, dict(params))
    assert new == legacy, (
        f"group_by={group_by} compare={compare}: bản GOM Ở SQL ra khác bản per-row cũ\n"
        f"legacy={legacy}\nnew={new}")


# ══════════════════════════════════════════════════════════════════════════════
#  2. Kiểm tay: JOIN MAX(id) chọn đúng phiên KẾT THÚC MỚI NHẤT
# ══════════════════════════════════════════════════════════════════════════════

def test_dat_xe_resubmit_lay_phien_moi_nhat_khong_phai_phien_dau(db, cap_quyen):
    admin = _actor(db, uid=9997, code="ADMDX3", dept=DEPT1, company=CTY1)
    cap_quyen(9997, "vehicle_booking", scope="all", read=True)
    _build_world(db, "none")

    data = _new_result(db, admin, _params("none", None))
    cur = data["totals"]["current"]
    #  c_resubmit: REJECTED 1h (id nhỏ) bị GHI ĐÈ bởi APPROVED 5h (id lớn) — tổng 3 phiếu có
    #  giờ duyệt: 5.0 (c_resubmit) + 0.5 (c_rejected_turn) + 1.25 (c_simple_turn) = 6.75.
    #  c_running (chưa kết thúc) và c_missing_start (thiếu started_at) KHÔNG góp vào.
    assert cur["approval_hours_count"] == 3
    assert cur["approval_hours_sum"] == pytest.approx(6.75)
    #  6.75/3 = 2.25 ĐÚNG BẰNG NỬA ĐƠN VỊ ở chữ số thập phân thứ 2 — `round(2.25, 1)` của Python
    #  làm tròn NỬA VỀ CHẴN (banker's rounding) ra `2.2`, không phải `2.3`. Đây là hành vi của
    #  `report_compute.compute_derived` (khung dùng chung, không đổi), không phải lỗi của bản
    #  GOM Ở SQL — ghi rõ ra đây để người sau khỏi tưởng nhầm là sai số.
    assert cur["avg_approval_hours"] == pytest.approx(2.2)


# ══════════════════════════════════════════════════════════════════════════════
#  3. Bench quy mô ~50k phiếu/3 năm — đo NGAY TRONG SQLite của pytest.
#
#  ⚠️ Con số TUYỆT ĐỐI ở đây KHÔNG thay cho benchmark MySQL thật: SQLite trong bộ nhớ không
#  có độ trễ MẠNG giữa app↔DB — chính độ trễ đó mới là chi phí thống trị của 105 lượt hỏi
#  chia lô trên MySQL thật (xem báo cáo load test). Phép đo này vẫn có giá trị cho MỘT điều:
#  SỐ CÂU LỆNH — chỉ số không phụ thuộc độ trễ mạng, và phải giảm từ hàng chục xuống ≤10
#  bất kể dialect nào.
# ══════════════════════════════════════════════════════════════════════════════

_BENCH_N = 50_000
_BENCH_START = date(2023, 1, 1)
_BENCH_SPAN_DAYS = 1095   # ~3 năm — đúng mốc "3-year range" của yêu cầu


def _bulk_bookings(db, n: int) -> None:
    rows = []
    for i in range(n):
        d = _BENCH_START + timedelta(days=i % _BENCH_SPAN_DAYS)
        status = (vm.BK_PENDING, vm.BK_APPROVED, vm.BK_DISPATCHED, vm.BK_COMPLETED,
                 vm.BK_REJECTED, vm.BK_CANCELLED, vm.BK_RETURNED)[i % 7]
        rows.append(dict(
            code=f"DXB{i}", request_type=vm.TYPE_CAR if i % 2 == 0 else vm.TYPE_DELIVERY,
            start_time=f"{d.isoformat()}T08:00", status=status,
            company_id=(i % 20) + 1, department_id=(i % 30) + 1,
            assigned_vehicle_id=((i % 25) + 1) if i % 3 else None,
            assigned_driver_id=((i % 20) + 1) if i % 4 else None,
            requester_id=(i % 100) + 1, requester=f"NV{(i % 100) + 1}",
            distance_km=float((i % 97) + 1) + 0.1, cost=(i % 500) * 1000,
            passenger_count=(i % 4) + 1, is_deleted=False, created_by=1, updated_by=1))
    db.execute(insert(vm.VehicleBooking), rows)
    db.commit()


def _bulk_instances(db, n_bookings: int, coverage: float = 0.4) -> None:
    step = max(1, int(1 / coverage))
    rows = []
    for bid in range(1, n_bookings + 1, step):
        started = datetime(2023, 1, 1, 8, 0) + timedelta(hours=bid % 1000)
        rows.append(dict(entity="vehicle_booking", entity_id=bid, flow_id=1,
                         status=INSTANCE_APPROVED if bid % 2 else INSTANCE_REJECTED,
                         started_at=started, finished_at=started + timedelta(hours=(bid % 48) + 1),
                         created_by=1, updated_by=1))
    db.execute(insert(ApprovalInstance), rows)
    db.commit()


def _measure(db, fn):
    tracemalloc.start()
    t0 = time.perf_counter()
    _, queries = _count_queries(db, fn)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return elapsed, peak / (1024 * 1024), len(queries)


def test_benchmark_gom_sql_o_quy_mo_50k(db, cap_quyen):
    admin = _actor(db, uid=8888, code="BENCHDX", dept=1, company=1)
    cap_quyen(8888, "vehicle_booking", scope="all", read=True)
    _bulk_bookings(db, _BENCH_N)
    _bulk_instances(db, _BENCH_N)

    params = {"preset": "custom", "date_from": _BENCH_START.isoformat(),
             "date_to": (_BENCH_START + timedelta(days=_BENCH_SPAN_DAYS - 1)).isoformat(),
             "compare": "none"}

    old_t, old_mb, old_q = _measure(db, lambda: _legacy_result(db, admin, dict(params)))
    new_t, new_mb, new_q = _measure(db, lambda: _new_result(db, admin, dict(params)))

    print(f"\n[BENCH 50k/3-năm] CŨ: {old_t * 1000:.0f}ms · {old_mb:.1f}MB · {old_q} câu lệnh | "
         f"MỚI: {new_t * 1000:.0f}ms · {new_mb:.1f}MB · {new_q} câu lệnh")

    #  Số câu lệnh + bộ nhớ KHÔNG phụ thuộc tải máy — chốt CỨNG đúng mục tiêu của task.
    assert new_q <= 10, f"MỚI phải ≤10 câu lệnh, đo được {new_q} (CŨ: {old_q})"
    assert new_mb < 20, f"MỚI phải <20MB, đo được {new_mb:.1f}MB"
    #  Thời gian TUYỆT ĐỐI (<1s) là mục tiêu đo trên MySQL thật (agent khác chạy sau) — container
    #  `api` chia sẻ CPU với phiên dev `--reload` + các agent khác đang chạy song song (xác nhận
    #  bằng `docker stats` lúc đo: container này đã ở ~100% CPU TRƯỚC khi bài này chạy), nên một
    #  ngưỡng giây tuyệt đối ở đây sẽ CHỚP TẮT (flaky) theo tải máy chứ không theo chất lượng mã.
    #  Chốt tương đối (nhanh hơn CŨ rõ rệt) + một trần RỘNG để bắt hồi quy thật sự (vd quên gỡ
    #  vòng lặp Python, JOIN tự nhân bản ghi).
    assert new_t < old_t / 2, (
        f"MỚI ({new_t:.2f}s) phải nhanh hơn CŨ ({old_t:.2f}s) ít nhất 2 lần — số câu lệnh đã "
        f"giảm {old_q} → {new_q} nên thời gian phải giảm theo, không chỉ số lượt hỏi")
    assert new_t < 5.0, f"MỚI phải dưới 5s kể cả khi máy đang tải nặng, đo được {new_t:.2f}s"
