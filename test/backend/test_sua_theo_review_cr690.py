"""duoc-CR-690 — sửa theo rà mã backend: phạm vi HĐLĐ ở thực tế / position-stats, luật xem tiền theo phòng, cấu trúc khoản
của người không xem được tiền, N+1, luật nguồn thực tế, Tổng A5 không suy ngược được lương, lùi kế hoạch hẹp sai luật,
người duyệt, ngữ nghĩa None, xung đột 409, tệp đính kèm của người không xem được tiền."""
from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from hdld_factory import client_as  # noqa: F401
from headcount_plan_factory import URL, add_costed_plan, basic_items, cost_item, grant_hr, plan_body
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from test_bao_cao_dinh_bien_ke_hoach_cr689 import A5, L_ITEM, QS5, TODAY, _a5_actor, _a5_plan, _emp, _get, _hd

from app.core.attachment_scope import ensure_in_scope
from app.core.auth import get_perm_profile
from app.modules.employee.model import Employee
from app.modules.headcount_plan.cost_model import HeadcountPlanCostItem, HrCostTemplate, HrCostTemplateItem
from app.modules.headcount_plan.costing import CostItem, PlanCalcError, PlanLine, compute_plan
from app.modules.headcount_plan.effective import load_effective_monthly
from app.modules.headcount_plan.model import HeadcountPlan, HeadcountPlanLine
from app.modules.headcount_plan.serializer import can_see_payroll
from app.modules.labor_contract.model import LaborContract

YEAR = TODAY.year
_n = {"v": 0}


def _statements(db, fn):
    stmts, eng = [], db.get_bind()

    def on(conn, cursor, statement, *a):
        stmts.append(statement)
    event.listen(eng, "before_cursor_execute", on)
    try:
        fn()
    finally:
        event.remove(eng, "before_cursor_execute", on)
    return len(stmts)


def _contract(db, world, emp, *, co="A", base=10_000_000, status=2, deleted=False, terminated=None, start=None):
    _n["v"] += 1
    db.add(LaborContract(code=f"RV{_n['v']:05d}", employee_id=emp.id, company_id=world.co[co],
                         department_id=emp.department_id, contract_type=2, status=status,
                         start_date=start or date(YEAR - 1, 1, 1), signed_file_id=1, base_salary=base, allowance=0,
                         insurance_salary=0, is_deleted=deleted, terminated_date=terminated))


def _a_emp(db, world, tag, dept="A.kt"):
    e = Employee(code=f"RV{tag}", full_name=f"Nhân sự {tag}", company_id=world.co["A"], department_id=world.dept[dept],
                 is_active=True, hire_date=date(YEAR - 1, 1, 1))
    db.add(e)
    db.flush()
    return e


# ---- C1: thực tế trong chi tiết kế hoạch đi qua phạm vi + bỏ HĐ xóa mềm ---------------------------------
def test_c1_thuc_te_chi_tiet_bo_hd_xoa_mem(db, world, client_as):
    for i in range(2):
        _contract(db, world, _a_emp(db, world, f"c{i}"))
    _contract(db, world, _a_emp(db, world, "del"), base=90_000_000, deleted=True)   # HĐ đã xóa mềm: KHÔNG được cộng
    db.commit()
    plan = add_costed_plan(db, world, "A.kt", [2] * 4, year=YEAR, items=[{**L_ITEM}], amounts={"L": 10_000_000})
    actual = grant_hr(world, client_as).get(f"{URL}/{plan.id}").json()["data"]["computed"]["actual"]
    first = next(v for v in actual["values"] if v is not None)
    assert first == 2 * 10_000_000 * next(c for c in actual["months_counted"] if c)


def test_c1_phong_bi_loai_tru_khong_xem_duoc_tien_ke_hoach_cua_phong_do(db, world, client_as):
    for i in range(2):
        _contract(db, world, _a_emp(db, world, f"x{i}"))
    db.commit()
    plan = add_costed_plan(db, world, "A.kt", [2] * 4, year=YEAR, items=[{**L_ITEM}], amounts={"L": 10_000_000})
    whole = add_costed_plan(db, world, None, [2] * 4, year=YEAR, items=[{**L_ITEM}], amounts={"L": 10_000_000})
    world.grant("a1", "headcount_plan", "all", actions=("read", "write", "export"))
    world.grant("a1", "labor_contract", "all", actions=("read",), exc_dept=("A.kt",))
    client = client_as(world.actor("a1"))
    got = client.get(f"{URL}/{plan.id}").json()["data"]
    assert got["can_see_money"] is False and got["computed"]["money_hidden"] is True
    assert got["computed"]["actual"]["values"] == [None] * 4
    whole_got = client.get(f"{URL}/{whole.id}").json()["data"]
    assert whole_got["can_see_money"] is True      # toàn pháp nhân xét theo pháp nhân
    #  E2E CR-690: thực tế toàn pháp nhân thiếu lương phòng bị loại trừ mà trông như đủ → không so, báo limited_scope
    assert whole_got["computed"]["actual"]["limited_scope"] is True
    assert whole_got["computed"]["actual"]["values"] == [None] * 4
    prof = get_perm_profile(db, world.actor("a1").user)
    assert not can_see_payroll(prof, world.co["A"], world.dept["A.kt"])
    assert can_see_payroll(prof, world.co["A"], world.dept["A.mua"]) and can_see_payroll(prof, world.co["A"])
    rows = client.get(URL).json()["data"]["items"]
    assert {r["id"]: r["total_cost"] for r in rows}[plan.id] is None


# ---- C2: position-stats ------------------------------------------------------------------------------
def test_c2_position_stats_chi_hd_cua_phap_nhan_xoa_mem_va_hd_cham_dut_sau_ngay(db, world, client_as):
    ok = _a_emp(db, world, "ok")
    other_co = _a_emp(db, world, "oc")
    gone = _a_emp(db, world, "gone")
    ended = _a_emp(db, world, "end")
    _contract(db, world, ok, base=10_000_000)
    _contract(db, world, other_co, co="B", base=99_000_000)                    # HĐ ký ở pháp nhân KHÁC: không tính
    _contract(db, world, gone, base=77_000_000, deleted=True)                  # xóa mềm: không tính
    _contract(db, world, ended, base=20_000_000, status=4, terminated=TODAY + timedelta(days=30))   # còn hiệu lực tại hôm nay
    db.commit()
    client = grant_hr(world, client_as)
    resp = client.get(f"{URL}/position-stats", params={"company_id": world.co["A"], "department_id": world.dept["A.kt"]})
    row = resp.json()["data"][0]
    assert row["avg_base_salary"] == 15_000_000     # (10tr + 20tr) / 2
    blind = grant_hr(world, client_as, key="a2", pay=False)
    assert blind.get(f"{URL}/position-stats", params={"company_id": world.co["A"]}).json()["data"][0]["avg_base_salary"] is None


def test_c2_position_stats_phong_bi_loai_tru_khong_hien_luong(db, world, client_as):
    _contract(db, world, _a_emp(db, world, "p1"))
    db.commit()
    world.grant("a1", "headcount_plan", "all", actions=("read",))
    world.grant("a1", "labor_contract", "all", actions=("read",), exc_dept=("A.kt",))
    client = client_as(world.actor("a1"))
    row = client.get(f"{URL}/position-stats", params={"company_id": world.co["A"], "department_id": world.dept["A.kt"]}).json()["data"][0]
    assert row["avg_base_salary"] is None


# ---- NÊN 1: người không xem được tiền không đổi cấu trúc khoản ----------------------------------------
def _blind_plan(db, world, client_as):
    admin = grant_hr(world, client_as, key="a1")
    plan = admin.post(URL, json=plan_body(world)).json()["data"]
    return plan, grant_hr(world, client_as, key="a2", pay=False)


BLIND_LINES = [{"position_id": 0, "headcounts": [2, 2, 3, 3], "amounts": None}]


def _quiet_items(**override):
    items = [cost_item("L", 1, name="Lương"), cost_item("BH", 2, name="BHXH", rate=17.5, base_codes=["L"], cap_amount=None),
             cost_item("B13", 3, name="Thưởng 13", factor=1, base_codes=["L"], months=[12])]
    for it in items:
        it.update(override.get(it["code"], {}))
    return items


@pytest.mark.parametrize("change", [
    {"BH": {"rate": 99}}, {"B13": {"months": [11]}}, {"L": {"actual_source": 1}}, {"BH": {"base_codes": []}},
    {"L": {"calc_method": 5, "applies_to": 3}}, {"L": {"group_id": 0, "applies_to": 2, "position_ids": [5]}}])
def test_nguoi_khong_xem_tien_khong_doi_cau_truc_khoan(db, world, client_as, change):
    plan, blind = _blind_plan(db, world, client_as)
    resp = blind.put(f"{URL}/{plan['id']}", json=plan_body(world, cost_items=_quiet_items(**change)))
    assert resp.status_code == 403 and "Cần quyền xem lương của pháp nhân này" in resp.json()["error"]["message"]


def test_nguoi_khong_xem_tien_khong_them_xoa_doi_ma_khoan_nhung_doi_ten_duoc(db, world, client_as):
    plan, blind = _blind_plan(db, world, client_as)
    url = f"{URL}/{plan['id']}"
    assert blind.put(url, json=plan_body(world, cost_items=_quiet_items()[:2], lines=BLIND_LINES)).status_code == 403          # xóa
    extra = _quiet_items() + [cost_item("NEW", 1)]
    assert blind.put(url, json=plan_body(world, cost_items=extra, lines=BLIND_LINES)).status_code == 403                       # thêm
    renamed = _quiet_items()
    renamed[0]["code"] = "L2"
    renamed[1]["base_codes"] = ["L2"]
    renamed[2]["base_codes"] = ["L2"]
    assert blind.put(url, json=plan_body(world, cost_items=renamed, lines=BLIND_LINES)).status_code == 403                     # đổi mã
    ok = blind.put(url, json=plan_body(world, cost_items=_quiet_items(L={"name": "Lương mới"}), note="đổi ghi chú", lines=BLIND_LINES))
    assert ok.status_code == 200, ok.text


# ---- NÊN 2: số truy vấn của danh sách không tăng theo số kế hoạch / mẫu -------------------------------
def test_danh_sach_ke_hoach_so_truy_van_co_dinh(db, world, client_as):
    client = grant_hr(world, client_as)
    items = [{"code": "L", "name": "Lương", "calc_method": 1, "actual_source": 1}]
    add_costed_plan(db, world, "A.kt", [1] * 4, year=YEAR, items=items, amounts={"L": 1_000_000})
    client.get(URL)   # khởi động nguội (hồ sơ quyền, bảng) không tính
    add_costed_plan(db, world, "A.mua", [1] * 4, year=YEAR, items=items, amounts={"L": 1_000_000})
    two = _statements(db, lambda: client.get(URL))     # từ 2 kế hoạch (cùng pháp nhân) trở đi số truy vấn không đổi
    for dept in ("B.kt", "B.hc"):
        add_costed_plan(db, world, dept, [1] * 4, co="B", year=YEAR, items=items, amounts={"L": 1_000_000})
    four = _statements(db, lambda: client.get(URL))
    print("N1", two, four)
    assert two > 0 and four - two <= 1


def test_danh_sach_mau_so_truy_van_co_dinh(db, world, client_as):
    client = grant_hr(world, client_as)

    def tpl(name):
        t = HrCostTemplate(name=name, note="")
        db.add(t)
        db.flush()
        db.add(HrCostTemplateItem(template_id=t.id, code="L", name="L", calc_method=1, base_codes=[], position_ids=[],
                                  months=[]))
        db.commit()
    tpl("M1")
    url = "/api/hr-cost-templates"
    client.get(url)
    one = _statements(db, lambda: client.get(url))
    for n in range(2, 6):
        tpl(f"M{n}")
    resp = client.get(url)
    assert _statements(db, lambda: client.get(url)) == one and {i["item_count"] for i in resp.json()["data"]["items"]} == {1}


# ---- NÊN 3: luật cách tính 4 và nguồn thực tế -----------------------------------------------------
def _ci(code, method, **kw):
    return CostItem(code=code, name=code, calc_method=method, **kw)


def test_cach_tinh_4_bat_buoc_chon_thang():
    with pytest.raises(PlanCalcError, match="chưa chọn tháng chi"):
        compute_plan(1, 1, YEAR, [_ci("A", 4, amount=1)], [PlanLine(0, (1, 1, 1, 1))])
    assert compute_plan(1, 1, YEAR, [_ci("A", 4, amount=1, months=(1,))], [PlanLine(0, (1, 1, 1, 1))])["total"]["total"] == 1


@pytest.mark.parametrize("method,source,ok", [(1, 1, True), (1, 2, True), (1, 3, False), (2, 3, True), (2, 1, False),
                                              (3, 1, False), (4, 2, False), (5, 3, False), (1, 0, True)])
def test_nguon_thuc_te_phai_khop_cach_tinh(method, source, ok):
    base = _ci("L", 1)
    extra = {"base_codes": ("L",), "months": (1,), "factor": 1, "amount": 1}
    item = _ci("X", method, actual_source=source, **(extra if method in (2, 3, 4) else {"amount": 1}))
    items = [base, item] if method in (2, 3) else [item]
    if ok:
        compute_plan(1, 1, YEAR, items, [])
    else:
        with pytest.raises(PlanCalcError, match="nguồn thực tế"):
            compute_plan(1, 1, YEAR, items, [])


def test_api_422_nguon_thuc_te_sai_cach_tinh(db, world, client_as):
    client = grant_hr(world, client_as)
    bad = plan_body(world, cost_items=[cost_item("L", 1, actual_source=3)])
    assert client.post(URL, json=bad).status_code == 422


# ---- NÊN 4: Tổng A5 không suy ngược được lương --------------------------------------------------
def test_a5_tong_phan_so_duoc_an_khi_con_noi_chua_co_ke_hoach(db, world, client_as):
    for i in range(3):
        _hd(db, world, _emp(db, world, f"k{i}", dept="B.kt"))
        _hd(db, world, _emp(db, world, f"h{i}", dept="B.hc"))
    _a5_plan(db, world, "B.kt", n=3)                     # B.hc có 3 người hưởng lương nhưng CHƯA có kế hoạch
    client = _a5_actor(db, world, client_as)
    data = _get(client, A5, qs=QS5, company_id=world.co["B"]).json()["data"]
    cur = data["totals"]["current"]
    assert cur["actual_comparable"] is None and cur["payroll_remaining"] is None and cur["payroll_use_rate"] is None
    assert any("Tổng phần so được không hiện" in n for n in data["notes"])
    _a5_plan(db, world, "B.hc", n=3)                     # đủ kế hoạch cho mọi nơi → Tổng hiện lại
    full = _get(client, A5, qs=QS5, company_id=world.co["B"]).json()["data"]
    assert full["totals"]["current"]["actual_comparable"] == 6 * 10_000_000 * 3
    assert not any("Tổng phần so được không hiện" in n for n in full["notes"])


def test_a5_tong_phan_so_duoc_an_khi_co_nhom_bi_che(db, world, client_as):
    for i in range(3):
        _hd(db, world, _emp(db, world, f"k{i}", dept="B.kt"))
    for i in range(2):                                   # nhóm 2 người: bị che
        _hd(db, world, _emp(db, world, f"h{i}", dept="B.hc"))
    _a5_plan(db, world, "B.kt", n=3)
    _a5_plan(db, world, "B.hc", n=2)
    client = _a5_actor(db, world, client_as)
    data = _get(client, A5, qs=QS5, company_id=world.co["B"], group_by="department").json()["data"]
    assert any(g.get("suppressed") for g in data["groups"])
    cur = data["totals"]["current"]
    assert cur["actual_comparable"] is None and cur["payroll_use_rate"] is None
    assert any("nhóm nhỏ bị che" in n for n in data["notes"])


# ---- NÊN 5: kế hoạch hẹp sai luật tính → lùi về kế hoạch rộng hơn -------------------------------
def test_ke_hoach_hep_sai_luat_lui_ve_ke_hoach_rong(db, world):
    add_costed_plan(db, world, "A.kt", [4, 4, 4, 4], year=YEAR)
    add_costed_plan(db, world, "A.kt", lines=[(0, [9], {})], year=YEAR, period_type=3, period_no=3)   # Quý 3 cần 3 cột, chỉ có 1
    world.grant("b1", "headcount_plan", "all", actions=("read",))
    user = world.actor("b1").user
    eff = load_effective_monthly(db, user, get_perm_profile(db, user), [(YEAR, 7), (YEAR, 2)])
    assert eff[(world.co["A"], world.dept["A.kt"], YEAR, 7)].headcount == 4          # lùi về kế hoạch Năm
    assert eff[(world.co["A"], world.dept["A.kt"], YEAR, 2)].headcount == 4


# ---- Nhỏ: người duyệt --------------------------------------------------------------------------
def test_nguoi_duyet_phai_ton_tai_va_trong_pham_vi_nhan_su(db, world, client_as):
    world.grant("a1", "employee", "company", actions=("read",))
    client = grant_hr(world, client_as, key="a1")
    own = _a_emp(db, world, "dy")
    foreign = Employee(code="RVF", full_name="Người pháp nhân B", company_id=world.co["B"], department_id=world.dept["B.hc"],
                       is_active=True, hire_date=date(YEAR - 1, 1, 1))
    db.add(foreign)
    db.commit()
    for approver in (999_999, foreign.id):
        resp = client.post(URL, json=plan_body(world, approver_employee_id=approver))
        assert resp.status_code == 422 and "Người duyệt không hợp lệ" in resp.json()["error"]["message"]
    plan = client.post(URL, json=plan_body(world, approver_employee_id=own.id)).json()["data"]
    assert plan["approver_name"] == own.full_name
    nobody = grant_hr(world, client_as, key="a2")        # không có employee.read
    assert nobody.get(f"{URL}/{plan['id']}").json()["data"]["approver_name"] == ""
    assert nobody.get(URL).json()["data"]["items"][0]["approver_name"] == ""


# ---- Nhỏ: None = giữ nguyên, 0 = xóa -------------------------------------------------------------
def test_none_giu_nguyen_con_0_xoa_cho_ca_nguoi_xem_duoc_tien(db, world, client_as):
    client = grant_hr(world, client_as)
    plan = client.post(URL, json=plan_body(world)).json()["data"]
    url = f"{URL}/{plan['id']}"
    keep = plan_body(world, cost_items=_quiet_items(), lines=[{"position_id": 0, "headcounts": [2, 2, 3, 3], "amounts": None}])
    assert client.put(url, json=keep).status_code == 200
    db.expire_all()
    assert db.query(HeadcountPlanCostItem).filter_by(plan_id=plan["id"], code="BH").one().cap_amount == 46_800_000
    assert db.query(HeadcountPlanLine).filter_by(plan_id=plan["id"]).one().amounts == {"L": 10_000_000}
    clear = plan_body(world, cost_items=_quiet_items(BH={"cap_amount": 0}),
                      lines=[{"position_id": 0, "headcounts": [2, 2, 3, 3], "amounts": {"L": 0}}])
    assert client.put(url, json=clear).status_code == 200
    db.expire_all()
    assert db.query(HeadcountPlanCostItem).filter_by(plan_id=plan["id"], code="BH").one().cap_amount == 0
    assert db.query(HeadcountPlanLine).filter_by(plan_id=plan["id"]).one().amounts == {"L": 0}


# ---- Nhỏ: xung đột ---------------------------------------------------------------------------------
def test_put_dung_unique_con_tra_409(db, world, client_as, monkeypatch):
    client = grant_hr(world, client_as)
    plan = client.post(URL, json=plan_body(world)).json()["data"]

    def boom(*a, **kw):
        raise IntegrityError("insert", {}, Exception("duplicate"))
    monkeypatch.setattr("app.modules.headcount_plan.controller.plan_save_service.replace_children", boom)
    resp = client.put(f"{URL}/{plan['id']}", json=plan_body(world))
    assert resp.status_code == 409 and "tải lại trang" in resp.json()["error"]["message"]


def test_nhap_csv_dung_unique_khi_commit_tra_loi_doc_duoc(db, world, client_as, monkeypatch):
    client = grant_hr(world, client_as)
    plan = client.post(URL, json=plan_body(world)).json()["data"]
    csv = "position_code,hc_1,hc_2,hc_3,hc_4\n,1,1,1,1\n".encode()

    def boom():
        raise IntegrityError("commit", {}, Exception("duplicate"))
    monkeypatch.setattr(db, "commit", boom)
    resp = client.post(f"{URL}/{plan['id']}/import/csv", files={"file": ("a.csv", csv, "text/csv")})
    assert resp.status_code == 400 and "tải lại trang" in resp.json()["error"]["message"]


# ---- Nhỏ: tệp đính kèm — gỡ / tải lên cũng cần xem được tiền ----------------------------------------
def test_dinh_kem_gan_go_cung_can_xem_duoc_tien(db, world, client_as):
    plan = add_costed_plan(db, world, "A.kt", [1] * 4, year=YEAR)
    grant_hr(world, client_as, key="a1")
    grant_hr(world, client_as, key="a2", pay=False)
    ensure_in_scope(db, world.actor("a1").user, "headcount_plan", plan.id, "manage")
    with pytest.raises(HTTPException) as exc:
        ensure_in_scope(db, world.actor("a2").user, "headcount_plan", plan.id, "manage")
    assert exc.value.status_code == 403
