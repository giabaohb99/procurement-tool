"""duoc-CR-744 — bấm tiêu đề cột các màn Nhân sự, Pháp nhân, Phòng ban xếp được tại SERVER.

Trước đây chỉ vài cột có `sortable` (Mã, Tên, Ngày cập nhật); Email, Công ty, Phòng ban, Chức vụ, Hình thức,
Cấp bậc, Quản lý trực tiếp, Tình trạng (Nhân sự) và Cấp, Mã số hiệu, Tên viết tắt, MST, Người đại diện, Email
hóa đơn, Trạng thái (Pháp nhân), Mã số hiệu, Loại đơn vị, Trưởng bộ phận, Trạng thái (Phòng ban) không bấm được.
Kiểm: từng khóa cột, cả hai chiều, trên cả tập; ô trống xuống cuối; tên (không phải id) cho cột tham chiếu; hạng
mã cho Tình trạng; cột nhạy cảm bị bỏ qua; khóa phụ `id` giảm dần.

Không đụng DB thật — fixture SQLite in-memory ở conftest. Dữ liệu dùng chữ ASCII vì SQLite so chuỗi theo mã byte
(MySQL thật so không phân biệt hoa thường / dấu — đã kiểm sống riêng).
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.datastructures import QueryParams

from app.modules.company import controller as company_ctl
from app.modules.company.model import Company
from app.modules.department import controller as dept_ctl
from app.modules.department.model import Department
from app.modules.employee import controller as emp_ctl
from app.modules.employee.model import Employee

PAGE = {"offset": 0, "limit": 100}


def _req(qs: str = ""):
    return SimpleNamespace(query_params=QueryParams(qs))


def _items(resp) -> list[dict]:
    return json.loads(resp.body)["data"]["items"]


@pytest.fixture()
def world(db, seed, cap_quyen):
    """Pháp nhân A/B, phòng X/Y, 5 nhân sự khác nhau ở MỌI cột + 1 nhân sự để trống hết các cột tham chiếu."""
    from app.modules.user.model import User
    cap_quyen(seed.u_req_id, "employee", read=True)
    cap_quyen(seed.u_req_id, "company", read=True)
    cap_quyen(seed.u_req_id, "department", read=True)

    boss = Employee(code="ZB00", full_name="Zeta Boss", is_active=True)
    mid = Employee(code="ZB01", full_name="Alpha Mid", is_active=True)
    db.add_all([boss, mid])
    db.flush()
    cty_b = Company(code="ZCB", name="Cty Beta", issue_code="BB", short_name="Beta", level=3, tax_code="0300",
                    invoice_email="b@x.vn", legal_representative_id=boss.id, is_active=True)
    cty_a = Company(code="ZCA", name="Cty Alpha", issue_code="AA", short_name="", level=1, tax_code="",
                    invoice_email="", legal_representative_id=mid.id, is_active=False)
    cty_none = Company(code="ZCN", name="Cty Khong Dai Dien", issue_code="", short_name="Khong", level=2,
                       tax_code="0100", invoice_email="n@x.vn", legal_representative_id=None, is_active=True)
    db.add_all([cty_b, cty_a, cty_none])
    db.flush()
    dep_b = Department(code="ZDB", name="Phong Beta", issue_code="PB", kind=3, company_id=cty_b.id,
                       manager_id=boss.id, is_active=True)
    dep_a = Department(code="ZDA", name="Phong Alpha", issue_code="", kind=1, company_id=cty_a.id,
                       manager_id=mid.id, is_active=False)
    dep_none = Department(code="ZDN", name="Phong Khong Truong", issue_code="PN", kind=2,
                          company_id=cty_a.id, manager_id=0, is_active=True)
    db.add_all([dep_b, dep_a, dep_none])
    db.flush()

    e1 = Employee(code="ZE1", full_name="Binh", email="binh@x.vn", position="Truong phong",
                  company_id=cty_b.id, department_id=dep_b.id, manager_id=boss.id,
                  employment_type=5, job_level=4, status="collaborator", is_active=True)
    e2 = Employee(code="ZE2", full_name="An", email="an@x.vn", position="Nhan vien",
                  company_id=cty_a.id, department_id=dep_a.id, manager_id=mid.id,
                  employment_type=1, job_level=1, status="official", is_active=True)
    e3 = Employee(code="ZE3", full_name="Chi", email="chi@x.vn", position="Ke toan",
                  company_id=cty_a.id, department_id=dep_b.id, manager_id=boss.id,
                  employment_type=6, job_level=2, status="resigned", is_active=True)
    e4 = Employee(code="ZE4", full_name="Dung", email="dung@x.vn", position="Ban hang",
                  company_id=cty_b.id, department_id=dep_a.id, manager_id=0,
                  employment_type=2, job_level=5, status="maternity_leave", is_active=True)
    #  Trống hết: chưa gán công ty / phòng / quản lý / chức vụ / email / hình thức / cấp bậc.
    e5 = Employee(code="ZE5", full_name="Em", email="", position="", company_id=0, department_id=0,
                  manager_id=0, employment_type=0, job_level=0, status="official", is_active=True)
    db.add_all([e1, e2, e3, e4, e5])
    db.flush()
    user = db.get(User, seed.u_req_id)
    return SimpleNamespace(user=user, boss=boss, mid=mid, cty_a=cty_a, cty_b=cty_b, cty_none=cty_none,
                           dep_a=dep_a, dep_b=dep_b, dep_none=dep_none, e1=e1, e2=e2, e3=e3, e4=e4, e5=e5)


# ── Nhân sự ───────────────────────────────────────────────────────────────────────

def _emp_ids(db, w, key, direction, mine):
    resp = emp_ctl.list_employees(request=_req(f"sort_by={key}&sort_dir={direction}"), pg=PAGE, db=db, user=w.user)
    return [it["id"] for it in _items(resp) if it["id"] in mine]


def test_nhan_su_cot_chu_xep_dung_va_o_trong_xuong_cuoi(db, world):
    w = world
    mine = {w.e1.id, w.e2.id, w.e3.id, w.e4.id, w.e5.id}
    #  email / chức vụ: e5 trống, bốn người còn lại xếp theo chữ.
    for key, ascending in [("email", [w.e2, w.e1, w.e3, w.e4]), ("position", [w.e4, w.e3, w.e2, w.e1])]:
        asc = _emp_ids(db, w, key, "asc", mine)
        desc = _emp_ids(db, w, key, "desc", mine)
        assert asc == [e.id for e in ascending] + [w.e5.id], key
        assert desc == [e.id for e in reversed(ascending)] + [w.e5.id], key


def test_nhan_su_cong_ty_phong_ban_quan_ly_xep_theo_ten_khong_theo_id(db, world):
    w = world
    mine = {w.e1.id, w.e2.id, w.e3.id, w.e4.id, w.e5.id}
    #  Cty Beta được tạo TRƯỚC (id nhỏ hơn) nhưng 'Cty Alpha' đứng trước khi tăng dần.
    assert w.cty_b.id < w.cty_a.id
    asc = _emp_ids(db, w, "company_name", "asc", mine)
    assert set(asc[:2]) == {w.e2.id, w.e3.id} and set(asc[2:4]) == {w.e1.id, w.e4.id} and asc[4] == w.e5.id
    desc = _emp_ids(db, w, "company_name", "desc", mine)
    assert set(desc[:2]) == {w.e1.id, w.e4.id} and set(desc[2:4]) == {w.e2.id, w.e3.id} and desc[4] == w.e5.id
    #  Phòng ban: Alpha (e2,e4) < Beta (e1,e3).
    asc = _emp_ids(db, w, "department_name", "asc", mine)
    assert set(asc[:2]) == {w.e2.id, w.e4.id} and set(asc[2:4]) == {w.e1.id, w.e3.id} and asc[4] == w.e5.id
    #  Quản lý trực tiếp: Alpha Mid (e2) < Zeta Boss (e1,e3); e4 + e5 chưa gán -> xuống cuối cả hai chiều.
    for direction in ("asc", "desc"):
        got = _emp_ids(db, w, "direct_manager_name", direction, mine)
        assert set(got[-2:]) == {w.e4.id, w.e5.id}, direction
    got = _emp_ids(db, w, "direct_manager_name", "asc", mine)
    assert got[0] == w.e2.id and set(got[1:3]) == {w.e1.id, w.e3.id}


def test_nhan_su_hinh_thuc_cap_bac_theo_ma_nghiep_vu_ma_0_la_o_trong(db, world):
    w = world
    mine = {w.e1.id, w.e2.id, w.e3.id, w.e4.id, w.e5.id}
    #  Hình thức: 1 Toàn TG(e2) < 2 Bán TG(e4) < 5 Thử việc(e1) < 6 Thực tập(e3); 0 (e5) = chưa khai.
    assert _emp_ids(db, w, "employment_type_label", "asc", mine) == [w.e2.id, w.e4.id, w.e1.id, w.e3.id, w.e5.id]
    assert _emp_ids(db, w, "employment_type_label", "desc", mine) == [w.e3.id, w.e1.id, w.e4.id, w.e2.id, w.e5.id]
    #  Cấp bậc: 1 Nhân viên(e2) < 2 Tổ trưởng(e3) < 4 Trưởng phòng(e1) < 5 Giám đốc khối(e4).
    assert _emp_ids(db, w, "job_level_label", "asc", mine) == [w.e2.id, w.e3.id, w.e1.id, w.e4.id, w.e5.id]
    assert _emp_ids(db, w, "job_level_label", "desc", mine) == [w.e4.id, w.e1.id, w.e3.id, w.e2.id, w.e5.id]


def test_nhan_su_tinh_trang_xep_theo_thu_tu_bo_ma_khong_theo_chu_cai_cua_ma(db, world):
    """Bộ mã khai: official < collaborator < maternity_leave < resigned. Xếp theo chữ cái của mã sẽ ra
    collaborator < maternity_leave < official < resigned — sai thứ tự đọc."""
    w = world
    mine = {w.e1.id, w.e2.id, w.e3.id, w.e4.id, w.e5.id}
    asc = _emp_ids(db, w, "status", "asc", mine)
    assert asc[0] in (w.e2.id, w.e5.id) and set(asc[:2]) == {w.e2.id, w.e5.id}
    assert asc[2:] == [w.e1.id, w.e4.id, w.e3.id]
    desc = _emp_ids(db, w, "status", "desc", mine)
    assert desc[:3] == [w.e3.id, w.e4.id, w.e1.id] and set(desc[3:]) == {w.e2.id, w.e5.id}


def test_nhan_su_khoa_phu_id_giam_dan_khi_gia_tri_bang_nhau(db, world):
    w = world
    mine = {w.e2.id, w.e5.id}   # cùng status 'official'
    assert _emp_ids(db, w, "status", "asc", mine) == sorted(mine, reverse=True)
    assert _emp_ids(db, w, "status", "desc", mine) == sorted(mine, reverse=True)


def test_nhan_su_cot_nhay_cam_va_khoa_la_bi_bo_qua_ve_thu_tu_mac_dinh(db, world):
    """`date_of_birth`, `bank_account_no`, `id_number`… từng xếp được bằng `apply_sort_from_request` — người
    không có `employee_sensitive.read` đoán được thứ tự dữ liệu họ không được xem. Nay là khóa lạ -> id giảm dần."""
    w = world
    default = [it["id"] for it in _items(emp_ctl.list_employees(request=_req(), pg=PAGE, db=db, user=w.user))]
    assert default == sorted(default, reverse=True)
    for key in ("date_of_birth", "bank_account_no", "id_number", "tax_code", "permanent_address",
                "no_such_column", "'; DROP TABLE tab_employee; --"):
        got = [it["id"] for it in _items(emp_ctl.list_employees(
            request=_req(f"sort_by={key}&sort_dir=asc"), pg=PAGE, db=db, user=w.user))]
        assert got == default, key


def test_nhan_su_van_chan_sap_xep_theo_luong(db, world):
    for key in ("salary_monthly", "allowance_monthly", "salary_updated_at"):
        with pytest.raises(HTTPException) as err:
            emp_ctl.list_employees(request=_req(f"sort_by={key}"), pg=PAGE, db=db, user=world.user)
        assert err.value.status_code == 400


def test_nhan_su_xep_cung_o_tim_nhanh_khong_loi_va_giu_dung_tap(db, world):
    w = world
    resp = emp_ctl.list_employees(request=_req("search=ZE&sort_by=company_name&sort_dir=desc"), pg=PAGE, db=db,
                                  user=w.user)
    got = [it["id"] for it in _items(resp)]
    assert {w.e1.id, w.e2.id, w.e3.id, w.e4.id, w.e5.id} <= set(got)


# ── Pháp nhân ─────────────────────────────────────────────────────────────────────

def _company_ids(db, w, key, direction):
    mine = {w.cty_a.id, w.cty_b.id, w.cty_none.id}
    resp = company_ctl.list_companies(request=_req(f"sort_by={key}&sort_dir={direction}"), pg=PAGE, db=db,
                                      user=w.user)
    return [it["id"] for it in _items(resp) if it["id"] in mine]


def test_phap_nhan_cot_chu_o_trong_xuong_cuoi_ca_hai_chieu(db, world):
    w = world
    #  issue_code: AA(a) < BB(b), none trống; short_name: Beta(b) < Khong(none), a trống;
    #  tax_code: 0100(none) < 0300(b), a trống; invoice_email: b@x.vn < n@x.vn, a trống.
    cases = {
        "issue_code": ([w.cty_a, w.cty_b], w.cty_none),
        "short_name": ([w.cty_b, w.cty_none], w.cty_a),
        "tax_code": ([w.cty_none, w.cty_b], w.cty_a),
        "invoice_email": ([w.cty_b, w.cty_none], w.cty_a),
    }
    for key, (ordered, blank) in cases.items():
        assert _company_ids(db, w, key, "asc") == [c.id for c in ordered] + [blank.id], key
        assert _company_ids(db, w, key, "desc") == [c.id for c in reversed(ordered)] + [blank.id], key


def test_phap_nhan_nguoi_dai_dien_xep_theo_ten_nhan_su_khong_theo_id(db, world):
    """Cty B đại diện 'Zeta Boss', Cty A đại diện 'Alpha Mid' (tạo SAU nhưng tên đứng trước); chưa khai -> cuối."""
    w = world
    assert w.boss.id < w.mid.id
    assert _company_ids(db, w, "legal_rep_name", "asc") == [w.cty_a.id, w.cty_b.id, w.cty_none.id]
    assert _company_ids(db, w, "legal_rep_name", "desc") == [w.cty_b.id, w.cty_a.id, w.cty_none.id]


def test_phap_nhan_cap_theo_ma_cap_bac_va_trang_thai(db, world):
    w = world
    assert _company_ids(db, w, "level", "asc") == [w.cty_a.id, w.cty_none.id, w.cty_b.id]
    assert _company_ids(db, w, "level", "desc") == [w.cty_b.id, w.cty_none.id, w.cty_a.id]
    #  is_active: False(a) < True(b, none); hai True bằng nhau -> khóa phụ id giảm dần.
    assert _company_ids(db, w, "is_active", "asc") == [w.cty_a.id, w.cty_none.id, w.cty_b.id]
    assert _company_ids(db, w, "is_active", "desc") == [w.cty_none.id, w.cty_b.id, w.cty_a.id]


def test_phap_nhan_khoa_cu_van_chay_qua_duong_cu(db, world):
    w = world
    got = _company_ids(db, w, "name", "asc")
    assert got == [w.cty_a.id, w.cty_b.id, w.cty_none.id]   # Cty Alpha < Cty Beta < Cty Khong Dai Dien
    #  Khóa lạ không nổ, về thứ tự mặc định.
    assert len(_company_ids(db, w, "khong_co_cot_nay", "asc")) == 3


# ── Phòng ban ─────────────────────────────────────────────────────────────────────

def _dept_ids(db, w, key, direction, q=None):
    mine = {w.dep_a.id, w.dep_b.id, w.dep_none.id}
    resp = dept_ctl.list_departments(
        request=_req(), q=q, is_active=None, kind=None, company_id=None, sort_by=key, sort_dir=direction,
        pg=PAGE, db=db, user=w.user)
    return [it["id"] for it in _items(resp) if it["id"] in mine]


def test_phong_ban_cot_chu_o_trong_xuong_cuoi_ca_hai_chieu(db, world):
    w = world
    #  issue_code: PB(b) < PN(none), a trống.
    assert _dept_ids(db, w, "issue_code", "asc") == [w.dep_b.id, w.dep_none.id, w.dep_a.id]
    assert _dept_ids(db, w, "issue_code", "desc") == [w.dep_none.id, w.dep_b.id, w.dep_a.id]


def test_phong_ban_truong_bo_phan_xep_theo_ten_khong_theo_id_va_khong_nham_khi_co_o_tim(db, world):
    """Trưởng 'Alpha Mid' (a) < 'Zeta Boss' (b); chưa có trưởng -> cuối. Có ô tìm `q` thì truy vấn ngoài đã nối
    sẵn `Employee`: câu con dùng bí danh nên không tự tương quan nhầm với phép nối đó."""
    w = world
    assert w.boss.id < w.mid.id
    assert _dept_ids(db, w, "manager_name", "asc") == [w.dep_a.id, w.dep_b.id, w.dep_none.id]
    assert _dept_ids(db, w, "manager_name", "desc") == [w.dep_b.id, w.dep_a.id, w.dep_none.id]
    assert _dept_ids(db, w, "manager_name", "asc", q="Phong") == [w.dep_a.id, w.dep_b.id, w.dep_none.id]
    assert _dept_ids(db, w, "manager_name", "desc", q="Phong") == [w.dep_b.id, w.dep_a.id, w.dep_none.id]


def test_phong_ban_loai_don_vi_va_trang_thai(db, world):
    w = world
    assert _dept_ids(db, w, "kind", "asc") == [w.dep_a.id, w.dep_none.id, w.dep_b.id]
    assert _dept_ids(db, w, "kind", "desc") == [w.dep_b.id, w.dep_none.id, w.dep_a.id]
    assert _dept_ids(db, w, "is_active", "asc") == [w.dep_a.id, w.dep_none.id, w.dep_b.id]
    assert _dept_ids(db, w, "is_active", "desc") == [w.dep_none.id, w.dep_b.id, w.dep_a.id]


def test_phong_ban_khoa_cu_van_chay_qua_duong_cu(db, world):
    w = world
    assert _dept_ids(db, w, "name", "asc") == [w.dep_a.id, w.dep_b.id, w.dep_none.id]
    assert len(_dept_ids(db, w, "khong_co_cot_nay", "asc")) == 3
