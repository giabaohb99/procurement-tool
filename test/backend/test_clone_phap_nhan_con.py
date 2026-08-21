"""CLONE XUỐNG PHÁP NHÂN CON (F06–F11).

Quyết định cũ từng CẤM HẲN việc nhân bản: *"sau 6 tháng sẽ có 12 bản khác nhau
và không ai biết bản nào đúng"*. Yêu cầu mới mở lại kèm **bốn điều kiện bắt
buộc** — thiếu bất kỳ điều nào thì đúng như cảnh báo cũ.

Bốn điều kiện đó chính là bốn nhóm bài kiểm dưới đây. Đây không phải test cho
vui: mỗi cái canh một cách mà tính năng này biến thành thảm họa.
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.link_rule_model import RELATION_BASED_ON
from app.modules.doc_catalog.model import DocType
from app.modules.document import clone_service, link_service, scope_service, service
from app.modules.document.model import APPLY_MODE_CLONE, STATUS_DRAFT, Document
from app.modules.document.schema import DocumentCreate, VersionCreate
from app.modules.document.scope_model import (DIM_COMPANY, MODE_INCLUDE,
                                              DocumentScope)
from app.modules.document.version_model import CHANGE_MAJOR

ACTOR = 1


@pytest.fixture()
def tap_doan(db, seed):
    """Tập đoàn đã ban hành một quy chế + hai công ty con."""
    me = db.get(Company, seed.company_id)
    me.issue_code = "DEGO"
    con_a = Company(code="ABA", name="Công ty A", issue_code="ABA", level=2, is_active=True)
    con_b = Company(code="IDA", name="Công ty B", issue_code="IDA", level=2, is_active=True)
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add_all([con_a, con_b, doc_type])
    db.commit()

    goc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế bảo mật",
        content_html="<p>Điều 1. Nội dung.</p>",
    ), ACTOR)
    service.submit(db, goc, ACTOR)
    service.approve(db, goc, ACTOR)

    return {"goc": goc, "a": con_a, "b": con_b, "seed": seed}


# ── F06 · sinh bản nháp ─────────────────────────────────────────────────────
def test_clone_sinh_ban_nhap_rieng_cho_tung_phap_nhan(db, tap_doan):
    clones = clone_service.create_clones(
        db, tap_doan["goc"], [tap_doan["a"].id, tap_doan["b"].id], None, "", ACTOR)

    assert len(clones) == 2
    assert {c.company_id for c in clones} == {tap_doan["a"].id, tap_doan["b"].id}
    assert all(c.status == STATUS_DRAFT for c in clones)
    assert all(c.apply_mode == APPLY_MODE_CLONE for c in clones)


def test_clone_chep_noi_dung_ban_goc(db, tap_doan):
    from app.modules.document.version_model import DocumentVersion

    clone = clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id],
                                        None, "", ACTOR)[0]
    version = db.get(DocumentVersion, clone.current_version_id)
    assert "Điều 1" in version.content_html


def test_clone_tu_dien_pham_vi_ban_hanh_cua_phap_nhan_nhan(db, tap_doan):
    """Bản của Công ty A chỉ nhận phần phạm vi của A, không kéo theo Công ty B."""
    goc = tap_doan["goc"]
    db.add_all([
        DocumentScope(
            document_id=goc.id, dim=DIM_COMPANY, mode=MODE_INCLUDE,
            company_id=tap_doan["a"].id, created_by=ACTOR, updated_by=ACTOR,
        ),
        DocumentScope(
            document_id=goc.id, dim=DIM_COMPANY, mode=MODE_INCLUDE,
            company_id=tap_doan["b"].id, created_by=ACTOR, updated_by=ACTOR,
        ),
    ])
    db.commit()

    clone = clone_service.create_clones(
        db, goc, [tap_doan["a"].id], None, "", ACTOR,
    )[0]
    rows = scope_service.scopes_of(db, clone.id)

    assert len(rows) == 1
    assert rows[0].mode == MODE_INCLUDE
    assert rows[0].dim == DIM_COMPANY
    assert rows[0].company_id == tap_doan["a"].id


def test_clone_tao_tay_khong_co_pham_vi_nguon_thi_mac_dinh_noi_nhan(db, tap_doan):
    """Thẻ phạm vi của bản nhận không để trống dù bản gốc chưa khai nơi đó."""
    clone = clone_service.create_clones(
        db, tap_doan["goc"], [tap_doan["a"].id], None, "", ACTOR,
    )[0]

    rows = scope_service.scopes_of(db, clone.id)
    assert len(rows) == 1
    assert rows[0].dim == DIM_COMPANY
    assert rows[0].mode == MODE_INCLUDE
    assert rows[0].company_id == tap_doan["a"].id


def test_khong_clone_van_ban_chua_ban_hanh(db, tap_doan, seed):
    nhap = service.create_document(db, DocumentCreate(
        doc_type_id=tap_doan["goc"].doc_type_id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=seed.emp_req_id,
        title="Quy chế còn nháp", content_html="<p>x</p>",
    ), ACTOR)

    with pytest.raises(HTTPException) as loi:
        clone_service.create_clones(db, nhap, [tap_doan["a"].id], None, "", ACTOR)
    assert "đã ban hành" in loi.value.detail


def test_moi_phap_nhan_chi_nhan_mot_ban_clone(db, tap_doan):
    """UNIQUE ở tầng dữ liệu cũng chặn, nhưng báo trước thì người dùng hiểu vì sao."""
    clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id], None, "", ACTOR)

    with pytest.raises(HTTPException) as loi:
        clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id], None, "", ACTOR)
    assert "đã có bản clone" in loi.value.detail


def test_khong_clone_ve_chinh_phap_nhan_da_ban_hanh(db, tap_doan):
    with pytest.raises(HTTPException):
        clone_service.create_clones(
            db, tap_doan["goc"], [tap_doan["goc"].company_id], None, "", ACTOR)


# ── ĐIỀU KIỆN 1 · liên kết ngược không xóa được ─────────────────────────────
def test_clone_luon_giu_lien_ket_nguoc_ve_ban_goc(db, tap_doan):
    clone = clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id],
                                        None, "", ACTOR)[0]

    links = link_service.links_of(db, clone.id)
    assert len(links) == 1
    assert links[0].relation == RELATION_BASED_ON
    assert links[0].target_document_id == tap_doan["goc"].id
    assert links[0].is_system is True


def test_khong_xoa_duoc_lien_ket_nguoc(db, tap_doan):
    """Xóa được thì vài tháng sau có bản clone mồ côi, không truy về gốc."""
    clone = clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id],
                                        None, "", ACTOR)[0]
    link = link_service.links_of(db, clone.id)[0]

    with pytest.raises(HTTPException) as loi:
        link_service.delete_link(db, clone, link.id)
    assert "không xóa được" in loi.value.detail


# ── ĐIỀU KIỆN 2 · số hiệu của pháp nhân con ─────────────────────────────────
def test_clone_mang_so_hieu_cua_phap_nhan_con(db, tap_doan):
    """Không dùng lại số của Tập đoàn — đây là cả lý do clone tồn tại."""
    clone = clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id],
                                        None, "", ACTOR)[0]
    assert not clone.doc_code

    service.submit(db, clone, ACTOR)
    service.approve(db, clone, ACTOR)

    assert clone.doc_code.startswith("ABA-")
    assert tap_doan["goc"].doc_code.startswith("DEGO-")
    assert clone.doc_code != tap_doan["goc"].doc_code


# ── ĐIỀU KIỆN 3 · gốc lên bản mới thì clone cần rà lại ──────────────────────
def test_goc_len_phien_ban_moi_thi_clone_bi_danh_dau(db, tap_doan):
    from app.modules.document.version_service import open_new_version

    clone = clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id],
                                        None, "", ACTOR)[0]
    assert clone.needs_review is False

    open_new_version(db, tap_doan["goc"], VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa Điều 1",
    ), ACTOR)
    service.submit(db, tap_doan["goc"], ACTOR)
    service.approve(db, tap_doan["goc"], ACTOR)

    db.refresh(clone)
    assert clone.needs_review is True
    assert clone.clone_status == clone_service.CLONE_STALE


def test_nguoi_phu_trach_duoc_bao_khi_goc_len_ban_moi(db, tap_doan, seed):
    """Đánh dấu mà không báo thì cái dấu nằm im tới lúc có người tình cờ mở ra."""
    from app.modules.notification.model import Notification
    from app.modules.user.model import User
    from app.modules.document.version_service import open_new_version

    #  Gắn một tài khoản vào pháp nhân con để có người mà báo.
    from app.modules.employee.model import Employee
    nhan_su = Employee(code="NV-A", full_name="Anh A", company_id=tap_doan["a"].id,
                       is_active=True)
    db.add(nhan_su)
    db.flush()
    db.add(User(email="a@dego.vn", password_hash="x", employee_id=nhan_su.id,
                is_active=True))
    db.commit()

    clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id], None, "", ACTOR)
    truoc = db.query(Notification).count()

    open_new_version(db, tap_doan["goc"], VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa Điều 1",
    ), ACTOR)
    service.submit(db, tap_doan["goc"], ACTOR)
    service.approve(db, tap_doan["goc"], ACTOR)

    assert db.query(Notification).count() > truoc


# ── ĐIỀU KIỆN 4 · bảng theo dõi ─────────────────────────────────────────────
def test_bang_theo_doi_tra_loi_ai_dang_o_phien_ban_nao(db, tap_doan):
    clone_service.create_clones(
        db, tap_doan["goc"], [tap_doan["a"].id, tap_doan["b"].id], None, "", ACTOR)

    bang = clone_service.tracking(db, tap_doan["goc"])

    assert len(bang) == 2
    assert {row["company_name"] for row in bang} == {"Công ty A", "Công ty B"}
    assert all(row["clone_status_label"] == "Đã gửi" for row in bang)
    assert all(row["is_outdated"] is False for row in bang)


def test_bang_theo_doi_chi_ra_ai_dang_lech_ban(db, tap_doan):
    """Câu khó nhất trong bốn câu — và là lý do cột `clone_source_version_id` tồn tại."""
    from app.modules.document.version_service import open_new_version

    clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id], None, "", ACTOR)

    open_new_version(db, tap_doan["goc"], VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa Điều 1",
    ), ACTOR)
    service.submit(db, tap_doan["goc"], ACTOR)
    service.approve(db, tap_doan["goc"], ACTOR)

    assert clone_service.tracking(db, tap_doan["goc"])[0]["is_outdated"] is True


def test_bang_theo_doi_chi_ra_ai_chua_dung_toi(db, tap_doan):
    clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id], None, "", ACTOR)

    chua_nhan = clone_service.pending_companies(db, tap_doan["goc"])

    ten = {row["company_name"] for row in chua_nhan}
    assert "Công ty B" in ten
    #  Không kể chính pháp nhân đã ban hành và pháp nhân đã nhận clone.
    assert "Công ty A" not in ten


def test_phap_nhan_con_cap_nhat_tinh_trang_xu_ly(db, tap_doan):
    clone = clone_service.create_clones(db, tap_doan["goc"], [tap_doan["a"].id],
                                        None, "", ACTOR)[0]

    clone_service.mark_handled(db, clone, clone_service.CLONE_REJECTED, ACTOR)

    assert clone.clone_status == clone_service.CLONE_REJECTED
    assert clone.clone_handled_at is not None


def test_van_ban_thuong_khong_cap_nhat_tinh_trang_clone_duoc(db, tap_doan):
    with pytest.raises(HTTPException) as loi:
        clone_service.mark_handled(db, tap_doan["goc"], clone_service.CLONE_ISSUED, ACTOR)
    assert "không phải bản clone" in loi.value.detail
