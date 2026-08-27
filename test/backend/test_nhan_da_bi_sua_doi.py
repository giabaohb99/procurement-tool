"""NHÃN "ĐÃ BỊ SỬA ĐỔI" và ba tác động tự động của quan hệ (J10).

| Quan hệ | Tác động lên văn bản cũ |
|---|---|
| sửa đổi  | **KHÔNG đổi trạng thái** |
| thay thế | cũ → bị thay thế |
| bãi bỏ   | cũ → bãi bỏ |

Bài kiểm nặng nhất là `test_sua_doi_khong_doi_trang_thai_nhung_van_gan_nhan`:
đó chính là ca nguy hiểm nhất của cả nhóm J. Văn bản vẫn hiện "Có hiệu lực" nên
người đọc không nghi ngờ gì — nếu cái nhãn không hiện thì họ đọc điều khoản cũ
và làm sai mà không ai phát hiện.
"""
import pytest

from app.modules.company.model import Company
from app.modules.doc_catalog.link_rule_model import (RELATION_AMEND,
                                                     RELATION_REPLACE,
                                                     RELATION_REVOKE,
                                                     DocTypeLinkRule)
from app.modules.doc_catalog.model import DocType
from app.modules.document import link_service, service, supersede_service
from app.modules.document.model import (STATUS_EFFECTIVE, STATUS_REPLACED,
                                        STATUS_REVOKED)
from app.modules.document.schema import DocumentCreate

ACTOR = 1


@pytest.fixture()
def bo_quyet_dinh(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    decision = DocType(code="QD", name="Quyết định", id_scheme=2, number_when=2)
    db.add(decision)
    db.commit()

    #  Quyết định được phép thay thế / sửa đổi / bãi bỏ Quyết định khác.
    for relation in (RELATION_REPLACE, RELATION_AMEND, RELATION_REVOKE):
        db.add(DocTypeLinkRule(source_type_id=decision.id, relation=relation,
                               target_type_id=decision.id))
    db.commit()
    return {"QD": decision, "seed": seed}


def _ban_hanh(db, ctx, title: str):
    seed = ctx["seed"]
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=ctx["QD"].id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=seed.emp_req_id,
        title=title, content_html="<p>Điều 5. Nội dung.</p>",
    ), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    return doc


def _noi(db, new, old, relation):
    link_service.add_link(db, new, relation, old.id, "", ACTOR)


# ── Ba tác động tự động ──────────────────────────────────────────────────────
def test_thay_the_thi_van_ban_cu_chuyen_sang_bi_thay_the(db, bo_quyet_dinh):
    old = _ban_hanh(db, bo_quyet_dinh, "Quyết định 15")

    new = service.create_document(db, DocumentCreate(
        doc_type_id=bo_quyet_dinh["QD"].id, company_id=bo_quyet_dinh["seed"].company_id,
        department_id=bo_quyet_dinh["seed"].dept_id,
        owner_employee_id=bo_quyet_dinh["seed"].emp_req_id,
        title="Quyết định 47", content_html="<p>Thay thế QĐ 15.</p>",
    ), ACTOR)
    _noi(db, new, old, RELATION_REPLACE)
    service.submit(db, new, ACTOR)
    service.approve(db, new, ACTOR)

    db.refresh(old)
    assert old.status == STATUS_REPLACED


def test_bai_bo_thi_van_ban_cu_chuyen_sang_bai_bo(db, bo_quyet_dinh):
    old = _ban_hanh(db, bo_quyet_dinh, "Quyết định 15")

    new = service.create_document(db, DocumentCreate(
        doc_type_id=bo_quyet_dinh["QD"].id, company_id=bo_quyet_dinh["seed"].company_id,
        department_id=bo_quyet_dinh["seed"].dept_id,
        owner_employee_id=bo_quyet_dinh["seed"].emp_req_id,
        title="Quyết định 50", content_html="<p>Bãi bỏ QĐ 15.</p>",
    ), ACTOR)
    _noi(db, new, old, RELATION_REVOKE)
    service.submit(db, new, ACTOR)
    service.approve(db, new, ACTOR)

    db.refresh(old)
    assert old.status == STATUS_REVOKED


def test_sua_doi_khong_doi_trang_thai_nhung_van_gan_nhan(db, bo_quyet_dinh):
    """Ca NGUY HIỂM NHẤT của nhóm J — xem chú thích đầu tệp."""
    old = _ban_hanh(db, bo_quyet_dinh, "Quyết định 15")

    new = service.create_document(db, DocumentCreate(
        doc_type_id=bo_quyet_dinh["QD"].id, company_id=bo_quyet_dinh["seed"].company_id,
        department_id=bo_quyet_dinh["seed"].dept_id,
        owner_employee_id=bo_quyet_dinh["seed"].emp_req_id,
        title="Quyết định 47", content_html="<p>Sửa đổi Điều 5 QĐ 15.</p>",
    ), ACTOR)
    _noi(db, new, old, RELATION_AMEND)
    service.submit(db, new, ACTOR)
    service.approve(db, new, ACTOR)

    db.refresh(old)
    #  Phần không bị sửa vẫn có hiệu lực — KHÔNG đổi trạng thái.
    assert old.status == STATUS_EFFECTIVE
    #  Nhưng nhãn thì BẮT BUỘC phải có, vì nhìn trạng thái không ai biết gì cả.
    label = supersede_service.amended_by(db, old.id)
    assert len(label) == 1
    assert label[0]["relation_label"] == "Sửa đổi"
    assert label[0]["title"] == "Quyết định 47"


# ── Nhãn ────────────────────────────────────────────────────────────────────
def test_chua_bi_gi_thi_khong_co_nhan(db, bo_quyet_dinh):
    old = _ban_hanh(db, bo_quyet_dinh, "Quyết định 15")
    assert supersede_service.amended_by(db, old.id) == []


def test_du_thao_sua_doi_chua_ban_hanh_thi_chua_gan_nhan(db, bo_quyet_dinh):
    """Gắn nhãn sớm là dọa người đọc bằng một thứ chưa có hiệu lực."""
    old = _ban_hanh(db, bo_quyet_dinh, "Quyết định 15")

    nhap = service.create_document(db, DocumentCreate(
        doc_type_id=bo_quyet_dinh["QD"].id, company_id=bo_quyet_dinh["seed"].company_id,
        department_id=bo_quyet_dinh["seed"].dept_id,
        owner_employee_id=bo_quyet_dinh["seed"].emp_req_id,
        title="Dự thảo sửa QĐ 15", content_html="<p>x</p>",
    ), ACTOR)
    _noi(db, nhap, old, RELATION_AMEND)

    assert supersede_service.amended_by(db, old.id) == []
    db.refresh(old)
    assert old.status == STATUS_EFFECTIVE


def test_khong_ghi_de_van_ban_da_bai_bo_tu_truoc(db, bo_quyet_dinh):
    """Ghi đè là xóa mất lý do bãi bỏ thật của nó."""
    old = _ban_hanh(db, bo_quyet_dinh, "Quyết định 15")
    service.revoke(db, old, "Bãi bỏ theo kết luận họp", ACTOR)
    assert old.status == STATUS_REVOKED

    new = service.create_document(db, DocumentCreate(
        doc_type_id=bo_quyet_dinh["QD"].id, company_id=bo_quyet_dinh["seed"].company_id,
        department_id=bo_quyet_dinh["seed"].dept_id,
        owner_employee_id=bo_quyet_dinh["seed"].emp_req_id,
        title="Quyết định 47", content_html="<p>Thay thế QĐ 15.</p>",
    ), ACTOR)
    _noi(db, new, old, RELATION_REPLACE)
    service.submit(db, new, ACTOR)
    service.approve(db, new, ACTOR)

    db.refresh(old)
    assert old.status == STATUS_REVOKED


def test_nhan_gom_nhieu_van_ban_cung_dung_vao_mot_van_ban(db, bo_quyet_dinh):
    old = _ban_hanh(db, bo_quyet_dinh, "Quyết định 15")

    for title in ("Quyết định 47", "Quyết định 48"):
        new = service.create_document(db, DocumentCreate(
            doc_type_id=bo_quyet_dinh["QD"].id, company_id=bo_quyet_dinh["seed"].company_id,
            department_id=bo_quyet_dinh["seed"].dept_id,
            owner_employee_id=bo_quyet_dinh["seed"].emp_req_id,
            title=title, content_html="<p>Sửa đổi.</p>",
        ), ACTOR)
        _noi(db, new, old, RELATION_AMEND)
        service.submit(db, new, ACTOR)
        service.approve(db, new, ACTOR)

    assert len(supersede_service.amended_by(db, old.id)) == 2


# ── Văn bản hẹn hiệu lực TƯƠNG LAI ──────────────────────────────────────────
#
# Ban hành hôm nay mà áp dụng từ tháng sau thì văn bản cũ phải còn hiệu lực
# nguyên tháng đó — nên `approve()` cố ý KHÔNG chạy tác động thay thế. Nhưng nếu
# không có gì chạy vào đúng ngày hiệu lực thì Quyết định 15 nằm im mãi ở trạng
# thái "có hiệu lực", và nhãn cảnh báo là thứ duy nhất còn đúng.
def test_hen_hieu_luc_tuong_lai_thi_chua_thay_the_ngay(db, bo_quyet_dinh):
    from datetime import date, timedelta

    old = _ban_hanh(db, bo_quyet_dinh, "Quyết định 15")
    new = service.create_document(db, DocumentCreate(
        doc_type_id=bo_quyet_dinh["QD"].id, company_id=bo_quyet_dinh["seed"].company_id,
        department_id=bo_quyet_dinh["seed"].dept_id,
        owner_employee_id=bo_quyet_dinh["seed"].emp_req_id,
        title="Quyết định 47", content_html="<p>Thay thế QĐ 15 từ tháng sau.</p>",
        effective_date=date.today() + timedelta(days=30),
    ), ACTOR)
    _noi(db, new, old, RELATION_REPLACE)
    service.submit(db, new, ACTOR)
    service.approve(db, new, ACTOR)

    db.refresh(old)
    #  Văn bản cũ CÒN hiệu lực cho tới ngày bản mới áp dụng.
    assert old.status == STATUS_EFFECTIVE
    #  Nhưng người đọc đã được cảnh báo ngay từ bây giờ.
    assert len(supersede_service.amended_by(db, old.id)) == 1


def test_toi_ngay_hieu_luc_thi_moi_thay_the(db, bo_quyet_dinh):
    """Lỗ đã vá 17/08: trước đây không có gì chạy vào ngày hiệu lực."""
    from datetime import date, timedelta

    from app.modules.document.version_model import DocumentVersion

    old = _ban_hanh(db, bo_quyet_dinh, "Quyết định 15")
    new = service.create_document(db, DocumentCreate(
        doc_type_id=bo_quyet_dinh["QD"].id, company_id=bo_quyet_dinh["seed"].company_id,
        department_id=bo_quyet_dinh["seed"].dept_id,
        owner_employee_id=bo_quyet_dinh["seed"].emp_req_id,
        title="Quyết định 47", content_html="<p>Thay thế QĐ 15.</p>",
        effective_date=date.today() + timedelta(days=30),
    ), ACTOR)
    _noi(db, new, old, RELATION_REPLACE)
    service.submit(db, new, ACTOR)
    service.approve(db, new, ACTOR)

    #  Tua tới ngày hiệu lực rồi chạy việc bảo trì.
    version = db.get(DocumentVersion, new.current_version_id)
    version.effective_from = date.today()
    db.commit()
    service.activate_due_versions(db)

    db.refresh(old)
    assert old.status == STATUS_REPLACED
