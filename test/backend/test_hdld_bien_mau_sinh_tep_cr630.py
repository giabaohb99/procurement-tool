"""duoc-CR-630 phase 03 — tích hợp: tải/thay/soạn mẫu theo danh mục động, giá trị biến theo hợp đồng,
sinh tệp (định dạng, bắt buộc, lưới an toàn), chặn «Đã ký» khi thiếu biến bắt buộc, che nhật ký."""
import json
import zipfile
from io import BytesIO

import pytest

from app.core.change_tracker import _is_allowed
from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.logging_policy import MASKED, mask_payload, sensitive_keys_for_path
from app.modules.labor_contract import document_archive_sync as sync
from app.modules.labor_contract.model import LaborContract
from app.modules.labor_contract.template_model import LaborContractTemplate
from app.modules.labor_contract.variable_model import LaborContractVariable
from hdld_factory import (DOCX_MIME, client_as, docx_text, grant_all, make_contract, make_docx,  # noqa: F401
                          storage, upload_template)

CT, TPL = "/api/labor-contracts", "/api/labor-contract-templates"
TEXT, MULTI, NUMBER, DATE, MONEY = 1, 2, 3, 4, 5


def add_var(db, code, vtype=TEXT, **kw):
    row = LaborContractVariable(code=code, source=2, value_type=vtype, label=kw.pop("label", code.upper()), **kw)
    db.add(row)
    db.commit()
    return row


@pytest.fixture
def setup(db, world, storage, client_as):  # noqa: F811
    grant_all(world, "a1")
    return world, client_as(world.actor("a1")), storage


def tpl_with(a1, world, *paragraphs, name="Mẫu biến"):
    res = upload_template(a1, company_id=world.co["A"], name=name, data=make_docx(*paragraphs))
    assert res.status_code == 201, res.text
    return res.json()["data"]["id"]


def gen(a1, cid, tid):
    return a1.post(f"{CT}/{cid}/generate", json={"template_id": tid})


# ── Tải / thay / soạn mẫu theo danh mục động ────────────────────────────────────────
def test_tai_mau_dung_bien_tuy_chinh_va_bang_chu(setup, db):
    world, a1, _ = setup
    add_var(db, "thuong", MONEY)
    add_var(db, "so_ngay", NUMBER)
    tid = tpl_with(a1, world, "{{ thuong }} / {{ thuong_bang_chu }} / {{ so_ngay }}")
    assert db.get(LaborContractTemplate, tid).placeholders == ["so_ngay", "thuong", "thuong_bang_chu"]


def test_tai_mau_bien_ngung_dung_bien_la_va_bang_chu_cua_bien_chu(setup, db):
    world, a1, _ = setup
    add_var(db, "cu", TEXT, is_active=False)
    add_var(db, "chu", TEXT)
    for text, phrase, unknown in (("{{ cu }}", "đã ngừng dùng", ["cu"]), ("{{ la_hoac }}", "ngoài danh mục", ["la_hoac"]),
                                  ("{{ chu_bang_chu }}", "ngoài danh mục", ["chu_bang_chu"])):
        res = upload_template(a1, company_id=world.co["A"], name=text, data=make_docx(text))
        assert res.status_code == 422, text
        err = res.json()["error"]
        assert phrase in err["message"] and err["details"]["unknown"] == unknown


def test_thay_tep_va_soan_web_mau_cu_van_giu_bien_da_ngung_dung(setup, db):
    world, a1, _ = setup
    var = add_var(db, "cu", TEXT)
    tid = tpl_with(a1, world, "A {{ cu }}")
    var.is_active = False
    db.commit()
    ok = a1.put(f"{TPL}/{tid}/file", files={"file": ("m.docx", make_docx("B {{ cu }} sửa chính tả"), DOCX_MIME)})
    assert ok.status_code == 200, ok.text
    web = a1.put(f"{TPL}/{tid}/content", json={"html": "<p>C {{ cu }}</p>"})
    assert web.status_code == 200, web.text
    add_var(db, "cu2", TEXT, is_active=False)
    bad = a1.put(f"{TPL}/{tid}/file", files={"file": ("m.docx", make_docx("{{ cu }} {{ cu2 }}"), DOCX_MIME)})
    assert bad.status_code == 422 and "ngừng dùng" in bad.json()["error"]["message"]
    assert db.get(LaborContractTemplate, tid).placeholders == ["cu"]


# ── Lập / sửa hợp đồng: lưu giá trị ─────────────────────────────────────────────────
def test_lap_hd_chuan_hoa_va_sao_mac_dinh(setup, db):
    world, a1, _ = setup
    add_var(db, "thuong", MONEY, default_value="1000000")
    add_var(db, "he_so", NUMBER)
    add_var(db, "ngay_hl", DATE, default_value="2026-10-01")
    add_var(db, "cu", TEXT, default_value="x", is_active=False)
    item = make_contract(a1, world.emp["a2"], custom_values={"he_so": "1,5", "ngay_hl": ""})
    assert item["custom_values"] == {"thuong": "1000000", "he_so": "1.5"}   # ngay_hl gửi rỗng = người dùng xóa
    # đổi mặc định sau đó KHÔNG đổi hợp đồng đã lập
    db.query(LaborContractVariable).filter_by(code="thuong").one().default_value = "9"
    db.commit()
    assert a1.get(f"{CT}/{item['id']}").json()["data"]["custom_values"]["thuong"] == "1000000"


def test_sua_hd_gop_xoa_giu_va_chan_gia_tri_sai(setup, db):
    world, a1, _ = setup
    add_var(db, "a_chu", TEXT)
    add_var(db, "b_tien", MONEY)
    add_var(db, "c_cu", TEXT)
    cid = make_contract(a1, world.emp["a2"], custom_values={"a_chu": "xin chào", "b_tien": 5000, "c_cu": "giữ"})["id"]
    db.query(LaborContractVariable).filter_by(code="c_cu").one().is_active = False
    db.commit()

    def patch(values):
        return a1.patch(f"{CT}/{cid}", json={"custom_values": values})

    assert patch({"a_chu": "mới"}).json()["data"]["item"]["custom_values"] == {"a_chu": "mới", "b_tien": "5000", "c_cu": "giữ"}
    assert patch({"b_tien": ""}).json()["data"]["item"]["custom_values"] == {"a_chu": "mới", "c_cu": "giữ"}
    assert patch({"b_tien": None, "a_chu": None}).json()["data"]["item"]["custom_values"] == {"c_cu": "giữ"}
    for bad, code in (({"khong_co": "1"}, 422), ({"ho_ten": "x"}, 422), ({"b_tien": "-1"}, 422),
                      ({"c_cu": "đổi"}, 422), ({"Sai_Ma": "1"}, 422), ({"a_chu": "x" * 256}, 422)):
        res = patch(bad)
        assert res.status_code == code, bad
        assert "x" * 20 not in res.text                                       # không lặp lại giá trị
    assert patch({"c_cu": "giữ"}).status_code == 200                           # gửi y cũ thì nhận
    assert patch({}).status_code == 200


def test_gioi_han_so_khoa_va_tong_kich_thuoc(setup, db):
    world, a1, _ = setup
    for i in range(10):
        add_var(db, f"bien_{i}", MULTI)
    cid = make_contract(a1, world.emp["a2"])["id"]
    too_many = {f"k{i:03d}": "1" for i in range(101)}
    assert a1.patch(f"{CT}/{cid}", json={"custom_values": too_many}).status_code == 422
    big = {f"bien_{i}": "ă" * 2000 for i in range(10)}                       # 20.000 ký tự giá trị + khóa > trần
    res = a1.patch(f"{CT}/{cid}", json={"custom_values": big})
    assert res.status_code == 422 and "20000" in res.json()["error"]["message"]
    assert a1.patch(f"{CT}/{cid}", json={"custom_values": {"bien_0": "x" * 2001}}).status_code == 422


def test_hd_da_ky_khong_sua_duoc_gia_tri(setup, db):
    world, a1, _ = setup
    add_var(db, "a_chu", TEXT)
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert a1.post(f"{CT}/{cid}/transition", json={"to_status": int(S.SIGNED), "date": "2026-01-02"}).status_code == 200
    assert a1.patch(f"{CT}/{cid}", json={"custom_values": {"a_chu": "x"}}).status_code == 409


def test_doi_gia_tri_bo_tep_cu_gui_lai_y_nguyen_giu_tep(setup, db):
    world, a1, _ = setup
    add_var(db, "a_chu", TEXT)
    tid = tpl_with(a1, world, "{{ a_chu }}")
    cid = make_contract(a1, world.emp["a2"], custom_values={"a_chu": "một"})["id"]
    assert gen(a1, cid, tid).json()["data"]["has_generated_file"] is True
    same = a1.patch(f"{CT}/{cid}", json={"custom_values": {"a_chu": "một"}}).json()["data"]["item"]
    assert same["has_generated_file"] is True
    changed = a1.patch(f"{CT}/{cid}", json={"custom_values": {"a_chu": "hai"}}).json()["data"]["item"]
    assert changed["has_generated_file"] is False


# ── Sinh tệp ───────────────────────────────────────────────────────────────────────
def test_sinh_tep_dinh_dang_dung_5_kieu(setup, db):
    world, a1, _ = setup
    add_var(db, "ghi_chu_tc", TEXT)
    add_var(db, "gioi_thieu", MULTI)
    add_var(db, "he_so", NUMBER)
    add_var(db, "ngay_hl", DATE)
    add_var(db, "thuong", MONEY)
    tid = tpl_with(a1, world, "{{ ghi_chu_tc }}|{{ he_so }}|{{ ngay_hl }}|{{ thuong }}|{{ thuong_bang_chu }}|{{ gioi_thieu }}")
    cid = make_contract(a1, world.emp["a2"], custom_values={
        "ghi_chu_tc": "Tuỳ ý", "he_so": "1234,5", "ngay_hl": "2026-10-01", "thuong": 15000000,
        "gioi_thieu": "Dòng 1\nDòng 2"})["id"]
    assert gen(a1, cid, tid).status_code == 200
    data = a1.get(f"{CT}/{cid}/document").content
    text = docx_text(data)
    assert "Tuỳ ý|1.234,5|01/10/2026|15.000.000|Mười lăm triệu đồng chẵn|Dòng 1" in text
    xml = zipfile.ZipFile(BytesIO(data)).read("word/document.xml").decode()
    assert "Dòng 1</w:t><w:br/><w:t" in xml and "Dòng 2" in xml                 # xuống dòng thành ngắt dòng Word


def test_gia_tri_trong_khong_bat_buoc_ra_chuoi_rong(setup, db):
    world, a1, _ = setup
    add_var(db, "tuy_chon", TEXT, default_value="chỉ sao lúc lập")
    tid = tpl_with(a1, world, "[{{ tuy_chon }}]")
    cid = make_contract(a1, world.emp["a2"], custom_values={"tuy_chon": ""})["id"]   # người dùng cố ý để trống
    assert gen(a1, cid, tid).status_code == 200
    assert "[]" in docx_text(a1.get(f"{CT}/{cid}/document").content)


def test_bat_buoc_thieu_chan_sinh_neu_mau_dung_va_khong_neu_gia_tri(setup, db):
    world, a1, _ = setup
    add_var(db, "so_ngay", NUMBER, is_required=True, label="Số ngày phép")
    add_var(db, "thuong", MONEY, is_required=True, label="Thưởng")
    add_var(db, "khong_dung", TEXT, is_required=True, label="Không dùng")
    tid = tpl_with(a1, world, "{{ so_ngay }} {{ thuong_bang_chu }}")
    cid = make_contract(a1, world.emp["a2"])["id"]
    res = gen(a1, cid, tid)
    assert res.status_code == 422
    message = res.json()["error"]["message"]
    assert "Số ngày phép" in message and "Thưởng" in message and "Không dùng" not in message
    a1.patch(f"{CT}/{cid}", json={"custom_values": {"so_ngay": "12", "thuong": "777"}})
    assert gen(a1, cid, tid).status_code == 200
    # lưu nháp thì không bao giờ bị chặn
    assert a1.patch(f"{CT}/{cid}", json={"custom_values": {"so_ngay": ""}}).status_code == 200


def test_bat_buoc_chan_chuyen_sang_da_ky_luu_nhap_thi_khong(setup, db):
    world, a1, _ = setup
    add_var(db, "so_ngay", NUMBER, is_required=True, label="Số ngày phép")
    tpl_with(a1, world, "{{ so_ngay }}")                       # mẫu đang dùng của pháp nhân A có dùng biến
    cid = make_contract(a1, world.emp["a2"])["id"]
    sign = lambda: a1.post(f"{CT}/{cid}/transition", json={"to_status": int(S.SIGNED), "date": "2026-01-02"})  # noqa: E731
    res = sign()
    assert res.status_code == 422 and "Số ngày phép" in res.json()["error"]["message"]
    assert db.get(LaborContract, cid).status == int(S.DRAFT)
    a1.patch(f"{CT}/{cid}", json={"custom_values": {"so_ngay": "12"}})
    assert sign().status_code == 200
    # hủy không bị chặn bởi biến bắt buộc
    cid2 = make_contract(a1, world.emp["a3"], contract_no="HD-2")["id"]
    assert a1.post(f"{CT}/{cid2}/transition", json={"to_status": int(S.CANCELLED), "reason": "x"}).status_code == 200


def test_ky_hd_da_sinh_tep_chi_xet_bien_ma_mau_dung(setup, db):
    world, a1, _ = setup
    var = add_var(db, "so_ngay", NUMBER, label="Số ngày phép")
    tid = tpl_with(a1, world, "{{ ho_ten }} {{ so_ngay }}")
    cid = make_contract(a1, world.emp["a2"], custom_values={"so_ngay": "3"})["id"]
    assert gen(a1, cid, tid).status_code == 200
    var.is_required = True
    add_var(db, "khac", TEXT, is_required=True, label="Khác")                  # mẫu không dùng → không chặn
    var.is_required = False
    db.commit()
    assert a1.post(f"{CT}/{cid}/transition", json={"to_status": int(S.SIGNED), "date": "2026-01-02"}).status_code == 200


def test_bien_ngung_dung_trong_mau_cu_van_sinh_bang_gia_tri_da_luu(setup, db):
    world, a1, _ = setup
    var = add_var(db, "cu", TEXT)
    tid = tpl_with(a1, world, "<{{ cu }}>")
    cid = make_contract(a1, world.emp["a2"], custom_values={"cu": "giữ nguyên"})["id"]
    var.is_active = False
    db.commit()
    assert gen(a1, cid, tid).status_code == 200
    assert "<giữ nguyên>" in docx_text(a1.get(f"{CT}/{cid}/document").content)


def test_dong_bien_bi_xoa_giua_chung_422_ro_rang(setup, db):
    world, a1, _ = setup
    var = add_var(db, "se_xoa", TEXT)
    tid = tpl_with(a1, world, "{{ se_xoa }}")
    cid = make_contract(a1, world.emp["a2"])["id"]
    db.delete(var)
    db.commit()
    res = gen(a1, cid, tid)
    assert res.status_code == 422 and "đã bị xóa" in res.json()["error"]["message"] and "se_xoa" in res.json()["error"]["message"]


# ── Che nhật ký, bản lưu trữ ────────────────────────────────────────────────────────
@pytest.mark.parametrize("path", ["/api/labor-contracts/7", "/api/employees/5/labor-contracts"])
def test_request_log_che_custom_values(path):
    che = mask_payload({"custom_values": {"thuong": "99000000"}, "contract_no": "HD-1"}, sensitive_keys_for_path(path))
    assert che["custom_values"] == MASKED and che["contract_no"] == "HD-1"


def test_change_log_khong_ghi_gia_tri_custom_values():
    assert _is_allowed("tab_labor_contract", "custom_values") is False
    assert _is_allowed("tab_labor_contract", "contract_no") is True


def test_ban_luu_tru_khong_chua_gia_tri_bien_o_tieu_de_hay_tom_tat(setup, db):
    world, a1, _ = setup
    add_var(db, "thuong", MONEY)
    cid = make_contract(a1, world.emp["a2"], custom_values={"thuong": "88888888"})["id"]
    row = db.get(LaborContract, cid)
    emp = db.get(__import__("app.modules.employee.model", fromlist=["Employee"]).Employee, row.employee_id)
    blob = json.dumps([sync._title(row, emp), sync._summary(row)], ensure_ascii=False)
    assert "88888888" not in blob and "88.888.888" not in blob


# ── Lượt 2 (review): M1 chốt «bắt buộc» khi ký chỉ xét biến mà mẫu CỦA PHÁP NHÂN HĐ dùng ─────────
def _sign(client, cid):
    return client.post(f"{CT}/{cid}/transition", json={"to_status": int(S.SIGNED), "date": "2026-01-02"})


def test_ky_khong_bi_chan_boi_bien_bat_buoc_cua_phap_nhan_khac(setup, db, world, client_as):  # noqa: F811
    _, a1, _ = setup
    add_var(db, "chi_a", TEXT, is_required=True, label="Chỉ của A")
    tpl_with(a1, world, "{{ chi_a }}")                              # chỉ mẫu pháp nhân A dùng biến
    grant_all(world, "b1")
    b1 = client_as(world.actor("b1"))
    cid = make_contract(b1, _employee_of(db, world, "B"))["id"]
    assert _sign(b1, cid).status_code == 200                        # B không có mẫu nào dùng biến của A


def _employee_of(db, world, company_key):
    from app.modules.employee.model import Employee

    emp = Employee(code=f"X{company_key}{db.query(Employee).count()}", full_name="NV thử", is_active=True,
                   company_id=world.co[company_key])
    db.add(emp)
    db.commit()
    return emp.id


def test_ky_hd_chua_co_mau_xet_mau_dang_dung_cung_loai_roi_moi_den_moi_loai(setup, db):
    world, a1, _ = setup
    add_var(db, "chi_loai2", TEXT, is_required=True, label="Chỉ loại 2")
    add_var(db, "chi_loai3", TEXT, is_required=True, label="Chỉ loại 3")
    # mẫu loại 2 dùng chi_loai2; mẫu loại 3 dùng chi_loai3
    assert upload_template(a1, company_id=world.co["A"], name="M2", contract_type=2,
                           data=make_docx("{{ chi_loai2 }}")).status_code == 201
    assert upload_template(a1, company_id=world.co["A"], name="M3", contract_type=3,
                           data=make_docx("{{ chi_loai3 }}")).status_code == 201
    cid = make_contract(a1, world.emp["a2"])["id"]                  # loại 2, chưa sinh tệp (template_id = 0)
    res = _sign(a1, cid)
    assert res.status_code == 422 and "Chỉ loại 2" in res.json()["error"]["message"]
    assert "Chỉ loại 3" not in res.json()["error"]["message"]
    a1.patch(f"{CT}/{cid}", json={"custom_values": {"chi_loai2": "ok"}})
    assert _sign(a1, cid).status_code == 200


def test_ky_hd_khong_co_mau_cung_loai_thi_lay_moi_loai_cua_phap_nhan(setup, db):
    world, a1, _ = setup
    add_var(db, "chi_loai3", TEXT, is_required=True, label="Chỉ loại 3")
    assert upload_template(a1, company_id=world.co["A"], name="M3", contract_type=3,
                           data=make_docx("{{ chi_loai3 }}")).status_code == 201
    cid = make_contract(a1, world.emp["a2"])["id"]                  # loại 2, pháp nhân A chỉ có mẫu loại 3
    assert _sign(a1, cid).status_code == 422


def test_ky_sau_khi_sua_hd_mat_mau_van_chi_xet_mau_cua_phap_nhan(setup, db):
    world, a1, _ = setup
    add_var(db, "so_ngay", NUMBER, is_required=True, label="Số ngày phép")
    tid = tpl_with(a1, world, "{{ so_ngay }}")
    cid = make_contract(a1, world.emp["a2"], custom_values={"so_ngay": "5"})["id"]
    assert gen(a1, cid, tid).status_code == 200
    a1.patch(f"{CT}/{cid}", json={"custom_values": {"so_ngay": ""}})   # sửa → template_id về 0, tệp bỏ
    assert db.get(LaborContract, cid).template_id == 0
    assert _sign(a1, cid).status_code == 422


# ── M2: dữ liệu lệch không làm hỏng việc sinh ───────────────────────────────────────
def test_bien_tuy_chinh_trung_ma_he_thong_gia_tri_he_thong_thang_va_ghi_log(setup, db, caplog):
    world, a1, _ = setup
    db.add(LaborContractVariable(code="ho_ten", source=2, value_type=TEXT, label="Trùng"))
    db.commit()
    tid = tpl_with(a1, world, "{{ ho_ten }}")
    cid = make_contract(a1, world.emp["a2"])["id"]
    with caplog.at_level("ERROR", logger="app.labor_contract"):
        assert gen(a1, cid, tid).status_code == 200
    assert "Nhân sự a2" in docx_text(a1.get(f"{CT}/{cid}/document").content)
    assert any("ho_ten" in r.getMessage() for r in caplog.records)


def test_seed_canh_bao_khi_dong_tuy_chinh_trung_ma_he_thong(db, caplog):
    from app.modules.labor_contract.variable_seed import ensure_system_variables

    db.add(LaborContractVariable(code="email", source=2, value_type=TEXT, label="Trùng"))
    db.commit()
    with caplog.at_level("WARNING", logger="app.labor_contract"):
        ensure_system_variables(db)
    assert any("email" in r.getMessage() for r in caplog.records)


# ── L4: số 0 là một giá trị thật ───────────────────────────────────────────────────
def test_so_khong_la_gia_tri_thoa_bat_buoc_va_in_ra_0(setup, db):
    world, a1, _ = setup
    add_var(db, "he_so", NUMBER, is_required=True, label="Hệ số")
    add_var(db, "thuong", MONEY, is_required=True, label="Thưởng")
    tid = tpl_with(a1, world, "[{{ he_so }}][{{ thuong }}][{{ thuong_bang_chu }}]")
    cid = make_contract(a1, world.emp["a2"], custom_values={"he_so": "0", "thuong": 0})["id"]
    assert a1.get(f"{CT}/{cid}").json()["data"]["custom_values"] == {"he_so": "0", "thuong": "0"}
    assert gen(a1, cid, tid).status_code == 200
    assert "[0][0][" in docx_text(a1.get(f"{CT}/{cid}/document").content)
