"""LỀ TRANG của phiên bản văn bản — Nghị định 30/2020 điều 8 khoản 3.

Lề trái phải rộng (30–35mm) để còn chỗ đóng gáy; in ra rồi mới phát hiện chữ bị
kẹp vào gáy thì phải in lại cả tập. Ba điều bài này canh:

1. Bản mới sinh ra đã đúng thể thức, người soạn không phải tự chỉnh.
2. Kéo thước lề **không** được xóa thân văn bản — thao tác đó chỉ gửi hai con
   số, mà `content_html` từng là trường bắt buộc.
3. Mở phiên bản mới thì lề đi theo bản gốc, không nhảy về mặc định.
"""
import pytest

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service, version_service
from app.modules.document.schema import (DocumentCreate, VersionContentUpdate,
                                         VersionCreate)
from app.modules.document.version_model import CHANGE_MINOR, DocumentVersion

ACTOR = 1


@pytest.fixture()
def doc(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    return service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế thử",
        content_html="<p>Điều 1.</p>",
    ), ACTOR)


def _ban_dang_mo(db, doc) -> DocumentVersion:
    return db.get(DocumentVersion, doc.current_version_id)


def test_ban_moi_theo_dung_the_thuc_nghi_dinh_30(db, doc):
    version = _ban_dang_mo(db, doc)

    assert version.margin_left_mm == 30
    assert version.margin_right_mm == 20


def test_chi_gui_le_thi_khong_xoa_than_van_ban(db, doc):
    version = _ban_dang_mo(db, doc)

    version_service.save_content(
        db, version, VersionContentUpdate(margin_left_mm=35, margin_right_mm=15), ACTOR)

    assert version.margin_left_mm == 35
    assert version.margin_right_mm == 15
    #  Chỗ này là cả lý do của bài kiểm: trường vắng mặt ≠ trường rỗng.
    assert version.content_html == "<p>Điều 1.</p>"


def test_ghi_noi_dung_khong_dung_toi_le(db, doc):
    version = _ban_dang_mo(db, doc)
    version_service.save_content(
        db, version, VersionContentUpdate(margin_left_mm=35), ACTOR)

    version_service.save_content(
        db, version, VersionContentUpdate(content_html="<p>Điều 2.</p>"), ACTOR)

    assert version.content_html == "<p>Điều 2.</p>"
    assert version.margin_left_mm == 35


def test_ban_moi_thua_huong_le_cua_ban_goc(db, doc):
    version = _ban_dang_mo(db, doc)
    version_service.save_content(
        db, version, VersionContentUpdate(margin_left_mm=32, margin_right_mm=18), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)

    ban_moi = version_service.open_new_version(db, doc, VersionCreate(
        change_kind=CHANGE_MINOR, change_summary="Sửa lỗi chính tả",
        change_reason="Đọc soát lại"), ACTOR)

    assert ban_moi.margin_left_mm == 32
    assert ban_moi.margin_right_mm == 18


def test_danh_so_muc_mac_dinh_tat(db, doc):
    """Bật sẵn thì văn bản cũ mở lên tự nhiên mọc số trước mọi tiêu đề."""
    assert _ban_dang_mo(db, doc).auto_heading_number is False


def test_bat_danh_so_muc_khong_dung_toi_noi_dung(db, doc):
    version = _ban_dang_mo(db, doc)

    version_service.save_content(
        db, version, VersionContentUpdate(auto_heading_number=True), ACTOR)

    assert version.auto_heading_number is True
    assert version.content_html == "<p>Điều 1.</p>"


def test_ban_moi_thua_huong_cach_danh_so_cua_ban_goc(db, doc):
    version = _ban_dang_mo(db, doc)
    version_service.save_content(
        db, version, VersionContentUpdate(auto_heading_number=True), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)

    ban_moi = version_service.open_new_version(db, doc, VersionCreate(
        change_kind=CHANGE_MINOR, change_summary="Sửa lỗi chính tả",
        change_reason="Đọc soát lại"), ACTOR)

    assert ban_moi.auto_heading_number is True


def test_le_vo_ly_bi_chan_ngay_o_schema(db):
    """Lề 5mm hay 200mm là gõ nhầm, không phải nhu cầu — chặn trước khi ghi."""
    with pytest.raises(ValueError):
        VersionContentUpdate(margin_left_mm=5)
    with pytest.raises(ValueError):
        VersionContentUpdate(margin_right_mm=200)
