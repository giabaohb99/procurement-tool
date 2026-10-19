"""duoc-CR-630 phase 02 — API Danh sách biến mẫu HĐLĐ: quyền (ghi đòi phạm vi «tất cả»), tạo/sửa/xóa,
khóa mã khi đã dùng, chặn xóa kèm danh sách mẫu trong phạm vi, `/placeholders` và `/input-fields`."""
from datetime import date

import pytest
from pydantic import ValidationError

from app.modules.labor_contract.model import LaborContract
from app.modules.labor_contract.template_model import LaborContractTemplate
from app.modules.labor_contract.variable_model import LaborContractVariable
from app.modules.labor_contract.variable_schema import VariableCreate, VariableUpdate
from app.modules.labor_contract.variable_seed import ensure_system_variables
from hdld_factory import client_as, grant_all, storage  # noqa: F401

URL = "/api/labor-contract-variables"


def body(**over):
    data = {"code": "so_ngay_phep", "label": "Số ngày phép", "value_type": 3}
    data.update(over)
    return data


@pytest.fixture
def setup(db, world, client_as):  # noqa: F811
    """a1 = HR toàn hệ thống (scope all) · b1 = HR chỉ công ty B · a2 chỉ đọc mẫu · a3 chỉ lập HĐ."""
    ensure_system_variables(db)
    db.commit()
    grant_all(world, "a1", scope="all", contract=False)
    grant_all(world, "b1", scope="company", contract=False)
    world.actor("a2").grant("labor_contract_template", "company", actions=("read",))
    world.actor("a3").grant("labor_contract", "company", actions=("create",))
    return world, client_as(world.actor("a1")), client_as


def _template(db, company_id, name, placeholders):
    row = LaborContractTemplate(company_id=company_id, contract_type=2, name=name, placeholders=placeholders)
    db.add(row)
    db.commit()
    return row


# ── Quyền ──────────────────────────────────────────────────────────────────────────
def test_quyen_doc_va_ghi(setup, db):
    world, admin, make = setup
    created = admin.post(URL, json=body()).json()["data"]
    vid = created["id"]
    a2, a3, b1 = (make(world.actor(k)) for k in ("a2", "a3", "b1"))
    assert a2.get(URL).status_code == 200 and a2.get(f"{URL}/{vid}").status_code == 200
    assert a3.get(URL).status_code == 403 and a3.get(f"{URL}/input-fields").status_code == 200
    assert a2.get(f"{URL}/input-fields").status_code == 200
    assert make(world.actor("khongphong")).get(f"{URL}/input-fields").status_code == 403
    assert a2.post(URL, json=body(code="khac_nua")).status_code == 403          # có read, thiếu write
    assert a2.delete(f"{URL}/{vid}").status_code == 403
    grant_all(world, "a3", scope="all", contract=False, actions=("read", "write"))
    assert make(world.actor("a3")).delete(f"{URL}/{vid}").status_code == 403    # write mà DELETE


def test_phap_nhan_don_le_chi_doc_khong_ghi(setup, db):
    world, admin, make = setup
    vid = admin.post(URL, json=body()).json()["data"]["id"]
    sys_id = db.query(LaborContractVariable).filter_by(code="ho_ten").one().id
    b1 = make(world.actor("b1"))
    listing = b1.get(URL).json()["data"]
    assert listing["can_manage"] is False and listing["can_delete"] is False
    assert admin.get(URL).json()["data"]["can_manage"] is True
    assert b1.post(URL, json=body(code="khac_nua")).status_code == 403
    assert b1.patch(f"{URL}/{vid}", json={"label": "Sửa"}).status_code == 403
    assert b1.patch(f"{URL}/{sys_id}", json={"label": "Sửa"}).status_code == 403   # nhãn biến hệ thống cũng vậy
    assert b1.delete(f"{URL}/{vid}").status_code == 403
    assert b1.get(f"{URL}/input-fields").status_code == 200                          # vẫn dùng được


def test_pham_vi_all_nhung_bi_gioi_han_cong_ty_rieng_cung_khong_duoc_ghi(db, world, client_as):  # noqa: F811
    grant_all(world, "a1", scope="all", contract=False, inc_company=["A"])
    assert client_as(world.actor("a1")).post(URL, json=body()).status_code == 403


# ── Tạo ────────────────────────────────────────────────────────────────────────────
def test_tao_hop_le_va_truong_tra_ve(setup):
    _, admin, _ = setup
    res = admin.post(URL, json=body(description="Phép năm", example="12", default_value="12", is_required=True,
                                    sort_order=5))
    assert res.status_code == 201, res.text
    item = res.json()["data"]
    assert (item["source"], item["value_type"], item["default_value"], item["is_required"]) == (2, 3, "12", True)
    assert item["group"] == "Biến tùy chỉnh" and item["is_active"] is True and item["created_by_name"]


@pytest.mark.parametrize("code", ["ho_ten", "Ho_Ten", "1abc", "a" * 41, "range", "luong_bang_chu"])
def test_tao_ma_sai_422(setup, code):
    assert setup[1].post(URL, json=body(code=code)).status_code == 422


def test_tao_trung_ma_400_va_vuot_tran_422(setup, db):
    _, admin, _ = setup
    assert admin.post(URL, json=body()).status_code == 201
    dup = admin.post(URL, json=body())
    assert dup.status_code == 400 and "đã tồn tại" in dup.json()["error"]["message"]
    for i in range(99):
        db.add(LaborContractVariable(code=f"bien_{i:03d}", source=2, value_type=1, label="x"))
    db.commit()
    full = admin.post(URL, json=body(code="bien_them"))
    assert full.status_code == 422 and "100" in full.json()["error"]["message"]


@pytest.mark.parametrize("bad", [
    {"label": "x" * 201}, {"description": "x" * 501}, {"example": "x" * 256}, {"default_value": "x" * 2001},
    {"label": "  "}, {"value_type": 9}, {"sort_order": 10000}, {"sort_order": -1}, {"code": "Ab"},
    {"tuy_y_la": 1}, {"value_type": 5, "default_value": "abc"}, {"value_type": 4, "default_value": "32/13"}])
def test_schema_chan_truoc_khi_xuong_db(bad):
    with pytest.raises(ValidationError):
        VariableCreate(**{**body(), **bad})


def test_tao_chuan_hoa_mac_dinh_theo_kieu(setup):
    _, admin, _ = setup
    ok = admin.post(URL, json=body(code="he_so", default_value="1,5")).json()["data"]
    assert ok["default_value"] == "1.5"
    assert admin.post(URL, json=body(code="thuong", value_type=5, default_value="abc")).status_code == 422
    assert admin.post(URL, json=body(code="ngay_x", value_type=4, default_value="32/13")).status_code == 422


# ── Biến hệ thống ───────────────────────────────────────────────────────────────────
def test_bien_he_thong_chi_sua_nhan_mo_ta_an(setup, db):
    _, admin, _ = setup
    sid = db.query(LaborContractVariable).filter_by(code="ho_ten").one().id
    ok = admin.patch(f"{URL}/{sid}", json={"label": "Tên NLĐ", "description": "Mô tả", "is_hidden": True})
    assert ok.status_code == 200 and ok.json()["data"]["label"] == "Tên NLĐ" and ok.json()["data"]["is_hidden"]
    for field, value in (("code", "x_y"), ("value_type", 3), ("is_active", False), ("default_value", "1"),
                         ("is_required", True), ("example", "x")):
        res = admin.patch(f"{URL}/{sid}", json={field: value})
        assert res.status_code == 422 and field in res.json()["error"]["message"], field
    res = admin.delete(f"{URL}/{sid}")
    assert res.status_code == 409 and "không xóa" in res.json()["error"]["message"]


def test_dong_he_thong_co_ma_khong_con_trong_code_bi_giau(setup, db):
    _, admin, _ = setup
    ghost = LaborContractVariable(code="bien_da_bo", source=1, value_type=1, label="Cũ")
    db.add(ghost)
    db.commit()
    assert admin.get(f"{URL}/{ghost.id}").status_code == 404
    assert "bien_da_bo" not in {i["code"] for i in admin.get(f"{URL}?source=1&page_size=200").json()["data"]["items"]}


def test_danh_sach_loc_va_sap_xep(setup):
    _, admin, _ = setup
    admin.post(URL, json=body(code="bb_phep", label="Phép B", sort_order=2))
    admin.post(URL, json=body(code="aa_phep", label="Phép A", sort_order=1, is_active=False))
    data = admin.get(f"{URL}?source=2").json()["data"]
    assert [i["code"] for i in data["items"]] == ["aa_phep", "bb_phep"] and data["total"] == 2
    assert [i["code"] for i in admin.get(f"{URL}?source=2&is_active=true").json()["data"]["items"]] == ["bb_phep"]
    assert admin.get(f"{URL}?q=ho_ten").json()["data"]["total"] >= 1
    assert admin.get(f"{URL}?q=Phép B").json()["data"]["total"] == 1
    assert admin.get(f"{URL}?source=1").json()["data"]["total"] > 40


# ── Khóa mã / kiểu / xóa khi đang dùng ──────────────────────────────────────────────
def test_dang_dung_trong_mau_khoa_ma_kieu_va_xoa(setup, db):
    world, admin, make = setup
    vid = admin.post(URL, json=body()).json()["data"]["id"]
    _template(db, world.co["A"], "Mẫu A", ["so_ngay_phep", "ho_ten"])
    _template(db, world.co["B"], "Mẫu B", ["so_ngay_phep"])
    detail = admin.get(f"{URL}/{vid}").json()["data"]
    assert detail["code_locked"] is True and detail["usage"]["template_count"] == 2
    assert admin.patch(f"{URL}/{vid}", json={"code": "ma_moi"}).status_code == 409
    assert admin.patch(f"{URL}/{vid}", json={"value_type": 1}).status_code == 409
    assert admin.patch(f"{URL}/{vid}", json={"code": "so_ngay_phep", "label": "Nhãn mới"}).status_code == 200
    res = admin.delete(f"{URL}/{vid}")
    assert res.status_code == 409
    err = res.json()["error"]
    assert "2 mẫu" in err["message"] and "Ngừng dùng" in err["message"]
    assert {t["name"] for t in err["details"]["templates"]} == {"Mẫu A", "Mẫu B"}   # scope all: thấy đủ


def test_409_chi_liet_ke_mau_trong_pham_vi_va_dem_phan_con_lai(setup, db):
    world, admin, make = setup
    vid = admin.post(URL, json=body()).json()["data"]["id"]
    _template(db, world.co["A"], "Mẫu A", ["so_ngay_phep"])
    _template(db, world.co["B"], "Mẫu B", ["so_ngay_phep"])
    grant_all(world, "a2", scope="all", contract=False, actions=("read", "write", "delete"))
    # a3: quyền ghi/xóa toàn hệ thống nhưng chỉ ĐỌC được mẫu công ty A → không lộ tên mẫu B
    world.actor("a3").grant("labor_contract_template", "all", actions=("write", "delete"))
    world.actor("a3").grant("labor_contract_template", "company", actions=("read",), inc_company=["A"])
    a3 = make(world.actor("a3"))
    res = a3.delete(f"{URL}/{vid}")
    assert res.status_code == 403 or res.status_code == 409
    if res.status_code == 409:
        details = res.json()["error"]["details"]
        assert [t["name"] for t in details["templates"]] == ["Mẫu A"] and details["hidden_template_count"] == 1
        assert "Mẫu B" not in res.text


def test_bien_tien_dung_qua_bang_chu_van_tinh_dang_dung(setup, db):
    world, admin, _ = setup
    vid = admin.post(URL, json=body(code="thuong", value_type=5)).json()["data"]["id"]
    _template(db, world.co["A"], "Mẫu A", ["thuong_bang_chu"])
    assert admin.delete(f"{URL}/{vid}").status_code == 409
    assert admin.patch(f"{URL}/{vid}", json={"code": "thuong_2"}).status_code == 409


def test_co_hop_dong_ke_ca_xoa_mem_giu_gia_tri_thi_khoa(setup, db):
    _, admin, _ = setup
    vid = admin.post(URL, json=body()).json()["data"]["id"]
    db.add(LaborContract(code="HDLD001", employee_id=1, company_id=1, contract_type=2,
                         start_date=date(2026, 1, 1), custom_values={"so_ngay_phep": "12"}, is_deleted=True))
    db.commit()
    assert admin.patch(f"{URL}/{vid}", json={"code": "ma_moi"}).status_code == 409
    res = admin.delete(f"{URL}/{vid}")
    assert res.status_code == 409 and "1 hợp đồng" in res.json()["error"]["message"]
    assert res.json()["error"]["details"]["contract_count"] == 1


def test_khong_ai_dung_thi_xoa_va_doi_ma_duoc(setup, db):
    _, admin, _ = setup
    vid = admin.post(URL, json=body()).json()["data"]["id"]
    assert admin.patch(f"{URL}/{vid}", json={"code": "ma_moi", "value_type": 1}).json()["data"]["code"] == "ma_moi"
    assert admin.patch(f"{URL}/{vid}", json={"code": "ho_ten"}).status_code == 422
    other = admin.post(URL, json=body(code="khac_nua")).json()["data"]
    assert admin.patch(f"{URL}/{vid}", json={"code": "khac_nua"}).status_code == 400
    assert admin.delete(f"{URL}/{vid}").status_code == 200
    assert admin.get(f"{URL}/{vid}").status_code == 404 and other["id"] != vid


def test_doi_kieu_chuan_hoa_lai_mac_dinh(setup):
    _, admin, _ = setup
    vid = admin.post(URL, json=body(value_type=1, default_value="abc")).json()["data"]["id"]
    assert admin.patch(f"{URL}/{vid}", json={"value_type": 3}).status_code == 422       # «abc» không phải số
    assert admin.patch(f"{URL}/{vid}", json={"value_type": 3, "default_value": "2,5"}).json()["data"][
        "default_value"] == "2.5"


def test_bien_tuy_chinh_khong_an_duoc(setup):
    _, admin, _ = setup
    vid = admin.post(URL, json=body()).json()["data"]["id"]
    assert admin.patch(f"{URL}/{vid}", json={"is_hidden": True}).status_code == 422


def test_update_schema_chan_truong_la_va_do_dai():
    with pytest.raises(ValidationError):
        VariableUpdate(label="x" * 201)
    with pytest.raises(ValidationError):
        VariableUpdate(gia_tri=1)


# ── Ngừng dùng, /placeholders, /input-fields ───────────────────────────────────────
def test_ngung_dung_roi_khoi_input_fields_va_placeholders_nhung_con_trong_list(setup):
    _, admin, _ = setup
    vid = admin.post(URL, json=body(code="thuong", value_type=5, label="Thưởng")).json()["data"]["id"]
    keys = lambda r: {x["key"] for x in r.json()["data"]}                         # noqa: E731
    assert {"thuong", "thuong_bang_chu"} <= keys(admin.get("/api/labor-contract-templates/placeholders"))
    assert admin.patch(f"{URL}/{vid}", json={"is_active": False}).json()["data"]["is_active"] is False
    assert not ({"thuong", "thuong_bang_chu"} & keys(admin.get("/api/labor-contract-templates/placeholders")))
    assert "thuong" not in {x["code"] for x in admin.get(f"{URL}/input-fields").json()["data"]}
    inactive = admin.get(f"{URL}/input-fields?include_inactive=true").json()["data"]
    assert [(x["code"], x["is_active"]) for x in inactive] == [("thuong", False)]
    assert "thuong" in {i["code"] for i in admin.get(f"{URL}?source=2").json()["data"]["items"]}


def test_placeholders_an_nhan_moi_va_bang_chu(setup, db):
    _, admin, _ = setup
    sid = db.query(LaborContractVariable).filter_by(code="ho_ten").one().id
    hid = db.query(LaborContractVariable).filter_by(code="email").one().id
    admin.patch(f"{URL}/{sid}", json={"label": "Tên người lao động", "description": "Họ tên đầy đủ"})
    admin.patch(f"{URL}/{hid}", json={"is_hidden": True})
    admin.post(URL, json=body(code="thuong", value_type=5, label="Thưởng", example="1.000.000"))
    rows = {r["key"]: r for r in admin.get("/api/labor-contract-templates/placeholders").json()["data"]}
    assert rows["ho_ten"]["label"] == "Tên người lao động" and rows["ho_ten"]["description"] == "Họ tên đầy đủ"
    assert rows["ho_ten"]["group"] == "Người lao động" and rows["ho_ten"]["example"] == "Nguyễn Văn An"
    assert "email" not in rows
    assert rows["thuong"]["group"] == "Biến tùy chỉnh" and rows["thuong"]["example"] == "1.000.000"
    assert rows["thuong_bang_chu"]["label"] == "Thưởng (bằng chữ)"
    assert {"key", "label", "group", "example", "description"} == set(rows["ho_ten"])


def test_placeholders_van_du_khi_chua_seed(db, world, client_as):  # noqa: F811
    grant_all(world, "a1", scope="all", contract=False)
    rows = client_as(world.actor("a1")).get("/api/labor-contract-templates/placeholders").json()["data"]
    assert any(r["key"] == "ho_ten" for r in rows)


def test_nhat_ky_ghi_theo_thao_tac(setup, db):
    from app.modules.audit.model import AuditLog

    _, admin, _ = setup
    vid = admin.post(URL, json=body()).json()["data"]["id"]
    admin.patch(f"{URL}/{vid}", json={"label": "Sửa"})
    admin.delete(f"{URL}/{vid}")
    actions = [a.action for a in db.query(AuditLog).filter(AuditLog.entity == "labor_contract_variable").order_by(AuditLog.id)]
    assert actions == ["create", "update", "delete"]
