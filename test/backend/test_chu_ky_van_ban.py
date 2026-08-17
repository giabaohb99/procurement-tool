"""CHỮ KÝ trên văn bản (J02, J03).

Nguy hiểm lớn nhất của nhóm này không phải lỗi kỹ thuật mà là **nhầm giá trị
pháp lý**: ký điện tử nội bộ chỉ có giá trị trong tập đoàn, ký số có chứng thư
mới có giá trị với bên ngoài. Nhầm hai thứ đó là gửi ra ngoài một văn bản tưởng
có giá trị pháp lý mà thật ra không.

Vì thế bài kiểm ở đây canh nặng nhất hai chỗ: không cho ghi "ký số" khi không có
chứng thư, và mã băm nội dung phải lộ ra khi nội dung đã đổi sau lúc ký.
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service, signature_service
from app.modules.document.schema import DocumentCreate, VersionCreate
from app.modules.document.signature_model import (SIGN_CERTIFIED, SIGN_INTERNAL,
                                                  SIGN_KIND_NOTES, SIGN_SCANNED)
from app.modules.document.version_model import CHANGE_MAJOR, DocumentVersion

ACTOR = 1


@pytest.fixture()
def da_ban_hanh(db, seed):
    """Văn bản đã duyệt — phiên bản 1.0 đã khóa và đã có mã băm."""
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QD", name="Quyết định", id_scheme=2, number_when=2)
    db.add(doc_type)
    db.commit()

    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quyết định bổ nhiệm",
        content_html="<p>Điều 1. Bổ nhiệm ông A.</p>",
    ), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    return doc, seed.emp_req_id


def _ky(db, doc, version_id, employee_id, **kwargs):
    return signature_service.sign(
        db, doc, version_id=version_id, signer_employee_id=employee_id,
        sign_kind=kwargs.get("sign_kind", SIGN_INTERNAL),
        cert_serial=kwargs.get("cert_serial", ""),
        cert_issuer=kwargs.get("cert_issuer", ""),
        ip="10.0.0.9", user_agent="pytest", actor=ACTOR,
    )


# ── J02 · bản ghi ký đủ giá trị nội bộ ───────────────────────────────────────
def test_chu_ky_ghi_du_nguoi_thoi_diem_dia_chi_va_ma_bam(db, da_ban_hanh):
    """Thiếu bất kỳ thứ nào thì chữ ký chỉ là một dòng ai cũng ghi được."""
    doc, employee_id = da_ban_hanh
    chu_ky = _ky(db, doc, doc.current_version_id, employee_id)

    assert chu_ky.signer_employee_id == employee_id
    assert chu_ky.signed_at is not None
    assert chu_ky.ip == "10.0.0.9"
    assert len(chu_ky.content_sha256) == 64


def test_ma_bam_chep_luc_ky_chu_khong_tro_sang_bang_phien_ban(db, da_ban_hanh):
    """Nội dung đổi sau khi ký thì chữ ký phải LỘ RA là đang lệch."""
    doc, employee_id = da_ban_hanh
    chu_ky = _ky(db, doc, doc.current_version_id, employee_id)
    assert signature_service.serialize(db, chu_ky)["content_matches"] is True

    #  Giả lập nội dung bị đổi sau lúc ký.
    version = db.get(DocumentVersion, doc.current_version_id)
    version.content_sha256 = "0" * 64
    db.commit()

    assert signature_service.serialize(db, chu_ky)["content_matches"] is False
    #  Bản thân chữ ký KHÔNG đổi theo — đó mới là bằng chứng.
    assert chu_ky.content_sha256 != "0" * 64


# ── Chỉ ký được bản đã khóa ─────────────────────────────────────────────────
def test_khong_ky_duoc_ban_nhap(db, da_ban_hanh):
    """Bản nháp còn sửa được — ký vào đó là ký một thứ sẽ đổi ngay sau."""
    from app.modules.document.version_service import open_new_version

    doc, employee_id = da_ban_hanh
    ban_moi = open_new_version(db, doc, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa điều 1",
    ), ACTOR)

    with pytest.raises(HTTPException) as loi:
        _ky(db, doc, ban_moi.id, employee_id)
    assert "chưa khóa" in loi.value.detail


def test_mot_nguoi_chi_ky_mot_lan_tren_mot_phien_ban(db, da_ban_hanh):
    doc, employee_id = da_ban_hanh
    _ky(db, doc, doc.current_version_id, employee_id)

    with pytest.raises(HTTPException) as loi:
        _ky(db, doc, doc.current_version_id, employee_id)
    assert "đã ký" in loi.value.detail


# ── J03 · không cho nhầm giá trị pháp lý ────────────────────────────────────
def test_ky_so_khong_co_chung_thu_bi_tu_choi(db, da_ban_hanh):
    """Thiếu chứng thư mà vẫn ghi là ký số = ký nội bộ đội lốt ký số."""
    doc, employee_id = da_ban_hanh

    with pytest.raises(HTTPException) as loi:
        _ky(db, doc, doc.current_version_id, employee_id, sign_kind=SIGN_CERTIFIED)
    assert "chứng thư" in loi.value.detail


def test_ky_so_co_du_chung_thu_thi_ghi_duoc(db, da_ban_hanh):
    doc, employee_id = da_ban_hanh
    chu_ky = _ky(db, doc, doc.current_version_id, employee_id,
                 sign_kind=SIGN_CERTIFIED, cert_serial="01ABCD",
                 cert_issuer="VNPT-CA")

    assert chu_ky.sign_kind == SIGN_CERTIFIED
    assert chu_ky.cert_serial == "01ABCD"


def test_moi_loai_chu_ky_deu_kem_cau_gia_tri_phap_ly(db, da_ban_hanh):
    """Câu này do backend cấp — giao diện không được tự viết lại nhẹ tay hơn."""
    doc, employee_id = da_ban_hanh
    chu_ky = _ky(db, doc, doc.current_version_id, employee_id)
    data = signature_service.serialize(db, chu_ky)

    assert data["legal_note"] == SIGN_KIND_NOTES[SIGN_INTERNAL]
    assert "KHÔNG có giá trị với bên ngoài" in data["legal_note"]


def test_ky_giay_da_quet_khong_doi_hoi_chung_thu(db, da_ban_hanh):
    doc, employee_id = da_ban_hanh
    assert _ky(db, doc, doc.current_version_id, employee_id,
               sign_kind=SIGN_SCANNED).sign_kind == SIGN_SCANNED


def test_loai_chu_ky_la_bi_tu_choi(db, da_ban_hanh):
    doc, employee_id = da_ban_hanh
    with pytest.raises(HTTPException):
        _ky(db, doc, doc.current_version_id, employee_id, sign_kind=9)
