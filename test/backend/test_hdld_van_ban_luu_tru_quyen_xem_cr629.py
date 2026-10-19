"""duoc-CR-629 — ai ĐỌC được BẢN LƯU TRỮ HĐLĐ ở phân hệ Văn bản.

Luật: CHỈ người có `labor_contract.read` trong phạm vi của HĐ đó. Người lao động, văn thư (kể cả phạm vi
*tất cả*), admin không có `labor_contract`, người được chia đích danh, thành viên sổ — KHÔNG thấy ở đâu cả
(danh sách, chi tiết, tệp, tìm, tổng quan, trợ lý AI, ô chọn quan hệ). Bản lưu trữ chỉ đọc.

Mỗi bài có cặp đối chứng trên văn bản THƯỜNG để chứng minh «chặn đúng chỗ» chứ không «chặn tất».
"""
import pytest
from sqlalchemy import func

from app.core.auth import get_perm_profile
from app.core.config import settings as core_settings
from app.modules.assistant.tools.base import ToolContext
from app.modules.assistant.tools.document_tool import _run_document_search
from app.modules.attachment.model import FileLink
from app.modules.doc_catalog.book_model import DocumentBook, DocumentBookMember
from app.modules.doc_catalog.model import DocType
from app.modules.document import access_service, link_service, search_index_service, service as doc_service
from app.modules.document.access_model import EFFECT_ALLOW, SUBJECT_EMPLOYEE, DocumentAccess
from app.modules.document.model import STATUS_EFFECTIVE, Document
from app.modules.document.schema import DocumentCreate
from app.modules.document.search_model import DocumentSearch
from app.modules.document.service import ATTACH_ENTITY
from app.modules.labor_contract.model import LaborContract
from hdld_factory import client_as, grant_all, make_contract, storage, upload_template  # noqa: F401

CT_URL = "/api/labor-contracts"
ALL = ("read", "create", "write", "delete", "approve")


@pytest.fixture(autouse=True)
def _sync_index(monkeypatch):
    monkeypatch.setattr(core_settings, "DOCUMENT_SEARCH_INDEX_SYNC", True)


@pytest.fixture
def ctx(db, world, storage, client_as):  # noqa: F811
    """a1 = Nhân sự (HĐLĐ công ty A + document.read 'own'); a2 = người lao động (có hồ sơ, đọc Văn bản
    công ty); a3 = văn thư công ty A; khongphong = quản trị Văn bản phạm vi tất cả, KHÔNG có labor_contract;
    b1 = Nhân sự công ty B."""
    grant_all(world, "a1")
    world.grant("a1", "document", "own", actions=("read",))
    grant_all(world, "b1")
    world.grant("b1", "document", "company", actions=("read",))
    world.grant("a2", "document", "company", actions=("read",))
    world.grant("a3", "document", "company", actions=ALL)
    world.grant("khongphong", "document", "all", actions=ALL)
    loai = DocType(code="HDLD", name="Hợp đồng lao động", id_scheme=2, number_when=2,
                   is_personal=True, needs_approval=False, needs_signature=False)
    thuong = DocType(code="CV", name="Công văn", id_scheme=2, number_when=2, needs_approval=False)
    db.add_all([loai, thuong])
    db.commit()
    hr = client_as(world.actor("a1"))
    tpl = upload_template(hr, company_id=world.co["A"]).json()["data"]["id"]
    cid = make_contract(hr, world.emp["a2"], contract_no="HĐ-A2-TOPSECRET")["id"]
    hr.post(f"{CT_URL}/{cid}/generate", json={"template_id": tpl})
    db.expire_all()
    archive = db.get(Document, db.get(LaborContract, cid).document_id)
    normal = doc_service.create_document(db, DocumentCreate(
        doc_type_id=thuong.id, company_id=world.co["A"], department_id=world.dept["A.kt"],
        owner_employee_id=world.emp["a3"], title="Công văn HĐ-A2-TOPSECRET thường"), world.user_id("a3"))
    search_index_service.reindex(db, normal.id)
    clients = {k: client_as(world.actor(k)) for k in ("a1", "a2", "a3", "khongphong", "b1")}
    return {"world": world, "db": db, "archive": archive, "normal": normal, "cid": cid, "c": clients,
            "client_as": client_as, "thuong": thuong, "loai": loai}


def _ids(client, **q):
    res = client.get("/api/documents", params={"page_size": 100, **q})
    assert res.status_code == 200, res.text
    return {r["id"] for r in res.json()["data"]["items"]}


def _profile(world, key, db):
    a = world.actor(key)
    return a.user, get_perm_profile(db, a.user)


def test_hr_trong_pham_vi_doc_duoc_chi_doc(ctx):
    world, db, d = ctx["world"], ctx["db"], ctx["archive"]
    user, prof = _profile(world, "a1", db)
    assert access_service.can(db, d, user, prof, "read")
    for action in ("write", "delete"):
        assert not access_service.can(db, d, user, prof, action)
    assert d.id in _ids(ctx["c"]["a1"])
    assert ctx["c"]["a1"].get(f"/api/documents/{d.id}").status_code == 200
    # đối chứng: HR (document.read 'own') không thấy công văn thường của người khác
    assert ctx["normal"].id not in _ids(ctx["c"]["a1"])


def test_hr_phap_nhan_khac_khong_thay_404(ctx):
    d = ctx["archive"]
    assert d.id not in _ids(ctx["c"]["b1"])
    assert ctx["c"]["b1"].get(f"/api/documents/{d.id}").status_code == 404


def test_nguoi_lao_dong_khong_thay_ke_ca_la_chu_van_ban(ctx):
    world, db, d = ctx["world"], ctx["db"], ctx["archive"]
    d.owner_employee_id = world.emp["a2"]
    d.created_by = world.user_id("a2")
    db.commit()
    a2 = ctx["c"]["a2"]
    assert d.id not in _ids(a2)
    assert a2.get(f"/api/documents/{d.id}").status_code == 404
    assert ctx["normal"].id in _ids(a2)   # đối chứng: công văn thường cùng công ty vẫn thấy


@pytest.mark.parametrize("key", ["a3", "khongphong"])
def test_van_thu_ke_ca_pham_vi_tat_ca_khong_thay(ctx, key):
    d = ctx["archive"]
    cl = ctx["c"][key]
    assert d.id not in _ids(cl) and ctx["normal"].id in _ids(cl)
    assert cl.get(f"/api/documents/{d.id}").status_code == 404
    assert cl.get(f"/api/documents/{d.id}/versions").status_code == 404
    assert cl.get(f"/api/documents/{d.id}/attachments").status_code == 404
    assert cl.patch(f"/api/documents/{d.id}", json={"title": "x"}).status_code in (403, 404)
    assert cl.delete(f"/api/documents/{d.id}").status_code in (403, 404)


def test_chia_dich_danh_va_so_van_ban_khong_mo_khoa(ctx):
    world, db, d = ctx["world"], ctx["db"], ctx["archive"]
    db.add(DocumentAccess(document_id=d.id, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a3"],
                          effect=EFFECT_ALLOW, can_read=True, can_write=True, can_delete=True,
                          created_by=1, updated_by=1))
    book = DocumentBook(code="SO-NS", name="Sổ nhân sự", kind=3, company_id=world.co["A"],
                        created_by=1, updated_by=1)
    db.add(book)
    db.flush()
    db.add(DocumentBookMember(book_id=book.id, employee_id=world.emp["a3"], role=1, created_by=1, updated_by=1))
    d.book_id = book.id
    db.commit()
    a3 = ctx["c"]["a3"]
    assert d.id not in _ids(a3)
    assert a3.get(f"/api/documents/{d.id}").status_code == 404
    user, prof = _profile(world, "a3", db)
    assert not any(access_service.can(db, d, user, prof, a) for a in ("read", "write", "delete"))


def test_khong_vao_chi_muc_va_tim_kiem_khong_ra(ctx):
    db, d, n = ctx["db"], ctx["archive"], ctx["normal"]
    assert search_index_service.reindex(db, d.id) is None
    assert db.query(DocumentSearch).filter(DocumentSearch.document_id == d.id).count() == 0
    # dù ai đó nhét dòng chỉ mục vào tay, lọc quyền vẫn chặn văn thư
    db.add(DocumentSearch(document_id=d.id, meta_text="topsecret", body_text="", file_text="",
                          file_text_raw="", file_names="", source_hash="x"))
    db.commit()
    res = ctx["c"]["a3"].get("/api/documents/search", params={"q": "TOPSECRET"})
    assert res.status_code == 200, res.text
    found = {r["id"] if "id" in r else r["document_id"] for r in res.json()["data"]["items"]}
    assert n.id in found and d.id not in found
    # khi lưu lại, reindex gỡ luôn dòng chỉ mục
    assert search_index_service.reindex(db, d.id) is None
    assert db.query(DocumentSearch).filter(DocumentSearch.document_id == d.id).count() == 0


def test_tai_tep_hr_duoc_van_thu_404(ctx, storage, monkeypatch):   # noqa: F811
    db, d = ctx["db"], ctx["archive"]
    #  Kho giả của `hdld_factory` không phủ đường đọc byte của `/api/attachments` → trỏ nó vào cùng kho giả.
    monkeypatch.setattr("app.modules.attachment.controller.read_file_bytes", lambda f: storage[f.file_key])
    link = db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY,
                                     FileLink.entity_id == d.current_version_id).one()
    assert ctx["c"]["a1"].get(f"/api/attachments/{link.id}/download").status_code == 200
    for key in ("a3", "khongphong", "a2"):
        assert ctx["c"][key].get(f"/api/attachments/{link.id}/download").status_code in (403, 404)
    res = ctx["c"]["a3"].get("/api/attachments", params={"entity": ATTACH_ENTITY,
                                                         "entity_id": d.current_version_id})
    assert res.status_code in (403, 404)


def test_tong_quan_khong_dem_ban_luu_tru(ctx):
    db, world = ctx["db"], ctx["world"]
    from app.modules.document import dashboard_service
    from app.modules.document.dashboard_service import DashboardFilters

    base = db.query(func.count(Document.id)).scalar()
    assert base == 2
    user, prof = _profile(world, "a3", db)
    total_a3 = dashboard_service.overview(db, user, prof, DashboardFilters(
        company_id=None, department_id=None, from_date=None, to_date=None))
    user, prof = _profile(world, "khongphong", db)
    total_all = dashboard_service.overview(db, user, prof, DashboardFilters(
        company_id=None, department_id=None, from_date=None, to_date=None))
    for out in (total_a3, total_all):
        assert "HĐLĐ" not in str(out)            # tiêu đề bản lưu trữ bắt đầu bằng «HĐLĐ»
        assert "Công văn HĐ-A2-TOPSECRET thường" in str(out)   # đối chứng: văn bản thường vẫn được tính


def test_tro_ly_ai_khong_tra_ban_luu_tru(ctx):
    db, world, d, n = ctx["db"], ctx["world"], ctx["archive"], ctx["normal"]
    user, prof = _profile(world, "a3", db)
    out = _run_document_search(ToolContext(db=db, user=user, _profile=prof), {"keyword": "TOPSECRET"})
    ids = [r.get("document_id") or r.get("id") for r in out.get("items", [])]
    assert out.get("total", 0) >= 0 and d.id not in ids
    assert "HĐ-A2" not in str([r for r in out.get("items", []) if (r.get("document_id") or r.get("id")) == d.id])


def test_o_chon_quan_he_khong_loi_tieu_de_ban_luu_tru(ctx):
    db, d, n = ctx["db"], ctx["archive"], ctx["normal"]
    assert d.status == 1
    d.status = STATUS_EFFECTIVE   # HĐ Đã ký = Có hiệu lực ∈ ALIVE_STATUSES
    n.status = STATUS_EFFECTIVE
    db.commit()

    class Rule:
        target_type_id = 0

    ids = {x.id for x in link_service.allowed_targets(db, Rule())}
    assert n.id in ids and d.id not in ids


def test_thao_tac_dan_xuat_va_doi_loai_bi_chan(ctx):
    world, db, d, thuong = ctx["world"], ctx["db"], ctx["archive"], ctx["thuong"]
    # HR có đủ quyền Văn bản + HĐLĐ ⇒ đọc được, nên đây là lúc chặn dẫn xuất mới phát huy
    world.grant("a1", "document", "company", actions=ALL)
    from app.core.auth import perm_cache_clear
    perm_cache_clear(world.user_id("a1"))
    hr = ctx["c"]["a1"]
    assert hr.get(f"/api/documents/{d.id}").status_code == 200
    assert hr.post(f"/api/documents/{d.id}/copy").status_code == 409
    assert hr.post(f"/api/documents/{d.id}/clones",
                   json={"company_ids": [world.co["B"]], "note": ""}).status_code == 409
    assert hr.post(f"/api/documents/{d.id}/excerpts",
                   json={"title": "t", "content_html": "x", "secrecy_level": 1, "note": ""}).status_code == 409
    assert hr.post(f"/api/documents/{d.id}/signatures",
                   json={"version_id": d.current_version_id, "signer_employee_id": world.emp["a1"],
                         "sign_kind": 1}).status_code == 409
    assert hr.post(f"/api/documents/{d.id}/reject", json={"reason": "x"}).status_code == 409
    assert hr.patch(f"/api/documents/{d.id}", json={"title": "x"}).status_code == 403
    # tạo / đổi sang loại HDLD ở Văn bản
    body = {"doc_type_id": ctx["loai"].id, "company_id": world.co["A"], "department_id": world.dept["A.kt"],
            "owner_employee_id": world.emp["a1"], "title": "Giả HĐLĐ"}
    assert hr.post("/api/documents", json=body).status_code == 400
    n = ctx["normal"]
    a3 = ctx["c"]["a3"]
    assert a3.patch(f"/api/documents/{n.id}", json={"doc_type_id": ctx["loai"].id}).status_code == 400
    # đối chứng: tạo loại thường vẫn được
    assert hr.post("/api/documents", json={**body, "doc_type_id": thuong.id}).status_code == 201


def test_hd_xoa_mem_hr_van_doc_van_thu_van_khong(ctx):
    d = ctx["archive"]
    # đưa HĐ về Nháp → xóa mềm
    assert ctx["c"]["a1"].delete(f"{CT_URL}/{ctx['cid']}").status_code == 200
    assert d.id in _ids(ctx["c"]["a1"])
    assert ctx["c"]["a1"].get(f"/api/documents/{d.id}").status_code == 200
    assert d.id not in _ids(ctx["c"]["a3"])
    assert ctx["c"]["a3"].get(f"/api/documents/{d.id}").status_code == 404


# ── Lượt 2 (review): H1 quan hệ · H2 nhật ký · M1 mồ côi · M2/H3 script · L chọn loại / mật ──────────────
def test_h1_van_thu_khai_quan_he_toi_ban_luu_tru_404_khong_lo_tieu_de(ctx):
    world, d, n = ctx["world"], ctx["archive"], ctx["normal"]
    a3 = ctx["c"]["a3"]
    res = a3.post(f"/api/documents/{n.id}/links", json={"relation": 8, "target_document_id": d.id})
    assert res.status_code == 404 and "TOPSECRET" not in res.text and "HĐLĐ" not in res.text
    assert a3.get(f"/api/documents/{n.id}/links").status_code == 200
    assert "HĐLĐ" not in a3.get(f"/api/documents/{n.id}/links").text
    # đối chứng: nối hai văn bản thường vẫn được
    other = doc_service.create_document(ctx["db"], DocumentCreate(
        doc_type_id=ctx["thuong"].id, company_id=world.co["A"], department_id=world.dept["A.kt"],
        owner_employee_id=world.emp["a3"], title="Công văn khác"), world.user_id("a3"))
    assert a3.post(f"/api/documents/{n.id}/links", json={"relation": 8, "target_document_id": other.id}).status_code == 201


def test_h1_nguoi_doc_duoc_van_bi_chan_409_va_ban_luu_tru_khong_la_nguon_quan_he(ctx):
    world, d, n = ctx["world"], ctx["archive"], ctx["normal"]
    from app.core.auth import perm_cache_clear
    world.grant("a1", "document", "company", actions=ALL)
    perm_cache_clear(world.user_id("a1"))
    hr = ctx["c"]["a1"]
    # HR đọc được bản lưu trữ ⇒ thấy 409 (không phải 404); nguồn là bản lưu trữ thì ghi bị chặn từ `can(write)`
    n.created_by = world.user_id("a1")
    ctx["db"].commit()
    assert hr.post(f"/api/documents/{n.id}/links", json={"relation": 8, "target_document_id": d.id}).status_code == 409
    assert hr.post(f"/api/documents/{d.id}/links", json={"relation": 8, "target_document_id": n.id}).status_code == 403


def _audit(client, **q):
    return client.get("/api/audit-logs", params=q)


def test_h2_nhat_ky_ban_luu_tru_chi_hien_cho_nguoi_doc_duoc(ctx, storage, monkeypatch):   # noqa: F811
    world, db, d = ctx["world"], ctx["db"], ctx["archive"]
    monkeypatch.setattr("app.modules.attachment.controller.read_file_bytes", lambda f: storage[f.file_key])
    link = db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY,
                                     FileLink.entity_id == d.current_version_id).one()
    assert ctx["c"]["a1"].get(f"/api/attachments/{link.id}/download").status_code == 200
    from app.core.audit import record
    record(db, world.user_id("a1"), "document", d.id, "update", "Tải về tệp «HDLD-HĐ-A2-TOPSECRET.docx»")
    db.commit()
    # HR đọc được ⇒ thấy
    r = _audit(ctx["c"]["a1"], entity="document", entity_id=d.id)
    assert r.status_code == 200 and "TOPSECRET" in r.text
    # văn thư: không có dòng nào (theo id lẫn theo loại)
    r = _audit(ctx["c"]["a3"], entity="document", entity_id=d.id)
    assert "TOPSECRET" not in r.text and (r.status_code in (403, 404) or not r.json()["data"])
    r = _audit(ctx["c"]["a3"], entity="document")
    assert "TOPSECRET" not in r.text
    # quản trị có quyền nhật ký nhưng KHÔNG có labor_contract: vẫn không thấy, cả khi tra toàn hệ
    world.grant("khongphong", "audit", "all", actions=("read",))
    from app.core.auth import perm_cache_clear
    perm_cache_clear(world.user_id("khongphong"))
    root = ctx["c"]["khongphong"]
    for params in ({"entity": "document", "entity_id": d.id}, {"entity": "document"}, {}):
        r = _audit(root, **params)
        assert r.status_code == 200 and "TOPSECRET" not in r.text, params
    # đối chứng: dòng nhật ký của văn bản thường vẫn hiện cho quản trị
    record(db, world.user_id("a3"), "document", ctx["normal"].id, "update", "Sửa công văn thường")
    db.commit()
    assert "Sửa công văn thường" in _audit(root, entity="document").text


def test_h2_chuong_canh_bao_khong_dung_tieu_de_ban_luu_tru(ctx):
    from app.modules.document import file_access_log
    db, d, n = ctx["db"], ctx["archive"], ctx["normal"]
    assert file_access_log._alert_label(db, d) == f"văn bản #{d.id}"
    assert file_access_log._alert_label(db, n) == n.title


def test_m1_van_ban_hdld_mo_coi_khong_ai_doc_ke_ca_quan_tri(ctx):
    world, db = ctx["world"], ctx["db"]
    orphan = doc_service.create_document(db, DocumentCreate(
        doc_type_id=ctx["loai"].id, company_id=world.co["A"], department_id=world.dept["A.kt"],
        owner_employee_id=world.emp["a1"], title="HĐLĐ mồ côi"), world.user_id("a1"))
    for key in ("a1", "a3", "khongphong"):
        cl = ctx["c"][key]
        assert orphan.id not in _ids(cl), key
        assert cl.get(f"/api/documents/{orphan.id}").status_code == 404, key
    user, prof = _profile(world, "khongphong", db)
    assert not access_service.can(db, orphan, user, prof, "read")


def test_m1_dong_bo_nhan_lai_van_ban_mo_coi_khong_sinh_ban_moi(ctx):
    world, db = ctx["world"], ctx["db"]
    from app.modules.labor_contract import document_archive_sync
    cid = ctx["cid"]
    lc = db.get(LaborContract, cid)
    doc_id = lc.document_id
    lc.document_id = 0          # giả lập lần ghi liên kết trượt
    db.commit()
    before = db.query(Document).count()
    assert document_archive_sync.archive_sync(db, cid, 1) == doc_id
    assert db.query(Document).count() == before
    assert db.get(LaborContract, cid).document_id == doc_id


def test_h3_kiem_loai_hdld_nguoi_dung_tu_tao(ctx):
    from app.modules.document import labor_contract_archive_access as aa
    db = ctx["db"]
    assert aa.check_doc_type(db) == []
    ctx["loai"].is_personal = False
    ctx["loai"].needs_approval = True
    db.commit()
    problems = aa.check_doc_type(db)
    assert any("is_personal" in p for p in problems) and any("duyệt" in p for p in problems)


def _script(monkeypatch, db, *argv):
    import importlib.util
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2]
    path = next(p for p in (root / "backend" / "scripts", root / "scripts")
                if (p / "backfill_hdld_van_ban_luu_tru.py").exists()) / "backfill_hdld_van_ban_luu_tru.py"
    spec = importlib.util.spec_from_file_location("backfill_cr629_m2", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    class Session:                      # đóng session thật của test sẽ làm hỏng các kiểm tra sau
        def __getattr__(self, name):
            return getattr(db, name)

        def close(self):
            pass
    monkeypatch.setattr(mod, "SessionLocal", lambda: Session())
    monkeypatch.setattr("sys.argv", ["backfill", *argv])
    return mod


def test_m2_script_mac_dinh_chay_thu_va_phai_co_apply_yes_moi_ghi(ctx, monkeypatch, capsys):
    db, cid = ctx["db"], ctx["cid"]
    # mặc định: chạy thử — kể cả kèm --soft-delete-all
    for argv in ([], ["--soft-delete-all"]):
        assert _script(monkeypatch, db, *argv).main() == 0
        assert db.get(LaborContract, cid).document_id > 0 and "CHẠY THỬ" in capsys.readouterr().out
    # --apply thiếu --yes (không phải terminal) ⇒ hủy, không ghi
    assert _script(monkeypatch, db, "--soft-delete-all", "--apply").main() == 1
    assert db.get(LaborContract, cid).document_id > 0
    # --yes lẻ loi ⇒ lỗi cú pháp
    with pytest.raises(SystemExit):
        _script(monkeypatch, db, "--yes").main()
    # --apply --yes ⇒ ghi thật, in DB đích
    assert _script(monkeypatch, db, "--soft-delete-all", "--apply", "--yes").main() == 0
    out = capsys.readouterr().out
    assert "DB đích" in out and "ĐÃ GHI" in out
    db.expire_all()
    assert db.get(LaborContract, cid).document_id == 0


def test_h3_script_check_va_apply_dung_khi_loai_hdld_la(ctx, monkeypatch, capsys):
    db = ctx["db"]
    ctx["loai"].needs_approval = True
    db.commit()
    assert _script(monkeypatch, db, "--check").main() == 2
    assert "ĐIỀU KIỆN DỪNG TRIỂN KHAI" in capsys.readouterr().out
    assert _script(monkeypatch, db, "--apply", "--yes").main() == 2   # dừng, không ghi


def test_low_loai_hdld_seed_la_loai_mat():
    from app.seed_data.document_phase1 import ALL_DOC_TYPES
    hdld = next(r for r in ALL_DOC_TYPES if r["code"] == "HDLD")
    assert hdld["is_confidential_type"] is True


# ── Lượt 2 (review): màn Nhật ký hệ thống (system_log) ────────────────────────────────────
def _syslog_fixture(ctx):
    from test_man_nhat_ky_he_thong_cr407 import _add_audit, _add_change, _add_request, _rid
    from app.core.auth import perm_cache_clear
    world, db, d = ctx["world"], ctx["db"], ctx["archive"]
    for key in ("khongphong", "a1"):
        world.grant(key, "audit", "all", actions=("read",))
        world.grant(key, "change_log", "all", actions=("read",))
        perm_cache_clear(world.user_id(key))
    rid, rid_ok = _rid(), _rid()
    _add_request(db, rid=rid, user_id=world.user_id("a1"), path=f"/api/attachments/9/download")
    _add_audit(db, rid, entity="document", entity_id=d.id, action="update",
               message="Tải về tệp «HDLD-HĐ-A2-TOPSECRET.docx»", created_by=world.user_id("a1"))
    _add_change(db, rid, table_name="tab_labor_contract", row_id=ctx["cid"], field="contract_no",
                before_value="", after_value="HĐ-A2-TOPSECRET")
    _add_change(db, rid, table_name="tab_document", row_id=d.id, field="title",
                before_value="", after_value="HĐLĐ HĐ-A2-TOPSECRET — Nhân sự a2")
    _add_change(db, rid, table_name="tab_file", row_id=77, field="filename",
                before_value="", after_value="HDLD-HĐ-A2-TOPSECRET.docx")
    # đối chứng: một lượt gọi thường
    _add_request(db, rid=rid_ok, user_id=world.user_id("a3"), path="/api/units")
    _add_audit(db, rid_ok, entity="unit", message="Sửa đơn vị tính")
    _add_change(db, rid_ok, table_name="tab_unit", row_id=1)
    db.commit()
    from app.modules.system_log.service import request_id_text
    return request_id_text(rid), request_id_text(rid_ok)


def test_system_log_an_dong_audit_va_thay_doi_cua_ban_luu_tru(ctx):
    rid, rid_ok = _syslog_fixture(ctx)
    root = ctx["c"]["khongphong"]          # có audit + change_log, KHÔNG có labor_contract
    listing = root.get("/api/system-logs").json()["data"]["items"]
    assert "TOPSECRET" not in str(listing)
    assert any(i["summary"] == "Sửa đơn vị tính" for i in listing)       # đối chứng
    detail = root.get(f"/api/system-logs/{rid}").json()["data"]
    assert "TOPSECRET" not in str(detail) and detail["audit"] == []
    assert detail["changes"] == []                                        # cả 3 bảng bị gỡ
    ok = root.get(f"/api/system-logs/{rid_ok}").json()["data"]
    assert len(ok["audit"]) == 1 and len(ok["changes"]) == 1              # đối chứng


def test_system_log_nguoi_doc_duoc_van_thay_du(ctx):
    rid, _ = _syslog_fixture(ctx)
    hr = ctx["c"]["a1"]
    assert any("TOPSECRET" in i["summary"] for i in hr.get("/api/system-logs").json()["data"]["items"])
    detail = hr.get(f"/api/system-logs/{rid}").json()["data"]
    assert len(detail["audit"]) == 1 and len(detail["changes"]) == 3


def test_system_log_khong_ro_nguoi_xem_thi_dong(ctx):
    from app.modules.system_log import service
    _syslog_fixture(ctx)
    db = ctx["db"]
    rows = service.build_page(db, service.build_query(db), 0, 20)      # viewer=None ⇒ che bản lưu trữ
    assert "TOPSECRET" not in str(rows)


def test_log_body_hdld_luong_va_cccd_da_che_theo_duong_dan():
    from app.core.logging_policy import MASKED, mask_payload, sensitive_keys_for_path
    body = {"base_salary": 15_000_000, "insurance_salary": 1, "allowance": 5, "allowance_note": "x",
            "contract_no": "HĐ-1", "id_number": "0123456789", "bank_account_no": "999"}
    for path in ("/api/labor-contracts/5", "/api/employees/7/labor-contracts"):
        masked = mask_payload(body, sensitive_keys_for_path(path))
        assert masked["base_salary"] == masked["insurance_salary"] == masked["allowance"] == MASKED
        assert masked["allowance_note"] == MASKED
    # tuyến văn bản không chứa trường nhạy cảm của HĐ ⇒ không cần che thêm (thân chỉ có tiêu đề/ghi chú do người dùng gõ)
    assert sensitive_keys_for_path("/api/documents/9/copy") == frozenset()


# ── Lượt 3 (re-review) ───────────────────────────────────────────────────────────────────
def test_n1_xoa_cung_ho_so_nhan_su_nhat_ky_van_giau(ctx):
    """HĐ Nháp bị xóa CỨNG cùng hồ sơ nhân sự ⇒ id văn bản rơi khỏi `archive_ids()`; nhật ký vẫn phải giấu."""
    from app.core.auth import perm_cache_clear
    from app.core.audit import record
    from app.modules.labor_contract import service as lc_service
    world, db, d, cid = ctx["world"], ctx["db"], ctx["archive"], ctx["cid"]
    rid, _ = _syslog_fixture(ctx)
    record(db, world.user_id("a1"), "labor_contract", cid, "create", "Lập hợp đồng lao động cho Nhân sự a2")
    record(db, world.user_id("a1"), "document", d.id, "update", "Tải về tệp «HDLD-HĐ-A2-TOPSECRET.docx»")
    db.commit()
    ctx["c"]["a1"].post(f"{CT_URL}/{cid}/transition", json={"to_status": 5, "reason": "x"})
    lc_service.delete_all_of(db, world.emp["a2"])
    db.commit()
    assert db.query(LaborContract).filter(LaborContract.id == cid).count() == 0
    root = ctx["c"]["khongphong"]
    for params in ({"entity": "document", "entity_id": d.id}, {"entity": "document"},
                   {"entity": "labor_contract"}, {}):
        r = _audit(root, **params)
        assert r.status_code == 200 and "TOPSECRET" not in r.text and "Lập hợp đồng lao động cho" not in r.text, params
    sl = root.get("/api/system-logs").json()["data"]["items"]
    assert "TOPSECRET" not in str(sl)
    detail = root.get(f"/api/system-logs/{rid}").json()["data"]
    assert detail["audit"] == [] and detail["changes"] == []


def test_l6_system_log_an_dong_audit_labor_contract(ctx):
    from test_man_nhat_ky_he_thong_cr407 import _add_audit, _add_request, _rid
    from app.core.auth import perm_cache_clear
    from app.modules.system_log.service import request_id_text
    world, db, cid = ctx["world"], ctx["db"], ctx["cid"]
    for key in ("khongphong", "a1"):
        world.grant(key, "audit", "all", actions=("read",))
        perm_cache_clear(world.user_id(key))
    rid = _rid()
    _add_request(db, rid=rid, user_id=world.user_id("a1"), path="/api/employees/1/labor-contracts")
    _add_audit(db, rid, entity="labor_contract", entity_id=cid, action="create",
               message="Lập hợp đồng lao động cho Nhân sự a2", doc_code="HDLD-SECRETCODE")
    db.commit()
    text = request_id_text(rid)
    root, hr = ctx["c"]["khongphong"], ctx["c"]["a1"]
    assert "SECRETCODE" not in str(root.get("/api/system-logs").json()["data"]["items"])
    assert root.get(f"/api/system-logs/{text}").json()["data"]["audit"] == []
    assert "SECRETCODE" in str(hr.get("/api/system-logs").json()["data"]["items"])     # đối chứng
    assert len(hr.get(f"/api/system-logs/{text}").json()["data"]["audit"]) == 1


def test_n2_loai_hdld_bi_khoa_moi_co_va_khong_tao_ma_hdld(ctx):
    world, loai = ctx["world"], ctx["loai"]
    from app.core.auth import perm_cache_clear
    world.grant("a3", "doc_type", "all", actions=("read", "create", "write", "delete"))
    perm_cache_clear(world.user_id("a3"))
    a3 = ctx["c"]["a3"]
    for body in ({"is_active": False}, {"is_personal": False}, {"needs_approval": True},
                 {"needs_signature": True}, {"code": "HDLD2"}, {"id_scheme": 1},
                 {"is_confidential_type": True}, {"default_secrecy": 1}):
        r = a3.patch(f"/api/doc-types/{loai.id}", json=body)
        assert r.status_code == 400, (body, r.status_code, r.text)
    assert a3.delete(f"/api/doc-types/{loai.id}").status_code == 400
    # đổi tên / mô tả (không phải cờ) vẫn được; ghi lại đúng giá trị cờ hiện có cũng không bị chặn
    assert a3.patch(f"/api/doc-types/{loai.id}", json={"name": "Hợp đồng lao động (lưu trữ)"}).status_code == 200
    assert a3.patch(f"/api/doc-types/{loai.id}", json={"is_active": True, "is_personal": True}).status_code == 200
    # tạo loại mới mã hdld / đổi một loại khác sang mã HDLD
    r = a3.post("/api/doc-types", json={"code": "hdld", "name": "Giả", "group_code": "C", "id_scheme": 2})
    assert r.status_code == 400, r.text
    r = a3.patch(f"/api/doc-types/{ctx['thuong'].id}", json={"code": "HDLD"})
    assert r.status_code == 400
    # đối chứng: loại thường sửa được
    assert a3.patch(f"/api/doc-types/{ctx['thuong'].id}", json={"name": "Công văn đi"}).status_code == 200


def test_l1_tao_van_ban_va_lien_ket_cung_giao_dich(ctx, monkeypatch):
    """Commit cuối lỗi ⇒ rollback sạch: không còn văn bản HDLD mồ côi."""
    from sqlalchemy.orm import Session
    from app.modules.labor_contract import document_archive_sync
    world, db = ctx["world"], ctx["db"]
    c2 = make_contract.__wrapped__ if hasattr(make_contract, "__wrapped__") else None  # noqa: F841
    lc = db.query(LaborContract).filter(LaborContract.id == ctx["cid"]).one()
    lc.document_id = 0
    db.query(Document).filter(Document.id == ctx["archive"].id).update({"keywords": "khác", "is_deleted": True})
    db.commit()
    before = db.query(Document).count()
    real_commit = Session.commit
    state = {"n": 0}

    def flaky(self):
        state["n"] += 1
        if state["n"] == 1:
            raise RuntimeError("commit hỏng")
        return real_commit(self)
    monkeypatch.setattr(Session, "commit", flaky)
    assert document_archive_sync.archive_sync(db, ctx["cid"], 1) == 0
    monkeypatch.setattr(Session, "commit", real_commit)
    db.expire_all()
    assert db.query(Document).count() == before          # văn bản vừa flush đã rollback, không mồ côi
    assert db.get(LaborContract, ctx["cid"]).document_id == 0


def test_l1_da_co_van_ban_thi_ban_du_cung_dau_bi_xoa_mem(ctx):
    from app.modules.labor_contract import document_archive_sync
    db, cid, d = ctx["db"], ctx["cid"], ctx["archive"]
    dup = doc_service.create_document(db, DocumentCreate(
        doc_type_id=ctx["loai"].id, company_id=ctx["world"].co["A"], department_id=ctx["world"].dept["A.kt"],
        owner_employee_id=0, title="bản dư", keywords=f"hdld:{cid}"), 1)
    assert document_archive_sync.archive_sync(db, cid, 1) == d.id
    db.expire_all()
    assert db.get(Document, dup.id).is_deleted is True and db.get(Document, d.id).is_deleted is False


def test_l2_cay_quan_he_va_van_ban_sua_doi_khong_hien_ban_luu_tru(ctx):
    from app.modules.document import link_serializer, supersede_service
    from app.modules.document.link_model import DocumentLink
    db, d, n = ctx["db"], ctx["archive"], ctx["normal"]
    n.status = STATUS_EFFECTIVE
    d.status = STATUS_EFFECTIVE
    db.add(DocumentLink(source_document_id=d.id, target_document_id=n.id, relation=1, created_by=1, updated_by=1))
    db.commit()
    assert link_serializer._children(db, n.id, 3, {n.id}) == []
    assert supersede_service.amended_by(db, n.id) == []
    # đối chứng: cùng liên kết từ một văn bản thường thì hiện
    other = doc_service.create_document(db, DocumentCreate(
        doc_type_id=ctx["thuong"].id, company_id=ctx["world"].co["A"], department_id=ctx["world"].dept["A.kt"],
        owner_employee_id=0, title="Công văn sửa đổi"), 1)
    other.status = STATUS_EFFECTIVE
    db.add(DocumentLink(source_document_id=other.id, target_document_id=n.id, relation=1, created_by=1, updated_by=1))
    db.commit()
    assert [x["document_id"] for x in supersede_service.amended_by(db, n.id)] == [other.id]


def test_l3_soft_delete_all_don_ca_van_ban_hdld_mo_coi(ctx, monkeypatch):
    db, world = ctx["db"], ctx["world"]
    orphan = doc_service.create_document(db, DocumentCreate(
        doc_type_id=ctx["loai"].id, company_id=world.co["A"], department_id=world.dept["A.kt"],
        owner_employee_id=0, title="mồ côi"), 1)
    script = _script(monkeypatch, db)
    counts = script.run(db, dry_run=True, soft_delete_all=True)
    assert counts["removed"] == 2 and db.get(Document, orphan.id).is_deleted is False   # 1 có HĐ + 1 mồ côi
    script.run(db, soft_delete_all=True)
    db.expire_all()
    assert db.get(Document, orphan.id).is_deleted is True and db.get(Document, ctx["archive"].id).is_deleted is True


def test_l6_script_bao_loai_hdld_tat(ctx, monkeypatch):
    db = ctx["db"]
    script = _script(monkeypatch, db)
    assert script.run(db, dry_run=True)["type_inactive"] == 0
    ctx["loai"].is_active = False
    db.commit()
    assert script.run(db, dry_run=True)["type_inactive"] == 1


def test_l5_wrap_visible_giu_van_ban_khong_loai(ctx):
    from app.modules.document import labor_contract_archive_access as aa
    sql = str(aa.wrap_visible(None, None, {}, "write").compile(compile_kwargs={"literal_binds": True}))
    assert "doc_type_id IS NULL" in sql


def test_l4_can_write_khong_hoi_lai_kiem_tra_ban_luu_tru(ctx):
    from sqlalchemy import event
    db, world, n = ctx["db"], ctx["world"], ctx["normal"]
    user, prof = _profile(world, "a3", db)
    sqls = []

    def hook(conn, cursor, statement, *a):
        sqls.append(statement)
    event.listen(db.get_bind(), "before_cursor_execute", hook)
    try:
        assert access_service.can(db, n, user, prof, "write")
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", hook)
    assert sum("WHERE tab_labor_contract.document_id = ?" in s for s in sqls) == 1      # trước đây 2 (can write + can read đệ quy)
