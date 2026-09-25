"""Chia văn bản cho người ngoài phạm vi thư mục → thư mục chứa nó tự hiện mức XEM
(đại ca chốt 25/09/2026).

Trước đó Văn thư SAM được chia một văn bản nằm ở thư mục «Nhân sự» của DEGO:
đọc được văn bản ở màn Văn bản, nhưng mở trang Thư mục thì không có đường nào
tới nó. Luật mới: thư mục chứa văn bản được chia đích danh (và tổ tiên của nó)
hiện ra ở mức Xem; trong đó người này vẫn chỉ thấy đúng văn bản được chia.
"""
import pytest

from app.modules.doc_catalog import folder_access_service, folder_root_service, folder_service
from app.modules.doc_catalog.folder_access_model import DocFolderAccess
from app.modules.doc_catalog.folder_constants import FolderAccessLevel
from app.modules.doc_catalog.folder_link_model import DocumentFolderLink
from app.modules.doc_catalog.folder_schema import FolderCreate
from app.modules.document.access_model import (EFFECT_ALLOW, EFFECT_DENY, SUBJECT_EMPLOYEE,
                                               DocumentAccess)
from app.modules.document.model import ORIGIN_INTERNAL, Document
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

VIEW = int(FolderAccessLevel.VIEW)


@pytest.fixture()
def setup(db, world):
    """a1 ở pháp nhân A (đọc văn bản trong công ty mình). Nhánh của pháp nhân B:
    gốc B › «Nhân sự» (có văn bản) + «Kế toán» (anh em, không liên quan)."""
    roots = {f.company_id: f for f in folder_root_service.ensure_company_roots(db)}
    actor = world.grant("a1", "document", scope="company", actions=("read",))
    root_b = roots[world.co["B"]]
    hr = folder_service.create_folder(db, FolderCreate(parent_id=root_b.id, name="Nhân sự"), 0)
    acc = folder_service.create_folder(db, FolderCreate(parent_id=root_b.id, name="Kế toán"), 0)
    doc = Document(origin=ORIGIN_INTERNAL, doc_type_id=0, company_id=world.co["B"],
                   department_id=0, owner_employee_id=0, title="Thông báo nghỉ lễ",
                   legacy_code="NL", created_by=0, updated_by=0)
    other = Document(origin=ORIGIN_INTERNAL, doc_type_id=0, company_id=world.co["B"],
                     department_id=0, owner_employee_id=0, title="Bảng lương",
                     legacy_code="BL", created_by=0, updated_by=0)
    db.add_all([doc, other])
    db.flush()
    db.add(DocumentFolderLink(document_id=doc.id, folder_id=hr.id, is_primary=True))
    db.add(DocumentFolderLink(document_id=other.id, folder_id=hr.id, is_primary=True))
    db.commit()
    return actor, root_b, hr, acc, doc


def _share(db, doc, actor, effect=EFFECT_ALLOW):
    row = DocumentAccess(document_id=doc.id, subject_kind=SUBJECT_EMPLOYEE,
                         subject_id=actor.employee.id, effect=effect, can_read=True)
    db.add(row)
    db.commit()
    return row


def _levels(db, actor):
    return folder_access_service.effective_levels(db, actor.user)


def test_chua_chia_thi_khong_thay_nhanh_phap_nhan_khac(db, setup):
    actor, root_b, hr, _acc, _doc = setup
    levels = _levels(db, actor)
    assert hr.id not in levels and root_b.id not in levels


def test_chia_van_ban_thi_thu_muc_chua_no_va_to_tien_hien_muc_xem(db, setup):
    actor, root_b, hr, _acc, doc = setup
    _share(db, doc, actor)
    levels = _levels(db, actor)
    assert levels[hr.id] == VIEW
    assert levels[root_b.id] == VIEW   # phải lần được từ gốc xuống


def test_thu_muc_anh_em_khong_lien_quan_van_an(db, setup):
    actor, _root_b, _hr, acc, doc = setup
    _share(db, doc, actor)
    assert acc.id not in _levels(db, actor)


def test_thu_muc_mo_ra_khong_mo_quyen_doc_van_ban_khac_trong_do(db, setup):
    #  Luật cũ giữ nguyên: quyền thư mục KHÔNG mở quyền đọc văn bản.
    from app.core.auth import get_perm_profile
    from app.modules.document import access_service

    actor, _root_b, hr, _acc, doc = setup
    _share(db, doc, actor)
    cond = access_service.visible_condition(actor.user, get_perm_profile(db, actor.user))
    in_folder = (db.query(Document.title)
                 .join(DocumentFolderLink, DocumentFolderLink.document_id == Document.id)
                 .filter(DocumentFolderLink.folder_id == hr.id, cond).all())
    assert [t for (t,) in in_folder] == ["Thông báo nghỉ lễ"]


def test_thu_hoi_chia_se_thi_thu_muc_tu_bien_mat(db, setup):
    from datetime import datetime

    actor, root_b, hr, _acc, doc = setup
    row = _share(db, doc, actor)
    row.revoked_at = datetime.now()
    db.commit()
    levels = _levels(db, actor)
    assert hr.id not in levels and root_b.id not in levels


def test_chia_roi_lai_cam_van_ban_thi_khong_mo_thu_muc(db, setup):
    actor, _root_b, hr, _acc, doc = setup
    _share(db, doc, actor)
    _share(db, doc, actor, effect=EFFECT_DENY)
    assert hr.id not in _levels(db, actor)


def test_thu_muc_bi_cam_dich_danh_van_giu_cam(db, setup):
    actor, _root_b, hr, _acc, doc = setup
    _share(db, doc, actor)
    db.add(DocFolderAccess(folder_id=hr.id, subject_kind=SUBJECT_EMPLOYEE,
                           subject_id=actor.employee.id, effect=EFFECT_DENY,
                           level=VIEW))
    db.commit()
    assert hr.id not in _levels(db, actor)
