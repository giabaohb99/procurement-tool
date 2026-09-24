"""GẮN VĂN BẢN VÀO THƯ MỤC (duoc-CR-475, phase 03) — `folder_link_service` +
`folder_link_bulk_service` + móc nối ở `document/service.py` và `clone_service.py`.

Ba luật kiểm xuyên suốt (`plan.md` §"Luật phải giữ"):
  * mọi văn bản luôn có ≥ 1 thư mục — không có văn bản mồ côi;
  * đúng MỘT thư mục chính tại mọi thời điểm;
  * thư mục mặc định của loại → thư mục pháp nhân, theo đúng thứ tự ưu tiên.
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog import folder_link_bulk_service, folder_link_service, folder_root_service, folder_service
from app.modules.doc_catalog.folder_constants import FolderKind, FolderStatus
from app.modules.doc_catalog.folder_link_model import DocumentFolderLink
from app.modules.doc_catalog.folder_model import DocFolder
from app.modules.doc_catalog.folder_schema import FolderCreate
from app.modules.doc_catalog.model import DocType
from app.modules.document import clone_service, service
from app.modules.document.model import ORIGIN_INTERNAL, STATUS_EFFECTIVE, Document
from app.modules.document.schema import DocumentCreate
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

ACTOR = 1


def _company_root(db, company_id: int) -> DocFolder:
    return (
        db.query(DocFolder)
        .filter(DocFolder.company_id == company_id, DocFolder.kind == int(FolderKind.COMPANY))
        .one()
    )


def _doc(db, *, company_id, created_by=0, code="X"):
    row = Document(origin=ORIGIN_INTERNAL, doc_type_id=0, company_id=company_id,
                   department_id=0, owner_employee_id=0, title=f"Văn bản {code}",
                   legacy_code=code, created_by=created_by, updated_by=created_by)
    db.add(row)
    db.flush()
    return row


# ── Thư mục mặc định lúc tạo văn bản (qua service.create_document thật) ────
def test_tao_van_ban_khong_chon_thu_muc_roi_vao_thu_muc_phap_nhan(db, seed):
    folder_root_service.ensure_company_roots(db)
    doc_type = DocType(code="TB1", name="Thông báo", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Thông báo A", content_html="<p>x</p>",
    ), ACTOR)

    root = _company_root(db, seed.company_id)
    link = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).one()
    assert link.folder_id == root.id
    assert link.is_primary is True


def test_tao_van_ban_uu_tien_thu_muc_mac_dinh_cua_loai(db, seed):
    folder_root_service.ensure_company_roots(db)
    root = _company_root(db, seed.company_id)
    target = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Thông báo"), 0)
    doc_type = DocType(code="TB2", name="Thông báo 2", id_scheme=1, number_when=2,
                       default_folder_id=target.id)
    db.add(doc_type)
    db.commit()

    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Thông báo B", content_html="<p>x</p>",
    ), ACTOR)

    link = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).one()
    assert link.folder_id == target.id


def test_thu_muc_mac_dinh_cua_loai_sai_phap_nhan_thi_bo_qua(db, seed, world):
    """`default_folder_id` trỏ vào thư mục của MỘT pháp nhân khác → rơi về
    thư mục pháp nhân của chính văn bản, không dùng nhầm thư mục kia."""
    folder_root_service.ensure_company_roots(db)
    other_root = _company_root(db, world.co["A"])
    doc_type = DocType(code="TB3", name="Thông báo 3", id_scheme=1, number_when=2,
                       default_folder_id=other_root.id)
    db.add(doc_type)
    db.commit()

    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Thông báo C", content_html="<p>x</p>",
    ), ACTOR)

    my_root = _company_root(db, seed.company_id)
    link = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).one()
    assert link.folder_id == my_root.id


# ── Đúng một thư mục chính, không mồ côi ────────────────────────────────────
def test_set_folders_dung_mot_thu_muc_chinh(db, world):
    folder_root_service.ensure_company_roots(db)
    root = _company_root(db, world.co["A"])
    f1 = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="F1"), 0)
    f2 = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="F2"), 0)
    doc = _doc(db, company_id=world.co["A"])

    rows = folder_link_service.set_folders(db, doc, [f1.id, f2.id], f2.id, 0)
    primaries = [r for r in rows if r.is_primary]
    assert len(primaries) == 1
    assert primaries[0].folder_id == f2.id


def test_add_khong_tao_primary_thu_hai(db, world):
    folder_root_service.ensure_company_roots(db)
    root = _company_root(db, world.co["A"])
    f1 = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="F1"), 0)
    f2 = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="F2"), 0)
    doc = _doc(db, company_id=world.co["A"])

    folder_link_service.add(db, doc, f1.id, 0)
    folder_link_service.add(db, doc, f2.id, 0)

    rows = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).all()
    assert len(rows) == 2
    assert sum(1 for r in rows if r.is_primary) == 1


def test_go_thu_muc_cuoi_cung_tu_quay_ve_thu_muc_phap_nhan(db, world):
    folder_root_service.ensure_company_roots(db)
    root = _company_root(db, world.co["A"])
    only = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Chỉ nó"), 0)
    doc = _doc(db, company_id=world.co["A"])
    folder_link_service.add(db, doc, only.id, 0)

    folder_link_service.remove(db, doc, only.id, 0)

    rows = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).all()
    assert len(rows) == 1
    assert rows[0].folder_id == root.id
    assert rows[0].is_primary is True


def test_go_mot_trong_hai_thu_muc_thi_khong_ve_goc(db, world):
    """Còn thư mục khác thì KHÔNG kích hoạt lưới đỡ — chỉ đúng thư mục cuối
    cùng mới quay về pháp nhân."""
    folder_root_service.ensure_company_roots(db)
    root = _company_root(db, world.co["A"])
    f1 = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="F1"), 0)
    f2 = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="F2"), 0)
    doc = _doc(db, company_id=world.co["A"])
    folder_link_service.add(db, doc, f1.id, 0)
    folder_link_service.add(db, doc, f2.id, 0)

    folder_link_service.remove(db, doc, f1.id, 0)

    rows = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).all()
    assert {r.folder_id for r in rows} == {f2.id}
    assert rows[0].is_primary is True   # dòng còn lại tự lên làm chính


def test_gan_vao_thu_muc_phap_nhan_khac_duoc(db, world):
    #  Luật cũ «bị chặn» BỎ ngày 24/09/2026 (đại ca chốt: thư mục là chỗ người
    #  dùng tự sắp xếp, không buộc theo pháp nhân) — bài kiểm lật lại theo luật mới.
    folder_root_service.ensure_company_roots(db)
    root_b = _company_root(db, world.co["B"])
    doc = _doc(db, company_id=world.co["A"])
    folder_link_service.add(db, doc, root_b.id, 0)
    assert db.query(DocumentFolderLink).filter_by(document_id=doc.id, folder_id=root_b.id).count() == 1


def test_gan_thu_muc_ngung_dung_bi_chan(db, world):
    folder_root_service.ensure_company_roots(db)
    root = _company_root(db, world.co["A"])
    f1 = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="F1"), 0)
    from app.modules.doc_catalog.folder_schema import FolderUpdate
    folder_service.update_folder(db, f1, FolderUpdate(status=int(FolderStatus.ARCHIVED)), 0)
    doc = _doc(db, company_id=world.co["A"])
    with pytest.raises(HTTPException) as exc:
        folder_link_service.add(db, doc, f1.id, 0)
    assert exc.value.status_code == 400


# ── Đổi pháp nhân ────────────────────────────────────────────────────────
def test_doi_phap_nhan_chi_dang_o_thu_muc_goc_cu_thi_tu_chuyen(db, world):
    folder_root_service.ensure_company_roots(db)
    doc = _doc(db, company_id=world.co["A"])
    folder_link_service.ensure_not_orphan(db, doc, 0)   # vào thư mục pháp nhân A

    doc.company_id = world.co["B"]
    db.commit()
    folder_link_service.on_company_change(db, doc, world.co["A"], 0)

    root_b = _company_root(db, world.co["B"])
    link = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).one()
    assert link.folder_id == root_b.id


def test_doi_phap_nhan_van_ban_da_chon_thu_muc_thuong_thi_giu_nguyen(db, world):
    """Văn bản đã có thư mục THƯỜNG tự chọn (không phải thư mục pháp nhân) —
    đổi pháp nhân KHÔNG được đụng vào lựa chọn đó."""
    folder_root_service.ensure_company_roots(db)
    root_a = _company_root(db, world.co["A"])
    custom = folder_service.create_folder(db, FolderCreate(parent_id=root_a.id, name="Tự chọn"), 0)
    doc = _doc(db, company_id=world.co["A"])
    folder_link_service.add(db, doc, custom.id, 0)

    doc.company_id = world.co["B"]
    db.commit()
    folder_link_service.on_company_change(db, doc, world.co["A"], 0)

    link = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).one()
    assert link.folder_id == custom.id   # không đổi


# ── Bản sao (clone) vào thư mục pháp nhân của pháp nhân nhận ───────────────
def test_ban_sao_tu_dong_vao_thu_muc_phap_nhan_dich(db, seed):
    folder_root_service.ensure_company_roots(db)
    dest = Company(name="Công ty con", code="CONX", is_active=True, parent=seed.company_id)
    doc_type = DocType(code="QCX", name="Quy chế X", id_scheme=1, number_when=2)
    db.add_all([dest, doc_type])
    db.commit()
    folder_root_service.ensure_company_roots(db)   # thêm thư mục gốc cho `dest`

    origin = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế cần sao", content_html="<p>x</p>",
    ), ACTOR)
    origin.status = STATUS_EFFECTIVE
    db.commit()

    clones = clone_service.create_clones(db, origin, [dest.id], None, "", ACTOR)
    clone = clones[0]

    dest_root = _company_root(db, dest.id)
    link = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == clone.id).one()
    assert link.folder_id == dest_root.id
    assert link.is_primary is True


# ── Hàng loạt: một dòng bị từ chối không chặn cả lô ─────────────────────────
def test_move_documents_lo_co_dong_bi_tu_choi(db, world):
    folder_root_service.ensure_company_roots(db)
    root_a = _company_root(db, world.co["A"])
    target = folder_service.create_folder(db, FolderCreate(parent_id=root_a.id, name="Đích"), 0)

    actor = world.grant("a1", "document", scope="company", actions=("read", "write"))
    ok_doc = _doc(db, company_id=world.co["A"], code="OK")
    #  Văn bản của công ty B — actor chỉ có phạm vi công ty A nên không sửa được.
    denied_doc = _doc(db, company_id=world.co["B"], code="DENY")
    db.commit()

    result = folder_link_bulk_service.move_documents(
        db, [ok_doc.id, denied_doc.id], target.id, "add", actor.user, actor.profile(), 0)

    assert result["moved"] == [ok_doc.id]
    assert len(result["denied"]) == 1
    assert result["denied"][0]["id"] == denied_doc.id


# ── H3 (rà soát 23/09/2026) — kiểm thư mục TRƯỚC khi ghi văn bản ────────────
def test_tao_van_ban_vao_thu_muc_phap_nhan_khac_duoc(db, seed, world):
    """Luật cũ chặn thư mục khác pháp nhân — BỎ 24/09/2026. Luật «chặn TRƯỚC
    khi ghi» vẫn được canh ở bài thư mục NGỪNG DÙNG ngay dưới."""
    folder_root_service.ensure_company_roots(db)
    root_b = _company_root(db, world.co["B"])
    doc_type = DocType(code="H3A", name="Loại thử H3", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Khác pháp nhân H3",
        content_html="<p>x</p>", folder_ids=[root_b.id],
    ), ACTOR)
    assert db.query(Document).filter(Document.title == "Khác pháp nhân H3").count() == 1


def test_tao_van_ban_thu_muc_ngung_dung_khong_luu_gi_ca(db, seed):
    """Cùng luật, nhánh KHÁC: thư mục tồn tại, đúng pháp nhân, nhưng đang
    NGỪNG DÙNG — cũng phải chặn TRƯỚC khi ghi, không phải sau."""
    folder_root_service.ensure_company_roots(db)
    root = _company_root(db, seed.company_id)
    stopped = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Ngừng dùng H3"), 0)
    from app.modules.doc_catalog.folder_schema import FolderUpdate
    folder_service.update_folder(db, stopped, FolderUpdate(status=int(FolderStatus.ARCHIVED)), 0)
    doc_type = DocType(code="H3B", name="Loại thử H3B", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        service.create_document(db, DocumentCreate(
            doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
            owner_employee_id=seed.emp_req_id, title="Thư mục ngừng dùng H3",
            content_html="<p>x</p>", folder_ids=[stopped.id],
        ), ACTOR)
    assert exc.value.status_code == 400
    assert db.query(Document).filter(Document.title == "Thư mục ngừng dùng H3").count() == 0


def test_tao_van_ban_company_id_0_khong_loi_khong_co_thu_muc(db):
    """`company_id=0` (đơn nghỉ phép của nhân sự chưa gắn pháp nhân, …) CỐ Ý
    không có gốc pháp nhân nào để rơi về — KHÔNG được raise, KHÔNG được coi là
    lỗi dữ liệu (H3)."""
    doc_type = DocType(code="H3C", name="Loại chưa gắn pháp nhân", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=0, department_id=0,
        owner_employee_id=0, title="Chưa gắn pháp nhân H3", content_html="<p>x</p>",
    ), ACTOR)

    assert db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).count() == 0


# ── H1 (rà soát 23/09/2026) — sao chép/trích/clone không mồ côi, lên chỉ mục ──
def test_sao_chep_van_ban_co_thu_muc_va_len_chi_muc(db, seed, monkeypatch):
    """`POST /{id}/copy` trước đây không gắn thư mục nào (mồ côi, không hiện
    trên cây) và không lên chỉ mục tìm kiếm cho tới khi ai chạy script tay."""
    from app.core.config import settings as core_settings
    from app.modules.document import duplicate_service
    from app.modules.document.search_model import DocumentSearch

    monkeypatch.setattr(core_settings, "DOCUMENT_SEARCH_INDEX_SYNC", True)
    folder_root_service.ensure_company_roots(db)
    doc_type = DocType(code="H1A", name="Loại thử sao chép", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    source = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Bản gốc để sao",
        content_html="<p>Nội dung gốc</p>",
    ), ACTOR)

    copy = duplicate_service.duplicate(db, source, ACTOR)

    assert db.query(DocumentFolderLink).filter(
        DocumentFolderLink.document_id == copy.id).count() >= 1
    assert db.get(DocumentSearch, copy.id) is not None


def test_ban_trich_co_thu_muc_va_len_chi_muc(db, seed, monkeypatch):
    """Bản trích nội bộ (C19) cùng bệnh: trước đây không thư mục, không chỉ mục."""
    from app.core.config import settings as core_settings
    from app.modules.document import excerpt_service
    from app.modules.document.search_model import DocumentSearch

    monkeypatch.setattr(core_settings, "DOCUMENT_SEARCH_INDEX_SYNC", True)
    folder_root_service.ensure_company_roots(db)
    doc_type = DocType(code="H1B", name="Loại thử trích", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    source = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Bản gốc để trích",
        content_html="<p>Đầy đủ nội dung</p>",
    ), ACTOR)

    excerpt = excerpt_service.create_excerpt(
        db, source, "Bản trích H1", "<p>Một phần</p>", source.secrecy_level, "", ACTOR)

    assert db.query(DocumentFolderLink).filter(
        DocumentFolderLink.document_id == excerpt.id).count() >= 1
    assert db.get(DocumentSearch, excerpt.id) is not None


def test_ban_clone_len_chi_muc_tim_kiem(db, seed, monkeypatch):
    """Bản CLONE (xuống pháp nhân con) đã có `ensure_not_orphan` từ trước
    (không mồ côi), nhưng THIẾU `queue_reindex` — không tìm được cho tới khi
    ai chạy script tay."""
    from app.core.config import settings as core_settings
    from app.modules.document.search_model import DocumentSearch

    monkeypatch.setattr(core_settings, "DOCUMENT_SEARCH_INDEX_SYNC", True)
    folder_root_service.ensure_company_roots(db)
    dest = Company(name="Công ty con H1", code="CONH1", is_active=True, parent=seed.company_id)
    doc_type = DocType(code="H1C", name="Quy chế thử clone", id_scheme=1, number_when=2)
    db.add_all([dest, doc_type])
    db.commit()
    folder_root_service.ensure_company_roots(db)   # thêm thư mục gốc cho `dest`

    origin = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế gốc H1", content_html="<p>x</p>",
    ), ACTOR)
    origin.status = STATUS_EFFECTIVE
    db.commit()

    clones = clone_service.create_clones(db, origin, [dest.id], None, "", ACTOR)
    clone = clones[0]

    assert db.get(DocumentSearch, clone.id) is not None


def test_move_documents_khong_ton_tai_van_ban_van_bi_tu_choi(db, world):
    folder_root_service.ensure_company_roots(db)
    root_a = _company_root(db, world.co["A"])
    target = folder_service.create_folder(db, FolderCreate(parent_id=root_a.id, name="Đích"), 0)
    actor = world.grant("a1", "document", scope="company", actions=("read", "write"))

    result = folder_link_bulk_service.move_documents(
        db, [999999], target.id, "add", actor.user, actor.profile(), 0)
    assert result["moved"] == []
    assert result["denied"][0]["id"] == 999999


def test_bulk_unlink_go_dung_van_ban_duoc_phep(db, world):
    folder_root_service.ensure_company_roots(db)
    root_a = _company_root(db, world.co["A"])
    f1 = folder_service.create_folder(db, FolderCreate(parent_id=root_a.id, name="F1"), 0)
    actor = world.grant("a1", "document", scope="company", actions=("read", "write"))
    doc = _doc(db, company_id=world.co["A"])
    folder_link_service.add(db, doc, f1.id, 0)
    db.commit()

    result = folder_link_bulk_service.bulk_unlink(
        db, [doc.id], f1.id, actor.user, actor.profile(), 0)

    assert result["moved"] == [doc.id]
    #  Gỡ khỏi thư mục cuối cùng → tự quay về thư mục pháp nhân (không mồ côi).
    link = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).one()
    assert link.folder_id == root_a.id
