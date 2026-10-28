"""duoc-CR-690 (phase 22) — API kế hoạch nhân sự theo kỳ `/api/headcount-plans`.

Canh: tạo từ mẫu (chép = bản chụp, sửa mẫu không đổi kế hoạch), PUT thay nguyên, `/compute`, kỳ hẹp thay kỳ rộng,
trùng khóa kỳ, che tiền theo pháp nhân (đọc + ghi + giữ nguyên số bị che), văn bản liên kết (đọc được / không đọc
được / đã xóa), tệp đính kèm, `/position-stats`, xuất xlsx, nhập CSV dòng vị trí, xóa dọn con.
"""
from datetime import date
from io import BytesIO

import pytest
from hdld_factory import client_as  # noqa: F401
from headcount_plan_factory import URL, add_plan, basic_items, cost_item, grant_hr, plan_body
from openpyxl import load_workbook

from app.modules.attachment.model import FileLink, StoredFile
from app.modules.document.model import ORIGIN_LEGAL, Document
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.headcount_plan.cost_model import HeadcountPlanCostItem, HrCostTemplate, HrCostTemplateItem
from app.modules.headcount_plan.model import HeadcountPlan, HeadcountPlanDocument, HeadcountPlanLine
from app.modules.labor_contract.model import LaborContract


def _create(client, world, **kw):
    resp = client.post(URL, json=plan_body(world, **kw))
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


def _template(db, items):
    t = HrCostTemplate(name="Mẫu thử", note="")
    db.add(t)
    db.flush()
    for n, it in enumerate(items):
        db.add(HrCostTemplateItem(template_id=t.id, sort_order=n, rate=it.get("rate", 0), factor=it.get("factor", 0),
                                  base_codes=it.get("base_codes", []), position_ids=[], months=it.get("months", []),
                                  code=it["code"], name=it["name"], calc_method=it["calc_method"],
                                  cap_amount=it.get("cap_amount", 0), amount=it.get("amount", 0)))
    db.commit()
    return t


def test_tao_tinh_va_doc_lai_so_tu_tinh(db, world, client_as):
    client = grant_hr(world, client_as)
    data = _create(client, world)
    got = client.get(f"{URL}/{data['id']}").json()["data"]
    assert got["period_label"] == "2026" and got["basis_no"] == "12/QĐ-BGĐ" and got["department_name"] == "Phòng Kế toán"
    c = got["computed"]
    assert c["headcount"] == [2, 2, 3, 3]
    lương = next(i for i in c["items"] if i["code"] == "L")
    assert lương["values"] == [2 * 10_000_000 * 3, 2 * 10_000_000 * 3, 3 * 10_000_000 * 3, 3 * 10_000_000 * 3]
    assert next(i for i in c["items"] if i["code"] == "BH")["values"][0] == round(2 * 10_000_000 * 0.175 * 3)
    assert next(i for i in c["items"] if i["code"] == "B13")["values"] == [0, 0, 0, 3 * 10_000_000]
    assert got["lines"][0]["position_name"] == "Không theo vị trí"
    listing = client.get(URL).json()["data"]["items"][0]
    assert listing["headcount_end"] == 3 and listing["total_cost"] == c["total"]["total"]


def test_tao_tu_mau_chep_ban_chup_sua_mau_khong_doi_ke_hoach(db, world, client_as):
    tpl = _template(db, [
        {"code": "L", "name": "Lương", "calc_method": 1},
        {"code": "BH", "name": "BHXH", "calc_method": 2, "rate": 17.5, "base_codes": ["L"], "cap_amount": 46_800_000},
        {"code": "B13", "name": "Thưởng 13", "calc_method": 3, "factor": 1, "base_codes": ["L"], "months": [12]}])
    client = grant_hr(world, client_as)
    body = plan_body(world, template_id=tpl.id)
    body.pop("cost_items")
    resp = client.post(URL, json=body)
    assert resp.status_code == 201, resp.text
    plan = resp.json()["data"]
    assert [i["code"] for i in plan["cost_items"]] == ["L", "BH", "B13"] and plan["template_id"] == tpl.id
    # sửa mẫu về sau: kế hoạch đã lập GIỮ NGUYÊN
    db.query(HrCostTemplateItem).filter(HrCostTemplateItem.code == "BH").update({"rate": 99})
    db.query(HrCostTemplateItem).filter(HrCostTemplateItem.code == "B13").delete()
    db.commit()
    again = client.get(f"{URL}/{plan['id']}").json()["data"]
    assert [i["code"] for i in again["cost_items"]] == ["L", "BH", "B13"]
    assert next(i for i in again["cost_items"] if i["code"] == "BH")["rate"] == 17.5
    assert client.post(URL, json={**body, "year": 2027, "template_id": 999_999}).status_code == 422


def test_chep_mau_vao_ky_quy_bo_khoan_roi_ngoai_ky_va_khoan_tro_vao_no(db, world, client_as):
    tpl = _template(db, [
        {"code": "L", "name": "Lương", "calc_method": 1},
        {"code": "B13", "name": "Thưởng 13", "calc_method": 3, "factor": 1, "base_codes": ["L"], "months": [12]},
        {"code": "P", "name": "Phần trăm thưởng", "calc_method": 2, "rate": 10, "base_codes": ["B13"]},
        {"code": "Q83", "name": "Quà 8/3", "calc_method": 4, "amount": 500_000, "months": [3, 12]}])
    client = grant_hr(world, client_as)
    body = plan_body(world, period_type=3, period_no=1, template_id=tpl.id,
                     lines=[{"position_id": 0, "headcounts": [1, 1, 1], "amounts": {"L": 100}}])
    body.pop("cost_items")
    data = client.post(URL, json=body).json()["data"]
    assert [i["code"] for i in data["cost_items"]] == ["L", "Q83"]
    assert data["cost_items"][1]["months"] == [3]
    assert sorted(data["skipped_items"]) == ["Phần trăm thưởng", "Thưởng 13"]


def test_trung_khoa_ky_400_va_ky_hep_cung_ton_tai_voi_ky_rong(db, world, client_as):
    client = grant_hr(world, client_as)
    _create(client, world)
    assert client.post(URL, json=plan_body(world)).status_code == 400
    q3 = plan_body(world, period_type=3, period_no=3, cost_items=[cost_item("L", 1)],
                   lines=[{"position_id": 0, "headcounts": [1, 1, 1], "amounts": {"L": 5}}])
    assert client.post(URL, json=q3).status_code == 201          # kỳ hẹp lập thêm, không đè kỳ gốc
    assert client.post(URL, json=q3).status_code == 400
    assert client.post(URL, json=plan_body(world, period_type=3, period_no=5)).status_code == 422   # quý 5
    assert client.post(URL, json=plan_body(world, period_type=2, period_no=3)).status_code == 422


@pytest.mark.parametrize("patch", [
    {"year": 1999}, {"year": 2101}, {"period_type": 9}, {"company_id": 0}, {"department_id": -1}, {"note": "x" * 501},
    {"basis_no": "x" * 101}, {"basis_date": "1999-01-01"}, {"bogus": 1},
    {"lines": [{"position_id": 0, "headcounts": [-1, 0, 0, 0]}]},
    {"lines": [{"position_id": 0, "headcounts": [1, 1]}]},                       # sai số kỳ con → luật tính
    {"cost_items": [cost_item("L", 1), cost_item("L", 1)]},                       # mã trùng
    {"cost_items": [cost_item("P", 2, rate=5, base_codes=["NO"])]},               # gốc không tồn tại
    {"cost_items": [cost_item("A bc", 1)]}, {"cost_items": [cost_item("L", 7)]},
    {"cost_items": [cost_item("L", 1, cap_amount=-1)]}, {"cost_items": [cost_item("L", 1, group_id=999_999)]},
    {"cost_items": [cost_item(f"K{i}", 1) for i in range(51)]},                  # trần 50 khoản
    {"lines": [{"position_id": p + 1, "headcounts": [1] * 4} for p in range(201)]},   # trần 200 dòng
    {"document_ids": list(range(1, 22))},
])
def test_kiem_dau_vao_422(db, world, client_as, patch):
    client = grant_hr(world, client_as)
    resp = client.post(URL, json=plan_body(world, **patch))
    assert resp.status_code == 422, (patch, resp.text)
    assert db.query(HeadcountPlan).count() == 0


def test_put_thay_nguyen_va_doi_khoa_trung_400(db, world, client_as):
    client = grant_hr(world, client_as)
    a = _create(client, world)
    b = _create(client, world, year=2027)
    new = plan_body(world, note="Điều chỉnh", cost_items=[cost_item("L", 1, name="Lương mới")],
                    lines=[{"position_id": 0, "headcounts": [1, 1, 1, 1], "amounts": {"L": 7}}])
    resp = client.put(f"{URL}/{a['id']}", json=new)
    assert resp.status_code == 200, resp.text
    got = resp.json()["data"]
    assert [i["code"] for i in got["cost_items"]] == ["L"] and got["note"] == "Điều chỉnh"
    assert got["computed"]["total"]["total"] == 7 * 12
    assert client.put(f"{URL}/{b['id']}", json=plan_body(world, year=2026)).status_code == 400
    assert db.query(HeadcountPlanCostItem).filter(HeadcountPlanCostItem.plan_id == a["id"]).count() == 1
    assert client.put(f"{URL}/999999", json=new).status_code == 404


def test_compute_xem_truoc_khong_luu_va_loi_422(db, world, client_as):
    client = grant_hr(world, client_as)
    draft = {k: v for k, v in plan_body(world).items() if k not in ("basis_no", "note")}
    resp = client.post(f"{URL}/compute", json=draft)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["total"]["total"] > 0 and db.query(HeadcountPlan).count() == 0
    bad = {**draft, "cost_items": [cost_item("P", 2, rate=5, base_codes=["X"])]}
    assert client.post(f"{URL}/compute", json=bad).status_code == 422


def test_che_tien_theo_phap_nhan_o_doc_compute_va_ghi(db, world, client_as):
    admin = grant_hr(world, client_as, key="a1")
    plan = _create(admin, world)
    blind = grant_hr(world, client_as, key="a2", pay=False)
    got = blind.get(f"{URL}/{plan['id']}").json()["data"]
    assert got["can_see_money"] is False and got["computed"]["money_hidden"] is True
    assert got["computed"]["headcount"] == [2, 2, 3, 3] and got["computed"]["total"] is None
    assert all(i["cap_amount"] is None and i["amount"] is None for i in got["cost_items"])
    assert got["lines"][0]["amounts"] is None and got["lines"][0]["headcounts"] == [2, 2, 3, 3]
    item = blind.get(URL).json()["data"]["items"][0]
    assert item["total_cost"] is None and item["headcount_end"] == 3
    comp = blind.post(f"{URL}/compute", json=plan_body(world)).json()["data"]
    assert comp["total"] is None and comp["items"] == []
    assert "17500000" not in blind.get(f"{URL}/export/csv").content.decode("utf-8-sig")

    # ghi: số tiền khác 0 → 403; ô tiền bỏ trống / 0 → GIỮ NGUYÊN số thật đang bị che
    body = plan_body(world, note="Chỉ sửa ghi chú", cost_items=[
        cost_item("L", 1, name="Lương", group_id=0), cost_item("BH", 2, name="BHXH", rate=17.5, base_codes=["L"],
                                                                 cap_amount=None),
        cost_item("B13", 3, name="Thưởng 13", factor=1, base_codes=["L"], months=[12])],
        lines=[{"position_id": 0, "headcounts": [5, 5, 5, 5], "amounts": None}])
    assert blind.put(f"{URL}/{plan['id']}", json=body).status_code == 200
    saved = db.query(HeadcountPlanCostItem).filter(HeadcountPlanCostItem.plan_id == plan["id"],
                                                   HeadcountPlanCostItem.code == "BH").one()
    db.refresh(saved)
    assert saved.cap_amount == 46_800_000
    line = db.query(HeadcountPlanLine).filter(HeadcountPlanLine.plan_id == plan["id"]).one()
    db.refresh(line)
    assert line.amounts == {"L": 10_000_000} and line.headcounts == [5, 5, 5, 5]
    loud = plan_body(world)
    assert blind.put(f"{URL}/{plan['id']}", json=loud).status_code == 403
    assert blind.post(URL, json=plan_body(world, year=2030)).status_code == 403
    assert blind.post(URL, json=plan_body(world, year=2031, cost_items=[cost_item("L", 1)],
                                          lines=[{"position_id": 0, "headcounts": [1] * 4}])).status_code == 201


def test_tien_chi_hien_khi_quyen_hdld_phu_dung_phap_nhan(db, world, client_as):
    world.grant("a1", "headcount_plan", "all", actions=("read", "create", "write", "delete", "export"))
    world.grant("a1", "labor_contract", "all", actions=("read",), inc_company=("A",))
    client = client_as(world.actor("a1"))
    a = add_plan(db, world, dept="A.kt", co="A", lump=12_000_000)
    b = add_plan(db, world, dept="B.hc", co="B", lump=24_000_000)
    totals = {i["id"]: i["total_cost"] for i in client.get(URL).json()["data"]["items"]}
    assert totals == {a.id: 12_000_000, b.id: None}
    assert client.get(f"{URL}/{b.id}").json()["data"]["can_see_money"] is False
    # dời pháp nhân khi một bên không xem được tiền → 403
    move = plan_body(world, company_id=world.co["B"], cost_items=[cost_item("QL", 5, applies_to=3, amount=1)])
    assert client.put(f"{URL}/{a.id}", json=move).status_code == 403


def test_pham_vi_phong_khong_thay_ke_hoach_ngoai_pham_vi_va_tao_ngoai_pham_vi_403(db, world, client_as):
    mine = add_plan(db, world, dept="A.kt")
    other = add_plan(db, world, dept="A.mua")
    client = grant_hr(world, client_as, scope="dept", inc_dept=("A.kt",))
    assert {i["id"] for i in client.get(URL).json()["data"]["items"]} == {mine.id}
    assert client.get(f"{URL}/{other.id}").status_code == 404
    assert client.put(f"{URL}/{other.id}", json=plan_body(world)).status_code == 404
    assert client.delete(f"{URL}/{other.id}").status_code == 404
    assert client.get(f"{URL}/{other.id}/export").status_code == 404
    assert client.post(URL, json=plan_body(world, year=2031, department_id=world.dept["A.mua"])).status_code == 403
    assert db.query(HeadcountPlan).filter(HeadcountPlan.year == 2031).count() == 0


def test_thieu_quyen_hanh_dong_403(db, world, client_as):
    world.grant("a1", "headcount_plan", "all", actions=("read",))
    client = client_as(world.actor("a1"))
    assert client.get(URL).status_code == 200
    assert client.post(URL, json=plan_body(world)).status_code == 403
    assert client.put(f"{URL}/1", json=plan_body(world)).status_code == 403
    assert client.get(f"{URL}/1/export").status_code == 403
    assert client.post(f"{URL}/1/import/csv", files={"file": ("a.csv", b"x", "text/csv")}).status_code == 403
    assert client.delete(f"{URL}/1").status_code == 403


# ---- Văn bản liên kết ----------------------------------------------------------------------------
def _legal_doc(db, world, co="A", title="Quyết định duyệt ngân sách"):
    d = Document(origin=ORIGIN_LEGAL, title=title, company_id=world.co[co], doc_code=f"QD-{title[:3]}-{co}", status=1,
                 created_by=0, updated_by=0)
    db.add(d)
    db.commit()
    return d


def test_van_ban_lien_ket_chi_gan_duoc_khi_doc_duoc_va_che_voi_nguoi_khong_doc(db, world, client_as):
    world.grant("a1", "document", "company", actions=("read",))
    world.grant("a2", "document", "company", actions=("read",), inc_company=("B",))
    mine, theirs = _legal_doc(db, world, "A"), _legal_doc(db, world, "B", "Tờ trình B")
    editor = grant_hr(world, client_as, key="a1")
    resp = editor.post(URL, json=plan_body(world, document_ids=[theirs.id]))
    assert resp.status_code == 403 and db.query(HeadcountPlan).count() == 0     # không đọc được → không gắn được
    assert editor.post(URL, json=plan_body(world, document_ids=[999_999])).status_code == 403   # cùng 403 với «không đọc được»
    plan = editor.post(URL, json=plan_body(world, document_ids=[mine.id])).json()["data"]
    assert plan["documents"] == [{"document_id": mine.id, "can_read": True, "code": mine.doc_code,
                                  "title": "Quyết định duyệt ngân sách", "status": 1}]
    viewer = grant_hr(world, client_as, key="a2", pay=False)                      # không đọc được văn bản của A
    docs = viewer.get(f"{URL}/{plan['id']}").json()["data"]["documents"]
    assert docs == [{"document_id": mine.id, "can_read": False}]                  # KHÔNG lộ số hiệu / trích yếu
    # người không đọc được lưu lại kế hoạch mà vẫn gửi id cũ → liên kết được GIỮ (không phải gắn mới)
    quiet = {"cost_items": [cost_item("L", 1), cost_item("BH", 2, name="BHXH", rate=17.5, base_codes=["L"], cap_amount=None),
                            cost_item("B13", 3, name="Thưởng 13", factor=1, base_codes=["L"], months=[12])],
             "lines": [{"position_id": 0, "headcounts": [2, 2, 3, 3]}]}
    kept = viewer.put(f"{URL}/{plan['id']}", json=plan_body(world, document_ids=[mine.id], **quiet))
    assert kept.status_code == 200 and db.query(HeadcountPlanDocument).count() == 1
    # văn bản bị xóa mềm
    mine.is_deleted = True
    db.commit()
    assert editor.get(f"{URL}/{plan['id']}").json()["data"]["documents"] == [
        {"document_id": mine.id, "can_read": False, "deleted": True}]
    assert editor.put(f"{URL}/{plan['id']}", json=plan_body(world, document_ids=[])).status_code == 200
    assert db.query(HeadcountPlanDocument).count() == 0


def test_tep_dinh_kem_hien_trong_chi_tiet_va_xoa_ke_hoach_don_con(db, world, client_as):
    client = grant_hr(world, client_as)
    plan = _create(client, world, document_ids=[])
    f = StoredFile(filename="ngan-sach.xlsx", file_key="k", url="u", content_type="x", size=10)
    db.add(f)
    db.flush()
    db.add(FileLink(file_id=f.id, entity="headcount_plan", entity_id=plan["id"]))
    db.commit()
    files = client.get(f"{URL}/{plan['id']}").json()["data"]["files"]
    assert files[0]["filename"] == "ngan-sach.xlsx" and files[0]["url"] == ""
    assert client.delete(f"{URL}/{plan['id']}").status_code == 200
    for model in (HeadcountPlanCostItem, HeadcountPlanLine, HeadcountPlanDocument):
        assert db.query(model).count() == 0
    assert db.query(FileLink).filter(FileLink.entity == "headcount_plan").count() == 0


# ---- Vị trí hiện có -------------------------------------------------------------------------------
def test_position_stats_dem_nguoi_dang_lam_va_binh_quan_luong_che_theo_quyen(db, world, client_as):
    p1, p2 = JobPosition(code="KTV", name="Kế toán viên"), JobPosition(code="KTT", name="Kế toán trưởng")
    db.add_all([p1, p2])
    db.flush()
    a1, a2, none = (db.get(Employee, world.emp[k]) for k in ("a1", "a2", "khongtk"))
    a1.position_id, a2.position_id = p1.id, p1.id
    none.position_id = 0
    for e, base, allow in ((a1, 10_000_000, 1_000_000), (a2, 14_000_000, 3_000_000)):
        db.add(LaborContract(code=f"HD{e.id}", employee_id=e.id, company_id=e.company_id, department_id=e.department_id,
                             contract_type=1, status=2, start_date=date(2020, 1, 1), base_salary=base, allowance=allow))
    db.commit()
    q = {"company_id": world.co["A"], "department_id": world.dept["A.kt"]}
    rows = grant_hr(world, client_as).get(f"{URL}/position-stats", params=q).json()["data"]
    ktv = next(r for r in rows if r["position_id"] == p1.id)
    assert ktv["current_count"] == 2 and ktv["avg_base_salary"] == 12_000_000 and ktv["avg_allowance"] == 2_000_000
    assert ktv["position_name"] == "Kế toán viên"
    assert next(r for r in rows if r["position_id"] == 0)["current_count"] >= 1
    blind = grant_hr(world, client_as, key="a2", pay=False).get(f"{URL}/position-stats", params=q).json()["data"]
    ktv = next(r for r in blind if r["position_id"] == p1.id)
    assert ktv["current_count"] == 2 and ktv["avg_base_salary"] is None and ktv["avg_allowance"] is None
    old = grant_hr(world, client_as, key="a3").get(f"{URL}/position-stats", params={**q, "as_of": "2000-01-01"})
    assert old.json()["data"] == []        # chưa ai vào làm


def test_position_stats_toan_phap_nhan_dem_ca_phap_nhan(db, world, client_as):
    #  Soát giao diện CR-690: department_id = 0 («Toàn pháp nhân») từng chỉ đếm người CHƯA gắn phòng.
    client = grant_hr(world, client_as)
    whole = client.get(f"{URL}/position-stats", params={"company_id": world.co["A"], "department_id": 0}).json()["data"]
    one = client.get(f"{URL}/position-stats", params={"company_id": world.co["A"], "department_id": world.dept["A.kt"]}).json()["data"]
    total = lambda rows: sum(r["current_count"] for r in rows)
    in_company = db.query(Employee).filter(Employee.company_id == world.co["A"]).count()
    assert total(whole) > total(one) and total(whole) <= in_company


# ---- Xuất / nhập -----------------------------------------------------------------------------------
def test_xuat_xlsx_co_hai_sheet_va_nguoi_khong_thay_tien_chi_co_dinh_bien(db, world, client_as):
    plan = _create(grant_hr(world, client_as), world)
    resp = grant_hr(world, client_as).get(f"{URL}/{plan['id']}/export")
    assert resp.status_code == 200 and "spreadsheetml" in resp.headers["content-type"]
    wb = load_workbook(BytesIO(resp.content))
    assert wb.sheetnames == ["Định biên", "Bảng tính"]
    assert [c.value for c in wb["Bảng tính"][1]][0] == "Khoản"
    blind = grant_hr(world, client_as, key="a2", pay=False).get(f"{URL}/{plan['id']}/export")
    wb = load_workbook(BytesIO(blind.content))
    assert wb.sheetnames == ["Định biên"]
    assert all(10_000_000 not in [c.value for c in r] for r in wb["Định biên"].iter_rows())


def test_xuat_csv_danh_sach_header_va_chong_cong_thuc(db, world, client_as):
    client = grant_hr(world, client_as)
    _create(client, world, note="=HYPERLINK(\"x\")")
    text = client.get(f"{URL}/export/csv", params={"year": 2026}).content.decode("utf-8-sig")
    head, first = text.strip().splitlines()[:2]
    assert head.startswith("year,period_type,period_no,period_label,company_code,department_code,headcount_end,total_cost")
    assert first.startswith("2026,1,1,2026,CTY_A,A_KT,3,") and "'=HYPERLINK" in text


def _csv(rows):
    return {"file": ("v.csv", ("\n".join(rows) + "\n").encode("utf-8-sig"), "text/csv")}


def test_nhap_csv_dong_vi_tri_thay_va_them(db, world, client_as):
    p1 = JobPosition(code="KTV", name="Kế toán viên")
    db.add(p1)
    db.commit()
    client = grant_hr(world, client_as)
    plan = _create(client, world)
    rows = ["position_code,hc_1,hc_2,hc_3,hc_4,L", ",1,1,1,1,5000000", "KTV,4,4,5,5,12000000"]
    resp = client.post(f"{URL}/{plan['id']}/import/csv", files=_csv(rows))
    assert resp.status_code == 200 and resp.json()["data"] == {"created": 1, "updated": 1}, resp.text
    got = client.get(f"{URL}/{plan['id']}").json()["data"]
    by = {ln["position_id"]: ln for ln in got["lines"]}
    assert by[0]["amounts"] == {"L": 5_000_000} and by[p1.id]["headcounts"] == [4, 4, 5, 5]
    assert got["computed"]["headcount"] == [5, 5, 6, 6]


@pytest.mark.parametrize("bad_row,needle", [
    ("KHONG_CO,1,1,1,1,5", "mã chức vụ"), ("KTV,1,1,1,x,5", "không phải số nguyên"), ("KTV,1,1,1,-1,5", "Định biên"),
    ("KTV,1,1,1,1,abc", "không phải số nguyên"),
])
def test_nhap_csv_nguyen_khoi_bao_loi_theo_dong(db, world, client_as, bad_row, needle):
    db.add(JobPosition(code="KTV", name="Kế toán viên"))
    db.commit()
    client = grant_hr(world, client_as)
    plan = _create(client, world)
    rows = ["position_code,hc_1,hc_2,hc_3,hc_4,L", ",9,9,9,9,1", bad_row]
    resp = client.post(f"{URL}/{plan['id']}/import/csv", files=_csv(rows))
    msg = resp.json()["error"]["message"]
    assert resp.status_code == 422 and "Dòng 3" in msg and "Dòng 2" not in msg and needle in msg, resp.text
    assert db.query(HeadcountPlanLine).filter(HeadcountPlanLine.plan_id == plan["id"]).one().headcounts == [2, 2, 3, 3]


def test_nhap_csv_thieu_cot_trung_vi_tri_khong_utf8_va_che_tien(db, world, client_as):
    db.add(JobPosition(code="KTV", name="Kế toán viên"))
    db.commit()
    client = grant_hr(world, client_as)
    plan = _create(client, world)
    url = f"{URL}/{plan['id']}/import/csv"
    assert client.post(url, files=_csv(["position_code,hc_1", "KTV,1"])).status_code == 400
    assert client.post(url, files={"file": ("v.csv", b"\xff\xfe\x00", "text/csv")}).status_code == 400
    dup = ["position_code,hc_1,hc_2,hc_3,hc_4", "KTV,1,1,1,1", "KTV,2,2,2,2"]
    assert client.post(url, files=_csv(dup)).status_code == 422
    blind = grant_hr(world, client_as, key="a2", pay=False)
    assert blind.post(url, files=_csv(["position_code,hc_1,hc_2,hc_3,hc_4,L", "KTV,1,1,1,1,100"])).status_code == 422
    ok = blind.post(url, files=_csv(["position_code,hc_1,hc_2,hc_3,hc_4", "KTV,1,1,1,1"]))
    assert ok.status_code == 200, ok.text
    line = db.query(HeadcountPlanLine).filter(HeadcountPlanLine.plan_id == plan["id"], HeadcountPlanLine.position_id == 0).one()
    assert line.amounts == {"L": 10_000_000}


def test_nhap_csv_ngoai_pham_vi_404(db, world, client_as):
    other = add_plan(db, world, dept="A.mua")
    client = grant_hr(world, client_as, scope="dept", inc_dept=("A.kt",))
    resp = client.post(f"{URL}/{other.id}/import/csv", files=_csv(["position_code,hc_1,hc_2,hc_3,hc_4", ",1,1,1,1"]))
    assert resp.status_code == 404
