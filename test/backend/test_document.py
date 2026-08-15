"""VĂN BẢN — vòng đời, cấp số, lọc `origin`.

Bốn thứ được canh ở đây, mỗi thứ là một chỗ mà sai thì không sửa lại được sau khi
văn bản đã ban hành:

1. **Lọc `origin = 1`** — bảng chứa cả văn bản pháp luật ngoài và văn bản đến;
   để lọt vào danh sách của phân hệ là lộ bản ghi không thuộc về nó.
2. **Cấp số theo `number_when`** — cấp lúc nháp hay lúc duyệt, và cấp đúng một lần.
3. **`status` của văn bản khác `status` của phiên bản** — lên bản 2.0 mà văn bản
   rơi khỏi trạng thái "có hiệu lực" thì cả công ty thấy quy chế biến mất.
4. **Xóa** chỉ khi còn nháp chưa cấp số — số đã cấp là số đã nằm trong sổ.
"""
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service
from app.modules.document.model import (ORIGIN_LEGAL, STATUS_DRAFT,
                                        STATUS_EFFECTIVE, STATUS_SUBMITTED,
                                        Document)
from app.modules.document.query import documents_query
from app.modules.document.schema import DocumentCreate
from app.modules.document.version_model import VERSION_APPROVED, DocumentVersion

ACTOR = 1


@pytest.fixture()
def doc_types(db):
    """Hai loại: một loại cấp số theo sổ, một loại mang mã tài liệu bất biến."""
    cv = DocType(code="CV", name="Công văn", id_scheme=2, number_when=2, default_secrecy=2)
    qc = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=1, default_secrecy=2)
    db.add_all([cv, qc])
    db.commit()
    return {"CV": cv, "QC": qc}


@pytest.fixture()
def company(db, seed):
    obj = db.get(Company, seed.company_id)
    obj.issue_code = "DEGO"
    db.commit()
    return obj


def _payload(doc_types, seed, type_code="CV", **kwargs):
    data = dict(
        doc_type_id=doc_types[type_code].id,
        company_id=seed.company_id,
        department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id,
        title="Văn bản thử",
        content_html="<p>Nội dung</p>",
    )
    data.update(kwargs)
    return DocumentCreate(**data)


def _create(db, doc_types, seed, **kwargs):
    return service.create_document(db, _payload(doc_types, seed, **kwargs), ACTOR)


# ── 1. Lọc origin ────────────────────────────────────────────────────────────
def test_truy_van_dung_chung_bo_qua_van_ban_ngoai(db, doc_types, seed, company):
    _create(db, doc_types, seed)
    db.add(Document(origin=ORIGIN_LEGAL, title="Nghị định 30/2020/NĐ-CP",
                    legal_issuer="Chính phủ"))
    db.commit()

    assert db.query(Document).count() == 2
    #  Đây là điều kiện then chốt: hàm dựng truy vấn dùng chung phải cắt bản ghi
    #  `origin = 2` ra khỏi mọi màn hình của phân hệ.
    rows = documents_query(db).all()
    assert len(rows) == 1
    assert rows[0].title == "Văn bản thử"


def test_goi_y_van_ban_trung_khong_lay_van_ban_ngoai(db, doc_types, seed, company):
    doc = _create(db, doc_types, seed)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)

    db.add(Document(origin=ORIGIN_LEGAL, doc_type_id=doc_types["CV"].id,
                    company_id=seed.company_id, department_id=seed.dept_id,
                    title="Văn bản ngoài", status=STATUS_EFFECTIVE))
    db.commit()

    found = service.suggestions(db, doc_types["CV"].id, seed.dept_id, seed.company_id)
    assert [item["title"] for item in found] == ["Văn bản thử"]


# ── 2. Cấp số ────────────────────────────────────────────────────────────────
def test_cap_so_luc_duyet_theo_number_when(db, doc_types, seed, company):
    doc = _create(db, doc_types, seed)
    #  `number_when = 2`: nháp thì CHƯA có số. Cấp sớm rồi hủy là thủng sổ.
    assert doc.issue_number == ""

    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    year = date.today().year
    assert doc.issue_number == f"01/{year}/CV-DEGO"
    assert doc.seq_no == 1


def test_cap_so_luc_tao_nhap_va_ma_bat_bien(db, doc_types, seed, company):
    doc = _create(db, doc_types, seed, type_code="QC")
    #  `number_when = 1` + `id_scheme = 1`: có mã ngay từ bản nháp.
    assert doc.doc_code == "DEGO-QC-001"
    assert doc.issue_number == ""


def test_so_da_cap_khong_cap_lai(db, doc_types, seed, company):
    doc = _create(db, doc_types, seed)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    first = doc.issue_number

    #  Duyệt phiên bản sau KHÔNG được cấp số mới: số hiệu thuộc về văn bản, không
    #  thuộc về phiên bản.
    from app.modules.document.schema import VersionCreate
    from app.modules.document import version_service
    version_service.open_new_version(
        db, doc, VersionCreate(change_summary="Sửa điều 2"), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    assert doc.issue_number == first


def test_van_ban_thu_hai_lay_so_ke_tiep(db, doc_types, seed, company):
    numbers = []
    for _ in range(3):
        doc = _create(db, doc_types, seed)
        service.submit(db, doc, ACTOR)
        service.approve(db, doc, ACTOR)
        numbers.append(doc.seq_no)
    assert numbers == [1, 2, 3]


# ── 3. Trạng thái ────────────────────────────────────────────────────────────
def test_ban_moi_dang_duyet_van_ban_van_con_hieu_luc(db, doc_types, seed, company):
    """Chỗ dễ sai số 7 của `van-thu/02` — bài kiểm quan trọng nhất tệp này."""
    from app.modules.document import version_service
    from app.modules.document.schema import VersionCreate

    doc = _create(db, doc_types, seed)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    current = doc.current_version_id

    version_service.open_new_version(
        db, doc, VersionCreate(change_summary="Sửa điều 2"), ACTOR)
    service.submit(db, doc, ACTOR)

    db.refresh(doc)
    assert doc.status == STATUS_EFFECTIVE, "văn bản phải VẪN có hiệu lực khi bản 2.0 đang duyệt"
    assert doc.current_version_id == current, "bản đang dùng vẫn phải là 1.0"


def test_tra_lai_ban_dau_thi_ve_nhap(db, doc_types, seed, company):
    doc = _create(db, doc_types, seed)
    service.submit(db, doc, ACTOR)
    assert doc.status == STATUS_SUBMITTED

    service.reject(db, doc, "Thiếu căn cứ pháp lý", ACTOR)
    assert doc.status == STATUS_DRAFT


def test_gui_duyet_khi_noi_dung_trong_bi_chan(db, doc_types, seed, company):
    doc = _create(db, doc_types, seed, content_html="")
    with pytest.raises(HTTPException) as err:
        service.submit(db, doc, ACTOR)
    assert err.value.status_code == 400


def test_ngay_hieu_luc_tuong_lai_chua_ap_dung_ngay(db, doc_types, seed, company):
    tomorrow = date.today() + timedelta(days=1)
    doc = _create(db, doc_types, seed, effective_date=tomorrow)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)

    #  Đã duyệt nhưng CHƯA tới ngày — không được ghi là đang có hiệu lực.
    assert doc.status != STATUS_EFFECTIVE
    assert service.activate_due_versions(db, doc.id) == 0

    #  Kéo ngày về hôm nay rồi chạy lại tác vụ: lúc này mới chuyển.
    version = db.get(DocumentVersion, doc.current_version_id) or db.query(
        DocumentVersion).filter(DocumentVersion.document_id == doc.id).first()
    version.effective_from = date.today()
    db.commit()
    assert service.activate_due_versions(db, doc.id) == 1
    db.refresh(doc)
    assert doc.status == STATUS_EFFECTIVE


# ── 4. Xóa và sửa ────────────────────────────────────────────────────────────
def test_khong_xoa_van_ban_da_cap_so(db, doc_types, seed, company):
    doc = _create(db, doc_types, seed)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)

    with pytest.raises(HTTPException) as err:
        service.delete_document(db, doc)
    assert err.value.status_code == 400


def test_xoa_duoc_nhap_chua_cap_so(db, doc_types, seed, company):
    doc = _create(db, doc_types, seed)
    doc_id = doc.id
    service.delete_document(db, doc)
    assert db.get(Document, doc_id) is None
    #  Xóa văn bản phải kéo theo phiên bản của nó, không để lại dòng mồ côi.
    assert db.query(DocumentVersion).filter(DocumentVersion.document_id == doc_id).count() == 0


def test_khong_doi_loai_sau_khi_da_cap_so(db, doc_types, seed, company):
    from app.modules.document.schema import DocumentUpdate

    doc = _create(db, doc_types, seed)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)

    with pytest.raises(HTTPException) as err:
        service.update_document(db, doc, DocumentUpdate(doc_type_id=doc_types["QC"].id), ACTOR)
    assert err.value.status_code == 400


def test_muc_mat_theo_mac_dinh_cua_loai(db, doc_types, seed, company):
    doc_types["CV"].default_secrecy = 3
    db.commit()
    doc = _create(db, doc_types, seed)
    assert doc.secrecy_level == 3


def test_phien_ban_dau_tien_duoc_tao_kem_van_ban(db, doc_types, seed, company):
    doc = _create(db, doc_types, seed)
    versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).all()
    assert len(versions) == 1
    assert (versions[0].major, versions[0].minor) == (1, 0)
    assert doc.current_version_id == versions[0].id
    assert versions[0].status != VERSION_APPROVED
