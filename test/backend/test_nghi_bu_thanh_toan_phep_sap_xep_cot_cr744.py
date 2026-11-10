"""duoc-CR-744 — bấm tiêu đề cột Phiếu nghỉ bù và Thanh toán nghỉ phép xếp được tại SERVER.

Trước đây hai bảng không khai `sortable` nên không bấm được cột nào (backend đã đọc `sort_by` nhưng chỉ cho cột
vật lý — Người nghỉ / Loại nghỉ / Trạng thái chi không có cột để xếp). Kiểm: từng khóa cột, cả hai chiều, trên
cả tập; Người nghỉ / Loại nghỉ xếp theo TÊN; Trạng thái chi theo hạng vòng đời YCTT (chưa có YCTT xuống cuối);
mã số trạng thái / lý do theo thứ tự hiển thị; ô trống xuống cuối; khóa phụ `id` giảm dần; khóa lạ về mặc định.

Không đụng DB thật — fixture SQLite in-memory ở conftest. Dữ liệu dùng chữ ASCII vì SQLite so chuỗi theo mã byte.
"""
import json
from datetime import date
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.modules.employee.model import Employee
from app.modules.leave import comp_request_controller as comp_ctl
from app.modules.leave import encashment_controller as enc_ctl
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.comp_request_model import LeaveCompRequest
from app.modules.leave.encashment_model import LeaveEncashment
from app.modules.payment_request.model import PaymentRequest
from app.modules.user.model import User

PAGE = {"offset": 0, "limit": 100}


def _req(qs: str = ""):
    return SimpleNamespace(query_params=QueryParams(qs))


def _items(resp) -> list[dict]:
    return json.loads(resp.body)["data"]["items"]


@pytest.fixture()
def world(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_comp_request", read=True)
    cap_quyen(seed.u_req_id, "leave_encashment", read=True)
    emp_z = Employee(code="NBZ", full_name="Zeta Nghi", is_active=True)
    emp_a = Employee(code="NBA", full_name="Alpha Nghi", is_active=True)
    emp_m = Employee(code="NBM", full_name="Mu Nghi", is_active=True)
    db.add_all([emp_z, emp_a, emp_m])
    db.flush()
    lt_z = LeaveType(code="NBLZ", name="Zeta Phep")
    lt_a = LeaveType(code="NBLA", name="Alpha Phep")
    db.add_all([lt_z, lt_a])
    db.flush()
    return SimpleNamespace(user=db.get(User, seed.u_req_id), emp_z=emp_z, emp_a=emp_a, emp_m=emp_m,
                           lt_z=lt_z, lt_a=lt_a)


# ── Phiếu nghỉ bù ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def comps(db, world):
    def _c(code, emp_id, day, days, status, reason):
        c = LeaveCompRequest(code=code, employee_id=emp_id, work_date=day, days=days, status=status,
                             reason=reason, is_deleted=False)
        db.add(c)
        db.flush()
        return c

    #  Người 'Zeta' tạo TRƯỚC (id nhỏ) nhưng đứng sau 'Alpha' khi xếp theo tên.
    world.c1 = _c("NB-01", world.emp_z.id, date(2026, 3, 1), 1.0, 3, "Truc le")
    world.c2 = _c("NB-02", world.emp_a.id, date(2026, 1, 1), 0.5, 1, "")
    world.c3 = _c("NB-03", world.emp_m.id, date(2026, 2, 1), 1.0, 6, "Di cong tac")
    world.c4 = _c("NB-04", 0, date(2026, 4, 1), 0.5, 2, "Ban giao")      # nhân sự không còn hồ sơ
    return world


def _comp_ids(db, w, qs):
    mine = {w.c1.id, w.c2.id, w.c3.id, w.c4.id}
    resp = comp_ctl.list_requests(request=_req(qs), pg=PAGE, q=None, db=db, user=w.user)
    return [it["id"] for it in _items(resp) if it["id"] in mine]


def test_nghi_bu_nguoi_nghi_xep_theo_ten_khong_theo_id_o_trong_cuoi(db, comps):
    w = comps
    assert _comp_ids(db, w, "sort_by=employee_name&sort_dir=asc") == [w.c2.id, w.c3.id, w.c1.id, w.c4.id]
    assert _comp_ids(db, w, "sort_by=employee_name&sort_dir=desc") == [w.c1.id, w.c3.id, w.c2.id, w.c4.id]


def test_nghi_bu_trang_thai_ngay_so_ngay_xep_dung(db, comps):
    w = comps
    #  status: 1 Nháp(c2) < 2 Chờ duyệt(c4) < 3 Đã duyệt(c1) < 6 Đã hủy(c3)
    assert _comp_ids(db, w, "sort_by=status&sort_dir=asc") == [w.c2.id, w.c4.id, w.c1.id, w.c3.id]
    assert _comp_ids(db, w, "sort_by=status&sort_dir=desc") == [w.c3.id, w.c1.id, w.c4.id, w.c2.id]
    assert _comp_ids(db, w, "sort_by=work_date&sort_dir=asc") == [w.c2.id, w.c3.id, w.c1.id, w.c4.id]
    assert _comp_ids(db, w, "sort_by=work_date&sort_dir=desc") == [w.c4.id, w.c1.id, w.c3.id, w.c2.id]
    #  days: 0.5 (c2, c4), 1.0 (c1, c3); bằng nhau -> id giảm dần.
    assert _comp_ids(db, w, "sort_by=days&sort_dir=asc") == [w.c4.id, w.c2.id, w.c3.id, w.c1.id]
    assert _comp_ids(db, w, "sort_by=days&sort_dir=desc") == [w.c3.id, w.c1.id, w.c4.id, w.c2.id]


def test_nghi_bu_ly_do_trong_xuong_cuoi_ca_hai_chieu(db, comps):
    w = comps
    assert _comp_ids(db, w, "sort_by=reason&sort_dir=asc") == [w.c4.id, w.c3.id, w.c1.id, w.c2.id]
    assert _comp_ids(db, w, "sort_by=reason&sort_dir=desc") == [w.c1.id, w.c3.id, w.c4.id, w.c2.id]


def test_nghi_bu_cot_id_khoa_la_va_mac_dinh(db, comps):
    w = comps
    all_ids = [w.c1.id, w.c2.id, w.c3.id, w.c4.id]
    assert _comp_ids(db, w, "sort_by=id&sort_dir=desc") == sorted(all_ids, reverse=True)
    #  Không bấm cột nào: mặc định ngày đi làm mới nhất trước (giữ hành vi cũ). Khóa lạ cũng về đó.
    default = [w.c4.id, w.c1.id, w.c3.id, w.c2.id]
    assert _comp_ids(db, w, "") == default
    assert _comp_ids(db, w, "sort_by=khong_co_cot&sort_dir=asc") == default


# ── Thanh toán nghỉ phép ──────────────────────────────────────────────────────────

@pytest.fixture()
def encashments(db, world):
    def _y(code, status):
        p = PaymentRequest(code=code, status=status, total=0)
        db.add(p)
        db.flush()
        return p

    y_draft, y_paid, y_cancel = _y("Y1", "draft"), _y("Y2", "paid"), _y("Y3", "cancelled")

    def _e(code, emp, lt, year, reason, days, status, note, pay_id):
        e = LeaveEncashment(code=code, employee_id=emp.id if emp else 0, leave_type_id=lt.id if lt else 0,
                            balance_year=year, reason_kind=reason, days=days, status=status, note=note,
                            payment_request_id=pay_id, is_deleted=False)
        db.add(e)
        db.flush()
        return e

    world.e1 = _e("TT-1", world.emp_z, world.lt_z, 2025, 2, 3.0, 3, "Nghi viec", y_paid.id)
    world.e2 = _e("TT-2", world.emp_a, world.lt_a, 2026, 1, 1.5, 3, "", y_draft.id)
    world.e3 = _e("TT-3", world.emp_m, world.lt_a, 2026, 1, 2.0, 1, "Cuoi nam", 0)           # chưa có YCTT
    world.e4 = _e("TT-4", None, None, 2025, 2, 0.5, 2, "Ghi chu", y_cancel.id)               # trống người / loại
    return world


def _enc_ids(db, w, qs):
    mine = {w.e1.id, w.e2.id, w.e3.id, w.e4.id}
    resp = enc_ctl.list_encashments(request=_req(qs), pg=PAGE, q=None, db=db, user=w.user)
    return [it["id"] for it in _items(resp) if it["id"] in mine]


def test_thanh_toan_nguoi_va_loai_nghi_xep_theo_ten_o_trong_cuoi(db, encashments):
    w = encashments
    #  Người: Alpha(e2) < Mu(e3) < Zeta(e1); e4 không có hồ sơ -> cuối cả hai chiều.
    assert _enc_ids(db, w, "sort_by=employee_name&sort_dir=asc") == [w.e2.id, w.e3.id, w.e1.id, w.e4.id]
    assert _enc_ids(db, w, "sort_by=employee_name&sort_dir=desc") == [w.e1.id, w.e3.id, w.e2.id, w.e4.id]
    #  Loại nghỉ: 'Alpha Phep' (e2, e3 -> id giảm dần khi bằng nhau) < 'Zeta Phep' (e1); e4 không có loại.
    assert _enc_ids(db, w, "sort_by=leave_type_name&sort_dir=asc") == [w.e3.id, w.e2.id, w.e1.id, w.e4.id]
    assert _enc_ids(db, w, "sort_by=leave_type_name&sort_dir=desc") == [w.e1.id, w.e3.id, w.e2.id, w.e4.id]


def test_thanh_toan_trang_thai_chi_theo_hang_vong_doi_chua_co_yctt_cuoi(db, encashments):
    """draft(e2) < paid(e1) < cancelled(e4) theo vòng đời YCTT; e3 chưa có YCTT -> cuối cả hai chiều.
    Theo chữ cái của mã: cancelled < draft < paid — sai thứ tự đọc."""
    w = encashments
    assert _enc_ids(db, w, "sort_by=payment_status&sort_dir=asc") == [w.e2.id, w.e1.id, w.e4.id, w.e3.id]
    assert _enc_ids(db, w, "sort_by=payment_status&sort_dir=desc") == [w.e4.id, w.e1.id, w.e2.id, w.e3.id]


def test_thanh_toan_ma_so_nam_so_ngay_xep_dung(db, encashments):
    w = encashments
    assert _enc_ids(db, w, "sort_by=status&sort_dir=asc") == [w.e3.id, w.e4.id, w.e2.id, w.e1.id]
    assert _enc_ids(db, w, "sort_by=days&sort_dir=asc") == [w.e4.id, w.e2.id, w.e3.id, w.e1.id]
    assert _enc_ids(db, w, "sort_by=days&sort_dir=desc") == [w.e1.id, w.e3.id, w.e2.id, w.e4.id]
    #  reason_kind: 1 Phép dư (e2, e3) < 2 Nghỉ việc (e1, e4); bằng nhau -> id giảm dần.
    assert _enc_ids(db, w, "sort_by=reason_kind&sort_dir=asc") == [w.e3.id, w.e2.id, w.e4.id, w.e1.id]
    assert _enc_ids(db, w, "sort_by=balance_year&sort_dir=desc") == [w.e3.id, w.e2.id, w.e4.id, w.e1.id]


def test_thanh_toan_ghi_chu_trong_xuong_cuoi_ca_hai_chieu(db, encashments):
    w = encashments
    assert _enc_ids(db, w, "sort_by=note&sort_dir=asc") == [w.e3.id, w.e4.id, w.e1.id, w.e2.id]
    assert _enc_ids(db, w, "sort_by=note&sort_dir=desc") == [w.e1.id, w.e4.id, w.e3.id, w.e2.id]


def test_thanh_toan_cot_id_khoa_la_va_mac_dinh(db, encashments):
    w = encashments
    all_ids = [w.e1.id, w.e2.id, w.e3.id, w.e4.id]
    assert _enc_ids(db, w, "sort_by=id&sort_dir=asc") == sorted(all_ids)
    assert _enc_ids(db, w, "") == sorted(all_ids, reverse=True)
    assert _enc_ids(db, w, "sort_by=khong_co_cot&sort_dir=asc") == sorted(all_ids, reverse=True)
