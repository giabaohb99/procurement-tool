"""duoc-CR-690 (phase 24) — A4 / A5 đọc kế hoạch nhân sự THEO KỲ + thực tế trong chi tiết kế hoạch + tệp đính kèm.

Canh: kế hoạch hiệu lực theo tháng (kỳ hẹp thay kỳ rộng, «Toàn pháp nhân» chống cộng đôi, số truy vấn cố định), A4 lấy định biên
của tháng cuối kỳ + chiều Vị trí khớp `/rows`, hàm tính thực tế theo nguồn (lương cơ bản · phụ cấp · % × lương đóng BHXH có trần),
`computed.actual` của chi tiết (kỳ con đã qua / tương lai / che tiền), tệp đính kèm chỉ mở cho người xem được tiền, hàm suy lại giá
trị của migration hcplan03 và số truy vấn cố định của A5 khi có kế hoạch.
"""
import importlib.util
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from hdld_factory import client_as  # noqa: F401
from headcount_plan_factory import URL, add_costed_plan, grant_hr
from sqlalchemy import event
from test_bao_cao_dinh_bien_ke_hoach_cr689 import A4, A5, QS5, TODAY, _a5_actor, _a5_plan, _actor, _cur, _emp, _get, _hd

from app.core.auth import get_perm_profile
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.headcount_plan.actual_cost import actual_by_item
from app.modules.headcount_plan.effective import ItemMeta, load_effective_monthly
from app.modules.labor_contract.model import LaborContract

YEAR = TODAY.year
L_ITEM = {"code": "L", "name": "Lương", "calc_method": 1, "actual_source": 1}
AN_ITEM = {"code": "AN", "name": "Ăn trưa", "calc_method": 1, "actual_source": 0}


def _eff(db, world, months, **kw):
    world.grant("b1", "headcount_plan", "all", actions=("read",))
    user = world.actor("b1").user
    return load_effective_monthly(db, user, get_perm_profile(db, user), months, **kw)


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


# ---- Kế hoạch hiệu lực theo tháng ------------------------------------------------------------------
def test_ky_hep_thay_ky_rong_chi_o_cac_thang_no_phu(db, world):
    add_costed_plan(db, world, "A.kt", [1, 2, 3, 4], year=YEAR)                            # Năm
    add_costed_plan(db, world, "A.kt", [7, 7, 7], year=YEAR, period_type=3, period_no=3)   # Quý 3: tháng 7–9
    add_costed_plan(db, world, "A.kt", [9], year=YEAR, period_type=4, period_no=8)         # Tháng 8 hẹp hơn Quý 3
    eff = _eff(db, world, [(YEAR, m) for m in range(1, 13)])
    heads = {m: eff[(world.co["A"], world.dept["A.kt"], YEAR, m)].headcount for m in range(1, 13)}
    assert heads == {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 7, 8: 9, 9: 7, 10: 4, 11: 4, 12: 4}


def test_toan_phap_nhan_chong_cong_doi_theo_thang(db, world):
    add_costed_plan(db, world, "A.kt", [3] * 4, year=YEAR)
    add_costed_plan(db, world, None, [10], year=YEAR, period_type=4, period_no=5)          # «Toàn pháp nhân» chỉ tháng 5
    eff = _eff(db, world, [(YEAR, 4), (YEAR, 5)])
    co, dept = world.co["A"], world.dept["A.kt"]
    assert eff[(co, dept, YEAR, 4)].top and not eff[(co, dept, YEAR, 5)].top
    assert eff[(co, 0, YEAR, 5)].top and (co, 0, YEAR, 4) not in eff


def test_dinh_bien_theo_vi_tri_va_khong_bo_truy_van_theo_so_ke_hoach(db, world):
    add_costed_plan(db, world, "A.kt", lines=[(11, [2] * 4, {}), (0, [1] * 4, {})], year=YEAR)
    entry = _eff(db, world, [(YEAR, 3)])[(world.co["A"], world.dept["A.kt"], YEAR, 3)]
    assert entry.by_position == {11: 2, 0: 1} and entry.headcount == 3
    months = [(YEAR, m) for m in range(1, 13)]
    one = _statements(db, lambda: _eff(db, world, months, with_costs=True))
    for dept in ("A.mua", "B.kt", "B.hc"):
        add_costed_plan(db, world, dept, [1] * 4, co="A" if dept.startswith("A") else "B", year=YEAR, items=[L_ITEM],
                        amounts={"L": 1_000_000})
    many = _statements(db, lambda: _eff(db, world, months, with_costs=True))
    assert one > 0 and many - one <= 3          # thêm kế hoạch chỉ thêm truy vấn nạp khoản (hằng số), không theo số kế hoạch


# ---- A4: định biên của tháng cuối kỳ + chiều Vị trí ---------------------------------------------------
def _period(date_from, date_to):
    return {"preset": "custom", "date_from": date_from, "date_to": date_to, "compare": "none"}


def test_a4_dinh_bien_la_cua_thang_cuoi_ky_va_ky_hep_thay_ky_rong(db, world, client_as):
    add_costed_plan(db, world, "B.hc", [1, 2, 3, 4], year=YEAR, co="B")
    add_costed_plan(db, world, "B.hc", [7, 7, 7], year=YEAR, co="B", period_type=3, period_no=3)
    _, client = _actor(db, world, client_as)
    planned = {}
    for end in ("03-31", "06-30", "08-31", "12-31"):
        qs = _period(f"{YEAR}-01-01", f"{YEAR}-{end}")
        planned[end] = _cur(_get(client, qs=qs, company_id=world.co["B"], department_id=world.dept["B.hc"]))["planned"]
    assert planned == {"03-31": 1, "06-30": 2, "08-31": 7, "12-31": 4}


def _position_dataset(db, world):
    kt, tp, other = (JobPosition(code=c, name=n) for c, n in (("KTV", "Kế toán viên"), ("KTT", "Trưởng phòng"),
                                                              ("KHAC", "Vị trí khác")))
    db.add_all([kt, tp, other])
    db.flush()
    for i, pos in enumerate((kt, kt, tp, other)):
        _emp(db, world, f"v{i}", position_id=pos.id)
    add_costed_plan(db, world, "B.hc", co="B", year=TODAY.year, lines=[(kt.id, [3] * 4, {}), (tp.id, [1] * 4, {})])
    db.commit()
    return kt, tp, other


def test_a4_xem_theo_vi_tri_va_rows_khop(db, world, client_as):
    kt, tp, other = _position_dataset(db, world)
    _, client = _actor(db, world, client_as)
    base = {"company_id": world.co["B"], "department_id": world.dept["B.hc"]}
    data = _get(client, group_by="position", **base).json()["data"]
    by = {g["label"]: g["current"] for g in data["groups"]}
    assert by["Kế toán viên"]["planned"] == 3 and by["Kế toán viên"]["actual"] == 2 and by["Kế toán viên"]["vacancies"] == 1
    assert by["Trưởng phòng"]["planned"] == 1 and by["Trưởng phòng"]["actual"] == 1 and by["Trưởng phòng"]["vacancies"] == 0
    none = by["(Chưa gắn)"]                      # người ở vị trí kế hoạch không liệt kê -> nhóm «(Chưa gắn)», tính Vượt
    assert none["planned"] == 0 and none["actual"] == 1 and none["over"] == 1
    assert data["totals"]["current"]["planned"] == 4 and data["totals"]["current"]["actual"] == 4
    assert sum(g["current"]["actual"] for g in data["groups"]) == 4
    for pos, expected in ((kt, 2), (tp, 1)):
        rows = _get(client, f"{A4}/rows", metric="actual", group_by="position", group_key=str(pos.id), **base)
        assert rows.json()["data"]["total"] == expected


def test_a4_vi_tri_phong_chua_co_ke_hoach_la_khong_ke_hoach(db, world, client_as):
    kt, _, _ = _position_dataset(db, world)
    _emp(db, world, "n1", dept="B.kt", position_id=kt.id)
    db.commit()
    _, client = _actor(db, world, client_as)
    data = _get(client, group_by="position", company_id=world.co["B"]).json()["data"]
    grp = {g["label"]: g["current"] for g in data["groups"]}
    assert grp["Kế toán viên"]["unplanned"] >= 1 and grp["Kế toán viên"]["planned"] == 3


# ---- Thực tế theo nguồn của khoản ---------------------------------------------------------------------
def test_thuc_te_theo_nguon_luong_co_ban_phu_cap_va_phan_tram_luong_dong_bhxh_co_tran():
    rows = [SimpleNamespace(base_salary=10_000_000, allowance=1_000_000, insurance_salary=20_000_000),
            SimpleNamespace(base_salary=8_000_000, allowance=500_000, insurance_salary=10_000_000)]
    metas = {"L": ItemMeta("L", "Lương", 1, Decimal(0), 0), "PC": ItemMeta("PC", "Phụ cấp", 2, Decimal(0), 0),
             "BH": ItemMeta("BH", "BHXH", 3, Decimal("17.5"), 15_000_000),
             "BHK": ItemMeta("BHK", "BHXH không trần", 3, Decimal("10"), 0),
             "AN": ItemMeta("AN", "Ăn trưa", 0, Decimal(0), 0)}
    got = actual_by_item(rows, metas)
    assert got == {"L": 18_000_000, "PC": 1_500_000,
                   "BH": round(15_000_000 * 0.175 + 10_000_000 * 0.175), "BHK": 3_000_000}      # khoản không nguồn vắng mặt


# ---- Chi tiết kế hoạch: computed.actual --------------------------------------------------------------
def _elapsed(sub_months):
    return [m for m in sub_months if m <= TODAY.month]


def _a_contracts(db, world, n=2, base=10_000_000):
    for i in range(n):
        e = Employee(code=f"AC{i}", full_name=f"Nhân sự A{i}", company_id=world.co["A"], department_id=world.dept["A.kt"],
                     is_active=True, hire_date=date(YEAR - 1, 1, 1))
        db.add(e)
        db.flush()
        db.add(LaborContract(code=f"AHD{i:04d}", employee_id=e.id, company_id=world.co["A"],
                             department_id=e.department_id, contract_type=2, status=2, start_date=date(YEAR - 1, 1, 1),
                             signed_file_id=1, base_salary=base, allowance=0, insurance_salary=0))
    db.commit()


def test_chi_tiet_co_thuc_te_ky_con_da_qua_va_tuong_lai(db, world, client_as):
    _a_contracts(db, world)
    plan = add_costed_plan(db, world, "A.kt", [2, 2, 3, 3], year=YEAR, items=[L_ITEM, AN_ITEM],
                           amounts={"L": 10_000_000, "AN": 730_000})
    client = grant_hr(world, client_as)
    actual = client.get(f"{URL}/{plan.id}").json()["data"]["computed"]["actual"]
    assert actual["covered_codes"] == ["L"] and actual["missing_codes"] == ["AN"]
    heads = [2, 2, 3, 3]
    for q in range(4):
        months = _elapsed([3 * q + 1, 3 * q + 2, 3 * q + 3])
        if not months:
            assert actual["values"][q] is None and actual["remaining"][q] is None and actual["headcount"][q] is None
            assert actual["months_counted"][q] is None
            continue
        assert actual["months_counted"][q] == len(months)
        assert actual["values"][q] == 2 * 10_000_000 * len(months)
        assert actual["planned_comparable"][q] == heads[q] * 10_000_000 * len(months)
        assert actual["remaining"][q] == actual["planned_comparable"][q] - actual["values"][q]
        assert actual["headcount"][q] >= 2


def test_chi_tiet_che_tien_thuc_te_van_tra_so_nguoi_va_ma_khoan(db, world, client_as):
    _a_contracts(db, world)
    plan = add_costed_plan(db, world, "A.kt", [2, 2, 3, 3], year=YEAR, items=[L_ITEM, AN_ITEM],
                           amounts={"L": 10_000_000, "AN": 730_000})
    blind = grant_hr(world, client_as, pay=False)
    body = blind.get(f"{URL}/{plan.id}").json()["data"]
    actual = body["computed"]["actual"]
    assert body["computed"]["money_hidden"] is True
    assert actual["values"] == [None] * 4 and actual["remaining"] == [None] * 4 and actual["planned_comparable"] == [None] * 4
    assert actual["covered_codes"] == ["L"] and actual["headcount"][0] >= 2
    assert body["files"] == [] and body["files_hidden"] is True


def test_chi_tiet_khong_khoan_nao_co_nguon_thi_khong_co_gi_de_so(db, world, client_as):
    _a_contracts(db, world)
    plan = add_costed_plan(db, world, "A.kt", [2] * 4, year=YEAR, items=[AN_ITEM], amounts={"AN": 730_000})
    actual = grant_hr(world, client_as).get(f"{URL}/{plan.id}").json()["data"]["computed"]["actual"]
    assert actual["covered_codes"] == [] and actual["values"] == [None] * 4 and actual["headcount"][0] >= 2


# ---- Tệp đính kèm: chỉ người xem được tiền ----------------------------------------------------------
def _attach(db, plan_id):
    f = StoredFile(filename="ngan-sach.xlsx", file_key="k", url="u", content_type="application/vnd.ms-excel", size=3)
    db.add(f)
    db.flush()
    link = FileLink(file_id=f.id, entity="headcount_plan", entity_id=plan_id)
    db.add(link)
    db.commit()
    return link


def test_tep_ke_hoach_chi_liet_ke_va_tai_khi_xem_duoc_tien(db, world, client_as):
    plan = add_costed_plan(db, world, "A.kt", [2] * 4, year=YEAR)
    link = _attach(db, plan.id)
    blind = grant_hr(world, client_as, pay=False)
    q = {"entity": "headcount_plan", "entity_id": plan.id}
    assert blind.get("/api/attachments", params=q).status_code == 403
    for tail in ("download", "view", "preview"):
        assert blind.get(f"/api/attachments/{link.id}/{tail}").status_code == 403
    seer = grant_hr(world, client_as, key="a2", pay=True)
    resp = seer.get("/api/attachments", params=q)
    assert resp.status_code == 200 and len(resp.json()["data"]) == 1
    assert seer.get(f"{URL}/{plan.id}").json()["data"]["files"][0]["filename"] == "ngan-sach.xlsx"


def test_tep_ke_hoach_nguoi_chi_xem_hdld_phong_cung_bi_chan(db, world, client_as):
    plan = add_costed_plan(db, world, "A.kt", [2] * 4, year=YEAR)
    _attach(db, plan.id)
    world.grant("a3", "headcount_plan", "all", actions=("read",))
    world.grant("a3", "labor_contract", "dept", actions=("read",))
    client = client_as(world.actor("a3"))
    assert client.get("/api/attachments", params={"entity": "headcount_plan", "entity_id": plan.id}).status_code == 403


# ---- Migration hcplan03: suy lại giá trị khi hạ cấp --------------------------------------------------
def test_hcplan03_suy_lai_dinh_bien_cuoi_ky_va_quy_luong_moi_thang(db, world):
    plan = add_costed_plan(db, world, "A.kt", [2, 2, 3, 3], year=YEAR, items=[L_ITEM], amounts={"L": 10_000_000})
    root = Path(__file__).resolve().parents[2]             # /app trong container, gốc repo trên máy (có thêm backend/)
    path = next(p for base in (root, root / "backend") for p in (base / "migrations/versions").glob("hcplan03_*.py"))
    spec = importlib.util.spec_from_file_location("hcplan03", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    row = SimpleNamespace(id=plan.id, year=YEAR, period_type=1, period_no=1)
    assert mod._derive(db.connection(), row) == (3, 3 * (2 + 2 + 3 + 3) * 10_000_000 // 12)


# ---- A5 có kế hoạch: số truy vấn cố định --------------------------------------------------------------
def test_a5_so_truy_van_co_dinh_khi_co_ke_hoach(db, world, client_as):
    for i in range(3):
        _hd(db, world, _emp(db, world, f"s{i}"))
    _a5_plan(db, world, "B.hc")
    client = _a5_actor(db, world, client_as)

    def call():
        assert _get(client, A5, qs=QS5, group_by="company").status_code == 200
    call()
    first = _statements(db, call)
    for i in range(10):
        _hd(db, world, _emp(db, world, f"m{i}"))
    for dept in ("B.kt", "B.hc"):
        _a5_plan(db, world, dept, year=2025)
    db.commit()
    call()                                       # commit làm hết hiệu lực đối tượng đã nạp -> khởi động lại rồi mới đo
    assert first > 0 and first == _statements(db, call)
