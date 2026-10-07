"""API Mẫu hợp đồng lao động (`/api/labor-contract-templates`) — chạy qua HTTP thật (TestClient),
kho tệp giả trong bộ nhớ, còn guard_upload / inspect_template / phạm vi / quyền chạy THẬT.

Góc nhìn kẻ phá: pháp nhân khác gõ id vào URL, tải tệp "docx" giả, vòng lặp lồng nhau, macro,
thay tệp hỏng không được làm mất tệp cũ, xóa mẫu đang dùng.
"""
import time

import pytest
from sqlalchemy import event

from app.modules.attachment.model import StoredFile
from app.modules.labor_contract.model import LaborContract
from app.modules.labor_contract.template_model import LaborContractTemplate
from hdld_factory import (DOCX_MIME, PDF_BYTES, client_as, grant_all, make_docx, storage,  # noqa: F401
                          upload_template)

URL = "/api/labor-contract-templates"


@pytest.fixture
def setup(db, world, storage, client_as):  # noqa: F811
    """a1 = HR công ty A (phạm vi `company`), b1 = HR công ty B. Mỗi người có CRUD + print."""
    grant_all(world, "a1")
    grant_all(world, "b1")
    return world, client_as(world.actor("a1")), client_as, storage


# ── Đường đẹp ─────────────────────────────────────────────────────────────────────────
def test_tao_mau_tra_ve_du_truong_va_khong_lo_url_hay_khoa_tep(setup, db):
    world, a1, _, storage = setup
    res = upload_template(a1, company_id=world.co["A"], note="Dùng cho NV mới")
    assert res.status_code == 201, res.text
    item = res.json()["data"]
    assert item["company_name"] == "Công ty A" and item["contract_type"] == 2
    #  Mã pháp nhân đi kèm tên — hai pháp nhân trùng tên thì chỉ mã mới phân biệt được (test Chrome 06/10).
    assert item["company_code"] == "CTY_A"
    assert item["placeholders"] == ["ho_ten", "luong_co_ban", "luong_co_ban_bang_chu", "so_hop_dong"]
    assert item["original_filename"] == "mau.docx" and item["file_size"] > 0 and item["contract_count"] == 0
    assert item["is_active"] is True and item["created_by_name"]
    leaked = {"url", "file_key", "file_id", "thumb_key"} & set(item)
    assert not leaked, f"lộ trường tệp: {leaked}"
    assert len(storage) == 1


def test_danh_muc_bien_can_quyen_doc_mau_hoac_tao_hop_dong(db, world, storage, client_as):  # noqa: F811
    world.actor("a1").grant("labor_contract_template", "company", actions=("read",))
    world.actor("a2").grant("labor_contract", "company", actions=("create",))
    world.actor("a3").grant("employee", "company", actions=("read",))      # có quyền khác, không dính HĐLĐ
    for who, status in (("a1", 200), ("a2", 200), ("a3", 403)):
        assert client_as(world.actor(who)).get(f"{URL}/placeholders").status_code == status, who
    rows = client_as(world.actor("a1")).get(f"{URL}/placeholders").json()["data"]
    assert {"key", "label", "group", "example"} == set(rows[0]) and any(r["key"] == "ho_ten" for r in rows)


# ── Phạm vi: pháp nhân khác ──────────────────────────────────────────────────────────
def test_phap_nhan_khac_khong_thay_khong_tai_khong_sua_khong_xoa_mau(setup):
    world, a1, make_client, _ = setup
    b1 = make_client(world.actor("b1"))
    tid = upload_template(b1, company_id=world.co["B"], name="Mẫu của B").json()["data"]["id"]

    assert a1.get(URL).json()["data"]["total"] == 0                      # danh sách: không thấy
    for method, path, kw in [("get", f"/{tid}", {}), ("get", f"/{tid}/file", {}),
                             ("patch", f"/{tid}", {"json": {"name": "x"}}),
                             ("delete", f"/{tid}", {}),
                             ("put", f"/{tid}/file", {"files": {"file": ("m.docx", make_docx("x"), DOCX_MIME)}})]:
        res = getattr(a1, method)(URL + path, **kw)
        assert res.status_code == 404, f"{method} {path} → {res.status_code} (phải 404, không lộ sự tồn tại)"
    assert b1.get(f"{URL}/{tid}").status_code == 200                      # chủ thật vẫn thấy


def test_tao_mau_cho_phap_nhan_ngoai_pham_vi_403_va_khong_de_lai_rac(setup, db):
    world, a1, _, storage = setup
    res = upload_template(a1, company_id=world.co["B"])
    assert res.status_code == 403 and "ngoài phạm vi" in res.json()["error"]["message"]
    assert db.query(LaborContractTemplate).count() == 0
    assert storage == {} and db.query(StoredFile).count() == 0


def test_danh_sach_chi_hien_phap_nhan_trong_pham_vi_va_loc_dung(setup):
    world, a1, make_client, _ = setup
    upload_template(a1, company_id=world.co["A"], name="A-thu-viec", contract_type=1)
    upload_template(a1, company_id=world.co["A"], name="A-xac-dinh", contract_type=2)
    upload_template(make_client(world.actor("b1")), company_id=world.co["B"], name="B-1")
    assert {i["name"] for i in a1.get(URL).json()["data"]["items"]} == {"A-thu-viec", "A-xac-dinh"}
    assert [i["name"] for i in a1.get(URL, params={"contract_type": 1}).json()["data"]["items"]] == ["A-thu-viec"]
    assert [i["name"] for i in a1.get(URL, params={"q": "xac"}).json()["data"]["items"]] == ["A-xac-dinh"]
    assert a1.get(URL, params={"company_id": world.co["B"]}).json()["data"]["total"] == 0   # lọc sang B vẫn bị phạm vi chặn


# ── Quyền ─────────────────────────────────────────────────────────────────────────────
def test_thieu_quyen_tung_hanh_dong_403(db, world, storage, client_as):  # noqa: F811
    world.actor("a1").grant("labor_contract_template", "company", actions=("read",))
    world.actor("a2").grant("labor_contract_template", "company", actions=("read", "create", "write", "delete"))
    admin = client_as(world.actor("a2"))
    tid = upload_template(admin, company_id=world.co["A"]).json()["data"]["id"]
    ro = client_as(world.actor("a1"))
    assert ro.get(f"{URL}/{tid}/file").status_code == 200
    assert upload_template(ro, company_id=world.co["A"], name="khác").status_code == 403
    assert ro.patch(f"{URL}/{tid}", json={"name": "x"}).status_code == 403
    assert ro.delete(f"{URL}/{tid}").status_code == 403
    nobody = client_as(world.actor("a3"))
    assert nobody.get(URL).status_code == 403 and nobody.get(f"{URL}/{tid}/file").status_code == 403


# ── Tải lên bị từ chối ────────────────────────────────────────────────────────────────
def test_bien_la_422_kem_ten_bien_trong_details(setup, db):
    world, a1, _, storage = setup
    res = upload_template(a1, company_id=world.co["A"], data=make_docx("{{ ho_ten }} {{ con_meo }} {{ luong_tang }}"))
    body = res.json()
    assert res.status_code == 422 and body["error"]["details"]["unknown"] == ["con_meo", "luong_tang"]
    assert db.query(LaborContractTemplate).count() == 0 and storage == {}


def test_vong_lap_long_nhau_bi_tu_choi_ngay_khong_treo_may(setup):
    world, a1, _, _ = setup
    payload = "{% for a in range(100000) %}{% for b in range(100000) %}x{% endfor %}{% endfor %}"
    start = time.monotonic()
    res = upload_template(a1, company_id=world.co["A"], data=make_docx(payload))
    assert res.status_code == 422 and time.monotonic() - start < 5
    assert "thẻ lệnh" in res.json()["error"]["message"]


@pytest.mark.parametrize("filename,data,status", [
    pytest.param("mau.pdf", PDF_BYTES, 400, id="sai-duoi"),
    pytest.param("mau.docx", b"", 400, id="rong"),
    #  đuôi đúng nhưng không phải .docx — guard_upload KHÔNG nhìn nội dung nên inspect_template phải bắt
    pytest.param("mau.docx", b"day khong phai zip", 422, id="khong-phai-zip"),
    pytest.param("mau.docx", b"PK\x03\x04" + b"\x00" * 100, 422, id="chu-ky-zip-gia"),
    pytest.param("mau.docx", b"\x00" * (11 * 1024 * 1024), 400, id="vuot-10MB"),
    pytest.param("a" * 300 + ".docx", b"x", 422, id="ten-qua-dai"),
])
def test_tep_xau_bi_tu_choi_dung_ma_va_khong_luu_gi(setup, db, filename, data, status):
    world, a1, _, storage = setup
    res = upload_template(a1, company_id=world.co["A"], data=data, filename=filename)
    assert res.status_code == status, res.text
    assert db.query(LaborContractTemplate).count() == 0 and storage == {}


def test_docx_co_macro_bi_tu_choi(setup):
    import zipfile
    from io import BytesIO

    world, a1, _, _ = setup
    src = make_docx("{{ ho_ten }}")
    out = BytesIO()
    with zipfile.ZipFile(BytesIO(src)) as zin, zipfile.ZipFile(out, "w") as zout:
        for info in zin.infolist():
            zout.writestr(info, zin.read(info.filename))
        zout.writestr("word/vbaProject.bin", b"\x00")
    res = upload_template(a1, company_id=world.co["A"], data=out.getvalue())
    assert res.status_code == 422 and "macro" in res.json()["error"]["message"]


@pytest.mark.parametrize("override,status", [
    ({"contract_type": 0}, 422), ({"contract_type": 7}, 422), ({"contract_type": -1}, 422),
    ({"name": "   "}, 422), ({"name": "n" * 201}, 422), ({"note": "n" * 501}, 422),
    ({"company_id": 0}, 422), ({"company_id": -5}, 422), ({"company_id": 999_999}, 403),   # ngoài phạm vi → 403 trước kiểm «không tồn tại» (L3)
])
def test_truong_form_sai_bi_chan_o_tang_schema_hoac_service(setup, override, status):
    world, a1, _, _ = setup
    form = {"name": "Mẫu", "company_id": str(world.co["A"]), "contract_type": "2", "note": ""}
    form.update({k: str(v) for k, v in override.items()})
    res = a1.post(URL, files={"file": ("m.docx", make_docx("{{ ho_ten }}"), DOCX_MIME)}, data=form)
    assert res.status_code == status, res.text


def test_phap_nhan_ngung_hoat_dong_va_trung_ten_400(setup, db):
    from app.modules.company.model import Company

    world, a1, _, _ = setup
    assert upload_template(a1, company_id=world.co["A"], name="Mẫu 1").status_code == 201
    dup = upload_template(a1, company_id=world.co["A"], name="Mẫu 1")
    assert dup.status_code == 400 and "đã tồn tại" in dup.json()["error"]["message"]
    db.get(Company, world.co["A"]).is_active = False
    db.commit()
    assert upload_template(a1, company_id=world.co["A"], name="Mẫu 2").status_code == 400


# ── Sửa / thay tệp ────────────────────────────────────────────────────────────────────
def test_patch_khong_doi_duoc_phap_nhan_va_khong_nhan_truong_la(setup):
    world, a1, _, _ = setup
    tid = upload_template(a1, company_id=world.co["A"]).json()["data"]["id"]
    assert a1.patch(f"{URL}/{tid}", json={"company_id": world.co["B"]}).status_code == 422
    assert a1.patch(f"{URL}/{tid}", json={"file_id": 5}).status_code == 422
    assert a1.patch(f"{URL}/{tid}", json={"contract_type": 0}).status_code == 422
    ok = a1.patch(f"{URL}/{tid}", json={"is_active": False, "contract_type": 3, "note": "ngừng"})
    assert ok.status_code == 200 and ok.json()["data"]["is_active"] is False and ok.json()["data"]["contract_type"] == 3
    # null cho cột NOT NULL không được ghi đè thành None (sẽ nổ 500 trên MySQL)
    assert a1.patch(f"{URL}/{tid}", json={"name": None, "is_active": None}).status_code == 200
    assert a1.get(f"{URL}/{tid}").json()["data"]["name"] == "Mẫu thử việc"


def test_patch_doi_ten_trung_400(setup):
    world, a1, _, _ = setup
    upload_template(a1, company_id=world.co["A"], name="Một")
    tid = upload_template(a1, company_id=world.co["A"], name="Hai").json()["data"]["id"]
    assert a1.patch(f"{URL}/{tid}", json={"name": "Một"}).status_code == 400
    assert a1.patch(f"{URL}/{tid}", json={"name": "Hai"}).status_code == 200   # giữ nguyên tên mình không phải trùng


def test_thay_tep_xoa_tep_cu_sau_khi_luu_tep_moi_va_cap_nhat_bien(setup, db):
    world, a1, _, storage = setup
    tid = upload_template(a1, company_id=world.co["A"]).json()["data"]["id"]
    old_keys = set(storage)
    res = a1.put(f"{URL}/{tid}/file", files={"file": ("moi.docx", make_docx("Chỉ {{ email }}"), DOCX_MIME)})
    assert res.status_code == 200 and res.json()["data"]["placeholders"] == ["email"]
    assert res.json()["data"]["original_filename"] == "moi.docx"
    assert len(storage) == 1 and not (old_keys & set(storage))            # tệp cũ đã dọn
    assert db.query(StoredFile).count() == 1


def test_thay_tep_hong_giu_nguyen_tep_cu(setup, db):
    world, a1, _, storage = setup
    tid = upload_template(a1, company_id=world.co["A"]).json()["data"]["id"]
    before = dict(storage)
    for bad in (make_docx("{{ bien_la }}"), b"khong phai docx", make_docx("{% for i in range(3) %}x{% endfor %}")):
        res = a1.put(f"{URL}/{tid}/file", files={"file": ("moi.docx", bad, DOCX_MIME)})
        assert res.status_code == 422
    assert storage == before                                               # không mất, không thêm
    assert a1.get(f"{URL}/{tid}/file").status_code == 200
    assert a1.get(f"{URL}/{tid}").json()["data"]["original_filename"] == "mau.docx"


# ── Tải tệp ───────────────────────────────────────────────────────────────────────────
def test_tai_tep_tra_dung_byte_voi_ten_an_toan(setup):
    world, a1, _, storage = setup
    tid = upload_template(a1, company_id=world.co["A"]).json()["data"]["id"]
    res = a1.get(f"{URL}/{tid}/file")
    assert res.status_code == 200 and res.content == next(iter(storage.values()))
    assert res.headers["content-type"] == DOCX_MIME
    assert "filename*=UTF-8''mau.docx" in res.headers["content-disposition"]
    assert "no-store" in res.headers["cache-control"]


# ── Xóa ───────────────────────────────────────────────────────────────────────────────
def test_xoa_mau_dang_duoc_hop_dong_dung_409_chua_dung_thi_xoa_va_don_tep(setup, db):
    world, a1, _, storage = setup
    used = upload_template(a1, company_id=world.co["A"], name="Đang dùng").json()["data"]["id"]
    free = upload_template(a1, company_id=world.co["A"], name="Chưa dùng").json()["data"]["id"]
    db.add(LaborContract(code="HDLD001", employee_id=world.emp["a2"], company_id=world.co["A"],
                         template_id=used, contract_type=2, start_date=__import__("datetime").date(2026, 1, 1)))
    db.commit()
    res = a1.delete(f"{URL}/{used}")
    assert res.status_code == 409 and "Ngừng dùng" in res.json()["error"]["message"]
    assert {i["name"]: i["contract_count"] for i in a1.get(URL).json()["data"]["items"]} == {"Đang dùng": 1, "Chưa dùng": 0}
    assert len(storage) == 2
    assert a1.delete(f"{URL}/{free}").status_code == 200
    assert len(storage) == 1 and a1.get(f"{URL}/{free}").status_code == 404


# ── Hiệu năng: số truy vấn cố định ────────────────────────────────────────────────────
def test_danh_sach_dem_hop_dong_bang_mot_truy_van_khong_n_cong_1(setup, db):
    world, a1, _, _ = setup
    for i in range(6):
        upload_template(a1, company_id=world.co["A"], name=f"Mẫu {i}")

    def count_queries(page_size: int) -> int:
        n = {"v": 0}

        def on_exec(*_a, **_k):
            n["v"] += 1

        event.listen(db.get_bind(), "before_cursor_execute", on_exec)
        try:
            assert a1.get(URL, params={"page_size": page_size}).status_code == 200
        finally:
            event.remove(db.get_bind(), "before_cursor_execute", on_exec)
        return n["v"]

    count_queries(6)   # lượt đầu dựng hồ sơ quyền (cache 60s) — không tính
    assert count_queries(2) == count_queries(6)


def test_thong_bao_the_lenh_noi_dung_the_va_khong_kem_meo_go_lai_bien(setup):
    """Lỗi cũ (test Chrome 06/10): thông báo ra «'If' … điều kiện.. Gõ lại biến một lượt…» — hai dấu chấm,
    tên nút Jinja thay vì thẻ người dùng gõ, và mẹo «gõ lại biến» không liên quan tới `{% if %}`."""
    world, a1, _, _ = setup
    res = upload_template(a1, company_id=world.co["A"], data=make_docx("{% if ho_ten %}x{% endif %}"))
    msg = res.json()["error"]["message"]
    assert res.status_code == 422 and "{% if %}" in msg
    assert ".." not in msg and "Gõ lại biến" not in msg
