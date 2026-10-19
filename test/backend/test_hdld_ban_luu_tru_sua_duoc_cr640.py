"""duoc-CR-640 — bản lưu trữ HĐLĐ SỬA ĐƯỢC bởi người có `labor_contract.write` phủ HĐ (không ai khác).

Cho phép: sửa thông tin, nội dung/phiên bản, tải/gỡ tệp «mềm», thư mục. Vẫn chặn (409): chia sẻ, sao chép, clone, trích,
quan hệ, phạm vi áp dụng, gửi duyệt / duyệt / ký / ban hành / cấp số, bãi bỏ, đổi loại, vào sổ. Đồng bộ KHÔNG đụng tệp người
dùng tải lên; bản sao do đồng bộ tạo thì theo phiên bản hiện hành.
"""
import pytest

from app.core.auth import perm_cache_clear
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.doc_catalog.model import DocType
from app.modules.document import access_service
from app.modules.document.model import Document
from app.modules.document.service import ATTACH_ENTITY
from app.modules.document.version_model import DocumentVersion
from app.modules.labor_contract import document_archive_sync
from app.modules.labor_contract.document_archive_files import SYNC_MARK
from app.modules.labor_contract.model import LaborContract
from hdld_factory import (PDF_BYTES, PNG_BYTES, client_as, grant_all, make_contract,  # noqa: F401
                          storage, upload_template)
from test_hdld_van_ban_luu_tru_quyen_xem_cr629 import ALL, _ids, _profile  # noqa: F401

CT_URL = "/api/labor-contract" + "s"


@pytest.fixture
def ctx(db, world, storage, client_as, monkeypatch):  # noqa: F811
    """a1 = HR ghi (labor_contract company A + document own); b1 = HR công ty B; a3 = văn thư; a2 = chỉ ĐỌC HĐLĐ."""
    grant_all(world, "a1")
    world.grant("a1", "document", "own", actions=("read", "write"))
    grant_all(world, "b1")
    world.grant("b1", "document", "company", actions=("read",))
    world.grant("a2", "labor_contract", "company", actions=("read",))        # chỉ đọc
    world.grant("a2", "document", "company", actions=("read", "write"))   # có write văn bản nhưng KHÔNG có labor_contract.write
    world.grant("a3", "document", "company", actions=ALL)
    thuong = DocType(code="CV", name="Công văn", id_scheme=2, number_when=2, needs_approval=False)
    db.add_all([DocType(code="HDLD", name="Hợp đồng lao động", id_scheme=2, number_when=2, is_personal=True,
                        needs_approval=False, needs_signature=False), thuong])
    db.commit()
    monkeypatch.setattr("app.modules.attachment.controller.read_file_bytes", lambda f: storage[f.file_key])
    monkeypatch.setattr("app.modules.attachment.controller.upload_fileobj",
                        lambda fileobj, key, ct="": storage.__setitem__(key, fileobj.read()) or f"/fake/{key}")
    monkeypatch.setattr("app.modules.attachment.controller.delete_key", lambda key: storage.pop(key, None))
    hr = client_as(world.actor("a1"))
    tpl = upload_template(hr, company_id=world.co["A"]).json()["data"]["id"]
    cid = make_contract(hr, world.emp["a3"])["id"]
    hr.post(f"{CT_URL}/{cid}/generate", json={"template_id": tpl})
    db.expire_all()
    doc = db.get(Document, db.get(LaborContract, cid).document_id)
    return {"client_as": client_as, "world": world, "db": db, "doc": doc, "cid": cid, "tpl": tpl, "storage": storage, "thuong": thuong,
            "c": {k: client_as(world.actor(k)) for k in ("a1", "a2", "a3", "b1")}}


def _upload(client, version_id, name="phu-luc.pdf", data=PDF_BYTES, mime="application/pdf"):
    return client.post("/api/attachments", data={"entity": ATTACH_ENTITY, "entity_id": str(version_id)},
                       files={"files": (name, data, mime)})


def _approve_current_version(db, doc):
    """Giả lập bản 1.0 đã duyệt (người dùng KHÔNG tự duyệt được bản lưu trữ) để mở được bản mới."""
    version = db.get(DocumentVersion, doc.current_version_id)
    version.status = 3
    version.is_locked = True
    db.commit()


def _user_links(db, doc):
    db.expire_all()
    return [(l, db.get(StoredFile, l.file_id)) for l in db.query(FileLink).filter(
        FileLink.entity == ATTACH_ENTITY, FileLink.entity_id == doc.current_version_id).all()
        if l.doc_type != SYNC_MARK]


# ── Cho phép ──────────────────────────────────────────────────────────────────────────
def test_nguoi_ghi_hdld_sua_duoc_thong_tin_noi_dung_phien_ban(ctx):
    hr, d, db = ctx["c"]["a1"], ctx["doc"], ctx["db"]
    r = hr.patch(f"/api/documents/{d.id}", json={"storage_location": "Tủ A2", "legacy_code": "BG-12"})
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(Document, d.id).storage_location == "Tủ A2" and db.get(Document, d.id).legacy_code == "BG-12"
    perms = hr.get(f"/api/documents/{d.id}/permissions").json()["data"]
    assert perms["read"] and perms["write"] and not perms["delete"] and perms["is_archive"] is True
    _approve_current_version(db, d)
    r = hr.post(f"/api/documents/{d.id}/versions", json={"change_kind": 1, "change_summary": "bản mới"})
    assert r.status_code in (200, 201), r.text


def test_nguoi_ghi_tai_va_go_tep_mem(ctx):
    hr, d, db = ctx["c"]["a1"], ctx["doc"], ctx["db"]
    r = _upload(hr, d.current_version_id)
    assert r.status_code == 201, r.text
    link_id = r.json()["data"][0]["id"]
    assert len(_user_links(db, d)) == 1
    assert hr.get(f"/api/attachments/{link_id}/download").status_code == 200
    assert hr.delete(f"/api/attachments/{link_id}").status_code == 200
    assert _user_links(db, d) == []


def test_nguoi_ghi_dat_thu_muc(ctx):
    d = ctx["doc"]
    r = ctx["c"]["a1"].get(f"/api/documents/{d.id}")
    assert r.status_code == 200      # thư mục: dùng chung `can(write)`; xem tệp riêng test_folder bên dưới


# ── Không được ────────────────────────────────────────────────────────────────────────
def test_chi_doc_hdld_khong_sua_duoc(ctx):
    a2, d = ctx["c"]["a2"], ctx["doc"]
    assert a2.get(f"/api/documents/{d.id}").status_code == 200           # đọc được
    assert a2.get(f"/api/documents/{d.id}/permissions").json()["data"]["write"] is False
    assert a2.patch(f"/api/documents/{d.id}", json={"storage_location": "x"}).status_code == 403
    assert _upload(a2, d.current_version_id).status_code in (403, 404)
    assert a2.post(f"/api/documents/{d.id}/versions", json={"change_kind": 1, "change_summary": "x"}).status_code == 403


def test_hr_cong_ty_khac_va_van_thu_khong_thay_khong_sua(ctx):
    d = ctx["doc"]
    for key in ("b1", "a3"):
        cl = ctx["c"][key]
        assert cl.get(f"/api/documents/{d.id}").status_code == 404
        assert cl.patch(f"/api/documents/{d.id}", json={"storage_location": "x"}).status_code in (403, 404)
        assert _upload(cl, d.current_version_id).status_code in (403, 404)


def test_hr_cong_ty_khac_co_ghi_nhung_ngoai_pham_vi_khong_sua(ctx):
    """b1 có labor_contract.write phạm vi công ty B, HĐ ở công ty A ⇒ không sửa."""
    d = ctx["doc"]
    assert ctx["c"]["b1"].patch(f"/api/documents/{d.id}", json={"storage_location": "x"}).status_code in (403, 404)


def test_van_chan_409_cac_thao_tac_day_di_noi_khac(ctx):
    hr, d, world, db = ctx["c"]["a1"], ctx["doc"], ctx["world"], ctx["db"]
    world.grant("a1", "document", "company", actions=ALL + ("cancel",))
    perm_cache_clear(world.user_id("a1"))
    n = f"/api/documents/{d.id}"
    other = ctx["thuong"]
    blocked = [
        ("post", f"{n}/copy", None),
        ("post", f"{n}/clones", {"company_ids": [world.co["B"]], "note": ""}),
        ("put", f"{n}/clone-plan", {"company_ids": []}),
        ("post", f"{n}/excerpts", {"title": "t", "content_html": "x", "secrecy_level": 1, "note": ""}),
        ("post", f"{n}/links", {"relation": 8, "target_document_id": d.id + 1000}),
        ("post", f"{n}/scopes", {"dim": 1, "mode": 1, "company_id": world.co["A"]}),
        ("post", f"{n}/access", {"subject_kind": 1, "subject_id": world.emp["a3"], "effect": 1, "can_read": True,
                                 "reason": "chia"}),
        ("post", f"{n}/submit", None),
        ("post", f"{n}/approve", {}),
        ("post", f"{n}/reject", {"reason": "x"}),
        ("post", f"{n}/issue", {}),
        ("post", f"{n}/revoke", {"reason": "x"}),
        ("post", f"{n}/reviewed", {"conclusion": "đã rà soát"}),
        ("patch", f"{n}/issue-number", {"issue_number": "1", "reason": "x"}),
        ("post", f"{n}/signatures", {"version_id": d.current_version_id, "signer_employee_id": world.emp["a1"],
                                     "sign_kind": 1}),
        ("patch", n, {"doc_type_id": other.id}),
        ("patch", n, {"book_id": 1}),
    ]
    for method, url, body in blocked:
        r = getattr(hr, method)(url, **({"json": body} if body is not None else {}))
        assert r.status_code in (409, 422), (method, url, r.status_code, r.text[:200])
        # 422 chỉ chấp nhận khi lỗi cú pháp thân — in ra để lộ ca nào thật sự chưa chạm chốt 409
    hard = [(m, u) for m, u, b in blocked
            if getattr(hr, m)(u, **({"json": b} if b is not None else {})).status_code != 409]
    assert hard == [], hard
    assert hr.delete(n).status_code in (403, 409)      # xóa chỉ qua hợp đồng
    db.expire_all()
    assert db.get(Document, d.id).doc_type_id != other.id


# ── Đồng bộ không đụng tệp người dùng ─────────────────────────────────────────────────
def test_dong_bo_giu_tep_nguoi_dung_qua_sinh_lai_thay_ban_ky_va_doi_trang_thai(ctx):
    hr, d, db, cid, storage = ctx["c"]["a1"], ctx["doc"], ctx["db"], ctx["cid"], ctx["storage"]
    r = _upload(hr, d.current_version_id, name="scan-phu-luc.png", data=PNG_BYTES, mime="image/png")
    assert r.status_code == 201
    mine, stored = _user_links(db, d)[0]
    key = stored.file_key
    assert hr.post(f"{CT_URL}/{cid}/generate", json={"template_id": ctx["tpl"]}).status_code == 200
    assert hr.put(f"{CT_URL}/{cid}/signed-file", files={"file": ("ky.pdf", PDF_BYTES, "application/pdf")}).status_code == 200
    assert hr.put(f"{CT_URL}/{cid}/signed-file", files={"file": ("ky2.pdf", PDF_BYTES + b"x", "application/pdf")}).status_code == 200
    assert hr.post(f"{CT_URL}/{cid}/transition", json={"to_status": 2, "date": "2026-01-05"}).status_code == 200
    assert hr.patch(f"/api/documents/{d.id}", json={"storage_location": "tay"}).status_code == 200
    document_archive_sync.archive_sync(db, cid, 1)
    db.expire_all()
    assert [s.file_key for _, s in _user_links(db, d)] == [key] and key in storage
    sync_links = db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY, FileLink.doc_type == SYNC_MARK,
                                           FileLink.entity_id == d.current_version_id).all()
    assert len(sync_links) == 2            # .docx + bản ký mới nhất, không nhân đôi


def test_phien_ban_moi_dong_bo_chi_chinh_ban_hien_hanh_ban_cu_giu_nguyen(ctx):
    hr, d, db, cid, tpl = ctx["c"]["a1"], ctx["doc"], ctx["db"], ctx["cid"], ctx["tpl"]
    mine = _upload(hr, d.current_version_id)
    assert mine.status_code == 201
    old_version = d.current_version_id
    _approve_current_version(db, d)
    r = hr.post(f"/api/documents/{d.id}/versions", json={"change_kind": 1, "change_summary": "v2"})
    assert r.status_code in (200, 201), r.text
    db.expire_all()
    new_version = db.get(Document, d.id).current_version_id
    if new_version == old_version:       # bản mới là bản nháp mở: coi là bản hiện hành để thử đồng bộ
        new_version = db.query(DocumentVersion.id).filter(DocumentVersion.document_id == d.id) \
            .order_by(DocumentVersion.id.desc()).first()[0]
        db.get(Document, d.id).current_version_id = new_version
        db.commit()
    # HĐ sinh lại tệp ⇒ bản sao đồng bộ của phiên bản hiện hành đổi; bản cũ + tệp người dùng ở yên
    assert hr.post(f"{CT_URL}/{cid}/generate", json={"template_id": tpl}).status_code == 200
    db.expire_all()
    cur = db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY, FileLink.entity_id == new_version).all()
    old = db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY, FileLink.entity_id == old_version).all()
    assert sorted(l.doc_type for l in cur) == sorted(["", SYNC_MARK])     # 1 tệp mềm + 1 bản sao đồng bộ
    assert sorted(l.doc_type for l in old) == sorted(["", SYNC_MARK])     # bản cũ giữ nguyên bộ tệp lúc đó
    storage = ctx["storage"]
    for l in old + cur:
        assert db.get(StoredFile, l.file_id).file_key in storage          # không tệp nào bị xóa nhầm


def test_nguoi_dung_xoa_ban_sao_dong_bo_thi_lan_sau_them_lai(ctx):
    hr, d, db, cid = ctx["c"]["a1"], ctx["doc"], ctx["db"], ctx["cid"]
    link = db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY, FileLink.doc_type == SYNC_MARK).one()
    assert hr.delete(f"/api/attachments/{link.id}").status_code == 200
    document_archive_sync.archive_sync(db, cid, 1)
    db.expire_all()
    assert db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY, FileLink.doc_type == SYNC_MARK).count() == 1


def test_ban_sao_cu_chua_co_dau_van_nhan_ra_nho_thu_muc_luu(ctx):
    """Bản sao tạo trước CR-640 (doc_type rỗng) vẫn là bản sao đồng bộ — gỡ khi HĐ đổi, không thành «tệp người dùng»."""
    d, db, cid = ctx["doc"], ctx["db"], ctx["cid"]
    link = db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY, FileLink.doc_type == SYNC_MARK).one()
    link.doc_type = ""
    db.commit()
    lc = db.get(LaborContract, cid)
    lc.generated_file_id = 0
    db.commit()
    document_archive_sync.archive_sync(db, cid, 1)
    db.expire_all()
    assert db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY,
                                     FileLink.entity_id == d.current_version_id).count() == 0


def test_van_khong_vao_chi_muc_va_tim_kiem(ctx):
    from app.modules.document import search_index_service
    d, db = ctx["doc"], ctx["db"]
    ctx["c"]["a1"].patch(f"/api/documents/{d.id}", json={"storage_location": "Tủ"})
    assert search_index_service.reindex(db, d.id) is None


def test_nguoi_ghi_chuyen_ban_luu_tru_sang_soan_thao(ctx):
    """Nút «Chuyển sang soạn thảo» gọi PATCH content_mode — phải chạy được với người ghi HĐLĐ."""
    hr, d, db = ctx["c"]["a1"], ctx["doc"], ctx["db"]
    assert hr.patch(f"/api/documents/{d.id}", json={"content_mode": 1}).status_code == 200
    db.expire_all()
    assert db.get(Document, d.id).content_mode == 1
    assert ctx["c"]["a2"].patch(f"/api/documents/{d.id}", json={"content_mode": 2}).status_code == 403


# ── Rà soát lượt 2: dấu đồng bộ, trường do đồng bộ sở hữu, quyền, thư mục ─────────────────────
def _second_contract(ctx):
    """HĐ thứ hai (nhân sự a2, công ty A) cùng văn bản lưu trữ riêng."""
    hr, db = ctx["c"]["a1"], ctx["db"]
    cid2 = make_contract(hr, ctx["world"].emp["a2"])["id"]
    db.expire_all()
    return cid2, db.get(Document, db.get(LaborContract, cid2).document_id)


def test_h1_truong_do_dong_bo_so_huu_sua_la_409_gui_lai_gia_tri_cu_thi_qua(ctx):
    hr, d, db = ctx["c"]["a1"], ctx["doc"], ctx["db"]
    n = f"/api/documents/{d.id}"
    for body in ({"title": "x"}, {"summary": "x"}, {"keywords": "hdld:999"}, {"effective_date": "2030-01-01"},
                 {"expire_date": "2030-01-01"}, {"book_id": 5}, {"company_id": ctx["world"].co["B"]},
                 {"department_id": 12345}, {"owner_employee_id": ctx["world"].emp["a1"]}):
        r = hr.patch(n, json=body)
        assert r.status_code == 409, (body, r.status_code)
    db.expire_all()
    cur = db.get(Document, d.id)
    same = hr.patch(n, json={"title": cur.title, "summary": cur.summary, "keywords": cur.keywords,
                             "company_id": cur.company_id, "department_id": cur.department_id,
                             "storage_location": "Kệ 3"})
    assert same.status_code == 200, same.text           # form gửi lại nguyên giá trị cũ vẫn lưu được


def test_h1_a_khong_ai_tu_xoa_mem_ban_luu_tru_khac_bang_dau_hdld(ctx):
    """Dù `keywords` của X bị đặt tay thành `hdld:{Y}` (dữ liệu cũ / ghi thẳng DB), đồng bộ Y không đụng tới X."""
    db = ctx["db"]
    cid2, doc2 = _second_contract(ctx)
    doc1 = ctx["doc"]
    doc1.keywords = f"hdld:{cid2}"
    db.commit()
    assert document_archive_sync.archive_sync(db, cid2, 1) == doc2.id
    db.expire_all()
    assert db.get(Document, doc1.id).is_deleted is False and db.get(Document, doc2.id).is_deleted is False


def test_h1_b_khong_chiem_tep_cua_hop_dong_khac_khi_document_id_bang_0(ctx):
    db, hr = ctx["db"], ctx["c"]["a1"]
    cid2, doc2 = _second_contract(ctx)
    doc1 = ctx["doc"]
    doc1.keywords = f"hdld:{cid2}"              # X giả mạo dấu của Y
    db.get(LaborContract, cid2).document_id = 0  # Y chưa có văn bản (hoặc mất liên kết)
    db.commit()
    new_id = document_archive_sync.archive_sync(db, cid2, 1)
    db.expire_all()
    assert new_id not in (0, doc1.id)           # tạo văn bản MỚI, không nhận lại văn bản đã gắn HĐ X
    assert db.get(LaborContract, ctx["cid"]).document_id == doc1.id
    assert db.get(LaborContract, cid2).document_id == new_id
    # tệp của X không bị gỡ / chép sang Y
    assert db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY,
                                     FileLink.entity_id == doc1.current_version_id).count() >= 1


def test_h1_c_van_ban_thuong_mang_dau_hdld_khong_bi_xoa_mem(ctx):
    from app.modules.document import service as doc_service
    from app.modules.document.schema import DocumentCreate
    db, world = ctx["db"], ctx["world"]
    normal = doc_service.create_document(db, DocumentCreate(
        doc_type_id=ctx["thuong"].id, company_id=world.co["A"], department_id=world.dept["A.kt"],
        owner_employee_id=world.emp["a3"], title="Công văn thường", keywords=f"hdld:{ctx['cid']}"), 1)
    assert document_archive_sync.archive_sync(db, ctx["cid"], 1) == ctx["doc"].id
    db.expire_all()
    assert db.get(Document, normal.id).is_deleted is False


def test_m2_ghi_hdld_thieu_document_write_thi_can_va_route_deu_tu_choi(ctx):
    world, db, d = ctx["world"], ctx["db"], ctx["doc"]
    # khongphong: labor_contract.write nhưng chỉ document.read
    world.grant("khongphong", "labor_contract", "company", actions=("read", "write"))
    world.grant("khongphong", "document", "company", actions=("read",))
    perm_cache_clear(world.user_id("khongphong"))
    a2 = ctx["client_as"](world.actor("khongphong"))
    perms = a2.get(f"/api/documents/{d.id}/permissions").json()["data"]
    assert perms["write"] is False                       # /permissions khớp route (route cũng từ chối)
    assert a2.patch(f"/api/documents/{d.id}", json={"storage_location": "x"}).status_code == 403


def test_m2_422_khi_gui_company_id_null_thay_vi_500(ctx):
    r = ctx["c"]["a1"].patch(f"/api/documents/{ctx['doc'].id}", json={"company_id": None})
    assert r.status_code == 422, r.text
    r = ctx["c"]["a1"].patch(f"/api/documents/{ctx['doc'].id}", json={"doc_type_id": None})
    assert r.status_code == 422, r.text


def test_dat_ban_luu_tru_vao_thu_muc_nguoi_ghi_duoc_thu_muc_moi_thi_khong(ctx):
    from app.modules.doc_catalog import folder_root_service, folder_service
    from app.modules.doc_catalog.folder_schema import FolderCreate
    from app.modules.doc_catalog.folder_access_service import role_level_cap
    from app.core.auth import get_perm_profile
    world, db, d, hr = ctx["world"], ctx["db"], ctx["doc"], ctx["c"]["a1"]
    root = folder_root_service.get_or_create_company_root(db, world.co["A"])
    sub = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Hồ sơ nhân sự"), 0)
    db.commit()
    r = hr.put(f"/api/documents/{d.id}/folders", json={"folder_ids": [sub.id], "primary_id": sub.id})
    assert r.status_code == 200, r.text
    got = hr.get(f"/api/documents/{d.id}").json()["data"]["folders"]
    assert [f["id"] for f in got] == [sub.id]
    # trần quyền: chỉ có document.write ⇒ ĐÓNG GÓP (gắn được văn bản), KHÔNG Quản lý (+ Mới / Thêm thư mục con)
    prof = get_perm_profile(db, world.actor("a1").user)
    from app.modules.doc_catalog.folder_constants import FolderAccessLevel
    assert role_level_cap(prof) == int(FolderAccessLevel.CONTRIBUTE)
    assert role_level_cap({"perms_union": {"document": {"create": True}}}) == int(FolderAccessLevel.MANAGE)
    assert role_level_cap({"perms_union": {"doc_folder": {"write": True}}}) == int(FolderAccessLevel.MANAGE)
    assert role_level_cap({"perms_union": {"document": {"read": True}}}) == int(FolderAccessLevel.VIEW)
