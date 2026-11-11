"""duoc-CR-748 (nhóm A) — bấm tiêu đề cột của các bảng Nhân sự phân trang tại SERVER xếp đúng chữ đang hiện.

Sáu màn: Duyệt sửa hồ sơ, Mẫu HĐLĐ, Biến mẫu HĐLĐ, Phân bổ chính sách, Quỹ phép thẻ Theo nhân sự (kèm Excel cùng
thứ tự), và trạng thái theo DÒNG ĐỜI của Đơn nghỉ phép / Phiếu nghỉ bù / Phiếu thanh toán phép / Phiếu đặt phòng họp.

Mỗi bảng: từng khóa cột cả hai chiều, ô trống xuống CUỐI cả hai chiều, khóa phụ `id`, khóa lạ / không chọn về thứ tự
mặc định cũ (không lỗi). Đi qua HTTP thật (TestClient) nên phạm vi `apply_scope` và tham số `sort_by`/`sort_dir` chạy
đúng đường đi của giao diện. Dữ liệu dùng chữ ASCII ở cột đem so vì SQLite so chuỗi theo mã byte.
"""
import io
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.labor_contract_codes import LaborContractVariableSource as Src
from app.core.vn_time import vn_today
from app.main import app
from app.modules.employee.change_request_model import EmployeeChangeRequest
from app.modules.employee.model import Employee
from app.modules.labor_contract.model import LaborContract
from app.modules.labor_contract.template_model import LaborContractTemplate
from app.modules.labor_contract.variable_model import LaborContractVariable
from app.modules.leave import comp_encashment_sort_expressions as comp_sort
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.comp_request_model import LeaveCompRequest
from app.modules.leave.encashment_model import LeaveEncashment
from app.modules.leave.policy_model import LeavePolicy, LeavePolicyAssignment
from app.modules.leave.request_model import LeaveRequest
from app.modules.meeting_room.model import RoomBooking

YEAR = vn_today().year + 1  # năm tới: loại cộng dần chưa tới tháng nào, ô số ngày không phụ thuộc ngày chạy bài


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _client(world, client_as, entity, actions=("read",), key="a1"):
    world.grant(key, entity, "all", actions=actions)
    return client_as(world.actor(key).user)


def _ids(client, url, qs="", mine=None, key="id"):
    """Danh sách `id` của các dòng trả về theo thứ tự; `mine` giữ lại đúng dòng của bài (bỏ dữ liệu nền)."""
    res = client.get(f"{url}?{qs}&page_size=100")
    assert res.status_code == 200, res.text
    out = [row[key] for row in res.json()["data"]["items"]]
    return [i for i in out if i in mine] if mine is not None else out


def _both_ways(client, url, key, expected, mine, id_key="id"):
    """Chiều tăng ra `expected`; chiều giảm ra đúng thứ tự ngược lại."""
    assert _ids(client, url, f"sort_by={key}&sort_dir=asc", mine, id_key) == expected, f"{key} asc"
    assert _ids(client, url, f"sort_by={key}&sort_dir=desc", mine, id_key) == list(reversed(expected)), f"{key} desc"


# ── 1. Duyệt sửa hồ sơ ───────────────────────────────────────────────────────────────

CR_URL = "/api/employees/change-requests"


def test_duyet_sua_ho_so_xep_theo_ma_ten_ngay_va_dong_doi_trang_thai(db, world, client_as):
    client = _client(world, client_as, "employee", ("read", "write"))
    emps = {}
    for tag, code, name in (("1", "CRA2", "Zed"), ("2", "CRB1", "Amy"), ("3", "CRC4", "Bob"), ("4", "CRD3", "Cat")):
        emps[tag] = Employee(code=code, full_name=name, company_id=world.co["A"], is_active=True)
        db.add(emps[tag])
    db.flush()

    def _r(tag, status, created):
        r = EmployeeChangeRequest(employee_id=emps[tag].id, status=status, changes=[], created_at=created,
                                  pending_employee_id=emps[tag].id if status == 1 else None)
        db.add(r)
        db.flush()
        return r.id

    r1 = _r("1", 2, datetime(2026, 3, 1))
    r2 = _r("2", 1, datetime(2026, 1, 1))
    r3 = _r("3", 4, datetime(2026, 2, 1))
    r4 = _r("4", 3, datetime(2026, 4, 1))
    mine = {r1, r2, r3, r4}
    db.commit()

    _both_ways(client, CR_URL, "employee_code", [r1, r2, r3, r4], mine)
    _both_ways(client, CR_URL, "employee_name", [r2, r3, r4, r1], mine)
    #  Dòng đời: 1 Chờ duyệt(r2) -> 2 Đã duyệt(r1) -> 3 Từ chối(r4) -> 4 Đã rút lại(r3)
    _both_ways(client, CR_URL, "status", [r2, r1, r4, r3], mine)
    _both_ways(client, CR_URL, "created_at", [r2, r3, r1, r4], mine)
    #  Cột tính từ JSON (nhóm / số trường) không xếp được -> mặc định cũ `id` giảm dần; khóa lạ cũng vậy, không lỗi.
    default = [r4, r3, r2, r1]
    assert _ids(client, CR_URL, "", mine) == default
    assert _ids(client, CR_URL, "sort_by=groups&sort_dir=asc", mine) == default
    assert _ids(client, CR_URL, "sort_by=khong_co_cot&sort_dir=desc", mine) == default
    assert _ids(client, CR_URL, "sort_by=employee_code&sort_dir=xyz", mine) == [r1, r2, r3, r4]  # chiều lạ = tăng


# ── 2. Mẫu HĐLĐ ──────────────────────────────────────────────────────────────────────

TPL_URL = "/api/labor-contract-templates"


def test_mau_hdld_xep_theo_ten_phap_nhan_loai_so_hd_dang_dung_ngay_tao(db, world, client_as):
    client = _client(world, client_as, "labor_contract_template")
    #  Pháp nhân: A = "Công ty A", B = "Công ty B"; mẫu t3 không có pháp nhân (id 0) -> ô trống.
    specs = [("t1", "m-b", "A", 2, True, datetime(2026, 3, 1)), ("t2", "m-a", "B", 1, False, datetime(2026, 1, 1)),
             ("t3", "m-c", None, 3, True, datetime(2026, 2, 1)), ("t4", "m-d", "A", 0, True, datetime(2026, 4, 1))]
    rows = {}
    for tag, name, co, ctype, active, created in specs:
        rows[tag] = LaborContractTemplate(name=name, company_id=world.co[co] if co else 0, contract_type=ctype,
                                          is_active=active, original_filename="f.docx", placeholders=[],
                                          created_at=created)
        db.add(rows[tag])
    db.flush()
    t1, t2, t3, t4 = (rows[k].id for k in ("t1", "t2", "t3", "t4"))
    #  Số HĐ đang dùng: t1 = 2 (HĐ đã xóa mềm KHÔNG tính), t2 = 1, t3 = 0, t4 = 3.
    emp = Employee(code="TPLE", full_name="Nguoi HD", is_active=True)
    db.add(emp)
    db.flush()
    seq = 0
    for tid, deleted in ((t1, False), (t1, False), (t1, True), (t2, False), (t4, False), (t4, False), (t4, False)):
        seq += 1
        db.add(LaborContract(code=f"HDX{seq}", employee_id=emp.id, template_id=tid, contract_type=2,
                             start_date=date(2026, 1, 1), is_deleted=deleted))
    db.commit()
    mine = {t1, t2, t3, t4}

    _both_ways(client, TPL_URL, "name", [t2, t1, t3, t4], mine)
    #  Pháp nhân theo TÊN (A < B), ô trống (t3) xuống CUỐI cả hai chiều; cùng pháp nhân thì id giảm dần.
    assert _ids(client, TPL_URL, "sort_by=company&sort_dir=asc", mine) == [t4, t1, t2, t3]
    assert _ids(client, TPL_URL, "sort_by=company&sort_dir=desc", mine) == [t2, t4, t1, t3]
    #  Loại HĐ: 0 = chưa khai -> ô trống (t4) xuống cuối.
    assert _ids(client, TPL_URL, "sort_by=contract_type&sort_dir=asc", mine) == [t2, t1, t3, t4]
    assert _ids(client, TPL_URL, "sort_by=contract_type&sort_dir=desc", mine) == [t3, t1, t2, t4]
    _both_ways(client, TPL_URL, "contract_count", [t3, t2, t1, t4], mine)
    #  "Đang dùng" đứng trước "Ngừng" khi xếp tăng; trong cùng nhóm id giảm dần.
    assert _ids(client, TPL_URL, "sort_by=is_active&sort_dir=asc", mine) == [t4, t3, t1, t2]
    assert _ids(client, TPL_URL, "sort_by=is_active&sort_dir=desc", mine) == [t2, t4, t3, t1]
    _both_ways(client, TPL_URL, "created_at", [t2, t3, t1, t4], mine)
    #  Mặc định cũ: pháp nhân, loại HĐ, tên. Cột "Tệp gốc" / khóa lạ không xếp được -> mặc định, không lỗi.
    default = [t3, t4, t1, t2]
    assert _ids(client, TPL_URL, "", mine) == default
    assert _ids(client, TPL_URL, "sort_by=file&sort_dir=desc", mine) == default


# ── 3. Biến mẫu HĐLĐ ─────────────────────────────────────────────────────────────────

VAR_URL = "/api/labor-contract-variables"


def test_bien_mau_hdld_xep_theo_chu_dang_hien_nhom_kieu_bat_buoc_trang_thai(db, world, client_as):
    client = _client(world, client_as, "labor_contract_template")
    S, C = int(Src.SYSTEM), int(Src.CUSTOM)

    def _v(code, source, vtype, label, example="", required=False, active=True, hidden=False):
        v = LaborContractVariable(code=code, source=source, value_type=vtype, label=label, example=example,
                                  is_required=required, is_active=active, is_hidden=hidden, sort_order=0)
        db.add(v)
        db.flush()
        return v.id

    #  Hệ thống: ho_ten (nhóm "Người lao động"), ten_cong_ty (nhóm "Pháp nhân (bên A)", bị ẩn).
    v1 = _v("ho_ten", S, 1, "Ho va ten", "Nguyen An")
    v2 = _v("ten_cong_ty", S, 1, "Ten phap nhan", "", hidden=True)
    #  Tùy chỉnh: tiền bắt buộc đang dùng / chữ đã ngừng / ngày đang dùng.
    v3 = _v("phu_cap_x", C, 5, "Phu cap x", "1.000.000", required=True)
    v4 = _v("ghi_chu_y", C, 1, "Ghi chu y", "abc", active=False)
    v5 = _v("ngay_z", C, 4, "Ngay z", "01/01/2026")
    db.commit()
    mine = {v1, v2, v3, v4, v5}

    #  code: ho_ten < ghi_chu_y? ASCII: "ghi_chu_y" < "ho_ten" < "ngay_z" < "phu_cap_x" < "ten_cong_ty"
    _both_ways(client, VAR_URL, "code", [v4, v1, v5, v3, v2], mine)
    #  label: "Ghi chu y" < "Ho va ten" < "Ngay z" < "Phu cap x" < "Ten phap nhan"
    _both_ways(client, VAR_URL, "label", [v4, v1, v5, v3, v2], mine)
    #  Nhóm theo CHỮ đang hiện: "Biến tùy chỉnh" < "Người lao động" < "Pháp nhân (bên A)"; cùng nhóm id giảm dần.
    assert _ids(client, VAR_URL, "sort_by=group&sort_dir=asc", mine) == [v5, v4, v3, v1, v2]
    assert _ids(client, VAR_URL, "sort_by=group&sort_dir=desc", mine) == [v2, v1, v5, v4, v3]
    #  Kiểu: biến hệ thống hiện "—" nên là ô trống, xuống CUỐI cả hai chiều. Chữ(1)=v4, Ngày(4)=v5, Tiền(5)=v3.
    assert _ids(client, VAR_URL, "sort_by=value_type&sort_dir=asc", mine) == [v4, v5, v3, v2, v1]
    assert _ids(client, VAR_URL, "sort_by=value_type&sort_dir=desc", mine) == [v3, v5, v4, v2, v1]
    #  Ví dụ (so theo chữ đang hiện, mã byte): "01/01/2026" < "1.000.000" < "Nguyen An" < "abc"; ô trống (v2) cuối cả hai chiều.
    assert _ids(client, VAR_URL, "sort_by=example&sort_dir=asc", mine) == [v5, v3, v1, v4, v2]
    assert _ids(client, VAR_URL, "sort_by=example&sort_dir=desc", mine) == [v4, v1, v3, v5, v2]
    #  Bắt buộc: chỉ biến tùy chỉnh bắt buộc (v3) mới hiện nhãn; bấm hai chiều đổi được thứ tự.
    assert _ids(client, VAR_URL, "sort_by=is_required&sort_dir=desc", mine)[0] == v3
    assert _ids(client, VAR_URL, "sort_by=is_required&sort_dir=asc", mine)[-1] == v3
    #  Trạng thái theo dòng đời: Đang dùng (v1 hệ thống, v3, v5) -> Ẩn (v2) -> Ngừng (v4).
    assert _ids(client, VAR_URL, "sort_by=status&sort_dir=asc", mine) == [v5, v3, v1, v2, v4]
    assert _ids(client, VAR_URL, "sort_by=status&sort_dir=desc", mine) == [v4, v2, v5, v3, v1]
    #  Mặc định cũ (nguồn, thứ tự, mã): "Số mẫu dùng" tính bằng Python nên không xếp được; khóa lạ không lỗi.
    default = [v1, v2, v4, v5, v3]  # hệ thống trước (ho_ten, ten_cong_ty), tùy chỉnh theo mã
    assert _ids(client, VAR_URL, "", mine) == default
    assert _ids(client, VAR_URL, "sort_by=template_count&sort_dir=desc", mine) == default
    assert _ids(client, VAR_URL, "sort_by=khong_co_cot", mine) == default


# ── 4. Phân bổ chính sách ─────────────────────────────────────────────────────────────

ASSIGN_URL = "/api/leave-policy-assignments"


def test_phan_bo_chinh_sach_xep_theo_ten_ngay_trang_thai_dong_doi_o_trong_cuoi(db, world, client_as):
    client = _client(world, client_as, "leave_balance")
    today = vn_today()
    ez = Employee(code="PBZ", full_name="Zeta Pb", company_id=world.co["A"], is_active=True)
    ea = Employee(code="PBA", full_name="Alpha Pb", company_id=world.co["A"], is_active=True)
    em = Employee(code="PBM", full_name="Mu Pb", company_id=world.co["A"], is_active=True)
    pz, pa = LeavePolicy(code="PBPZ", name="Zeta Goi"), LeavePolicy(code="PBPA", name="Alpha Goi")
    db.add_all([ez, ea, em, pz, pa])
    db.flush()

    def _a(emp, policy, start, end, note):
        a = LeavePolicyAssignment(employee_id=emp.id if emp else 0, company_id=world.co["A"],
                                  policy_id=policy.id if policy else 0, effective_from=start, effective_to=end,
                                  note=note)
        db.add(a)
        db.flush()
        return a.id

    d = timedelta(days=1)
    #  a1 Đã kết thúc, a2 Đang hiệu lực (không thời hạn), a3 Sắp tới, a4 Đang hiệu lực (có hạn), nhân sự + gói trống.
    a1 = _a(ez, pz, today - 100 * d, today - 10 * d, "Cu")
    a2 = _a(ea, pa, today - 50 * d, None, "")
    a3 = _a(em, pa, today + 10 * d, today + 40 * d, "Moi")
    a4 = _a(None, None, today - 5 * d, today + 5 * d, "Bang")
    db.commit()
    mine = {a1, a2, a3, a4}

    #  Nhân sự theo HỌ TÊN (Alpha a2 < Mu a3 < Zeta a1); nhân sự đã mất hồ sơ (a4) ô trống -> cuối cả hai chiều.
    assert _ids(client, ASSIGN_URL, "sort_by=employee_name&sort_dir=asc", mine) == [a2, a3, a1, a4]
    assert _ids(client, ASSIGN_URL, "sort_by=employee_name&sort_dir=desc", mine) == [a1, a3, a2, a4]
    #  Chính sách theo TÊN gói (Alpha a2, a3 cùng gói -> id giảm dần; Zeta a1); a4 trống cuối.
    assert _ids(client, ASSIGN_URL, "sort_by=policy_name&sort_dir=asc", mine) == [a3, a2, a1, a4]
    assert _ids(client, ASSIGN_URL, "sort_by=policy_name&sort_dir=desc", mine) == [a1, a3, a2, a4]
    _both_ways(client, ASSIGN_URL, "effective_from", [a1, a2, a4, a3], mine)
    #  Đến ngày: "Không thời hạn" (a2) là ô trống -> luôn CUỐI, KHÔNG coi là vô cực nằm đầu khi xếp giảm dần.
    assert _ids(client, ASSIGN_URL, "sort_by=effective_to&sort_dir=asc", mine) == [a1, a4, a3, a2]
    assert _ids(client, ASSIGN_URL, "sort_by=effective_to&sort_dir=desc", mine) == [a3, a4, a1, a2]
    #  Trạng thái dòng đời: 1 Sắp tới (a3) -> 2 Đang hiệu lực (a2, a4; id giảm dần) -> 3 Đã kết thúc (a1).
    assert _ids(client, ASSIGN_URL, "sort_by=state&sort_dir=asc", mine) == [a3, a4, a2, a1]
    assert _ids(client, ASSIGN_URL, "sort_by=state&sort_dir=desc", mine) == [a1, a4, a2, a3]
    #  Ghi chú: ô trống (a2) cuối cả hai chiều.
    assert _ids(client, ASSIGN_URL, "sort_by=note&sort_dir=asc", mine) == [a4, a1, a3, a2]
    assert _ids(client, ASSIGN_URL, "sort_by=note&sort_dir=desc", mine) == [a3, a1, a4, a2]
    #  Mặc định cũ (từ ngày giảm dần); "Hạn mức năm nay" / khóa lạ không xếp được -> mặc định, không lỗi.
    default = [a3, a4, a2, a1]
    assert _ids(client, ASSIGN_URL, "", mine) == default
    assert _ids(client, ASSIGN_URL, "sort_by=current_year_quotas&sort_dir=asc", mine) == default
    assert _ids(client, ASSIGN_URL, "sort_by=khong_co_cot", mine) == default


# ── 5. Quỹ phép thẻ Theo nhân sự ──────────────────────────────────────────────────────

MATRIX_URL = "/api/leave-balances/matrix"


def test_quy_phep_theo_nhan_su_xep_theo_ma_ten_phong_ban_va_excel_cung_thu_tu(db, world, client_as):
    client = _client(world, client_as, "leave_balance", ("read", "export"))
    lt = LeaveType(code="PN746", name="Phep nam", counts_balance=True, annual_quota_days=12.0, sort_order=1)
    db.add(lt)
    db.flush()
    #  Phòng: A.kt "Phòng Kế toán", A.mua "Phòng Thu mua", B.hc "Phòng Hành chính"; p4 chưa gắn phòng -> ô trống.
    specs = [("MX3", "Zeta Mx", "A.mua"), ("MX1", "Alpha Mx", "A.kt"), ("MX4", "Mu Mx", None),
             ("MX2", "Beta Mx", "B.hc")]
    emp_ids = []
    for code, name, dept in specs:
        e = Employee(code=code, full_name=name, company_id=world.co["A"],
                     department_id=world.dept[dept] if dept else 0, is_active=True, hire_date=date(2020, 1, 1))
        db.add(e)
        db.flush()
        db.add(LeaveBalance(employee_id=e.id, year=YEAR, leave_type_id=lt.id, company_id=world.co["A"],
                            allocated_days=12))
        emp_ids.append(e.id)
    db.commit()
    p3, p1, p4, p2 = emp_ids   # theo thứ tự `specs`

    def order(qs):
        res = client.get(f"{MATRIX_URL}?year={YEAR}&{qs}&page_size=100")
        assert res.status_code == 200, res.text
        return [r["employee_id"] for r in res.json()["data"]["items"]]

    assert order("sort_by=code&sort_dir=asc") == [p1, p2, p3, p4]
    assert order("sort_by=code&sort_dir=desc") == [p4, p3, p2, p1]
    assert order("sort_by=name&sort_dir=asc") == [p1, p2, p4, p3]
    assert order("sort_by=name&sort_dir=desc") == [p3, p4, p2, p1]
    #  Phòng ban theo TÊN: Hành chính (p2) < Kế toán (p1) < Thu mua (p3); p4 chưa gắn phòng cuối cả hai chiều.
    assert order("sort_by=department_name&sort_dir=asc") == [p2, p1, p3, p4]
    assert order("sort_by=department_name&sort_dir=desc") == [p3, p1, p2, p4]
    #  Mặc định cũ (mã NV); cột số ngày / khóa lạ không xếp được -> mặc định, không lỗi.
    default = [p1, p2, p3, p4]
    assert order("") == default
    assert order("sort_by=total&sort_dir=desc") == default
    assert order("sort_by=khong_co_cot") == default

    #  Tệp Excel đi cùng thứ tự với bảng: cột đầu = Mã NV.
    from openpyxl import load_workbook

    def exported_codes(qs):
        res = client.get(f"{MATRIX_URL}/export?year={YEAR}&{qs}")
        assert res.status_code == 200, res.text
        sheet = load_workbook(io.BytesIO(res.content)).active
        return [row[0] for row in sheet.iter_rows(min_row=2, values_only=True) if row[0]]

    assert exported_codes("sort_by=name&sort_dir=desc") == ["MX3", "MX4", "MX2", "MX1"]
    assert exported_codes("sort_by=department_name&sort_dir=asc") == ["MX2", "MX1", "MX3", "MX4"]
    assert exported_codes("") == ["MX1", "MX2", "MX3", "MX4"]


# ── 6. Trạng thái theo DÒNG ĐỜI ───────────────────────────────────────────────────────
#  Mã số khai theo thứ tự thêm vào: 1 Nháp, 2 Chờ duyệt, 3 Đã duyệt, 4 Từ chối, 5 Trả về, 6 Đã hủy.
#  Dòng đời đọc: Nháp(1) -> Chờ duyệt(2) -> Trả về(5) -> Đã duyệt(3) -> Từ chối(4) -> Đã hủy(6).
LIFECYCLE_CODES = [1, 2, 5, 3, 4, 6]


def test_don_nghi_phep_trang_thai_xep_theo_dong_doi(db, world, client_as):
    client = _client(world, client_as, "leave_request")
    emp = Employee(code="LRS", full_name="Nguoi Nghi", company_id=world.co["A"], is_active=True)
    db.add(emp)
    db.flush()
    by_status = {}
    for status in (4, 6, 1, 3, 5, 2):   # cố ý tạo lộn xộn để id không trùng thứ tự dòng đời
        r = LeaveRequest(code=f"LRS-{status}", employee_id=emp.id, company_id=world.co["A"],
                         from_date=date(2026, 1, 5), to_date=date(2026, 1, 5), status=status, total_days=1.0)
        db.add(r)
        db.flush()
        by_status[status] = r.id
    db.commit()
    mine = set(by_status.values())
    expected = [by_status[s] for s in LIFECYCLE_CODES]
    _both_ways(client, "/api/leave-requests", "status", expected, mine)


def test_dat_phong_hop_trang_thai_xep_theo_dong_doi(db, world, client_as):
    client = _client(world, client_as, "room_booking")
    by_status = {}
    for status in (4, 6, 1, 3, 5, 2):
        b = RoomBooking(code=f"RBS-{status}", company_id=world.co["A"], status=status,
                        start_at=datetime(2026, 1, 5, 9), end_at=datetime(2026, 1, 5, 10), title=f"Hop {status}")
        db.add(b)
        db.flush()
        by_status[status] = b.id
    db.commit()
    mine = set(by_status.values())
    expected = [by_status[s] for s in LIFECYCLE_CODES]
    _both_ways(client, "/api/room-bookings", "status", expected, mine)


def test_phieu_nghi_bu_va_thanh_toan_phep_trang_thai_xep_theo_dong_doi(db, world):
    comps, encashes = {}, {}
    emp = Employee(code="CE746", full_name="Nguoi Bu", is_active=True)
    lt = LeaveType(code="CE746L", name="Loai Bu")
    db.add_all([emp, lt])
    db.flush()
    for status in (4, 6, 1, 3, 5, 2):
        c = LeaveCompRequest(code=f"CB-{status}", employee_id=emp.id, work_date=date(2026, 1, 1), days=1.0,
                             status=status, is_deleted=False)
        e = LeaveEncashment(code=f"TT-{status}", employee_id=emp.id, leave_type_id=lt.id, balance_year=2026,
                            reason_kind=1, days=1.0, status=status, is_deleted=False)
        db.add_all([c, e])
        db.flush()
        comps[status], encashes[status] = c.id, e.id

    comp_rows = lambda d: [r.id for r in db.query(LeaveCompRequest).order_by(*comp_sort.build_comp_order_by("status", d)).all()]
    enc_rows = lambda d: [r.id for r in db.query(LeaveEncashment).order_by(*comp_sort.build_encashment_order_by("status", d)).all()]
    assert comp_rows("asc") == [comps[s] for s in LIFECYCLE_CODES]
    assert comp_rows("desc") == [comps[s] for s in reversed(LIFECYCLE_CODES)]
    assert enc_rows("asc") == [encashes[s] for s in LIFECYCLE_CODES]
    assert enc_rows("desc") == [encashes[s] for s in reversed(LIFECYCLE_CODES)]
    #  Khóa lạ -> rỗng để nơi gọi dùng đường cũ (không lỗi).
    assert comp_sort.build_comp_order_by("khong_co_cot", "asc") == []
    assert comp_sort.build_encashment_order_by("khong_co_cot", "asc") == []
