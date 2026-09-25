"""CÂY THƯ MỤC VĂN BẢN (duoc-CR-475, phase 03) — `folder_service` +
`folder_move_service` + `folder_root_service` + `folder_tree_service`.

Dựng dữ liệu trên thế giới mẫu của cụm 00 (`scope_factory.build_world`) — hai
pháp nhân A/B sẵn có, đủ để kiểm luật "thư mục thường không chuyển được sang
pháp nhân khác".
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import event

from app.modules.doc_catalog import folder_move_service, folder_root_service, folder_service, folder_tree_service
from app.modules.doc_catalog.folder_constants import MAX_DEPTH, FolderKind, FolderStatus
from app.modules.doc_catalog.folder_link_model import DocumentFolderLink
from app.modules.doc_catalog.folder_model import DocFolder
from app.modules.doc_catalog.folder_schema import FolderCreate, FolderUpdate
from app.modules.document.model import ORIGIN_INTERNAL, Document
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó


def _doc(db, *, company_id, created_by=0, code="X"):
    row = Document(origin=ORIGIN_INTERNAL, doc_type_id=0, company_id=company_id,
                   department_id=0, owner_employee_id=0, title=f"Văn bản {code}",
                   legacy_code=code, created_by=created_by, updated_by=created_by)
    db.add(row)
    db.flush()
    return row


def _count_queries(engine, fn):
    """Số câu SQL thực thi trong `fn()` — dùng để chứng minh `tree()` không
    phình theo số thư mục (Rủi ro §"số truy vấn cố định" của phase-03)."""
    count = {"n": 0}

    def _before(*_a, **_k):
        count["n"] += 1

    event.listen(engine, "before_cursor_execute", _before)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", _before)
    return count["n"]


@pytest.fixture()
def roots(db, world):
    created = folder_root_service.ensure_company_roots(db)
    return {f.company_id: f for f in created}


# ── Thư mục pháp nhân (gốc) ──────────────────────────────────────────────
def test_ensure_company_roots_moi_cong_ty_mot_thu_muc(db, world, roots):
    assert set(roots.keys()) == {world.co["A"], world.co["B"]}
    #  24/09/2026: thư mục pháp nhân nằm TRONG thư mục nhóm «Công ty» (cấp 2),
    #  không còn đứng thẳng ở gốc cây.
    group = folder_root_service.get_or_create_company_group(db)
    for folder in roots.values():
        assert folder.kind == int(FolderKind.COMPANY)
        assert folder.depth == 2
        assert folder.parent_id == group.id
        assert folder.path == f"{group.path}{folder.id}/"
        assert folder.name == ""  # tên lấy từ Company lúc đọc, không lưu ở đây


def test_ensure_company_roots_goi_lai_khong_tao_trung(db, world, roots):
    again = folder_root_service.ensure_company_roots(db)
    assert again == []
    assert db.query(DocFolder).filter(DocFolder.kind == int(FolderKind.COMPANY)).count() == 2


# ── M8 (rà soát 23/09/2026) — chặn HAI gốc trùng company_id ─────────────────
def test_ux_root_company_chan_hai_goc_trung_cong_ty(db, roots):
    """Chỉ mục UNIQUE `ux_doc_folder_root_company` phải CHẶN được ở tầng DB —
    điều kiện cần để `ensure_company_roots` bắt `IntegrityError` mà tự vá."""
    from sqlalchemy.exc import IntegrityError

    root = next(iter(roots.values()))
    dup = DocFolder(company_id=root.company_id, root_company_id=root.company_id,
                    parent_id=0, kind=int(FolderKind.COMPANY), name="", path="/999999/",
                    depth=1, sort_order=0, status=int(FolderStatus.ACTIVE))
    db.add(dup)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_ensure_company_roots_dua_tao_trung_tu_vet_duoc(db, world, roots, monkeypatch):
    """Giả lập ĐUA (M8): một giao dịch KHÁC thắng cuộc, chèn xong gốc của công
    ty ngay lúc `ensure_company_roots` cũng đang cố chèn — `db.flush()` ném
    `IntegrityError`. Hàm phải BẮT, `rollback()`, KHÔNG crash, không tạo gốc
    thứ hai — trả về danh sách KHÔNG có công ty đó (thua cuộc, dùng gốc của
    người thắng, không tự thêm)."""
    from sqlalchemy.exc import IntegrityError

    from app.modules.company.model import Company

    new_co = Company(name="Cty đua", code="DUA", is_active=True)
    db.add(new_co)
    db.commit()   # roots fixture đã tạo gốc cho A/B — new_co là công ty DUY
                  # NHẤT chưa có gốc, nên vòng lặp chỉ `flush()` đúng một lần.

    real_flush = db.flush
    calls = {"n": 0}

    def _thua_cuoc_dua(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed"))
        return real_flush(*a, **k)

    monkeypatch.setattr(db, "flush", _thua_cuoc_dua)

    created = folder_root_service.ensure_company_roots(db)

    assert calls["n"] == 1
    assert new_co.id not in {f.company_id for f in created}
    #  Session vẫn DÙNG ĐƯỢC sau rollback — không phải "đứng hình" transaction.
    assert db.query(Company.id).filter(Company.id == new_co.id).first() is not None


# ── Tạo / đổi tên ─────────────────────────────────────────────────────────
def test_tao_thu_muc_con_tinh_dung_path_va_depth(db, world, roots):
    root = roots[world.co["A"]]
    child = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Hợp đồng"), 0)
    assert child.path == f"{root.path}{child.id}/"
    assert child.depth == root.depth + 1
    assert child.company_id == root.company_id
    assert child.kind == int(FolderKind.NORMAL)


def test_tao_thu_muc_trung_ten_anh_em_gap_dau_bi_chan(db, world, roots):
    """«Hợp đồng» và «hợp đồng» (khác hoa/thường, có dấu) phải coi là TRÙNG."""
    root = roots[world.co["A"]]
    folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Hợp đồng"), 0)
    with pytest.raises(HTTPException) as exc:
        folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="hợp đồng"), 0)
    assert exc.value.status_code == 400


def test_tao_thu_muc_khac_cha_khong_bi_coi_la_trung(db, world, roots):
    """Cùng tên nhưng KHÁC cha (khác nhánh) thì không chặn."""
    root = roots[world.co["A"]]
    folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Hợp đồng"), 0)
    sibling_parent = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="2026"), 0)
    dup = folder_service.create_folder(db, FolderCreate(parent_id=sibling_parent.id, name="Hợp đồng"), 0)
    assert dup.name == "Hợp đồng"


def test_tao_thu_muc_thieu_cha_bi_chan(db):
    """`parent_id=0` không tạo được thư mục thường — cả ở lớp service, không
    chỉ ở ràng buộc `gt=0` của schema (phòng khi có đường gọi khác API)."""
    with pytest.raises(HTTPException) as exc:
        folder_service._get_active_parent_or_400(db, 0)
    assert exc.value.status_code == 400


def test_tao_thu_muc_sau_qua_muc_toi_da_bi_chan(db, world, roots):
    """Gốc = cấp 1. Tạo tới cấp `MAX_DEPTH` thì hợp lệ; cấp `MAX_DEPTH + 1` bị chặn."""
    parent = roots[world.co["A"]]
    for depth in range(parent.depth + 1, MAX_DEPTH + 1):
        parent = folder_service.create_folder(
            db, FolderCreate(parent_id=parent.id, name=f"Cấp {depth}"), 0)
        assert parent.depth == depth
    with pytest.raises(HTTPException) as exc:
        folder_service.create_folder(db, FolderCreate(parent_id=parent.id, name="Quá sâu"), 0)
    assert exc.value.status_code == 400


def test_doi_ten_thu_muc_phap_nhan_duoc(db, world, roots):
    #  Luật cũ «bị chặn» BỎ ngày 24/09/2026 (đại ca chốt: thư mục là chỗ người
    #  dùng tự sắp xếp, không buộc theo pháp nhân) — bài kiểm lật lại theo luật mới.
    root = roots[world.co["A"]]
    folder_service.update_folder(db, root, FolderUpdate(name="Kho lưu trữ A"), 0)
    db.refresh(root)
    assert root.name == "Kho lưu trữ A"


# ── Chuyển cha (move) ────────────────────────────────────────────────────
def test_chuyen_thu_muc_cap_nhat_dung_path_ca_nhanh(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    b = folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="B"), 0)
    c = folder_service.create_folder(db, FolderCreate(parent_id=b.id, name="C"), 0)
    other = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Khác"), 0)

    folder_move_service.move_folder(db, a, other.id, 0)
    db.refresh(a); db.refresh(b); db.refresh(c)

    assert a.parent_id == other.id
    assert a.path == f"{other.path}{a.id}/"
    assert a.depth == other.depth + 1
    #  Hậu duệ B, C phải đổi THEO — cùng một câu UPDATE, không đệ quy.
    assert b.path == f"{a.path}{b.id}/"
    assert b.depth == a.depth + 1
    assert c.path == f"{b.path}{c.id}/"
    assert c.depth == b.depth + 1


def test_chuyen_vao_vong_lap_bi_chan(db, world, roots):
    """A → B → C, chuyển A vào TRONG C (hậu duệ của chính A) phải bị chặn."""
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    b = folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="B"), 0)
    c = folder_service.create_folder(db, FolderCreate(parent_id=b.id, name="C"), 0)

    with pytest.raises(HTTPException) as exc:
        folder_move_service.move_folder(db, a, c.id, 0)
    assert exc.value.status_code == 400


def test_chuyen_vao_chinh_no_bi_chan(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    with pytest.raises(HTTPException):
        folder_move_service.move_folder(db, a, a.id, 0)


def test_chuyen_thu_muc_phap_nhan_vao_goc_khac_duoc(db, world, roots):
    #  Luật cũ «bị chặn» BỎ ngày 24/09/2026 (đại ca chốt: thư mục là chỗ người
    #  dùng tự sắp xếp, không buộc theo pháp nhân) — bài kiểm lật lại theo luật mới.
    root_a = roots[world.co["A"]]
    root_b = roots[world.co["B"]]
    folder_move_service.move_folder(db, root_a, root_b.id, 0)
    db.refresh(root_a)
    assert root_a.parent_id == root_b.id
    assert root_a.path == f"{root_b.path}{root_a.id}/"
    assert root_a.company_id == world.co["A"]   # pháp nhân của thư mục KHÔNG đổi theo chỗ mới


def test_chuyen_ra_goc_cay_roi_chuyen_lai(db, world, roots):
    root_a = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root_a.id, name="A"), 0)
    sub = folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="Con"), 0)
    folder_move_service.move_folder(db, a, 0, 0)
    db.refresh(a)
    db.refresh(sub)
    assert (a.parent_id, a.path, a.depth) == (0, f"/{a.id}/", 1)
    assert (sub.path, sub.depth) == (f"/{a.id}/{sub.id}/", 2)
    folder_move_service.move_folder(db, a, root_a.id, 0)
    db.refresh(sub)
    assert sub.path == f"{root_a.path}{a.id}/{sub.id}/"


def test_chuyen_goc_vao_chinh_con_cua_no_van_bi_chan(db, world, roots):
    """Nới pháp nhân KHÔNG được nới luật chống vòng."""
    root_a = roots[world.co["A"]]
    child = folder_service.create_folder(db, FolderCreate(parent_id=root_a.id, name="Con"), 0)
    with pytest.raises(HTTPException) as exc:
        folder_move_service.move_folder(db, root_a, child.id, 0)
    assert exc.value.status_code == 400


def test_chuyen_sang_nhanh_phap_nhan_khac_duoc(db, world, roots):
    #  Luật cũ «bị chặn» BỎ ngày 24/09/2026 (đại ca chốt: thư mục là chỗ người
    #  dùng tự sắp xếp, không buộc theo pháp nhân) — bài kiểm lật lại theo luật mới.
    root_a = roots[world.co["A"]]
    root_b = roots[world.co["B"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root_a.id, name="A"), 0)
    target = folder_service.create_folder(db, FolderCreate(parent_id=root_b.id, name="Đích"), 0)
    folder_move_service.move_folder(db, a, target.id, 0)
    db.refresh(a)
    assert a.parent_id == target.id


def test_chuyen_vuot_do_sau_toi_da_bi_chan(db, world, roots):
    """Một nhánh cao 2 cấp (A→B) chuyển vào một đích đã ở cấp `MAX_DEPTH` là vượt trần."""
    root = roots[world.co["A"]]
    deep = root
    for depth in range(root.depth + 1, MAX_DEPTH + 1):
        deep = folder_service.create_folder(db, FolderCreate(parent_id=deep.id, name=f"D{depth}"), 0)
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="B"), 0)  # A cao 2 cấp

    with pytest.raises(HTTPException) as exc:
        folder_move_service.move_folder(db, a, deep.id, 0)
    assert exc.value.status_code == 400


# ── Sắp thứ tự anh em ─────────────────────────────────────────────────────
def test_sap_thu_tu_khac_cha_bi_chan(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    b = folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="B"), 0)
    with pytest.raises(HTTPException) as exc:
        folder_service.reorder_siblings(
            db, [{"id": a.id, "sort_order": 1}, {"id": b.id, "sort_order": 2}], 0)
    assert exc.value.status_code == 400


# ── Ngừng dùng cả nhánh / khôi phục / xóa ──────────────────────────────────
def test_ngung_dung_keo_ca_nhanh_khoi_phuc_chi_dung_no(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    b = folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="B"), 0)

    folder_service.update_folder(db, a, FolderUpdate(status=int(FolderStatus.ARCHIVED)), 0)
    db.refresh(a); db.refresh(b)
    assert a.status == int(FolderStatus.ARCHIVED)
    assert b.status == int(FolderStatus.ARCHIVED)   # kéo theo cả nhánh

    folder_service.update_folder(db, a, FolderUpdate(status=int(FolderStatus.ACTIVE)), 0)
    db.refresh(a); db.refresh(b)
    assert a.status == int(FolderStatus.ACTIVE)
    assert b.status == int(FolderStatus.ARCHIVED)   # khôi phục KHÔNG kéo con


def test_xoa_thu_muc_con_con_bi_chan(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="B"), 0)
    with pytest.raises(HTTPException) as exc:
        folder_service.delete_folder(db, a, 0)
    assert exc.value.status_code == 400


# ── Xóa thư mục CÒN văn bản (đại ca chốt 25/09/2026 — trước đó chặn cứng) ───
def _links(db, doc_id):
    return {(r.folder_id, r.is_primary) for r in
            db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc_id)}


def test_xoa_thu_muc_con_van_ban_chuyen_van_ban_mo_coi_sang_thu_muc_da_chon(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    dich = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Đích"), 0)
    doc = _doc(db, company_id=root.company_id)
    db.add(DocumentFolderLink(document_id=doc.id, folder_id=a.id, is_primary=True))
    db.commit()
    folder_service.delete_folder(db, a, 0, dich)
    assert db.get(DocFolder, a.id) is None
    assert db.get(Document, doc.id) is not None          # văn bản KHÔNG bị xóa theo
    assert _links(db, doc.id) == {(dich.id, True)}


def test_xoa_thu_muc_khong_chon_dich_van_ban_mo_coi_ve_thu_muc_phap_nhan(db, world, roots):
    #  Xóa hàng loạt không hỏi đích — luật «không mồ côi» có sẵn đỡ lấy.
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    doc = _doc(db, company_id=root.company_id)
    db.add(DocumentFolderLink(document_id=doc.id, folder_id=a.id, is_primary=True))
    db.commit()
    folder_service.delete_folder(db, a, 0)
    assert _links(db, doc.id) == {(root.id, True)}


def test_xoa_thu_muc_van_ban_con_o_noi_khac_chi_bi_go_va_doi_thu_muc_chinh(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    b = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="B"), 0)
    dich = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Đích"), 0)
    doc = _doc(db, company_id=root.company_id)
    db.add(DocumentFolderLink(document_id=doc.id, folder_id=a.id, is_primary=True))
    db.add(DocumentFolderLink(document_id=doc.id, folder_id=b.id, is_primary=False))
    db.commit()
    folder_service.delete_folder(db, a, 0, dich)
    #  KHÔNG bị kéo sang «Đích» — nó vẫn còn chỗ ở, và B lên làm thư mục chính.
    assert _links(db, doc.id) == {(b.id, True)}


def test_xem_truoc_xoa_dem_van_ban_va_van_ban_se_mo_coi(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    b = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="B"), 0)
    chi_o_a = _doc(db, company_id=root.company_id, code="X1")
    o_ca_hai = _doc(db, company_id=root.company_id, code="X2")
    db.add(DocumentFolderLink(document_id=chi_o_a.id, folder_id=a.id, is_primary=True))
    db.add(DocumentFolderLink(document_id=o_ca_hai.id, folder_id=a.id, is_primary=True))
    db.add(DocumentFolderLink(document_id=o_ca_hai.id, folder_id=b.id, is_primary=False))
    db.commit()
    preview = folder_service.delete_preview(db, a)
    assert preview == {"blocked_reason": "", "document_count": 2, "orphan_count": 1,
                       "parent_id": root.id}


def test_xem_truoc_xoa_bao_ly_do_khi_con_thu_muc_con(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="B"), 0)
    assert "thư mục con" in folder_service.delete_preview(db, a)["blocked_reason"]


def test_xoa_thu_muc_khong_cho_chuyen_van_ban_vao_chinh_no(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    with pytest.raises(HTTPException) as exc:
        folder_service.delete_folder(db, a, 0, a)
    assert exc.value.status_code == 400
    assert db.get(DocFolder, a.id) is not None


def test_xoa_thu_muc_khong_cho_chuyen_vao_thu_muc_ngung_dung(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    cu = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Cũ"), 0)
    folder_service.update_folder(db, cu, FolderUpdate(status=int(FolderStatus.ARCHIVED)), 0)
    with pytest.raises(HTTPException) as exc:
        folder_service.delete_folder(db, a, 0, cu)
    assert exc.value.status_code == 400


def test_xoa_thu_muc_rong_thanh_cong(db, world, roots):
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    folder_service.delete_folder(db, a, 0)
    assert db.get(DocFolder, a.id) is None


# ── Thư mục PHÁP NHÂN xóa được như thư mục thường (rà soát 24/09/2026) ──────
def test_xoa_thu_muc_phap_nhan_bi_chan_ke_ca_khi_rong(db, world, roots):
    """Đại ca chốt 24/09/2026 (ĐẢO quyết định cho xóa gốc trước đó cùng ngày):
    thư mục pháp nhân KHÔNG xóa được, kể cả khi rỗng."""
    root = roots[world.co["A"]]
    with pytest.raises(HTTPException) as exc:
        folder_service.delete_folder(db, root, 0)
    assert exc.value.status_code == 400
    assert db.get(DocFolder, root.id) is not None


def test_nhom_cong_ty_chi_mot_dong_khong_xoa_khong_chuyen(db, world, roots):
    group = folder_root_service.get_or_create_company_group(db)
    assert folder_root_service.get_or_create_company_group(db).id == group.id
    assert db.query(DocFolder).filter(DocFolder.kind == int(FolderKind.COMPANY_GROUP)).count() == 1
    assert (group.parent_id, group.company_id, group.depth) == (0, 0, 1)
    with pytest.raises(HTTPException):
        folder_service.delete_folder(db, group, 0)
    other = folder_service.create_folder(db, FolderCreate(parent_id=roots[world.co["B"]].id, name="Đích"), 0)
    with pytest.raises(HTTPException):
        folder_move_service.move_folder(db, group, other.id, 0)


def _drop_root_directly(db, root):
    """Gốc pháp nhân KHÔNG xóa được qua service nữa (24/09/2026) — mô phỏng dữ
    liệu thiếu gốc (xóa tay trong DB, gốc chưa từng được sinh) để vẫn kiểm được
    đường tự tạo lại LAZY."""
    db.delete(root)
    db.commit()


def test_xoa_thu_muc_phap_nhan_con_con_bi_chan(db, world, roots):
    root = roots[world.co["A"]]
    folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    with pytest.raises(HTTPException) as exc:
        folder_service.delete_folder(db, root, 0)
    assert exc.value.status_code == 400


def test_xoa_thu_muc_phap_nhan_con_van_ban_bi_chan(db, world, roots):
    root = roots[world.co["A"]]
    doc = _doc(db, company_id=root.company_id)
    db.add(DocumentFolderLink(document_id=doc.id, folder_id=root.id, is_primary=True))
    db.commit()
    with pytest.raises(HTTPException) as exc:
        folder_service.delete_folder(db, root, 0)
    assert exc.value.status_code == 400


def test_xoa_goc_khong_con_bi_khoa_ngung_dung_van_duoc(db, world, roots):
    """«Ngừng dùng» (khôi phục) vẫn là ngoại lệ ĐƯỢC PHÉP trên gốc — chỉ đổi
    tên/mô tả/mức nền là còn khóa, khoản duy nhất được nới là XÓA + Ngừng dùng."""
    root = roots[world.co["A"]]
    folder_service.update_folder(db, root, FolderUpdate(status=int(FolderStatus.ARCHIVED)), 0)
    db.refresh(root)
    assert root.status == int(FolderStatus.ARCHIVED)

    #  Đổi tên gốc nay CŨNG được (mở 24/09/2026).
    folder_service.update_folder(db, root, FolderUpdate(name="Đổi tên gốc"), 0)
    db.refresh(root)
    assert root.name == "Đổi tên gốc"


def test_xoa_goc_xong_van_ban_moi_tu_tao_lai_dung_cong_ty(db, world, roots):
    """Xóa gốc RỖNG xong, văn bản MỚI của ĐÚNG công ty đó không gắn thư mục
    nào → `ensure_not_orphan` tự tạo LẠI một gốc mới (lazy get-or-create),
    không tự mọc lại nếu không ai cần (`plan.md` §"gốc không tự mọc lại")."""
    from app.modules.doc_catalog import folder_link_service

    company_id = world.co["A"]
    other_root_id = roots[world.co["B"]].id
    root = roots[company_id]
    _drop_root_directly(db, root)
    assert db.query(DocFolder).filter(DocFolder.kind == int(FolderKind.COMPANY)).count() == 1

    doc = _doc(db, company_id=company_id)
    folder_link_service.ensure_not_orphan(db, doc, 0)

    new_root = (
        db.query(DocFolder)
        .filter(DocFolder.company_id == company_id, DocFolder.kind == int(FolderKind.COMPANY))
        .one()
    )
    assert new_root.id != root.id   # gốc MỚI, không phải hồi sinh dòng cũ
    #  Gốc sinh lại cũng nằm TRONG nhóm «Công ty», không lọt ra gốc cây.
    assert new_root.parent_id == folder_root_service.get_or_create_company_group(db).id
    link = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).one()
    assert link.folder_id == new_root.id
    #  Gốc của công ty B — KHÔNG dính chuyện gì, tạo lại gốc của A không hồi
    #  sinh/đụng vào gốc của công ty khác (khác hẳn gọi lại `ensure_company_roots`).
    assert db.get(DocFolder, other_root_id) is not None


def test_xoa_ca_hai_goc_roi_tao_van_ban_cong_ty_khac_khong_dung_lai_goc_kia(db, world, roots):
    """Xóa RỖNG cả hai gốc A và B, rồi chỉ tạo văn bản cho B — CHỈ gốc B được
    tạo lại, gốc A vẫn vắng mặt (chứng minh get-or-create SCOPED đúng một công
    ty, không lỡ tay gọi `ensure_company_roots` hồi sinh mọi gốc đã xóa)."""
    from app.modules.doc_catalog import folder_link_service

    co_a, co_b = world.co["A"], world.co["B"]
    _drop_root_directly(db, roots[co_a])
    _drop_root_directly(db, roots[co_b])
    assert db.query(DocFolder).filter(DocFolder.kind == int(FolderKind.COMPANY)).count() == 0

    doc_b = _doc(db, company_id=co_b, code="B1")
    folder_link_service.ensure_not_orphan(db, doc_b, 0)

    remaining = db.query(DocFolder).filter(DocFolder.kind == int(FolderKind.COMPANY)).all()
    assert {f.company_id for f in remaining} == {co_b}


def test_get_or_create_company_root_cong_ty_khong_ton_tai_tra_none(db, world, roots):
    assert folder_root_service.get_or_create_company_root(db, 999_999) is None


# ── Không còn tự sinh ở tạo pháp nhân (rà soát 24/09/2026) ─────────────────
def test_tao_phap_nhan_khong_tu_tao_thu_muc_goc(db):
    """`create_company` KHÔNG còn gọi `ensure_company_roots` — gốc chỉ sinh
    LAZY khi có văn bản thật sự cần, không phải ngay lúc tạo pháp nhân."""
    from app.modules.company.schema import CompanyCreate
    from app.modules.company.service import create_company

    before = db.query(DocFolder).filter(DocFolder.kind == int(FolderKind.COMPANY)).count()
    company = create_company(db, CompanyCreate(name="Cty mới, chưa cần thư mục"), 0)

    after = db.query(DocFolder).filter(DocFolder.kind == int(FolderKind.COMPANY)).count()
    assert after == before
    assert db.query(DocFolder).filter(DocFolder.company_id == company.id).count() == 0


def test_seed_khong_con_goi_ensure_company_roots(db):
    """Chốt CODE, không chỉ hành vi: `app.seed`/`app.seed_prod` không còn gọi
    `ensure_company_roots` ở đường khởi động — hồi quy kiểu "ai đó thêm lại
    lời gọi" phải đỏ ngay ở đây (cùng phong cách `inspect.getsource` với
    `test_van_ban_thu_muc_quyen.test_seed_doc_folder_write_khong_con_scope_all`)."""
    import inspect

    from app import seed, seed_prod

    #  Tìm dạng GỌI HÀM (`ensure_company_roots(`), không chặn nhắc tên suông
    #  trong lời chú thích (comment vẫn được nhắc "còn cho script vận hành").
    assert "ensure_company_roots(" not in inspect.getsource(seed), (
        "seed.py không còn được gọi ensure_company_roots — gốc bị xóa tay không "
        "được tự mọc lại mỗi lần khởi động")
    assert "ensure_company_roots(" not in inspect.getsource(seed_prod), (
        "seed_prod.py không còn được gọi ensure_company_roots — cùng lý do trên, "
        "áp cho môi trường thật (dev-UAT/prod)")


# ── Cây đọc + số đếm (folder_tree_service) ─────────────────────────────────
def test_tree_dem_truc_tiep_va_ca_nhanh_khu_trung(db, world, roots):
    """Một văn bản nằm ở HAI thư mục (A và B, B là con của A) — đếm CẢ NHÁNH
    của A chỉ tính đúng MỘT lần, không cộng dồn theo số thư mục chứa nó."""
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    b = folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="B"), 0)

    actor = world.grant("a1", "document", scope="company", actions=("read",))
    doc = _doc(db, company_id=root.company_id, created_by=actor.user.id)
    db.add_all([
        DocumentFolderLink(document_id=doc.id, folder_id=a.id, is_primary=True),
        DocumentFolderLink(document_id=doc.id, folder_id=b.id, is_primary=False),
    ])
    db.commit()

    nodes = {n["id"]: n for n in folder_tree_service.tree(db, actor.user)}
    assert nodes[a.id]["document_count"] == 1          # trực tiếp trong A
    assert nodes[a.id]["document_count_branch"] == 1    # cả nhánh — KHÔNG phải 2
    assert nodes[b.id]["document_count"] == 1
    assert nodes[b.id]["document_count_branch"] == 1


def test_get_detail_dem_ca_nhanh_gom_van_ban_thu_muc_con(db, world, roots):
    """Lỗi 24/09/2026: tiêu đề thư mục gốc ghi «0 văn bản» trong khi bảng
    (mặc định «Gồm thư mục con») liệt kê 7 — `get_detail` chỉ đưa MỘT thư mục
    vào hàm đếm nên số cả nhánh rơi về số trực tiếp. Phải khớp `tree()`."""
    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    b = folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="B"), 0)

    actor = world.grant("a1", "document", scope="company", actions=("read",))
    doc1 = _doc(db, company_id=root.company_id, created_by=actor.user.id, code="1")
    doc2 = _doc(db, company_id=root.company_id, created_by=actor.user.id, code="2")
    db.add_all([
        DocumentFolderLink(document_id=doc1.id, folder_id=b.id, is_primary=True),
        DocumentFolderLink(document_id=doc2.id, folder_id=b.id, is_primary=True),
        DocumentFolderLink(document_id=doc2.id, folder_id=a.id, is_primary=False),
    ])
    db.commit()

    detail = folder_tree_service.get_detail(db, root, actor.user)
    assert detail["document_count"] == 0           # gốc không chứa trực tiếp
    assert detail["document_count_branch"] == 2    # cả nhánh, khử trùng doc2
    nodes = {n["id"]: n for n in folder_tree_service.tree(db, actor.user)}
    assert nodes[root.id]["document_count_branch"] == detail["document_count_branch"]


def test_tree_khong_dem_van_ban_nguoi_xem_khong_doc_duoc(db, world, roots):
    """Người KHÔNG có quyền đọc văn bản thì số đếm = 0, dù thư mục vẫn hiện
    (luật "quyền thư mục không mở quyền văn bản").

    Từ phase 04 (duoc-CR-475), THẤY THƯ MỤC tự nó cũng cần quyền — `khongcty`
    không gắn pháp nhân nên không "với tới" nhánh A qua `document.read` bằng
    bất cứ bậc nào. Cấp thẳng một dòng ACL thư mục (chia sẻ xuyên rào, không
    đụng gì tới quyền văn bản) để giữ đúng ý định gốc của ca này: thấy thư mục
    ≠ đọc được văn bản bên trong.
    """
    from app.core.subject_match import SUBJECT_EMPLOYEE
    from app.modules.doc_catalog import folder_access_grant_service
    from app.modules.doc_catalog.folder_access_schema import FolderAccessGrantIn
    from app.modules.doc_catalog.folder_constants import FolderAccessLevel

    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    doc = _doc(db, company_id=root.company_id)
    db.add(DocumentFolderLink(document_id=doc.id, folder_id=a.id, is_primary=True))
    db.commit()

    #  `khongcty` không có grant nào trên entity `document` — chỉ thấy thư mục
    #  nhờ dòng CHO đích danh dưới đây, không nhờ phạm vi pháp nhân.
    no_grant = world.actor("khongcty")
    folder_access_grant_service.grant(
        db, a, FolderAccessGrantIn(subject_kind=SUBJECT_EMPLOYEE, subject_id=no_grant.employee.id,
                                   level=int(FolderAccessLevel.VIEW)),
        0)
    nodes = {n["id"]: n for n in folder_tree_service.tree(db, no_grant.user)}
    assert nodes[a.id]["document_count"] == 0
    assert nodes[a.id]["document_count_branch"] == 0


def test_tree_display_name_cong_ty_uu_tien_short_name_lui_ve_name(db, world, roots):
    """`display_name` (yêu cầu giao diện cây kiểu VS Code, 23/09/2026) — gốc
    pháp nhân ưu tiên `Company.short_name`, chưa khai thì lùi về tên đầy đủ;
    `name` giữ nguyên tên pháp lý đầy đủ ở CẢ HAI trường hợp. Thư mục thường
    không có khái niệm tên gọi tắt nên `display_name == name`."""
    from app.modules.company.model import Company

    root_a = roots[world.co["A"]]
    root_b = roots[world.co["B"]]
    company_a = db.get(Company, root_a.company_id)
    company_a.short_name = "DEGO A"
    db.commit()

    child = folder_service.create_folder(db, FolderCreate(parent_id=root_a.id, name="Hợp đồng"), 0)

    #  scope="all" (mặc định của `world.grant`) — cần thấy CẢ HAI pháp nhân để
    #  so sánh công ty đã khai short_name với công ty chưa khai.
    actor = world.grant("a1", "document")
    nodes = {n["id"]: n for n in folder_tree_service.tree(db, actor.user)}

    assert nodes[root_a.id]["display_name"] == "DEGO A"
    assert nodes[root_a.id]["name"] == company_a.name

    assert nodes[root_b.id]["display_name"] == nodes[root_b.id]["name"]  # chưa khai -> lùi về tên đầy đủ
    assert nodes[root_b.id]["display_name"] != ""

    assert nodes[child.id]["display_name"] == nodes[child.id]["name"] == "Hợp đồng"


def test_tree_so_truy_van_khong_phinh_theo_so_thu_muc(db, world, roots):
    actor = world.grant("a1", "document", scope="company", actions=("read",))
    engine = db.get_bind()

    def measure() -> int:
        #  Gọi "nóng" NGAY TRƯỚC lượt đo, không tính vào kết quả: session mặc
        #  định `expire_on_commit=True` nên `actor.user` bị đánh dấu hết hạn
        #  sau MỌI `db.commit()` xen giữa (kể cả của `create_folder` bên dưới,
        #  không liên quan tới `tree()`) — chạm vào nó tốn một câu `SELECT
        #  tab_user` một lần, không phải chi phí của chính `tree()`.
        folder_tree_service.tree(db, actor.user)
        return _count_queries(engine, lambda: folder_tree_service.tree(db, actor.user))

    small = measure()
    root = roots[world.co["A"]]
    for i in range(8):
        folder_service.create_folder(db, FolderCreate(parent_id=root.id, name=f"Thêm {i}"), 0)
    big = measure()

    assert big == small


def test_breadcrumb_map_theo_dung_thu_tu_tu_goc(db, world, roots):
    from app.modules.company.model import Company

    root = roots[world.co["A"]]
    a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A"), 0)
    b = folder_service.create_folder(db, FolderCreate(parent_id=a.id, name="B"), 0)

    crumbs = folder_tree_service.breadcrumb_map(db, {b.id})[b.id]
    group = folder_root_service.get_or_create_company_group(db)
    #  Bắt đầu từ nhóm «Công ty» (24/09/2026).
    assert [c["id"] for c in crumbs] == [group.id, root.id, a.id, b.id]
    assert crumbs[0]["name"] == "Công ty"
    #  Thư mục pháp nhân không lưu tên — breadcrumb phải rơi về TÊN CÔNG TY.
    company_name = db.get(Company, root.company_id).name
    assert crumbs[1]["name"] == company_name
    assert crumbs[2]["name"] == "A"
    assert crumbs[3]["name"] == "B"


def test_get_detail_tra_ve_default_access_hien_tai(db, world, roots):
    """`default_access` (hộp «Chia sẻ» kiểu Drive, rà UI 23/09/2026) — cột
    NULLABLE trên `DocFolder`, trước nay chỉ NHẬN qua `FolderUpdate`, chưa từng
    có mặt trong response nào nên ô chọn «Quyền chung» luôn hiện placeholder dù
    đã đặt giá trị. `_node()` (dùng chung `tree()`/`get_detail()`) nay trả kèm
    ở CHI TIẾT."""
    world.grant("a1", "doc_folder", scope="all", actions=("read", "write"))
    a1 = world.actor("a1")
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Chưa đặt"), 0)

    detail = folder_tree_service.get_detail(db, folder, a1.user)
    assert detail["default_access"] is None

    folder_service.update_folder(db, folder, FolderUpdate(default_access=1), 0)
    detail = folder_tree_service.get_detail(db, folder, a1.user)
    assert detail["default_access"] == 1


def test_search_folders_gap_dau(db, world, roots):
    root = roots[world.co["A"]]
    folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Hợp đồng mua bán"), 0)
    #  Phase 04 (duoc-CR-475): tìm kiếm cũng đi qua `_visible_folder_ids` —
    #  `a1` cần với tới nhánh pháp nhân A mới thấy thư mục vừa tạo.
    world.grant("a1", "document", scope="company", actions=("read",))
    actor = world.actor("a1")
    results = folder_tree_service.search_folders(db, actor.user, "hop dong")
    assert any("Hợp đồng" in r["name"] for r in results)
