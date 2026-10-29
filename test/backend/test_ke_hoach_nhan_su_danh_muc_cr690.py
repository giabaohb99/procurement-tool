"""duoc-CR-690 (phase 22) — nhóm chi phí, mẫu khoản chi phí và dời / gieo dữ liệu của migration `hcplan02`.

Canh: CRUD nhóm + mẫu (tên duy nhất, đọc/ghi theo khóa `headcount_plan`), kiểm cấu trúc khoản của mẫu, sao chép mẫu,
xóa nhóm đang dùng bị chặn, trần độ dài ở schema, hàm dời dữ liệu đợt 4 (idempotent) và gieo mẫu gợi ý dùng được thật.
"""
import pytest
from hdld_factory import client_as  # noqa: F401
from headcount_plan_factory import URL, add_plan, cost_item, grant_hr, plan_body
from pydantic import ValidationError

from app.modules.headcount_plan import legacy_seed
from app.modules.headcount_plan.cost_model import (HeadcountPlanCostItem, HrCostGroup, HrCostTemplate,
                                                   HrCostTemplateItem)
from app.modules.headcount_plan.model import HeadcountPlan, HeadcountPlanLine
from app.modules.headcount_plan.schema import CostGroupIn, CostItemIn, CostTemplateIn, PlanLineIn

GROUPS, TEMPLATES = "/api/hr-cost-groups", "/api/hr-cost-templates"


def test_nhom_chi_phi_crud_ten_duy_nhat_va_quyen(db, world, client_as):
    client = grant_hr(world, client_as, pay=False)
    g = client.post(GROUPS, json={"name": "Quỹ lương", "sort_order": 10})
    assert g.status_code == 201, g.text
    gid = g.json()["data"]["id"]
    assert client.post(GROUPS, json={"name": "Quỹ lương"}).status_code == 400
    other = client.post(GROUPS, json={"name": "Phúc lợi", "sort_order": 5}).json()["data"]["id"]
    assert client.patch(f"{GROUPS}/{other}", json={"name": "Quỹ lương"}).status_code == 400
    assert client.patch(f"{GROUPS}/{other}", json={"name": None}).status_code == 422
    assert client.patch(f"{GROUPS}/{other}", json={"is_active": False}).json()["data"]["is_active"] is False
    items = client.get(GROUPS).json()["data"]["items"]
    assert [i["name"] for i in items] == ["Phúc lợi", "Quỹ lương"]           # theo sort_order
    assert [i["id"] for i in client.get(GROUPS, params={"is_active": True}).json()["data"]["items"]] == [gid]
    assert client.delete(f"{GROUPS}/{other}").status_code == 200
    assert client.get(f"{GROUPS}/{other}").status_code == 404
    reader = None
    world.grant("a2", "headcount_plan", "all", actions=("read",))
    reader = client_as(world.actor("a2"))
    assert reader.get(GROUPS).status_code == 200
    assert reader.post(GROUPS, json={"name": "X"}).status_code == 403
    assert reader.delete(f"{GROUPS}/{gid}").status_code == 403
    assert reader.post(TEMPLATES, json={"name": "T"}).status_code == 403


def test_xoa_nhom_dang_duoc_mau_hoac_ke_hoach_dung_bi_chan(db, world, client_as):
    client = grant_hr(world, client_as)
    gid = client.post(GROUPS, json={"name": "Quỹ lương"}).json()["data"]["id"]
    tpl = client.post(TEMPLATES, json={"name": "M", "items": [cost_item("L", 1, group_id=gid)]})
    assert tpl.status_code == 201, tpl.text
    assert client.delete(f"{GROUPS}/{gid}").status_code == 400
    client.delete(f"{TEMPLATES}/{tpl.json()['data']['id']}")
    assert client.post(f"{URL}", json=plan_body(world, cost_items=[cost_item("L", 1, group_id=gid)])).status_code == 201
    assert client.delete(f"{GROUPS}/{gid}").status_code == 400
    assert db.get(HrCostGroup, gid) is not None


def test_mau_crud_thay_nguyen_danh_sach_khoan_va_sao_chep(db, world, client_as):
    client = grant_hr(world, client_as)
    items = [cost_item("L", 1, name="Lương", sort_order=1),
             cost_item("BH", 2, name="BHXH", rate=17.5, base_codes=["L"], cap_amount=46_800_000, sort_order=2)]
    t = client.post(TEMPLATES, json={"name": "Mẫu văn phòng", "note": "ghi chú", "items": items})
    assert t.status_code == 201, t.text
    tid = t.json()["data"]["id"]
    got = client.get(f"{TEMPLATES}/{tid}").json()["data"]
    assert [i["code"] for i in got["items"]] == ["L", "BH"] and got["items"][1]["cap_amount"] == 46_800_000
    assert client.post(TEMPLATES, json={"name": "Mẫu văn phòng"}).status_code == 400
    patched = client.patch(f"{TEMPLATES}/{tid}", json={"items": [cost_item("X", 1, name="Khoản X")]}).json()["data"]
    assert [i["code"] for i in patched["items"]] == ["X"]
    assert client.patch(f"{TEMPLATES}/{tid}", json={"note": "mới"}).json()["data"]["items"][0]["code"] == "X"   # không gửi items = giữ
    c1 = client.post(f"{TEMPLATES}/{tid}/duplicate").json()["data"]
    c2 = client.post(f"{TEMPLATES}/{tid}/duplicate").json()["data"]
    assert c1["name"] == "Mẫu văn phòng (bản sao)" and c2["name"] == "Mẫu văn phòng (bản sao) 2"
    assert [i["code"] for i in c1["items"]] == ["X"] and c1["id"] != tid
    listing = client.get(TEMPLATES).json()["data"]
    assert listing["total"] == 3 and all("items" not in i and i["item_count"] == 1 for i in listing["items"])
    assert client.delete(f"{TEMPLATES}/{tid}").status_code == 200
    assert db.query(HrCostTemplateItem).filter(HrCostTemplateItem.template_id == tid).count() == 0
    assert client.get(f"{TEMPLATES}/{tid}").status_code == 404 and client.post(f"{TEMPLATES}/{tid}/duplicate").status_code == 404


@pytest.mark.parametrize("items", [
    [cost_item("L", 1), cost_item("L", 1)],                                              # mã trùng
    [cost_item("P", 2, rate=5, base_codes=["NO"])],                                      # gốc không tồn tại
    [cost_item("L", 1), cost_item("P", 2, rate=5, base_codes=["L"]), cost_item("Q", 2, rate=1, base_codes=["P"])],
    [cost_item("L", 1), cost_item("B", 3, factor=1, base_codes=["L"])],                  # số tháng thiếu tháng rơi
    [cost_item("A", 4, amount=1, applies_to=3)],                                         # cả phòng sai cách tính
    [cost_item("L", 1, group_id=999_999)],                                               # nhóm không tồn tại
])
def test_mau_kiem_cau_truc_khoan_422(db, world, client_as, items):
    client = grant_hr(world, client_as)
    assert client.post(TEMPLATES, json={"name": "Hỏng", "items": items}).status_code == 422
    assert db.query(HrCostTemplate).count() == 0


def test_schema_chan_chuoi_dai_so_am_va_danh_sach_qua_tran():
    with pytest.raises(ValidationError):
        CostGroupIn(name="x" * 101)
    with pytest.raises(ValidationError):
        CostTemplateIn(name="x" * 151)
    with pytest.raises(ValidationError):
        CostTemplateIn(name="a", note="x" * 501)
    with pytest.raises(ValidationError):
        CostItemIn(code="x" * 31, name="a", calc_method=1)
    with pytest.raises(ValidationError):
        CostItemIn(code="a", name="x" * 151, calc_method=1)
    with pytest.raises(ValidationError):
        CostItemIn(code="a", name="a", calc_method=6)
    with pytest.raises(ValidationError):
        CostItemIn(code="a", name="a", calc_method=1, months=[13])
    with pytest.raises(ValidationError):
        CostItemIn(code="a", name="a", calc_method=1, rate=1000)
    with pytest.raises(ValidationError):
        PlanLineIn(headcounts=[1] * 5)
    with pytest.raises(ValidationError):
        PlanLineIn(headcounts=[1], note="x" * 501)
    with pytest.raises(ValidationError):
        PlanLineIn(headcounts=[1], amounts={"L": 10**13 + 1})
    assert CostItemIn(code="a_1", name="x" * 150, calc_method=5, rate=999.9999, factor=9999.99).calc_method == 5


# ---- Dời dữ liệu đợt 4 và gieo gợi ý (hàm dùng trong migration hcplan02) ------------------------------
def _set_legacy(db, plan_id: int, headcount: int, payroll: int) -> None:
    """Hai cột đợt 4 đã DROP khỏi model (hcplan03) nhưng migration hcplan02 còn đọc chúng: dựng lại trên bảng thử
    (SQLite) rồi ghi giá trị cũ, đúng như DB thật ở thời điểm hcplan02 chạy."""
    from sqlalchemy import text

    have = {r[1] for r in db.execute(text("PRAGMA table_info(tab_headcount_plan)"))}
    for col in ("planned_headcount", "planned_payroll_monthly"):
        if col not in have:
            db.execute(text(f"ALTER TABLE tab_headcount_plan ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0"))
    db.execute(text("UPDATE tab_headcount_plan SET planned_headcount = :h, planned_payroll_monthly = :p WHERE id = :i"),
               {"h": headcount, "p": payroll, "i": plan_id})
    db.commit()


def test_doi_du_lieu_dot_4_thanh_ke_hoach_nam_khoan_quy_luong_tong(db, world):
    old = HeadcountPlan(year=2026, company_id=world.co["A"], department_id=world.dept["A.kt"], note="cũ")
    zero = HeadcountPlan(year=2026, company_id=world.co["A"], department_id=0, note="")
    db.add_all([old, zero])
    db.commit()
    _set_legacy(db, old.id, 7, 50_000_000)
    conn = db.connection()
    legacy_seed.seed_suggestions(conn)
    assert legacy_seed.move_legacy_rows(conn) == 2
    assert legacy_seed.move_legacy_rows(conn) == 0                        # idempotent
    db.expire_all()
    line = db.query(HeadcountPlanLine).filter(HeadcountPlanLine.plan_id == old.id).one()
    assert line.position_id == 0 and line.headcounts == [7, 7, 7, 7]
    item = db.query(HeadcountPlanCostItem).filter(HeadcountPlanCostItem.plan_id == old.id).one()
    assert (item.code, item.calc_method, item.amount, item.applies_to) == ("QUY_LUONG", 5, 600_000_000, 3)
    assert item.name == "Quỹ lương (nhập tổng)" and item.group_id == db.query(HrCostGroup).filter(
        HrCostGroup.name == "Quỹ lương").one().id
    assert (old.period_type, old.period_no) == (1, 1)


def test_doi_du_lieu_cu_tinh_ra_dung_so_cu(db, world, client_as):
    row = add_plan(db, world, dept="A.kt", n=10)
    db.query(HeadcountPlanLine).delete()
    db.query(HeadcountPlanCostItem).delete()
    db.commit()
    _set_legacy(db, row.id, 10, 80_000_000)
    legacy_seed.move_legacy_rows(db.connection())
    db.expire_all()
    got = grant_hr(world, client_as).get(f"{URL}/{row.id}").json()["data"]
    assert got["computed"]["total"]["total"] == 12 * 80_000_000 and got["computed"]["headcount"] == [10] * 4


def test_gieo_goi_y_chi_khi_bang_rong_va_mau_goi_y_dung_duoc(db, world, client_as):
    conn = db.connection()
    legacy_seed.seed_suggestions(conn)
    legacy_seed.seed_suggestions(conn)                                    # chạy lại không nhân đôi
    db.expire_all()
    assert [g.name for g in db.query(HrCostGroup).order_by(HrCostGroup.sort_order)] == [
        "Quỹ lương", "Bắt buộc theo luật", "Phúc lợi", "Khác"]
    tpl = db.query(HrCostTemplate).one()
    items = {i.code: i for i in db.query(HrCostTemplateItem).filter(HrCostTemplateItem.template_id == tpl.id)}
    assert set(items) == {"LUONG", "PHU_CAP", "BAO_HIEM", "THUONG_13"}        # bộ gọn (28/10/2026)
    bh = items["BAO_HIEM"]
    assert bh.calc_method == 2 and float(bh.rate) == 23.5 and bh.cap_amount == 50_600_000
    assert bh.base_codes == ["LUONG", "PHU_CAP"] and items["THUONG_13"].months == [12]
    # mẫu gợi ý lập được kế hoạch thật và tính ra số hợp lý
    client = grant_hr(world, client_as)
    body = plan_body(world, template_id=tpl.id, lines=[{"position_id": 0, "headcounts": [1] * 4,
                                                        "amounts": {"LUONG": 10_000_000, "PHU_CAP": 2_000_000}}])
    body.pop("cost_items")
    got = client.post(URL, json=body).json()["data"]
    by = {i["code"]: i["total"] for i in got["computed"]["items"]}
    assert by["LUONG"] == 120_000_000 and by["THUONG_13"] == 10_000_000
    assert by["BAO_HIEM"] == round(12_000_000 * 0.235 * 12)
    # xóa hết nhóm / mẫu rồi gieo lại: bảng RỖNG thì gieo lại (người dùng chủ động xóa hết)
    db.query(HrCostTemplateItem).delete()
    db.query(HrCostTemplate).delete()
    db.query(HrCostGroup).delete()
    db.commit()
    legacy_seed.seed_suggestions(db.connection())
    db.expire_all()
    assert db.query(HrCostTemplate).count() == 1


def test_thu_gon_mau_goi_y_ban_dau_chi_khi_con_nguyen_bo_8_khoan(db):
    conn = db.connection()
    legacy_seed.seed_suggestions(conn)
    tpl = db.query(HrCostTemplate).one()
    db.query(HrCostTemplateItem).delete()
    for i, code in enumerate(sorted(legacy_seed._FIRST_SUGGESTED_CODES)):
        db.add(HrCostTemplateItem(template_id=tpl.id, code=code, name=code, calc_method=1, sort_order=i))
    db.flush()
    assert legacy_seed.simplify_suggested_template(db.connection()) is True
    db.expire_all()
    codes = {i.code for i in db.query(HrCostTemplateItem).filter(HrCostTemplateItem.template_id == tpl.id)}
    assert codes == {"LUONG", "PHU_CAP", "BAO_HIEM", "THUONG_13"}
    # người dùng đã sửa bộ khoản (khác bộ 8 mã) → không đụng
    assert legacy_seed.simplify_suggested_template(db.connection()) is False

