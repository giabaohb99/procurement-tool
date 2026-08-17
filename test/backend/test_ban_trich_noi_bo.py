"""BẢN TRÍCH NỘI BỘ (C19) và ba ràng buộc khóa cứng của quan hệ "trích từ" (E11).

Vì sao "trích từ" không dùng chung với "thuộc về": Biểu mẫu thuộc về Quy trình
là hai văn bản KHÁC nội dung, cha đổi thì con chưa chắc sai. Bản trích là CÙNG
nội dung, chỉ ít hơn — cha đổi là con sai theo. Dùng chung một quan hệ cho hai
việc này thì mất luôn ba ràng buộc dưới đây:

  (a) gốc lên phiên bản mới → bản trích bị đánh dấu *cần rà lại*;
  (b) gốc bị bãi bỏ        → bản trích *hết hiệu lực* theo;
  (c) mức mật bản trích    → luôn ≤ gốc.
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.link_rule_model import (EXCERPT_LOCKED_FIELDS,
                                                     NEW_VERSION_NOTHING,
                                                     OBSOLETE_NOTHING,
                                                     RELATION_EXCERPT)
from app.modules.doc_catalog.link_rule_schema import DocTypeLinkRuleCreate
from app.modules.doc_catalog.link_rule_service import create_rule
from app.modules.doc_catalog.model import DocType
from app.modules.document import excerpt_service, link_service, service
from app.modules.document.model import STATUS_EXPIRED, Document
from app.modules.document.schema import (DocumentCreate, DocumentUpdate,
                                         VersionCreate)
from app.modules.document.version_model import CHANGE_MAJOR

ACTOR = 1


@pytest.fixture()
def goc(db, seed):
    """Một Quy chế mức Mật (3) đã ban hành, sẵn sàng để trích."""
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế lương",
        secrecy_level=3, content_html="<p>Toàn văn quy chế lương</p>",
    ), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    return doc


def _trich(db, goc, secrecy=2, title="Trích lương bộ phận sản xuất"):
    return excerpt_service.create_excerpt(
        db, goc, title, "<p>Điều 5 — phụ cấp ca đêm</p>", secrecy, "", ACTOR,
    )


# ── C19 · tạo bản trích ──────────────────────────────────────────────────────
def test_ban_trich_mang_dung_loai_cua_ban_goc(db, goc):
    """C19 không thêm loại nào vào danh mục — đó là điểm khác C20."""
    trich = _trich(db, goc)
    assert trich.doc_type_id == goc.doc_type_id
    assert trich.company_id == goc.company_id


def test_ban_trich_luon_kem_dong_trich_tu_ghi_ro_phien_ban_goc(db, goc):
    trich = _trich(db, goc)
    link = excerpt_service.source_link_of(db, trich.id)

    assert link is not None
    assert link.relation == RELATION_EXCERPT
    assert link.target_document_id == goc.id
    #  Thiếu cột này thì sáu tháng sau không ai biết bản trích nói theo bản nào.
    assert link.source_version_id == goc.current_version_id
    assert link.is_system is True


def test_khong_xoa_duoc_dong_trich_tu(db, goc):
    """Xóa được thì bản trích thành mồ côi, không truy về gốc được nữa."""
    trich = _trich(db, goc)
    link = excerpt_service.source_link_of(db, trich.id)

    with pytest.raises(HTTPException) as loi:
        link_service.delete_link(db, trich, link.id)
    assert "không xóa được" in loi.value.detail


def test_khong_khai_tay_duoc_quan_he_trich_tu(db, goc):
    """Khai tay thì thiếu `source_version_id` — mất luôn khả năng biết đã lạc hậu chưa."""
    khac = _trich(db, goc)
    with pytest.raises(HTTPException) as loi:
        link_service.add_link(db, khac, RELATION_EXCERPT, goc.id, "", ACTOR)
    assert "không khai tay được" in loi.value.detail


def test_ban_trich_khong_duoc_cap_so_hieu_rieng(db, goc):
    """C19: bản trích gọi theo số của gốc. Cấp số riêng là đẻ ra số thứ hai cho cùng nội dung."""
    trich = _trich(db, goc)
    service.submit(db, trich, ACTOR)
    service.approve(db, trich, ACTOR)

    assert goc.doc_code, "bản gốc phải có mã tài liệu"
    assert not trich.doc_code
    assert not trich.issue_number


def test_khong_trich_duoc_khi_chua_chon_noi_dung(db, goc):
    with pytest.raises(HTTPException):
        excerpt_service.create_excerpt(db, goc, "Trích rỗng", "   ", 2, "", ACTOR)


# ── E11 (c) · mức mật bản trích ≤ gốc ────────────────────────────────────────
def test_khong_dat_duoc_muc_mat_cao_hon_goc(db, goc):
    with pytest.raises(HTTPException) as loi:
        _trich(db, goc, secrecy=4)
    assert "cao hơn bản gốc" in loi.value.detail


def test_dat_bang_muc_mat_goc_thi_duoc(db, goc):
    assert _trich(db, goc, secrecy=3).secrecy_level == 3


def test_khong_nang_duoc_muc_mat_ban_trich_sau_khi_tao(db, goc):
    """Chặn cả ở đường SỬA, không chỉ lúc tạo — nếu không thì tạo thấp rồi nâng lên."""
    trich = _trich(db, goc, secrecy=2)

    with pytest.raises(HTTPException) as loi:
        service.update_document(db, trich, DocumentUpdate(secrecy_level=4), ACTOR)
    assert "cao hơn bản gốc" in loi.value.detail


def test_van_ban_thuong_khong_bi_rang_buoc_muc_mat(db, goc):
    """Ràng buộc chỉ áp cho bản trích — văn bản thường vẫn tự do đặt mức mật."""
    service.update_document(db, goc, DocumentUpdate(secrecy_level=4), ACTOR)
    assert goc.secrecy_level == 4


# ── E11 (a) · gốc lên phiên bản mới → bản trích cần rà lại ───────────────────
def test_goc_len_phien_ban_moi_thi_ban_trich_bi_danh_dau_can_ra_lai(db, goc):
    trich = _trich(db, goc)
    assert trich.needs_review is False

    from app.modules.document.version_service import open_new_version
    open_new_version(db, goc, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa Điều 5",
    ), ACTOR)
    service.submit(db, goc, ACTOR)
    service.approve(db, goc, ACTOR)

    db.refresh(trich)
    assert trich.needs_review is True
    assert "phiên bản 2.0" in trich.needs_review_note


def test_he_thong_chi_danh_dau_khong_tu_sua_ban_trich(db, goc):
    """Tài liệu nói rõ: hệ thống chỉ liệt kê và cảnh báo, người rà quyết định."""
    trich = _trich(db, goc)
    noi_dung_cu = trich.title

    from app.modules.document.version_service import open_new_version
    open_new_version(db, goc, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa Điều 5",
    ), ACTOR)
    service.submit(db, goc, ACTOR)
    service.approve(db, goc, ACTOR)

    db.refresh(trich)
    assert trich.title == noi_dung_cu
    assert trich.status != STATUS_EXPIRED


# ── E11 (b) · gốc bị bãi bỏ → bản trích hết hiệu lực theo ────────────────────
def test_bai_bo_goc_thi_ban_trich_het_hieu_luc_theo(db, goc):
    """Gốc bị bãi bỏ mà bản trích còn sống là phát tán nội dung đã bỏ."""
    trich = _trich(db, goc)
    service.submit(db, trich, ACTOR)
    service.approve(db, trich, ACTOR)

    service.revoke(db, goc, "Thay bằng quy chế mới", ACTOR)

    db.refresh(trich)
    assert trich.status == STATUS_EXPIRED
    assert trich.needs_review is True


def test_bai_bo_goc_khong_dung_toi_van_ban_khong_phai_ban_trich(db, goc, seed):
    khac = service.create_document(db, DocumentCreate(
        doc_type_id=goc.doc_type_id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=seed.emp_req_id,
        title="Quy chế khác", content_html="<p>x</p>",
    ), ACTOR)
    service.submit(db, khac, ACTOR)
    service.approve(db, khac, ACTOR)

    service.revoke(db, goc, "Thay bằng quy chế mới", ACTOR)

    db.refresh(khac)
    assert khac.status != STATUS_EXPIRED


# ── E11 · ba cột khóa cứng trong bảng quy tắc ────────────────────────────────
def test_quy_tac_trich_tu_bi_ep_lai_ba_cot_du_khai_gi(db, goc):
    """Giao diện tắt ô hay không cũng mặc — chặn ở tầng dịch vụ."""
    rule = create_rule(db, DocTypeLinkRuleCreate(
        source_type_id=goc.doc_type_id,
        relation=RELATION_EXCERPT,
        target_type_id=goc.doc_type_id,
        #  Khai đúng ba giá trị NGUY HIỂM nhất, phải bị ép lại hết.
        on_parent_new_version=NEW_VERSION_NOTHING,
        on_parent_obsolete=OBSOLETE_NOTHING,
        inherit_secrecy=False,
    ), ACTOR)

    for cot, gia_tri in EXCERPT_LOCKED_FIELDS.items():
        assert getattr(rule, cot) == gia_tri, f"cột {cot} chưa bị ép lại"


def test_quan_he_khac_van_khai_tu_do_ba_cot_do(db, goc):
    from app.modules.doc_catalog.link_rule_model import RELATION_REFERENCE

    rule = create_rule(db, DocTypeLinkRuleCreate(
        source_type_id=goc.doc_type_id, relation=RELATION_REFERENCE,
        on_parent_new_version=NEW_VERSION_NOTHING,
        on_parent_obsolete=OBSOLETE_NOTHING,
        inherit_secrecy=False,
    ), ACTOR)

    assert rule.on_parent_new_version == NEW_VERSION_NOTHING
    assert rule.on_parent_obsolete == OBSOLETE_NOTHING
    assert rule.inherit_secrecy is False


def test_ban_trich_bi_danh_dau_lac_hau_khi_goc_doi_phien_ban(db, goc):
    from app.modules.document.link_serializer import serialize_link
    from app.modules.document.version_service import open_new_version

    trich = _trich(db, goc)
    link = excerpt_service.source_link_of(db, trich.id)
    assert serialize_link(db, link, viewed_from=trich.id)["is_outdated"] is False

    open_new_version(db, goc, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa Điều 5",
    ), ACTOR)
    service.submit(db, goc, ACTOR)
    service.approve(db, goc, ACTOR)

    assert serialize_link(db, link, viewed_from=trich.id)["is_outdated"] is True
