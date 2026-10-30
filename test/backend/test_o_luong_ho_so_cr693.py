"""duoc-CR-693 — ô LƯƠNG trên hồ sơ nhân sự (`salary_monthly`, `allowance_monthly`).

Luật đại ca chốt: CHỈ chính nhân sự đó đọc được SỐ (không ai khác — kể cả admin, người nhập, người có
`employee_sensitive` / `labor_contract`); người khác chỉ biết cờ `salary_set`. Ghi cần `employee.write` trong phạm vi,
nhưng không ai tự đổi lương của mình. Lương không vào nhật ký. Ký HĐLĐ tự điền ô hồ sơ.
"""
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.vn_time import vn_today
from app.main import app
from app.modules.audit.model import AuditLog
from app.modules.employee import sensitive
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeUpdate

SAL, ALW = 23_456_789, 1_234_567


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _set_salary(db, world, key, salary=SAL, allow=ALW):
    e = db.get(Employee, world.emp[key])
    e.salary_monthly, e.allowance_monthly = salary, allow
    db.commit()
    return e


def _rich_actor(world, key):
    """Người có MỌI quyền liên quan: employee đủ + nhạy cảm + HĐLĐ — vẫn KHÔNG được đọc lương người khác."""
    world.grant(key, "employee", "all", actions=("read", "write", "export", "create", "delete"))
    world.grant(key, "employee_sensitive", "all", actions=("read", "write"))
    world.grant(key, "labor_contract", "all", actions=("read", "write", "export"))
    return world.actor(key)


# ---------- ĐỌC ----------
def test_chinh_chu_thay_so_o_chi_tiet_va_me(db, world, client_as):
    me = _set_salary(db, world, "a1")
    world.grant("a1", "employee", "all", actions=("read",))
    client = client_as(world.actor("a1").user)
    for url in (f"/api/employees/{me.id}", "/api/employees/me"):
        d = client.get(url).json()["data"]
        assert d["salary_monthly"] == SAL and d["allowance_monthly"] == ALW and d["salary_set"] is True


def test_nguoi_khac_ke_ca_admin_khong_thay_so_chi_thay_co(db, world, client_as):
    victim = _set_salary(db, world, "a2")
    actor = _rich_actor(world, "a1")
    client = client_as(actor.user)
    resp = client.get(f"/api/employees/{victim.id}")
    d = resp.json()["data"]
    assert d["salary_monthly"] == 0 and d["allowance_monthly"] == 0 and d["salary_set"] is True
    assert str(SAL) not in resp.text
    # người chưa nhập lương: cờ false
    other = db.get(Employee, world.emp["a3"])
    assert client.get(f"/api/employees/{other.id}").json()["data"]["salary_set"] is False


def test_danh_sach_chi_dong_cua_chinh_minh_co_so(db, world, client_as):
    a1 = _set_salary(db, world, "a1", 11_111_111, 0)
    _set_salary(db, world, "a2", 22_222_222, 0)
    actor = _rich_actor(world, "a1")
    resp = client_as(actor.user).get("/api/employees", params={"page_size": 100})
    items = {i["id"]: i for i in resp.json()["data"]["items"]}
    assert items[a1.id]["salary_monthly"] == 11_111_111
    assert items[world.emp["a2"]]["salary_monthly"] == 0 and items[world.emp["a2"]]["salary_set"] is True
    assert "22222222" not in resp.text


def test_khong_sap_xep_theo_luong(db, world, client_as):
    world.grant("a1", "employee", "all", actions=("read",))
    client = client_as(world.actor("a1").user)
    for col in ("salary_monthly", "allowance_monthly", "salary_updated_at"):
        assert client.get("/api/employees", params={"sort_by": col}).status_code == 400


def test_csv_khong_lo_luong(db, world, client_as):
    _set_salary(db, world, "a2")
    actor = _rich_actor(world, "a1")
    resp = client_as(actor.user).get("/api/employees/export/csv")
    assert resp.status_code == 200 and str(SAL) not in resp.text and str(ALW) not in resp.text


def test_mask_va_mask_many_che_luong_mac_dinh():
    row = {"id": 5, "salary_monthly": SAL, "allowance_monthly": ALW, "salary_set": True, "bank_name": "X"}
    assert sensitive.mask(dict(row), True)["salary_monthly"] == 0      # mặc định an toàn: không truyền profile = che
    # có quyền nhạy cảm cũng không mở lương
    prof = {"employee_id": 9, "perms_union": {"employee_sensitive": {"read": True}}}
    out = sensitive.mask_many([dict(row)], prof)[0]
    assert out["salary_monthly"] == 0 and out["bank_name"] == "X" and out["salary_set"] is True
    # chính chủ
    me = {"employee_id": 5, "perms_union": {}}
    assert sensitive.mask_many([dict(row)], me)[0]["salary_monthly"] == SAL
    # employee_id = 0 (tài khoản chưa gắn nhân sự) không khớp hồ sơ id 0
    assert sensitive.mask({"id": 0, "salary_monthly": SAL}, True, {"employee_id": 0})["salary_monthly"] == 0


def test_xuat_che_theo_dong_ke_ca_khi_co_quyen_nhay_cam():
    from app.modules.employee.export_mask import mask_export_rows
    prof = {"employee_id": 2, "perms_union": {"employee_sensitive": {"read": True}}}
    rows = [{"salary_monthly": SAL}, {"salary_monthly": SAL}]
    mask_export_rows(rows, [1, 2], prof)
    assert rows[0]["salary_monthly"] == 0 and rows[1]["salary_monthly"] == SAL


def test_tro_ly_ai_khong_co_luong():
    from app.modules.assistant.tools import employee_tool
    assert not set(employee_tool._OUT_FIELDS) & {"salary_monthly", "allowance_monthly", "salary_set"}
    e = Employee(code="X", full_name="X", salary_monthly=SAL, allowance_monthly=ALW)
    assert "salary_monthly" not in employee_tool._dump(e)


def test_nhat_ky_va_log_request_khong_giu_so():
    from app.core import change_tracker, logging_policy
    assert {"salary_monthly", "allowance_monthly"} <= change_tracker._table_field_denylist()["tab_employee"]
    assert not change_tracker._is_allowed("tab_employee", "salary_monthly")
    assert {"salary_monthly", "allowance_monthly"} <= logging_policy.sensitive_keys_for_path("/api/employees/5")


# ---------- GHI ----------
def test_nguoi_co_quyen_ghi_duoc_luong_nguoi_khac_cau_tra_loi_van_che(db, world, client_as):
    world.grant("a1", "employee", "all", actions=("read", "write"))
    victim = db.get(Employee, world.emp["a2"])
    client = client_as(world.actor("a1").user)
    r = client.patch(f"/api/employees/{victim.id}", json={"salary_monthly": SAL, "allowance_monthly": ALW})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["salary_monthly"] == 0 and d["salary_set"] is True            # cửa GHI cũng che
    db.expire_all()
    t = db.get(Employee, victim.id)
    assert (t.salary_monthly, t.allowance_monthly) == (SAL, ALW) and t.salary_updated_at is not None
    # nhật ký: ghi «Cập nhật lương», KHÔNG kèm số
    msgs = [a.message for a in db.query(AuditLog).filter(AuditLog.entity == "employee", AuditLog.entity_id == victim.id)]
    assert any("Cập nhật lương" in m for m in msgs)
    assert not any(str(SAL) in m or str(ALW) in m for m in msgs)


def test_null_vang_giu_nguyen_gui_0_la_xoa(db, world, client_as):
    victim = _set_salary(db, world, "a2")
    world.grant("a1", "employee", "all", actions=("read", "write"))
    client = client_as(world.actor("a1").user)
    assert client.patch(f"/api/employees/{victim.id}", json={"salary_monthly": None, "phone": "0900"}).status_code == 200
    assert client.patch(f"/api/employees/{victim.id}", json={"phone": "0911"}).status_code == 200
    db.expire_all()
    t = db.get(Employee, victim.id)
    assert (t.salary_monthly, t.allowance_monthly) == (SAL, ALW)
    # chỉ gửi một ô: ô kia giữ nguyên
    assert client.patch(f"/api/employees/{victim.id}", json={"allowance_monthly": 0}).status_code == 200
    db.expire_all()
    t = db.get(Employee, victim.id)
    assert (t.salary_monthly, t.allowance_monthly) == (SAL, 0)
    assert client.patch(f"/api/employees/{victim.id}", json={"salary_monthly": 0}).status_code == 200
    db.expire_all()
    assert db.get(Employee, victim.id).salary_set is False


def test_khong_tu_sua_luong_cua_minh_kem_ca_nguoi_quyen_cao(db, world, client_as):
    me = _set_salary(db, world, "a1")
    actor = _rich_actor(world, "a1")
    client = client_as(actor.user)
    assert client.patch(f"/api/employees/{me.id}", json={"salary_monthly": SAL * 2}).status_code == 403
    assert client.patch(f"/api/employees/{me.id}", json={"allowance_monthly": 1}).status_code == 403
    db.expire_all()
    assert db.get(Employee, me.id).salary_monthly == SAL
    # gửi lại NGUYÊN giá trị cũ (màn hồ sơ gửi mọi ô) + sửa ô khác -> được
    r = client.patch(f"/api/employees/{me.id}", json={"salary_monthly": SAL, "allowance_monthly": ALW, "phone": "0922"})
    assert r.status_code == 200
    assert r.json()["data"]["salary_monthly"] == SAL      # chính chủ thấy số của mình trong câu trả lời


def test_ngoai_pham_vi_va_khong_quyen_ghi(db, world, client_as):
    world.grant("a1", "employee", "dept", actions=("read", "write"))
    client = client_as(world.actor("a1").user)
    assert client.patch(f"/api/employees/{world.emp['b1']}", json={"salary_monthly": 1}).status_code == 404
    world.grant("a3", "employee", "all", actions=("read",))
    assert client_as(world.actor("a3").user).patch(
        f"/api/employees/{world.emp['a2']}", json={"salary_monthly": 1}).status_code == 403


@pytest.mark.parametrize("bad", [-1, 10**10 + 1, 10**15])
def test_tran_gia_tri_422(bad):
    with pytest.raises(ValidationError):
        EmployeeUpdate(salary_monthly=bad)
    with pytest.raises(ValidationError):
        EmployeeUpdate(allowance_monthly=bad)
    assert EmployeeUpdate(salary_monthly=10**10).salary_monthly == 10**10


# ---------- NHẬP EXCEL ----------
def test_nhap_excel_bo_qua_cot_luong_va_canh_bao(db, seed, cap_quyen):
    from test_nhap_excel_nhan_su_cr628 import make_wb, run_import, logs, savepoint_that
    from app.modules.import_tool.employee_import_fields import EMPLOYEE_FIELDS
    from app.modules.import_tool.model import LogLevel
    assert not {f["attr"] for f in EMPLOYEE_FIELDS} & {"salary_monthly", "allowance_monthly"}
    savepoint_that(db)
    uid = seed.u_req_id
    cap_quyen(uid, "employee", scope="all", read=True, create=True, write=True)
    b = run_import(db, [{"Mã NV *": "NSU9301", "Họ tên *": "Lương Test", "Lương": 99_000_000, "Phụ cấp": 5}], uid)
    db.expire_all()
    e = db.query(Employee).filter(Employee.code == "NSU9301").first()
    assert e is not None and e.salary_monthly == 0 and e.allowance_monthly == 0
    warn = [lg.message for lg in logs(db, b.id, LogLevel.WARNING)]
    assert any("không nhập được từ tệp" in m and "Lương" in m and "Phụ cấp" in m for m in warn)
    assert not any("99000000" in m for m in warn)


# ---------- KÝ HĐLĐ ----------
def _contract(db, world, emp_id, **kw):
    from app.modules.labor_contract.model import LaborContract
    n = db.query(LaborContract).count() + 1
    vals = dict(code=f"HDX{n:04d}", employee_id=emp_id, company_id=world.co["A"], department_id=world.dept["A.kt"],
                contract_type=3, status=1, start_date=vn_today() - timedelta(days=30),
                base_salary=15_000_000, allowance=2_000_000, insurance_salary=0)
    vals.update(kw)
    row = LaborContract(**vals)
    db.add(row)
    db.commit()
    return row


def _sign(db, world, row):
    from app.modules.labor_contract import service
    from app.modules.labor_contract.schema import TransitionIn
    actor = world.actor("a1")
    service.transition(db, actor.user, row, TransitionIn(to_status=2, date=vn_today()))
    db.expire_all()
    return db.get(Employee, row.employee_id)


def test_ky_hdld_cap_nhat_o_ho_so(db, world):
    emp = db.get(Employee, world.emp["a2"])
    assert not emp.salary_set
    e = _sign(db, world, _contract(db, world, emp.id))
    assert (e.salary_monthly, e.allowance_monthly) == (15_000_000, 2_000_000) and e.salary_updated_at is not None
    msgs = [a.message for a in db.query(AuditLog).filter(AuditLog.entity == "employee", AuditLog.entity_id == emp.id)]
    assert any("ký hợp đồng" in m for m in msgs) and not any("15000000" in m for m in msgs)


def test_ky_hd_cu_hon_hoac_chua_hieu_luc_hoac_het_han_khong_ghi_de(db, world):
    emp = db.get(Employee, world.emp["a2"])
    new = _contract(db, world, emp.id, base_salary=30_000_000, allowance=0, start_date=vn_today() - timedelta(days=10))
    assert _sign(db, world, new).salary_monthly == 30_000_000
    # HĐ cũ hơn ký sau: không ghi đè lương của HĐ mới nhất đang chạy
    old = _contract(db, world, emp.id, base_salary=8_000_000, allowance=0, start_date=vn_today() - timedelta(days=200))
    assert _sign(db, world, old).salary_monthly == 30_000_000
    # chưa tới ngày hiệu lực
    future = _contract(db, world, emp.id, base_salary=50_000_000, start_date=vn_today() + timedelta(days=30))
    assert _sign(db, world, future).salary_monthly == 30_000_000
    # đã hết hạn
    expired = _contract(db, world, emp.id, base_salary=1_000_000, start_date=vn_today() - timedelta(days=400),
                        end_date=vn_today() - timedelta(days=5), contract_type=2)
    assert _sign(db, world, expired).salary_monthly == 30_000_000


def test_ky_hd_moi_hon_ghi_de_va_hd_nhap_khong_dong_toi_ho_so(db, world):
    emp = db.get(Employee, world.emp["a2"])
    _contract(db, world, emp.id, base_salary=1, allowance=1)             # nháp: không đụng hồ sơ
    db.expire_all()
    assert db.get(Employee, emp.id).salary_set is False
    first = _contract(db, world, emp.id, base_salary=10_000_000, allowance=0, start_date=vn_today() - timedelta(days=100))
    assert _sign(db, world, first).salary_monthly == 10_000_000
    second = _contract(db, world, emp.id, base_salary=12_000_000, allowance=500_000, start_date=vn_today() - timedelta(days=5))
    e = _sign(db, world, second)
    assert (e.salary_monthly, e.allowance_monthly) == (12_000_000, 500_000)
