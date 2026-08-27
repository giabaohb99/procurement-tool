"""MÀN BAN HÀNH — bản xem trước và chốt chặn Quyết định kèm theo (J04, J11).

Ban hành là thao tác **không lùi được**: số cấp ra là cấp vĩnh viễn, phiên bản
khóa là khóa một chiều, văn bản cũ bị thay thế thì đổi trạng thái ngay. Bản xem
trước tồn tại để người ban hành nhìn thấy đủ bốn thứ đó TRƯỚC khi bấm.

Hai loại thông tin phải tách bạch: **chặn** là thứ backend sẽ từ chối, **cảnh
báo** là thứ vẫn ban hành được nhưng gần như chắc chắn là quên. Gộp chung thì
người dùng học được thói quen bỏ qua tất.
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.link_rule_model import (RELATION_ATTACHED,
                                                     RELATION_REPLACE,
                                                     DocTypeLinkRule)
from app.modules.doc_catalog.model import DocType
from app.modules.document import issue_service, link_service, service
from app.modules.document.schema import DocumentCreate
from app.modules.document.scope_model import (DIM_COMPANY, MODE_INCLUDE,
                                              DocumentScope)

ACTOR = 1


@pytest.fixture()
def ctx(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    regulation = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2,
                      needs_decision=True)
    decision = DocType(code="QD", name="Quyết định", id_scheme=2, number_when=2)
    db.add_all([regulation, decision])
    db.commit()

    #  Quy chế ban hành kèm ĐÚNG MỘT Quyết định; Quyết định thay thế Quyết định.
    db.add(DocTypeLinkRule(source_type_id=regulation.id, relation=RELATION_ATTACHED,
                           target_type_id=decision.id))
    db.add(DocTypeLinkRule(source_type_id=decision.id, relation=RELATION_REPLACE,
                           target_type_id=decision.id))
    db.commit()
    return {"QC": regulation, "QD": decision, "seed": seed}


def _tao(db, ctx, code: str, title: str):
    seed = ctx["seed"]
    return service.create_document(db, DocumentCreate(
        doc_type_id=ctx[code].id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=seed.emp_req_id,
        title=title, content_html="<p>Nội dung</p>",
    ), ACTOR)


def _ban_hanh(db, doc):
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    return doc


# ── J11 · loại phải kèm Quyết định ──────────────────────────────────────────
def test_thieu_quyet_dinh_thi_khong_ban_hanh_duoc(db, ctx):
    regulation = _tao(db, ctx, "QC", "Quy chế lương")
    service.submit(db, regulation, ACTOR)

    with pytest.raises(HTTPException) as error:
        service.approve(db, regulation, ACTOR)
    assert "kèm một Quyết định" in error.value.detail


def test_co_quyet_dinh_kem_theo_thi_ban_hanh_duoc(db, ctx):
    decision = _ban_hanh(db, _tao(db, ctx, "QD", "Quyết định ban hành quy chế lương"))
    regulation = _tao(db, ctx, "QC", "Quy chế lương")
    link_service.add_link(db, regulation, RELATION_ATTACHED, decision.id, "", ACTOR)

    _ban_hanh(db, regulation)
    assert regulation.doc_code


def test_loai_khong_doi_quyet_dinh_thi_ban_hanh_thoai_mai(db, ctx):
    """Chốt chặn chỉ áp cho loại có khai `needs_decision`."""
    _ban_hanh(db, _tao(db, ctx, "QD", "Quyết định đứng một mình"))


# ── J04 · bản xem trước ─────────────────────────────────────────────────────
def test_xem_truoc_khong_dung_vao_du_lieu(db, ctx):
    """Gọi bao nhiêu lần cũng không chiếm số, không khóa phiên bản."""
    regulation = _tao(db, ctx, "QC", "Quy chế lương")
    service.submit(db, regulation, ACTOR)

    issue_service.preview(db, regulation)
    issue_service.preview(db, regulation)

    db.refresh(regulation)
    assert not regulation.doc_code
    assert service.open_version(db, regulation).is_locked is False


def test_xem_truoc_neu_ro_so_hieu_sap_cap_va_phien_ban_sap_khoa(db, ctx):
    regulation = _tao(db, ctx, "QC", "Quy chế lương")
    service.submit(db, regulation, ACTOR)

    data = issue_service.preview(db, regulation)

    assert data["version_no"] == "1.0"
    assert data["number_on_approve"] is True
    assert data["issue_number_preview"].startswith("DEGO-QC-")


def test_thieu_quyet_dinh_hien_o_muc_CHAN_chu_khong_phai_canh_bao(db, ctx):
    regulation = _tao(db, ctx, "QC", "Quy chế lương")
    service.submit(db, regulation, ACTOR)

    data = issue_service.preview(db, regulation)

    assert any("Quyết định" in item for item in data["blockers"])
    assert not any("Quyết định" in item for item in data["warnings"])


def test_chua_khai_pham_vi_khong_chan_ma_cung_khong_canh_bao(db, ctx):
    """Từ 19/08/2026: không khai dòng nào = áp cho đúng pháp nhân ban hành.

    Nên đây không còn là thiếu sót để dọa người ban hành — dọa mỗi lần thì họ
    học cách bỏ qua mọi cảnh báo, kể cả cái thật.
    """
    decision = _tao(db, ctx, "QD", "Quyết định 15")
    service.submit(db, decision, ACTOR)

    data = issue_service.preview(db, decision)

    assert data["scope_count"] == 0
    assert not any("phạm vi" in item for item in data["warnings"])
    assert data["blockers"] == []


def test_khai_pham_vi_roi_thi_het_canh_bao(db, ctx):
    decision = _tao(db, ctx, "QD", "Quyết định 15")
    service.submit(db, decision, ACTOR)
    db.add(DocumentScope(document_id=decision.id, dim=DIM_COMPANY,
                         company_id=ctx["seed"].company_id, mode=MODE_INCLUDE))
    db.commit()

    data = issue_service.preview(db, decision)

    assert data["scope_count"] == 1
    assert not any("phạm vi" in item for item in data["warnings"])


def test_xem_truoc_liet_ke_van_ban_se_bi_thay_the(db, ctx):
    """Đây là hậu quả không lùi được — phải thấy TRƯỚC khi bấm."""
    old = _ban_hanh(db, _tao(db, ctx, "QD", "Quyết định 15"))
    new = _tao(db, ctx, "QD", "Quyết định 47")
    link_service.add_link(db, new, RELATION_REPLACE, old.id, "", ACTOR)
    service.submit(db, new, ACTOR)

    data = issue_service.preview(db, new)

    assert len(data["will_supersede"]) == 1
    muc = data["will_supersede"][0]
    assert muc["title"] == "Quyết định 15"
    assert muc["current_status_label"] == "Có hiệu lực"
    assert muc["next_status_label"] == "Đã thay thế"


def test_xem_truoc_noi_ro_co_hieu_luc_ngay_hay_khong(db, ctx):
    from datetime import date, timedelta

    decision = _tao(db, ctx, "QD", "Quyết định 15")
    service.submit(db, decision, ACTOR)
    assert issue_service.preview(db, decision)["effective_now"] is True

    decision.effective_date = date.today() + timedelta(days=30)
    db.commit()
    assert issue_service.preview(db, decision)["effective_now"] is False
