"""CLONE TỰ SINH KHI BAN HÀNH + vòng đời cột theo dõi (20/08/2026).

Chốt nghiệp vụ đảo lại quyết định cũ: *"ban hành xuống thì các pháp nhân đó nhận
1 bản clone, dạng nháp có thể chỉnh lại cho đúng thông tin với cty đó rồi bấm ban
hành cho cty đó"*. Trước đó phải vào thẻ Quan hệ bấm tay.

Ba lỗ được vá cùng lúc, mỗi lỗ một nhóm bài kiểm dưới đây — cả ba đều đã dựng lại
được trên hệ đang chạy, không phải lo xa:

  1. bản clone ban hành xong mà bảng theo dõi vẫn ghi "Đã gửi";
  2. rà xong rồi mà cột "lệch bản" vẫn đỏ vĩnh viễn;
  3. loại văn bản cấp số lúc nháp thì bản clone không bao giờ có số hiệu.
"""
import pytest

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import clone_service, service
from app.modules.document.clone_service import (CLONE_DRAFTING, CLONE_ISSUED,
                                                CLONE_SENT, CLONE_STALE,
                                                CLONE_SUBMITTED)
from app.modules.document.model import STATUS_DRAFT
from app.modules.document.schema import DocumentCreate, VersionCreate
from app.modules.document.scope_model import (DIM_COMPANY, DIM_DEPARTMENT,
                                              MODE_EXCLUDE, MODE_INCLUDE,
                                              DocumentScope)
from app.modules.document.version_model import CHANGE_MAJOR

ACTOR = 1


def _pham_vi(db, doc_id, company_id, mode=MODE_INCLUDE, dim=DIM_COMPANY,
             department_id=None):
    db.add(DocumentScope(document_id=doc_id, dim=dim, mode=mode,
                         company_id=company_id, department_id=department_id,
                         created_by=ACTOR, updated_by=ACTOR))
    db.commit()


@pytest.fixture()
def nen(db, seed):
    """Tập đoàn + hai công ty con + một loại văn bản cấp số lúc duyệt."""
    me = db.get(Company, seed.company_id)
    me.issue_code = "DEGO"
    con_a = Company(code="ABA", name="Công ty A", issue_code="ABA", level=2, is_active=True)
    con_b = Company(code="IDA", name="Công ty B", issue_code="IDA", level=2, is_active=True)
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add_all([con_a, con_b, doc_type])
    db.commit()
    return {"a": con_a, "b": con_b, "doc_type": doc_type, "seed": seed}


def _tao_nhap(db, nen, title="Quy chế bảo mật", doc_type=None):
    seed = nen["seed"]
    return service.create_document(db, DocumentCreate(
        doc_type_id=(doc_type or nen["doc_type"]).id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=seed.emp_req_id,
        title=title, content_html="<p>Điều 1. Nội dung.</p>",
    ), ACTOR)


def _ban_hanh(db, doc):
    service.submit(db, doc, ACTOR)
    return service.approve(db, doc, ACTOR)


# ── Sinh tự động lúc ban hành ────────────────────────────────────────────────
def test_ban_hanh_thi_moi_phap_nhan_trong_pham_vi_co_ngay_mot_ban_nhap(db, nen):
    goc = _tao_nhap(db, nen)
    _pham_vi(db, goc.id, nen["a"].id)
    _pham_vi(db, goc.id, nen["b"].id)

    _ban_hanh(db, goc)

    clones = clone_service.clones_of(db, goc.id)
    assert {c.company_id for c in clones} == {nen["a"].id, nen["b"].id}
    #  Dạng NHÁP để pháp nhân con sửa lại cho đúng công ty mình.
    assert all(c.status == STATUS_DRAFT for c in clones)


def test_ban_clone_chep_noi_dung_ban_goc(db, nen):
    from app.modules.document.version_model import DocumentVersion

    goc = _tao_nhap(db, nen)
    _pham_vi(db, goc.id, nen["a"].id)
    _ban_hanh(db, goc)

    clone = clone_service.clones_of(db, goc.id)[0]
    assert "Điều 1" in db.get(DocumentVersion, clone.current_version_id).content_html


def test_khong_khai_pham_vi_thi_khong_sinh_ban_nao(db, nen):
    """Văn bản chỉ áp trong pháp nhân ban hành — đẻ clone ra là thừa văn bản."""
    goc = _tao_nhap(db, nen)

    _ban_hanh(db, goc)

    assert clone_service.clones_of(db, goc.id) == []


def test_khong_clone_ve_chinh_phap_nhan_ban_hanh(db, nen, seed):
    goc = _tao_nhap(db, nen)
    _pham_vi(db, goc.id, seed.company_id)

    _ban_hanh(db, goc)

    assert clone_service.clones_of(db, goc.id) == []


def test_dong_loai_tru_khong_sinh_clone(db, nen):
    """Loại trừ nói nơi đó KHÔNG áp dụng — clone về đó là tạo cho nơi vừa bị loại."""
    goc = _tao_nhap(db, nen)
    _pham_vi(db, goc.id, nen["a"].id, mode=MODE_EXCLUDE)

    _ban_hanh(db, goc)

    assert clone_service.clones_of(db, goc.id) == []


def test_dong_phong_ban_khong_sinh_clone(db, nen, seed):
    """Clone tách theo PHÁP NHÂN; dòng phòng ban không nói được nên tách cho ai."""
    goc = _tao_nhap(db, nen)
    _pham_vi(db, goc.id, nen["a"].id, dim=DIM_DEPARTMENT, department_id=seed.dept_id)

    _ban_hanh(db, goc)

    assert clone_service.clones_of(db, goc.id) == []


def test_len_phien_ban_moi_khong_de_them_ban_clone_thu_hai(db, nen):
    """Ban hành 2.0 mà sinh thêm một bản nữa là pháp nhân con có hai văn bản trùng."""
    from app.modules.document import version_service

    goc = _tao_nhap(db, nen)
    _pham_vi(db, goc.id, nen["a"].id)
    _ban_hanh(db, goc)
    assert len(clone_service.clones_of(db, goc.id)) == 1

    version_service.open_new_version(db, goc, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa điều 1"), ACTOR)
    _ban_hanh(db, goc)

    assert len(clone_service.clones_of(db, goc.id)) == 1


def test_ban_clone_mang_so_hieu_cua_phap_nhan_con(db, nen):
    goc = _tao_nhap(db, nen)
    _pham_vi(db, goc.id, nen["a"].id)
    _ban_hanh(db, goc)

    clone = clone_service.clones_of(db, goc.id)[0]
    _ban_hanh(db, clone)

    #  Mã pháp nhân CON, không dùng lại số của Tập đoàn.
    assert clone.doc_code.startswith("ABA-")
    assert not goc.doc_code.startswith("ABA-")


# ── Lỗ 1 · cột theo dõi đổi theo văn bản ─────────────────────────────────────
def test_clone_ban_hanh_xong_thi_bang_theo_doi_ghi_da_ban_hanh(db, nen):
    """Từng ghi "Đã gửi" mãi mãi: API đổi trạng thái có, nhưng không màn nào gọi."""
    goc = _tao_nhap(db, nen)
    _pham_vi(db, goc.id, nen["a"].id)
    _ban_hanh(db, goc)
    clone = clone_service.clones_of(db, goc.id)[0]
    assert clone.clone_status == CLONE_SENT

    service.submit(db, clone, ACTOR)
    assert clone.clone_status == CLONE_SUBMITTED

    service.approve(db, clone, ACTOR)
    assert clone.clone_status == CLONE_ISSUED
    assert clone.clone_handled_at is not None
    assert clone_service.tracking(db, goc)[0]["clone_status_label"] == "Đã ban hành"


def test_clone_bi_tra_lai_thi_ve_dang_soan(db, nen):
    goc = _tao_nhap(db, nen)
    _pham_vi(db, goc.id, nen["a"].id)
    _ban_hanh(db, goc)
    clone = clone_service.clones_of(db, goc.id)[0]

    service.submit(db, clone, ACTOR)
    service.reject(db, clone, "Sai tên công ty", ACTOR)

    assert clone.clone_status == CLONE_DRAFTING


def test_van_ban_thuong_khong_dinh_cot_clone(db, nen):
    """Văn bản không phải bản clone thì cột này phải im — nó thuộc về bản gốc."""
    goc = _tao_nhap(db, nen)
    _ban_hanh(db, goc)

    assert goc.clone_status == 0


# ── Lỗ 2 · rà xong thì hết lệch bản ──────────────────────────────────────────
def test_ra_soat_xong_thi_het_lech_ban(db, nen):
    """Nút «Đã rà xong» từng tắt băng vàng mà quên dời con trỏ phiên bản."""
    from app.modules.document import version_service

    goc = _tao_nhap(db, nen)
    _pham_vi(db, goc.id, nen["a"].id)
    _ban_hanh(db, goc)
    clone = clone_service.clones_of(db, goc.id)[0]
    _ban_hanh(db, clone)

    version_service.open_new_version(db, goc, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa điều 1"), ACTOR)
    _ban_hanh(db, goc)
    db.refresh(clone)
    assert clone.needs_review is True
    assert clone.clone_status == CLONE_STALE
    assert clone_service.tracking(db, goc)[0]["is_outdated"] is True

    service.xac_nhan_da_ra_soat(db, clone, "Đã đối chiếu, vẫn đúng", ACTOR)

    assert clone.needs_review is False
    assert clone_service.tracking(db, goc)[0]["is_outdated"] is False
    #  Trả về đúng chỗ bản clone đang đứng, không kẹt ở "Cần rà lại".
    assert clone.clone_status == CLONE_ISSUED


def test_ra_soat_van_ban_thuong_khong_dung_toi_cot_clone(db, nen):
    goc = _tao_nhap(db, nen)
    goc.needs_review = True
    db.commit()

    service.xac_nhan_da_ra_soat(db, goc, "Đã đối chiếu", ACTOR)

    assert goc.clone_status == 0
    assert goc.clone_source_version_id is None


# ── Lỗ 3 · loại cấp số lúc nháp ──────────────────────────────────────────────
def test_loai_cap_so_luc_nhap_thi_ban_clone_cung_co_so_ngay(db, nen):
    """Trước đây `create_clones` không cấp số, `approve` chỉ cấp cho loại "lúc
    duyệt" — nên bản clone của loại này ban hành xong vẫn không có số hiệu nào."""
    dt = DocType(code="TB", name="Thông báo", id_scheme=2, number_when=1)
    db.add(dt)
    db.commit()

    goc = _tao_nhap(db, nen, title="Thông báo X", doc_type=dt)
    _pham_vi(db, goc.id, nen["a"].id)
    _ban_hanh(db, goc)

    clone = clone_service.clones_of(db, goc.id)[0]
    assert (clone.doc_code or clone.issue_number), "bản clone phải có số ngay lúc nháp"
    #  Số của pháp nhân CON, không phải số Tập đoàn.
    assert "ABA" in (clone.doc_code or clone.issue_number)
    assert (clone.doc_code or clone.issue_number) != (goc.doc_code or goc.issue_number)
