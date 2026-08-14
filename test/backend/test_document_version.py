"""PHIÊN BẢN VĂN BẢN — bất biến hóa và "một bản đang mở".

Hai chốt chặn của `version_service`, và cả hai đều phải chặn ở **tầng dịch vụ**
chứ không phải ẩn nút trên giao diện — nên bài kiểm ở đây gọi thẳng hàm service,
đúng như một người gọi thẳng API sẽ làm.

⚠️ Bài "hai người bấm cùng lúc" chỉ kiểm được phần logic. Phần chặn THẬT nằm ở
cột sinh `open_slot` + UNIQUE ở tầng dữ liệu; SQLite (bộ kiểm thử này) có ghi
nhận cột sinh nên `test_ep_o_tang_du_lieu` vẫn kiểm được, nhưng cạnh tranh thật
giữa hai kết nối thì phải chạy trên MySQL.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service, version_service
from app.modules.document.schema import (DocumentCreate, VersionContentUpdate,
                                         VersionCreate)
from app.modules.document.version_model import (CHANGE_MINOR, VERSION_APPROVED,
                                                VERSION_DRAFT, VERSION_SUPERSEDED,
                                                DocumentVersion)

ACTOR = 1
OTHER_ACTOR = 2


@pytest.fixture()
def doc(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    obj = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế thử",
        content_html="<p>Bản 1</p>",
    ), ACTOR)
    service.submit(db, obj, ACTOR)
    service.approve(db, obj, ACTOR)
    return obj


def _versions(db, doc):
    return (db.query(DocumentVersion)
            .filter(DocumentVersion.document_id == doc.id)
            .order_by(DocumentVersion.major, DocumentVersion.minor).all())


# ── Bất biến hóa ─────────────────────────────────────────────────────────────
def test_ban_da_duyet_bi_khoa_va_co_dau_van_tay(db, doc):
    version = db.get(DocumentVersion, doc.current_version_id)
    assert version.is_locked is True
    assert version.status == VERSION_APPROVED
    #  sha256 tính lúc khóa — sau đó nội dung không đổi nữa nên con số này dùng
    #  được để đối chiếu bản in với bản đã duyệt.
    assert len(version.content_sha256) == 64
    assert version.approved_at is not None


def test_sua_ban_da_duyet_bi_tu_choi_409(db, doc):
    version = db.get(DocumentVersion, doc.current_version_id)
    with pytest.raises(HTTPException) as err:
        version_service.save_content(
            db, version, VersionContentUpdate(content_html="<p>Sửa lén</p>"), ACTOR)
    assert err.value.status_code == 409
    db.rollback()
    assert db.get(DocumentVersion, version.id).content_html == "<p>Bản 1</p>"


# ── Mở phiên bản mới ─────────────────────────────────────────────────────────
def test_sua_lon_len_2_0_sua_nho_len_1_1(db, doc):
    version_service.open_new_version(db, doc, VersionCreate(change_summary="Sửa lớn"), ACTOR)
    assert [(v.major, v.minor) for v in _versions(db, doc)] == [(1, 0), (2, 0)]

    #  Chốt bản 2.0 rồi mới mở tiếp được bản sửa nhỏ.
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    version_service.open_new_version(
        db, doc, VersionCreate(change_kind=CHANGE_MINOR, change_summary="Sửa chính tả"), ACTOR)
    assert [(v.major, v.minor) for v in _versions(db, doc)] == [(1, 0), (2, 0), (2, 1)]


def test_ban_moi_chep_noi_dung_ban_cu(db, doc):
    new = version_service.open_new_version(
        db, doc, VersionCreate(change_summary="Sửa điều 2"), ACTOR)
    assert new.content_html == "<p>Bản 1</p>"
    assert new.prev_version_id == doc.current_version_id


def test_sua_lon_mac_dinh_bat_xac_nhan_lai(db, doc):
    major = version_service.open_new_version(
        db, doc, VersionCreate(change_summary="Sửa lớn"), ACTOR)
    assert major.requires_reconfirm is True

    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    minor = version_service.open_new_version(
        db, doc, VersionCreate(change_kind=CHANGE_MINOR, change_summary="Sửa nhỏ"), ACTOR)
    assert minor.requires_reconfirm is False


def test_nguoi_thu_hai_bi_chan_va_biet_ai_dang_giu_nhap(db, doc):
    version_service.open_new_version(db, doc, VersionCreate(change_summary="Sửa lớn"), ACTOR)

    with pytest.raises(HTTPException) as err:
        version_service.open_new_version(
            db, doc, VersionCreate(change_summary="Tôi cũng sửa"), OTHER_ACTOR)
    assert err.value.status_code == 409
    #  Câu báo phải nói RÕ bản nào đang mở — "không mở được" thì người thứ hai
    #  không biết đi hỏi ai.
    assert "2.0" in err.value.detail


def test_ep_o_tang_du_lieu_khong_chi_trong_ma(db, doc):
    """Chèn thẳng một bản nháp thứ hai, bỏ qua service. `open_slot` phải chặn."""
    version_service.open_new_version(db, doc, VersionCreate(change_summary="Sửa lớn"), ACTOR)

    db.add(DocumentVersion(document_id=doc.id, major=3, minor=0,
                           status=VERSION_DRAFT, content_html=""))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_ban_cu_chuyen_sang_da_thay_the_khi_ban_moi_duoc_duyet(db, doc):
    old_id = doc.current_version_id
    version_service.open_new_version(db, doc, VersionCreate(change_summary="Sửa lớn"), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)

    db.refresh(doc)
    assert db.get(DocumentVersion, old_id).status == VERSION_SUPERSEDED
    assert doc.current_version_id != old_id
    #  Bản cũ KHÔNG bị xóa, không bị ẩn — người cầm giấy tờ theo bản 1.0 vẫn
    #  phải tra ra nó (C18).
    assert len(_versions(db, doc)) == 2


def test_mo_ban_moi_khi_dang_co_ban_nhap_bi_chan(db, doc):
    """Bản 2.0 còn nháp thì không mở tiếp 3.0 — hai bản nháp cùng lúc là hai
    người sửa hai hướng rồi không biết bản nào đúng."""
    version_service.open_new_version(db, doc, VersionCreate(change_summary="Sửa lớn"), ACTOR)
    with pytest.raises(HTTPException) as err:
        version_service.open_new_version(db, doc, VersionCreate(change_summary="Sửa nữa"), ACTOR)
    assert err.value.status_code == 409


def test_bat_khai_ly_do_tu_ban_thu_hai(db, doc):
    version_service.open_new_version(db, doc, VersionCreate(change_summary="Sửa lớn"), ACTOR)
    version = service.open_version(db, doc)
    version.change_summary = ""
    db.commit()

    with pytest.raises(HTTPException) as err:
        service.submit(db, doc, ACTOR)
    assert err.value.status_code == 400


def test_dinh_kem_duoc_chep_sang_ban_moi(db, doc):
    from app.modules.attachment.model import FileLink

    db.add(FileLink(file_id=99, entity="document_version",
                    entity_id=doc.current_version_id))
    db.commit()

    new = version_service.open_new_version(
        db, doc, VersionCreate(change_summary="Sửa lớn"), ACTOR)
    copied = db.query(FileLink).filter(FileLink.entity == "document_version",
                                       FileLink.entity_id == new.id).all()
    assert [link.file_id for link in copied] == [99]
    #  Bản cũ vẫn giữ liên kết của nó: bản đã duyệt phải luôn tra ra đúng bộ tệp
    #  lúc duyệt, kể cả khi bản mới gỡ bớt.
    assert db.query(FileLink).filter(FileLink.entity_id == doc.current_version_id).count() == 1
