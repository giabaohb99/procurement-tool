"""Sinh tệp .docx từ mẫu, tải bản sinh (quyền `print`), tải lên bản scan đã ký — qua HTTP thật.

Góc nhìn kẻ phá: dùng mẫu của pháp nhân khác / sai loại / đã ngừng, sinh lại khi đã ký, tải bản sinh
khi chỉ có quyền đọc, dữ liệu NLĐ chứa cú pháp Jinja / ký tự phá XML, tên tệp độc hại, scan giả,
tệp cũ phải bị dọn đúng lúc, lỗi giữa chừng không để lại tệp mồ côi.
"""
import pytest

from app.core.labor_contract_codes import LaborContractStatus as S
from app.modules.attachment.model import StoredFile
from app.modules.employee.model import Employee
from app.modules.labor_contract import file_response
from app.modules.labor_contract.file_response import safe_filename
from app.modules.labor_contract.model import LaborContract
from hdld_factory import (DOCX_MIME, PDF_BYTES, PNG_BYTES, client_as, contract_payload,  # noqa: F401
                          docx_text, grant_all, make_contract, make_docx, storage, upload_template)

CT_URL = "/api/labor-contracts"


@pytest.fixture
def setup(db, world, storage, client_as):  # noqa: F811
    grant_all(world, "a1")
    grant_all(world, "b1")
    a1 = client_as(world.actor("a1"))
    tid = upload_template(a1, company_id=world.co["A"]).json()["data"]["id"]
    return world, a1, client_as, storage, tid


def gen(client, cid, tid):
    return client.post(f"{CT_URL}/{cid}/generate", json={"template_id": tid})


# ── Sinh ──────────────────────────────────────────────────────────────────────────────
def test_sinh_dien_dung_du_lieu_va_tai_ve_dung_ten(setup, db):
    world, a1, _, storage, tid = setup
    cid = make_contract(a1, world.emp["a2"], contract_no="HD/2026-07", base_salary=15_000_000)["id"]
    res = gen(a1, cid, tid)
    assert res.status_code == 200, res.text
    item = res.json()["data"]
    assert item["has_generated_file"] and item["template_id"] == tid and item["template_name"] == "Mẫu thử việc"
    assert item["can_print"] is True

    doc = a1.get(f"{CT_URL}/{cid}/document")
    assert doc.status_code == 200 and doc.headers["content-type"] == DOCX_MIME
    text = docx_text(doc.content)
    assert "HĐLĐ số HD/2026-07" in text and "Họ tên: Nhân sự a2" in text
    assert "15.000.000" in text and "mười lăm triệu" in text.lower()
    disposition = doc.headers["content-disposition"]
    assert disposition.startswith("attachment; filename*=UTF-8''HDLD-HD-2026-07-Nh")   # `/` trong số HĐ bị làm sạch
    assert "/" not in disposition.split("''", 1)[1]


def test_du_lieu_nguoi_dung_chua_cu_phap_jinja_va_ky_tu_xml_khong_bi_chay_hay_phá_tep(setup, db):
    """Họ tên do người dùng nhập: `{{ 7*7 }}`, `{% for %}`, `</w:t>` phải ra NGUYÊN VĂN, tệp vẫn mở lại được."""
    world, a1, _, _, tid = setup
    nasty = "{{ 7*7 }} {% for i in range(9**9) %}x{% endfor %} </w:t></w:p> A&B <c>"
    db.get(Employee, world.emp["a2"]).full_name = nasty
    db.commit()
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert gen(a1, cid, tid).status_code == 200
    assert f"Họ tên: {nasty}" in docx_text(a1.get(f"{CT_URL}/{cid}/document").content)


def test_sinh_lai_xoa_tep_cu_sau_khi_luu_tep_moi(setup, db):
    world, a1, _, storage, tid = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    gen(a1, cid, tid)
    keys_after_first = set(storage)
    row = db.get(LaborContract, cid)
    first_file = row.generated_file_id
    assert gen(a1, cid, tid).status_code == 200
    db.refresh(row)
    assert row.generated_file_id != first_file and db.get(StoredFile, first_file) is None
    assert len(storage) == len(keys_after_first)                       # 1 mẫu + 1 bản sinh, không phình
    assert set(storage) != keys_after_first                            # bản cũ đã bị thay


def test_sinh_khi_da_ky_hoac_da_huy_409(setup):
    world, a1, _, _, tid = setup
    signed = make_contract(a1, world.emp["a2"], contract_no="S")["id"]
    a1.post(f"{CT_URL}/{signed}/transition", json={"to_status": 2, "date": "2026-01-05"})
    assert gen(a1, signed, tid).status_code == 409
    cancelled = make_contract(a1, world.emp["a3"], contract_no="C")["id"]
    a1.post(f"{CT_URL}/{cancelled}/transition", json={"to_status": 5, "reason": "nhầm"})
    assert gen(a1, cancelled, tid).status_code == 409


def test_mau_sai_phap_nhan_sai_loai_ngung_dung_hoac_khong_ton_tai_400(setup, db):
    world, a1, make_client, _, tid = setup
    cid = make_contract(a1, world.emp["a2"])["id"]             # loại 2, pháp nhân A
    b_tpl = upload_template(make_client(world.actor("b1")), company_id=world.co["B"]).json()["data"]["id"]
    wrong_type = upload_template(a1, company_id=world.co["A"], name="Thử việc", contract_type=1).json()["data"]["id"]
    off = upload_template(a1, company_id=world.co["A"], name="Ngừng").json()["data"]["id"]
    a1.patch(f"/api/labor-contract-templates/{off}", json={"is_active": False})
    for bad_id, why in [(b_tpl, "pháp nhân khác"), (wrong_type, "sai loại"), (off, "ngừng dùng"), (999_999, "không tồn tại")]:
        res = gen(a1, cid, bad_id)
        assert res.status_code == 400, f"{why} → {res.status_code}"
    assert db.get(LaborContract, cid).generated_file_id == 0


def test_mau_phai_theo_phap_nhan_cua_hd_chu_khong_phai_phap_nhan_hien_tai_cua_nhan_su(setup, db):
    """NV chuyển sang B sau khi lập HĐ ở A: sinh lại vẫn chỉ dùng mẫu của A (tránh in tiêu đề B lên HĐ A)."""
    world, a1, make_client, _, tid = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    db.get(Employee, world.emp["a2"]).company_id = world.co["B"]
    db.commit()
    b_tpl = upload_template(make_client(world.actor("b1")), company_id=world.co["B"]).json()["data"]["id"]
    assert gen(a1, cid, b_tpl).status_code == 400
    assert gen(a1, cid, tid).status_code == 200


def test_ban_sinh_chi_thay_sau_khi_thay_tep_mau_khong_doi_hd_cu(setup, db):
    """Thay tệp mẫu về sau không đụng bản đã sinh (bản chụp riêng)."""
    world, a1, _, _, tid = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    gen(a1, cid, tid)
    before = a1.get(f"{CT_URL}/{cid}/document").content
    a1.put(f"/api/labor-contract-templates/{tid}/file", files={"file": ("moi.docx", make_docx("Khác hẳn"), DOCX_MIME)})
    assert a1.get(f"{CT_URL}/{cid}/document").content == before


def test_tep_mau_trong_kho_bi_thay_bang_ban_doc_hai_thi_sinh_422_khong_500(setup, storage):
    """Tệp trên storage có thể bị thay ngoài hệ thống: sinh phải kiểm lại, trả 422 chứ không chạy vòng lặp."""
    world, a1, _, _, tid = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    (key,) = storage
    storage[key] = make_docx("{% for a in range(100000) %}{% for b in range(100000) %}x{% endfor %}{% endfor %}")
    res = gen(a1, cid, tid)
    assert res.status_code == 422 and "Mẫu không sinh được" in res.json()["error"]["message"]
    assert len(storage) == 1                                           # không để lại bản sinh nửa vời


def test_tep_mau_mat_khoi_kho_404_va_loi_ghi_giua_chung_khong_de_tep_mo_coi(setup, db, storage, monkeypatch):
    world, a1, _, _, tid = setup
    cid = make_contract(a1, world.emp["a2"])["id"]

    def boom(*_a, **_k):
        raise RuntimeError("DB chết giữa chừng")

    monkeypatch.setattr("app.modules.labor_contract.generate_service.datetime", type("D", (), {"now": boom}))
    before = dict(storage)
    with pytest.raises(RuntimeError):
        a1.post(f"{CT_URL}/{cid}/generate", json={"template_id": tid})
    assert storage == before                                           # tệp đã đẩy lên được dọn lại
    assert db.get(LaborContract, cid).generated_file_id == 0


# ── Tải bản sinh: quyền print ─────────────────────────────────────────────────────────
def test_tai_ban_sinh_can_quyen_print_chi_doc_thi_403(setup, db, client_as):  # noqa: F811
    world, a1, _, _, tid = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    gen(a1, cid, tid)
    world.actor("a3").grant("labor_contract", "company", actions=("read",))
    reader = client_as(world.actor("a3"))
    assert reader.get(f"{CT_URL}/{cid}").status_code == 200
    res = reader.get(f"{CT_URL}/{cid}/document")
    assert res.status_code == 403 and "print" in res.json()["error"]["message"]
    assert reader.get(f"{CT_URL}/{cid}").json()["data"]["can_print"] is False


def test_tai_ban_sinh_khi_chua_sinh_404(setup):
    world, a1, _, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert a1.get(f"{CT_URL}/{cid}/document").status_code == 404
    assert a1.get(f"{CT_URL}/{cid}/signed-file").status_code == 404


def test_quyen_print_ngoai_pham_vi_van_404(setup, client_as):  # noqa: F811
    world, a1, make_client, _, tid = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    gen(a1, cid, tid)
    assert make_client(world.actor("b1")).get(f"{CT_URL}/{cid}/document").status_code == 404


def test_sinh_can_quyen_write(setup, client_as, db):  # noqa: F811
    world, a1, _, _, tid = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    world.actor("a3").grant("labor_contract", "company", actions=("read", "print"))
    assert gen(client_as(world.actor("a3")), cid, tid).status_code == 403


def test_sinh_body_sai_422(setup):
    world, a1, _, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    for body in ({}, {"template_id": 0}, {"template_id": -1}, {"template_id": "x"}, {"template_id": 1, "x": 1}):
        assert a1.post(f"{CT_URL}/{cid}/generate", json=body).status_code == 422, body


# ── Bản scan đã ký ────────────────────────────────────────────────────────────────────
def test_tai_ban_scan_pdf_va_png_khi_nhap_va_da_ky_thay_ban_cu_xoa_ban_cu(setup, db):
    world, a1, _, storage, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    up = a1.put(f"{CT_URL}/{cid}/signed-file", files={"file": ("scan.pdf", PDF_BYTES, "application/pdf")})
    assert up.status_code == 200 and up.json()["data"]["has_signed_file"] is True
    row = db.get(LaborContract, cid)
    first = row.signed_file_id
    assert a1.get(f"{CT_URL}/{cid}/signed-file").content == PDF_BYTES
    a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 2, "date": "2026-01-05"})   # DRAFT → SIGNED không cần tệp
    assert a1.put(f"{CT_URL}/{cid}/signed-file", files={"file": ("scan.png", PNG_BYTES, "image/png")}).status_code == 200
    db.refresh(row)
    assert row.signed_file_id != first and db.get(StoredFile, first) is None
    got = a1.get(f"{CT_URL}/{cid}/signed-file")
    assert got.content == PNG_BYTES and got.headers["content-type"] == "image/png"


@pytest.mark.parametrize("filename,data,status", [
    pytest.param("scan.pdf", b"khong phai pdf", 400, id="pdf-gia"),
    pytest.param("scan.png", PDF_BYTES, 400, id="png-ma-ruot-pdf"),
    pytest.param("scan.svg", b"<svg onload=alert(1)/>", 400, id="svg-xss"),
    pytest.param("scan.docx", b"PK\x03\x04", 400, id="sai-loai"),
    pytest.param("scan.exe", b"MZ", 400, id="exe"),
    pytest.param("scan.pdf", b"", 400, id="rong"),
    pytest.param("scan.pdf", PDF_BYTES + b"\x00" * (51 * 1024 * 1024), 400, id="vuot-50MB"),
])
def test_scan_gia_hoac_xau_bi_tu_choi_khong_ghi_gi(setup, db, filename, data, status):
    world, a1, _, storage, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    before = dict(storage)
    res = a1.put(f"{CT_URL}/{cid}/signed-file", files={"file": (filename, data, "application/octet-stream")})
    assert res.status_code == status, res.text
    assert storage == before and db.get(LaborContract, cid).signed_file_id == 0


def test_ten_scan_qua_dai_duoc_cat_ngan_nhung_giu_duoi_tep(setup, db):
    world, a1, _, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    res = a1.put(f"{CT_URL}/{cid}/signed-file", files={"file": ("a" * 400 + ".pdf", PDF_BYTES, "application/pdf")})
    assert res.status_code == 200
    stored = db.get(StoredFile, db.get(LaborContract, cid).signed_file_id)
    assert stored.filename.endswith(".pdf") and len(stored.filename) <= 150


def test_khong_tai_scan_khi_da_huy_hoac_da_cham_dut_409(setup):
    world, a1, _, _, _ = setup
    cancelled = make_contract(a1, world.emp["a2"], contract_no="C")["id"]
    a1.post(f"{CT_URL}/{cancelled}/transition", json={"to_status": 5, "reason": "nhầm"})
    terminated = make_contract(a1, world.emp["a3"], contract_no="T")["id"]
    a1.post(f"{CT_URL}/{terminated}/transition", json={"to_status": 2, "date": "2026-01-05"})
    a1.post(f"{CT_URL}/{terminated}/transition", json={"to_status": 4, "date": "2026-06-01", "reason": "x"})
    for cid in (cancelled, terminated):
        res = a1.put(f"{CT_URL}/{cid}/signed-file", files={"file": ("s.pdf", PDF_BYTES, "application/pdf")})
        assert res.status_code == 409


def test_xoa_hd_nhap_don_ca_hai_tep(setup, db):
    world, a1, _, storage, tid = setup
    base = len(storage)
    cid = make_contract(a1, world.emp["a2"])["id"]
    gen(a1, cid, tid)
    a1.put(f"{CT_URL}/{cid}/signed-file", files={"file": ("s.pdf", PDF_BYTES, "application/pdf")})
    assert len(storage) == base + 2
    assert a1.delete(f"{CT_URL}/{cid}").status_code == 200
    assert len(storage) == base and db.query(StoredFile).count() == 1


# ── Tên tệp: chặn header injection / path traversal ───────────────────────────────────
@pytest.mark.parametrize("raw", [
    "../../etc/passwd", "a\r\nSet-Cookie: x=1", "a\x00b", 'a"b', "a/b\\c", "..", "", "   ", "***", "x" * 1000,
])
def test_ten_tep_tai_ve_luon_sach(raw):
    clean = safe_filename(raw)
    assert clean and len(clean) <= 150
    assert not any(ch in clean for ch in '/\\\r\n\x00"')      # không còn dấu phân cách đường dẫn / xuống dòng / nháy
    assert clean not in (".", "..")


def test_cat_ten_dai_giu_duoi_tep():
    assert safe_filename("a" * 400 + ".pdf").endswith(".pdf") and len(safe_filename("a" * 400 + ".pdf")) == 150
    assert len(safe_filename("b" * 400)) == 150          # không có đuôi thì chỉ cắt


def test_ten_tep_giu_chu_tieng_viet_va_dau_gach():
    assert safe_filename("HDLD-001-Nguyễn Văn Ân") == "HDLD-001-Nguyễn Văn Ân"


def test_tai_ve_header_khong_chua_xuong_dong_du_ho_ten_doc_hai(setup, db):
    world, a1, _, _, tid = setup
    db.get(Employee, world.emp["a2"]).full_name = 'An\r\nX-Evil: 1"; filename="a.exe'
    db.commit()
    cid = make_contract(a1, world.emp["a2"])["id"]
    gen(a1, cid, tid)
    res = a1.get(f"{CT_URL}/{cid}/document")
    assert res.status_code == 200 and "x-evil" not in {k.lower() for k in res.headers}
    assert "\n" not in res.headers["content-disposition"] and ".exe" not in res.headers["content-disposition"].split("''")[0]


def test_loi_kho_luu_tru_tra_502_khong_phai_500(setup, monkeypatch):
    world, a1, _, _, tid = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    gen(a1, cid, tid)

    def down(_key):
        raise ConnectionError("R2 timeout")

    monkeypatch.setattr(file_response, "download_bytes", down)
    assert a1.get(f"{CT_URL}/{cid}/document").status_code == 502


@pytest.mark.parametrize("contract_no,expected", [
    ("", "HDLD005.docx"),             # để trống → mã hệ thống, không thành HDLD-HDLD005
    ("HDLD-CHROME-01", "HDLD-CHROME-01.docx"),
    ("hdld-12", "hdld-12.docx"),      # so không phân biệt hoa thường
    ("12/2026", "HDLD-12-2026.docx"),  # số tự gõ không có tiền tố thì vẫn thêm cho dễ nhận
])
def test_ten_tep_khong_lap_tien_to_hdld(db, contract_no, expected):
    """Lỗi thật (test Chrome 06/10): tải về ra `HDLD-HDLD-CHROME-01-….docx` và `HDLD-HDLD005-….docx`."""
    from app.modules.labor_contract.generate_service import document_filename
    row = LaborContract(code="HDLD005", contract_no=contract_no, employee_id=0)
    #  Không có hồ sơ nhân sự (employee_id=0) nên không có phần họ tên ở đuôi.
    assert document_filename(db, row) == expected
