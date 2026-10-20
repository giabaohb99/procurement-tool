"""duoc-CR-652 — «Hợp đồng của tôi»: nhân sự TỰ XEM HĐLĐ của chính mình (chỉ đọc), kể cả tệp mềm / bản ký và
bản lưu trữ ở Văn bản. Mỗi luật chặn có cặp đối chứng để chứng minh «chặn đúng chỗ» chứ không «chặn tất»."""
from datetime import date

import pytest

from app.core.auth import get_perm_profile
from app.core.config import settings as core_settings
from app.modules.doc_catalog.model import DocType
from app.modules.document import access_service
from app.modules.document.model import Document
from app.modules.labor_contract.model import LaborContract
from app.modules.user.model import User
from hdld_factory import PDF_BYTES, client_as, grant_all, make_contract, storage, upload_template  # noqa: F401

CT_URL = "/api/labor-contracts"
ME_URL = "/api/me/labor-contracts"


@pytest.fixture(autouse=True)
def _sync_index(monkeypatch):
    monkeypatch.setattr(core_settings, "DOCUMENT_SEARCH_INDEX_SYNC", True)


@pytest.fixture
def ctx(db, world, storage, client_as):  # noqa: F811
    """a1 = Nhân sự (đủ quyền HĐLĐ, công ty A); a2 / a3 = nhân viên thường, KHÔNG có `labor_contract`,
    nhưng đọc được Văn bản công ty. a2 có hợp đồng; a3 là «người khác»."""
    grant_all(world, "a1")
    world.grant("a1", "document", "own", actions=("read",))
    for k in ("a2", "a3"):
        world.grant(k, "document", "company", actions=("read",))
    db.add(DocType(code="HDLD", name="Hợp đồng lao động", id_scheme=2, number_when=2,
                   is_personal=True, needs_approval=False, needs_signature=False))
    db.commit()
    hr = client_as(world.actor("a1"))
    tpl = upload_template(hr, company_id=world.co["A"]).json()["data"]["id"]

    def new(emp_key, *, generate=True, sign=None, **over):
        """Lập HĐ; `sign` = None giữ Nháp, 'signed' = ký, 'terminated' = ký rồi chấm dứt."""
        cid = make_contract(hr, world.emp[emp_key], **over)["id"]
        if generate:
            assert hr.post(f"{CT_URL}/{cid}/generate", json={"template_id": tpl}).status_code == 200
        if sign:
            assert hr.put(f"{CT_URL}/{cid}/signed-file",
                          files={"file": ("ky.pdf", PDF_BYTES, "application/pdf")}).status_code == 200
            assert hr.post(f"{CT_URL}/{cid}/transition", json={"to_status": 2, "date": "2026-01-05"}).status_code == 200
        if sign == "terminated":
            assert hr.post(f"{CT_URL}/{cid}/transition",
                           json={"to_status": 4, "date": "2026-06-01", "reason": "Nghỉ việc"}).status_code == 200
        return cid

    return {"world": world, "db": db, "hr": hr, "new": new,
            "a2": client_as(world.actor("a2")), "a3": client_as(world.actor("a3")), "client_as": client_as}


def _mine(client):
    res = client.get(ME_URL)
    assert res.status_code == 200, res.text
    return res.json()["data"]["items"]


def _doc(db, cid):
    db.expire_all()
    return db.get(Document, db.get(LaborContract, cid).document_id)


def _can(ctx, key, doc, action="read"):
    world, db = ctx["world"], ctx["db"]
    a = world.actor(key)
    return access_service.can(db, doc, a.user, get_perm_profile(db, a.user), action)


# ── Danh sách ────────────────────────────────────────────────────────────────────────────────
def test_hop_dong_da_ky_cua_minh_hien_kem_luong_va_co_tep(ctx):
    cid = ctx["new"]("a2", sign="signed")
    items = _mine(ctx["a2"])
    assert [i["id"] for i in items] == [cid]
    it = items[0]
    assert it["base_salary"] == 15_000_000 and it["status"] == 2
    assert it["has_generated_file"] and it["has_signed_file"]
    #  không lộ trường nội bộ / id tệp / url
    assert not {"custom_values", "file_key", "url", "generated_file_id", "signed_file_id", "note",
                "employee_id", "created_by_name"} & set(it)


def test_da_cham_dut_va_het_han_van_hien(ctx, db):
    done = ctx["new"]("a2", sign="terminated", start_date="2025-01-01", end_date="2025-12-31")
    expired = ctx["new"]("a2", sign="signed", start_date="2020-01-01", end_date="2020-12-31")
    by_id = {i["id"]: i for i in _mine(ctx["a2"])}
    assert by_id[done]["effective_status"] == 4
    assert by_id[expired]["status"] == 2 and by_id[expired]["effective_status"] == 3


def test_nhap_va_da_huy_khong_hien(ctx):
    draft = ctx["new"]("a2")
    cancelled = ctx["new"]("a2")
    assert ctx["hr"].post(f"{CT_URL}/{cancelled}/transition",
                          json={"to_status": 5, "reason": "Nhập nhầm"}).status_code == 200
    signed = ctx["new"]("a2", sign="signed")
    assert [i["id"] for i in _mine(ctx["a2"])] == [signed]
    for cid in (draft, cancelled):   # tải thẳng theo id cũng 404
        assert ctx["a2"].get(f"{ME_URL}/{cid}/document").status_code == 404
        assert ctx["a2"].get(f"{ME_URL}/{cid}/signed-file").status_code == 404


def test_da_xoa_mem_khong_hien(ctx, db):
    cid = ctx["new"]("a2", sign="signed")
    db.get(LaborContract, cid).is_deleted = True
    db.commit()
    assert _mine(ctx["a2"]) == []
    assert ctx["a2"].get(f"{ME_URL}/{cid}/document").status_code == 404


def test_hop_dong_nguoi_khac_khong_thay_va_404(ctx):
    other = ctx["new"]("a3", sign="signed")
    assert _mine(ctx["a2"]) == []
    for suffix in ("document", "signed-file"):
        assert ctx["a2"].get(f"{ME_URL}/{other}/{suffix}").status_code == 404
    #  đối chứng: chính chủ tải được
    assert ctx["a3"].get(f"{ME_URL}/{other}/document").status_code == 200


def test_khong_co_tham_so_chon_nguoi(ctx):
    ctx["new"]("a3", sign="signed")
    assert _mine_with(ctx["a2"], {"employee_id": ctx["world"].emp["a3"]}) == []


def _mine_with(client, params):
    res = client.get(ME_URL, params=params)
    assert res.status_code == 200
    return res.json()["data"]["items"]


def test_tai_khoan_khong_gan_nhan_su_ra_rong_khong_khop_employee_id_0(ctx, db):
    #  HĐ mồ côi employee_id = 0 ĐÃ KÝ — tài khoản employee_id = 0 tuyệt đối không được thấy.
    db.add(LaborContract(code="HDLD-ZERO", employee_id=0, contract_type=2, status=2,
                         start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), generated_file_id=1,
                         signed_file_id=1, created_by=1, updated_by=1))
    user = User(email="khonggan", employee_id=0, password_hash="x", is_active=True)
    db.add(user)
    db.commit()
    cl = ctx["client_as"](user)
    assert _mine(cl) == []
    zero = db.query(LaborContract).filter_by(code="HDLD-ZERO").one().id
    assert cl.get(f"{ME_URL}/{zero}/document").status_code == 404
    assert cl.get(f"{ME_URL}/{zero}/signed-file").status_code == 404


# ── Tải tệp ─────────────────────────────────────────────────────────────────────────────────
def test_tai_ban_mem_va_ban_ky_cua_minh(ctx):
    cid = ctx["new"]("a2", sign="signed")
    doc = ctx["a2"].get(f"{ME_URL}/{cid}/document")
    assert doc.status_code == 200 and doc.content[:2] == b"PK"
    assert "attachment" in doc.headers["content-disposition"]
    signed = ctx["a2"].get(f"{ME_URL}/{cid}/signed-file")
    assert signed.status_code == 200 and signed.content == PDF_BYTES


def test_thieu_tep_thi_404(ctx):
    cid = ctx["new"]("a2", generate=False, sign="signed")
    it = _mine(ctx["a2"])[0]
    assert not it["has_generated_file"] and it["has_signed_file"]
    assert ctx["a2"].get(f"{ME_URL}/{cid}/document").status_code == 404
    assert ctx["a2"].get(f"{ME_URL}/{cid}/signed-file").status_code == 200


def test_chi_doc_khong_co_duong_ghi(ctx):
    cid = ctx["new"]("a2", sign="signed")
    a2 = ctx["a2"]
    assert a2.post(ME_URL, json={}).status_code == 405
    assert a2.put(f"{ME_URL}/{cid}/signed-file", files={"file": ("x.pdf", PDF_BYTES, "application/pdf")}).status_code == 405
    assert a2.delete(f"{ME_URL}/{cid}").status_code in (404, 405)
    #  và không mở cửa HR cho chính chủ
    assert a2.get(f"{CT_URL}/{cid}").status_code == 403
    assert a2.post(f"{CT_URL}/{cid}/transition", json={"to_status": 4}).status_code == 403


# ── Bản lưu trữ ở Văn bản ────────────────────────────────────────────────────────────────────
def test_chu_hop_dong_doc_duoc_ban_luu_tru_khi_da_ky(ctx):
    cid = ctx["new"]("a2", sign="signed")
    d = _doc(ctx["db"], cid)
    assert _can(ctx, "a2", d, "read")
    a2 = ctx["a2"]
    assert a2.get(f"/api/documents/{d.id}").status_code == 200
    res = a2.get("/api/documents", params={"page_size": 100})
    assert d.id in {r["id"] for r in res.json()["data"]["items"]}
    #  người khác cùng công ty (cũng document.read 'company') KHÔNG thấy
    assert not _can(ctx, "a3", d, "read")
    assert ctx["a3"].get(f"/api/documents/{d.id}").status_code == 404


def test_chu_hop_dong_doc_duoc_ban_luu_tru_khi_cham_dut(ctx):
    d = _doc(ctx["db"], ctx["new"]("a2", sign="terminated"))
    assert _can(ctx, "a2", d, "read")


def test_ban_luu_tru_nhap_chu_khong_doc_duoc(ctx):
    d = _doc(ctx["db"], ctx["new"]("a2"))
    assert not _can(ctx, "a2", d, "read")
    assert ctx["a2"].get(f"/api/documents/{d.id}").status_code == 404


def test_ban_luu_tru_da_huy_hoac_xoa_mem_chu_khong_doc_duoc(ctx, db):
    cid = ctx["new"]("a2", sign="signed")
    d = _doc(db, cid)
    assert _can(ctx, "a2", d, "read")
    db.get(LaborContract, cid).is_deleted = True
    db.commit()
    assert not _can(ctx, "a2", d, "read")


def test_chu_hop_dong_khong_bao_gio_ghi_hay_xoa_ban_luu_tru(ctx):
    world = ctx["world"]
    #  kể cả khi cấp cho a2 document.write ở mọi phạm vi
    world.grant("a2", "document", "all", actions=("read", "write", "delete", "create"))
    d = _doc(ctx["db"], ctx["new"]("a2", sign="signed"))
    assert _can(ctx, "a2", d, "read")
    for action in ("write", "delete", "approve"):
        assert not _can(ctx, "a2", d, action), action
    a2 = ctx["a2"]
    assert a2.patch(f"/api/documents/{d.id}", json={"note": "sửa"}).status_code in (403, 404, 409)
    assert a2.delete(f"/api/documents/{d.id}").status_code in (403, 404, 409)
    assert a2.get(f"/api/documents/{d.id}/permissions").json()["data"].get("can_write") in (False, None)


def test_quyen_hr_khong_doi(ctx):
    cid = ctx["new"]("a3", sign="signed")
    d = _doc(ctx["db"], cid)
    assert _can(ctx, "a1", d, "read") and not _can(ctx, "a1", d, "delete")
    assert ctx["hr"].get(f"{CT_URL}/{cid}").status_code == 200
    assert ctx["hr"].get(f"{CT_URL}/{cid}/signed-file").status_code == 200
    #  HR vẫn thấy cả HĐ Nháp ở đường HR
    draft = ctx["new"]("a3")
    assert ctx["hr"].get(f"{CT_URL}/{draft}").status_code == 200
    assert not _can(ctx, "a3", _doc(ctx["db"], draft), "read")


def test_nhat_ky_khong_mo_cho_chu_hop_dong(ctx):
    from app.modules.document import labor_contract_archive_access as lca
    db, world = ctx["db"], ctx["world"]
    d = _doc(db, ctx["new"]("a2", sign="signed"))
    a2 = world.actor("a2")
    viewer = (a2.user, get_perm_profile(db, a2.user))
    assert d.id in lca.blocked_archive_doc_ids(db, viewer, [d.id])


def test_logging_policy_che_luong_cho_duong_cua_toi():
    from app.core.logging_policy import sensitive_keys_for_path
    assert {"base_salary", "custom_values"} <= sensitive_keys_for_path(ME_URL)
    assert {"base_salary"} <= sensitive_keys_for_path(f"{ME_URL}/5/document")
