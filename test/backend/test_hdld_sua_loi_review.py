"""Hồi quy cho các lỗi review HĐLĐ (05/10/2026): H1 phạm vi own, H2 DoS bộ nhớ, M1 ô chọn mẫu theo HĐ,
M2 tệp sinh cũ sau khi sửa, M3 che lương ở nhật ký thay đổi, M4 khóa dòng, L2 liên kết ngoài / nhúng,
L3 thứ tự kiểm phạm vi khi tải mẫu.

Góc nhìn kẻ phá: người phạm vi `own` lập HĐ / tải mẫu sang pháp nhân khác, tệp .docx khai man vài
nghìn biến, móc liên kết ngoài, sửa HĐ rồi tải bản sinh cũ.
"""
import time
import uuid
import zipfile
from io import BytesIO

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.logging_codes import ACTOR_KIND_USER
from app.core.logging_policy import MASKED
from app.core.request_context import RequestContext, reset_context, set_context
from app.modules.employee.model import Employee
from app.modules.labor_contract import docx_engine
from app.modules.labor_contract.docx_engine import TemplateRejected
from app.modules.labor_contract.model import LaborContract
from app.modules.labor_contract.placeholder_catalog import sample_context
from hdld_factory import (client_as, contract_payload, grant_all, make_contract, make_docx,  # noqa: F401
                          storage, upload_template)

CT_URL = "/api/labor-contracts"
EMP_URL = "/api/employees/{}/labor-contracts"


@pytest.fixture
def setup(db, world, storage, client_as):  # noqa: F811
    grant_all(world, "a1")
    grant_all(world, "b1")
    return world, client_as(world.actor("a1")), client_as, storage


def _employee_b(db, world, code="B_X") -> int:
    emp = Employee(code=code, full_name="Đồng nghiệp B", company_id=world.co["B"],
                   department_id=world.dept["B.kt"], is_active=True)
    db.add(emp)
    db.commit()
    return emp.id


def _rewrap(data: bytes, extra: dict[str, bytes]) -> bytes:
    out = BytesIO()
    with zipfile.ZipFile(BytesIO(data)) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            dst.writestr(info.filename, src.read(info.filename))
        for name, body in extra.items():
            dst.writestr(name, body)
    return out.getvalue()


# ── H1: phạm vi own không được mở rộng thành «lập cho bất kỳ ai» ───────────────────────
@pytest.fixture
def own_user(db, world, storage, client_as):  # noqa: F811
    """a3 (pháp nhân A) chỉ có phạm vi `own` trên cả hai khóa."""
    grant_all(world, "a3", scope="own")
    return client_as(world.actor("a3"))


def test_own_khong_lap_duoc_hd_cho_nhan_su_phap_nhan_khac(setup, own_user, db):
    world, _, _, _ = setup
    res = own_user.post(EMP_URL.format(_employee_b(db, world)), json=contract_payload())
    assert res.status_code == 403 and db.query(LaborContract).count() == 0


def test_own_khong_lap_duoc_ca_cho_dong_nghiep_cung_phap_nhan(setup, own_user, db):
    world, _, _, _ = setup
    assert own_user.post(EMP_URL.format(world.emp["a2"]), json=contract_payload()).status_code == 403
    assert db.query(LaborContract).count() == 0


def test_own_o_chon_mau_cua_nhan_su_phap_nhan_khac_403(setup, own_user, db):
    world, _, _, _ = setup
    url = f"/api/employees/{_employee_b(db, world)}/labor-contract-templates"
    assert own_user.get(url).status_code == 403


def test_own_tai_mau_vao_phap_nhan_khac_403_nhung_phap_nhan_cua_minh_van_duoc(setup, own_user, db):
    """`own` của mẫu rơi về `company` (không `owner`/`self`): pháp nhân MÌNH được, pháp nhân khác thì 403."""
    world, _, _, _ = setup
    assert upload_template(own_user, company_id=world.co["B"]).status_code == 403
    assert upload_template(own_user, company_id=world.co["A"]).status_code == 201


def test_khong_tu_lap_hd_cho_chinh_minh_du_co_quyen_company(setup, db):
    world, a1, _, _ = setup
    res = a1.post(EMP_URL.format(world.emp["a1"]), json=contract_payload())
    assert res.status_code == 403 and "chính mình" in res.json()["error"]["message"]
    assert db.query(LaborContract).count() == 0
    assert a1.get(f"/api/employees/{world.emp['a1']}/labor-contract-templates").status_code == 403


def test_tai_khoan_chua_gan_ho_so_o_phap_vi_own_khong_thay_gi(setup, db, world, client_as):  # noqa: F811
    """Không `owner` → `own` chỉ còn nhánh `self`; thiếu hồ sơ nhân sự thì CHẶN HẾT chứ không mở."""
    boss = setup[1]
    make_contract(boss, world.emp["a2"])
    actor = world.actor("khongcty")
    actor.grant("labor_contract", "own", actions=("read",))
    actor.user.employee_id = 0
    db.commit()
    assert client_as(actor).get(EMP_URL.format(world.emp["a2"])).json()["data"]["items"] == []


# ── H2 / L2: gói .docx độc hại bị từ chối nhanh, TRƯỚC khi Jinja chạy ─────────────────
def _many_placeholders(n: int) -> bytes:
    return make_docx(*["{{ ho_ten }}"] * n)


def test_1500_bien_bi_tu_choi_nhanh(setup):
    world, a1, _, _ = setup
    data = _many_placeholders(1500)
    started = time.monotonic()
    res = upload_template(a1, company_id=world.co["A"], data=data)
    assert res.status_code == 422 and "quá nhiều" in res.json()["error"]["message"]
    assert time.monotonic() - started < 2


def test_dung_tran_1000_bien_van_nhan():
    assert docx_engine.inspect_template(_many_placeholders(1000)) == ["ho_ten"]


def test_bien_bi_tach_run_van_bi_dem():
    """Word hay tách `{{` thành hai run — đếm `{` thô nên không lọt ca tách."""
    xml = b"<w:r><w:t>{</w:t></w:r><w:r><w:t>{ ho_ten }}</w:t></w:r>" * 1500
    data = _rewrap(make_docx("x"), {"word/extra.xml": xml})
    with pytest.raises(TemplateRejected, match="quá nhiều"):
        docx_engine.check_package(data)


def test_phan_xml_qua_5mb_bi_tu_choi_du_nen_rat_nho():
    data = _rewrap(make_docx("x"), {"word/big.xml": b" " * (6 * 1024 * 1024)})
    assert len(data) < 100_000
    with pytest.raises(TemplateRejected, match="quá lớn"):
        docx_engine.check_package(data)


def test_render_luc_sinh_cung_kiem_lai_tep_luu_bi_thay():
    with pytest.raises(TemplateRejected, match="quá nhiều"):
        docx_engine.render(_many_placeholders(1500), sample_context())


@pytest.mark.parametrize("name,body", [
    ("word/_rels/document.xml.rels",
     b'<Relationships xmlns="x"><Relationship Id="r9" Type="t" Target="http://evil.test/a" '
     b'TargetMode="External"/></Relationships>'),
    ("word/embeddings/oleObject1.bin", b"\x00"),
    ("word/oleObject2.bin", b"\x00"),
])
def test_lien_ket_ngoai_va_doi_tuong_nhung_bi_tu_choi(name, body):
    base = make_docx("{{ ho_ten }}")
    if name.endswith(".rels"):   # ghi đè rels sẵn có bằng bản có liên kết ngoài
        out = BytesIO()
        with zipfile.ZipFile(BytesIO(base)) as src, zipfile.ZipFile(out, "w") as dst:
            for info in src.infolist():
                if info.filename != name:
                    dst.writestr(info.filename, src.read(info.filename))
            dst.writestr(name, body)
        data = out.getvalue()
    else:
        data = _rewrap(base, {name: body})
    with pytest.raises(TemplateRejected):
        docx_engine.check_package(data)


def test_mau_sach_khong_bi_chan_nham():
    docx_engine.check_package(make_docx("Xin chào {{ ho_ten }}"))


# ── M1: ô chọn mẫu theo HĐ, không theo pháp nhân hiện tại của nhân sự ──────────────────
def test_o_chon_mau_theo_hd_van_ra_mau_cu_sau_khi_nhan_su_chuyen_phap_nhan(setup, db):
    world, a1, make_client, _ = setup
    tid_a = upload_template(a1, company_id=world.co["A"], name="Mẫu A").json()["data"]["id"]
    upload_template(a1, company_id=world.co["A"], name="Khác loại", contract_type=1)
    off = upload_template(a1, company_id=world.co["A"], name="Ngừng").json()["data"]["id"]
    a1.patch(f"/api/labor-contract-templates/{off}", json={"is_active": False})
    upload_template(make_client(world.actor("b1")), company_id=world.co["B"], name="Mẫu B")
    cid = make_contract(a1, world.emp["a2"])["id"]
    db.get(Employee, world.emp["a2"]).company_id = world.co["B"]
    db.commit()
    res = a1.get(f"{CT_URL}/{cid}/templates")
    assert res.status_code == 200
    assert res.json()["data"] == [{"id": tid_a, "name": "Mẫu A", "contract_type": 2}]
    # sinh được bằng đúng mẫu mà ô chọn đưa ra
    assert a1.post(f"{CT_URL}/{cid}/generate", json={"template_id": tid_a}).status_code == 200


def test_o_chon_mau_theo_hd_tuan_thu_pham_vi_va_quyen(setup, db, world, client_as):  # noqa: F811
    _, a1, make_client, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert make_client(world.actor("b1")).get(f"{CT_URL}/{cid}/templates").status_code == 404
    world.actor("a3").grant("labor_contract", "company", actions=("read",))
    assert client_as(world.actor("a3")).get(f"{CT_URL}/{cid}/templates").status_code == 403
    assert a1.get(f"{CT_URL}/999999/templates").status_code == 404


# ── M2: sửa nội dung HĐ thì tệp đã sinh thành bản cũ → bỏ ──────────────────────────────
def _generated(setup):
    world, a1, _, storage = setup
    tid = upload_template(a1, company_id=world.co["A"]).json()["data"]["id"]
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert a1.post(f"{CT_URL}/{cid}/generate", json={"template_id": tid}).status_code == 200
    return a1, cid, storage


def test_sua_noi_dung_xoa_tep_da_sinh_va_goi_y_sinh_lai(setup, db):
    a1, cid, storage = _generated(setup)
    old_id = db.get(LaborContract, cid).generated_file_id
    files_before = len(storage)
    res = a1.patch(f"{CT_URL}/{cid}", json={"base_salary": 99_000_000})
    item = res.json()["data"]["item"]
    assert res.status_code == 200 and item["has_generated_file"] is False
    assert item["generated_at"] is None and item["template_id"] == 0
    assert a1.get(f"{CT_URL}/{cid}/document").status_code == 404
    assert len(storage) == files_before - 1 and old_id
    assert item["can_generate"] is True


def test_sua_trung_gia_tri_cu_khong_lam_mat_tep(setup, db):
    a1, cid, storage = _generated(setup)
    cur = a1.get(f"{CT_URL}/{cid}").json()["data"]
    res = a1.patch(f"{CT_URL}/{cid}", json={"base_salary": cur["base_salary"], "note": cur["note"]})
    assert res.json()["data"]["item"]["has_generated_file"] is True
    assert a1.get(f"{CT_URL}/{cid}/document").status_code == 200


@pytest.mark.parametrize("field,value", [("note", "ghi chú mới"), ("job_title", "Chức danh mới"),
                                          ("allowance_note", "Phụ cấp mới"), ("end_date", "2027-06-30")])
def test_moi_truong_di_vao_mau_deu_lam_het_han_tep(setup, field, value):
    a1, cid, _ = _generated(setup)
    item = a1.patch(f"{CT_URL}/{cid}", json={field: value}).json()["data"]["item"]
    assert item["has_generated_file"] is False


# ── M3: lương không lọt vào nhật ký thay đổi ───────────────────────────────────────────
@pytest.fixture
def ctx(db, monkeypatch):
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)
    context = RequestContext(request_id=uuid.uuid4().bytes, user_id=7, actor_kind=ACTOR_KIND_USER)
    token = set_context(context)
    try:
        yield context
    finally:
        reset_context(token)


def test_nhat_ky_thay_doi_khong_chua_gia_tri_luong(db, world, ctx):
    from datetime import date

    ctx.changes = []
    row = LaborContract(code="HDLD_LOG", employee_id=world.emp["a2"], company_id=world.co["A"],
                        contract_type=2, status=1, start_date=date(2026, 1, 1),
                        base_salary=12_345_678, insurance_salary=8_765_432, allowance=111_222,
                        allowance_note="Xăng xe bí mật", job_title="Kế toán", created_by=1, updated_by=1)
    db.add(row)
    db.commit()
    snap = next(e for e in ctx.changes if e.table_name == "tab_labor_contract").snapshot
    for col in ("base_salary", "insurance_salary", "allowance", "allowance_note"):
        assert snap[col] == MASKED
    assert snap["job_title"] == "Kế toán"           # cột thường vẫn giữ để tra

    ctx.changes = []
    row.base_salary = 99_999_999
    row.job_title = "Trưởng phòng"
    db.commit()
    fields = {e.field: e for e in ctx.changes if e.table_name == "tab_labor_contract"}
    assert fields["base_salary"].is_masked and fields["base_salary"].after_value is None
    assert fields["job_title"].after_value == "Trưởng phòng"
    assert "99999999" not in repr([(e.before_value, e.after_value, e.snapshot) for e in ctx.changes])


# ── M4: đường ghi khóa dòng HĐ ─────────────────────────────────────────────────────────
def test_cac_duong_ghi_deu_khoa_dong(setup, monkeypatch):
    from sqlalchemy.orm import Query

    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    calls = []
    original = Query.with_for_update

    def spy(self, *a, **kw):
        calls.append(1)
        return original(self, *a, **kw)

    monkeypatch.setattr(Query, "with_for_update", spy)
    steps = [
        ("patch", f"{CT_URL}/{cid}", {"json": {"note": "x"}}),
        ("put", f"{CT_URL}/{cid}/signed-file",
         {"files": {"file": ("a.pdf", b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF", "application/pdf")}}),
        ("post", f"{CT_URL}/{cid}/transition", {"json": {"to_status": 5, "reason": "x"}}),
        ("delete", f"{CT_URL}/{cid}", {}),
    ]
    for method, path, kw in steps:
        before = len(calls)
        res = getattr(a1, method)(path, **kw)
        assert res.status_code == 200, f"{method} {path}: {res.text}"
        assert len(calls) > before, f"{method} {path} không khóa dòng"


def test_duong_ghi_tren_hd_vua_bi_xoa_van_404(setup):
    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert a1.delete(f"{CT_URL}/{cid}").status_code == 200
    assert a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 5, "reason": "x"}).status_code == 404


# ── L3: ngoài phạm vi thì 403, không lộ «pháp nhân không tồn tại» / «trùng tên» ────────
def test_tai_mau_ngoai_pham_vi_403_ke_ca_khi_ten_trung_hoac_phap_nhan_khong_ton_tai(setup):
    world, a1, make_client, _ = setup
    assert upload_template(make_client(world.actor("b1")), company_id=world.co["B"], name="Tên B").status_code == 201
    assert upload_template(a1, company_id=world.co["B"], name="Tên B").status_code == 403   # trùng tên nhưng ngoài phạm vi
    assert upload_template(a1, company_id=999_999).status_code == 403
    assert upload_template(a1, company_id=world.co["A"], name="Tên B").status_code == 201


def test_nguoi_pham_vi_all_van_nhan_400_khi_phap_nhan_khong_ton_tai(db, world, storage, client_as):  # noqa: F811
    grant_all(world, "a1", scope="all")
    assert upload_template(client_as(world.actor("a1")), company_id=999_999).status_code == 400
