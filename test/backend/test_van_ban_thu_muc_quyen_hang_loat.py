"""HỘP «CHIA SẺ» KIỂU DRIVE — cấp quyền thư mục HÀNG LOẠT + đổi mức tại chỗ
(phase 10B, đặc tả §C, duoc-CR-476 bổ sung 23/09/2026).

`POST /api/doc-folders/{id}/access/bulk` + `PATCH /api/doc-folders/{id}/access/{access_id}`
— dựng trên thế giới mẫu `world` (`scope_factory.build_world`), cùng nền với
`test_van_ban_thu_muc_quyen.py` (phase 04).
"""
import json

import pytest
from fastapi import HTTPException

from app.core.subject_match import EFFECT_ALLOW, EFFECT_DENY, SUBJECT_EMPLOYEE
from app.modules.doc_catalog import (folder_access_bulk_service, folder_access_controller,
                                     folder_access_grant_service, folder_root_service,
                                     folder_service)
from app.modules.doc_catalog.folder_access_schema import (MAX_BULK_ACCESS_SUBJECTS,
                                                           FolderAccessBulkGrantIn,
                                                           FolderAccessBulkSubjectIn,
                                                           FolderAccessLevelPatchIn)
from app.modules.doc_catalog.folder_constants import FolderAccessLevel
from app.modules.doc_catalog.folder_schema import FolderCreate
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

VIEW = int(FolderAccessLevel.VIEW)
CONTRIBUTE = int(FolderAccessLevel.CONTRIBUTE)


@pytest.fixture()
def roots(db, world):
    created = folder_root_service.ensure_company_roots(db)
    return {f.company_id: f for f in created}


@pytest.fixture()
def folder(db, world, roots):
    return folder_service.create_folder(
        db, FolderCreate(parent_id=roots[world.co["A"]].id, name="Chia sẻ hàng loạt"), 0)


def _bulk(subjects, **kw) -> FolderAccessBulkGrantIn:
    return FolderAccessBulkGrantIn(
        subjects=[FolderAccessBulkSubjectIn(subject_kind=k, subject_id=i) for k, i in subjects],
        **kw)


def _payload(response):
    return json.loads(response.body)["data"]


# ── Trần 200 đối tượng / rỗng — chặn ở SCHEMA, không tới tầng service ────────
def test_bulk_vuot_tran_bi_chan_o_schema():
    subjects = [(SUBJECT_EMPLOYEE, i + 1) for i in range(MAX_BULK_ACCESS_SUBJECTS + 1)]
    with pytest.raises(ValueError):
        _bulk(subjects)


def test_bulk_dung_tran_thi_khong_sao():
    subjects = [(SUBJECT_EMPLOYEE, i + 1) for i in range(MAX_BULK_ACCESS_SUBJECTS)]
    assert len(_bulk(subjects).subjects) == MAX_BULK_ACCESS_SUBJECTS


def test_bulk_danh_sach_rong_bi_chan_o_schema():
    with pytest.raises(ValueError):
        _bulk([])


def test_bulk_subject_kind_khong_hop_le_bi_chan_o_schema():
    with pytest.raises(ValueError):
        _bulk([(99, 1)])


# ── Tạo mới, đếm đúng ─────────────────────────────────────────────────────────
def test_bulk_tao_moi_dem_dung_khong_bi_skip(db, world, folder):
    data = _bulk([(SUBJECT_EMPLOYEE, world.emp["a1"]), (SUBJECT_EMPLOYEE, world.emp["a2"])],
                level=CONTRIBUTE)
    result = folder_access_bulk_service.grant_bulk(db, folder, data, 0)
    assert result == {"created": 2, "updated": 0, "skipped": []}
    rows = folder_access_grant_service.list_direct(db, folder.id)
    assert len(rows) == 2
    assert {r.level for r in rows} == {CONTRIBUTE}


def test_bulk_trung_lap_trong_cung_mot_luot_chi_tao_mot_dong(db, world, folder):
    """Dán nhầm cùng một người hai lần trong CÙNG một lượt gửi — không tạo hai dòng."""
    data = _bulk([(SUBJECT_EMPLOYEE, world.emp["a1"]), (SUBJECT_EMPLOYEE, world.emp["a1"])])
    result = folder_access_bulk_service.grant_bulk(db, folder, data, 0)
    assert result["created"] == 1
    assert len(folder_access_grant_service.list_direct(db, folder.id)) == 1


def test_bulk_da_co_quyen_thi_cap_nhat_khong_tao_trung(db, world, folder):
    first = _bulk([(SUBJECT_EMPLOYEE, world.emp["a1"])], level=VIEW)
    folder_access_bulk_service.grant_bulk(db, folder, first, 0)

    second = _bulk([(SUBJECT_EMPLOYEE, world.emp["a1"])], level=CONTRIBUTE)
    result = folder_access_bulk_service.grant_bulk(db, folder, second, 0)

    assert result == {"created": 0, "updated": 1, "skipped": []}
    rows = folder_access_grant_service.list_direct(db, folder.id)
    assert len(rows) == 1
    assert rows[0].level == CONTRIBUTE


def test_bulk_chu_the_khong_ton_tai_bi_skip_khong_chan_ca_lo(db, world, folder):
    data = _bulk([(SUBJECT_EMPLOYEE, world.emp["a1"]), (SUBJECT_EMPLOYEE, 999999)])
    result = folder_access_bulk_service.grant_bulk(db, folder, data, 0)

    assert result["created"] == 1
    assert result["skipped"] == [
        {"subject": {"subject_kind": SUBJECT_EMPLOYEE, "subject_id": 999999},
         "reason": "Không tìm thấy đối tượng"}
    ]
    assert len(folder_access_grant_service.list_direct(db, folder.id)) == 1


def test_bulk_cam_va_cho_cung_luc_ra_hai_dong_rieng(db, world, folder):
    """Cùng một người, gọi lần 1 CHO PHÉP rồi lần 2 CẤM — hai dòng riêng, dòng
    CHO không bị dòng CẤM ghi đè (dedupe theo chủ thể VÀ chiều tác động)."""
    allow = _bulk([(SUBJECT_EMPLOYEE, world.emp["a1"])], effect=EFFECT_ALLOW, level=CONTRIBUTE)
    deny = _bulk([(SUBJECT_EMPLOYEE, world.emp["a1"])], effect=EFFECT_DENY)

    r1 = folder_access_bulk_service.grant_bulk(db, folder, allow, 0)
    r2 = folder_access_bulk_service.grant_bulk(db, folder, deny, 0)

    assert r1["created"] == 1
    assert r2["created"] == 1   # KHÔNG phải "updated" — chiều tác động khác, dòng khác
    rows = folder_access_grant_service.list_direct(db, folder.id)
    assert len(rows) == 2
    assert {r.effect for r in rows} == {EFFECT_ALLOW, EFFECT_DENY}


# ── Cổng quyền Quản lý — dùng CHUNG `_folder_for_manage` với đường đơn lẻ ────
def test_bulk_khong_du_quyen_bi_chan_403(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read",))   # → CONTRIBUTE, chưa MANAGE
    root = roots[world.co["A"]]
    a1 = world.actor("a1")
    with pytest.raises(HTTPException) as exc:
        folder_access_controller._folder_for_manage(db, root.id, a1.user, a1.profile())
    assert exc.value.status_code == 403


def test_bulk_qua_controller_thanh_cong_tra_dung_hinh_dang(db, world, folder):
    world.grant("a1", "doc_folder", scope="all", actions=("read", "write"))
    a1 = world.actor("a1")
    data = _bulk([(SUBJECT_EMPLOYEE, world.emp["a2"])], level=VIEW)

    response = folder_access_controller.grant_access_bulk(folder.id, data, db, a1.user)
    body = _payload(response)
    assert body == {"created": 1, "updated": 0, "skipped": []}


# ── Đổi mức tại chỗ (PATCH) ───────────────────────────────────────────────────
def test_update_level_gia_tri_khong_hop_le_bi_chan_o_schema():
    with pytest.raises(ValueError):
        FolderAccessLevelPatchIn(level=9)


def test_update_level_doi_muc_thanh_cong(db, world, folder):
    row = folder_access_grant_service.grant(
        db, folder,
        _single_grant_in(SUBJECT_EMPLOYEE, world.emp["a1"], level=VIEW), 0)

    updated = folder_access_bulk_service.update_level(db, folder, row.id, CONTRIBUTE, 0)
    assert updated.id == row.id
    assert updated.level == CONTRIBUTE
    assert folder_access_grant_service.list_direct(db, folder.id)[0].level == CONTRIBUTE


def test_update_level_dong_cam_khong_co_muc_de_doi(db, world, folder):
    row = folder_access_grant_service.grant(
        db, folder,
        _single_grant_in(SUBJECT_EMPLOYEE, world.emp["a1"], effect=EFFECT_DENY), 0)

    with pytest.raises(HTTPException) as exc:
        folder_access_bulk_service.update_level(db, folder, row.id, CONTRIBUTE, 0)
    assert exc.value.status_code == 400


def test_update_level_da_thu_hoi_thi_bao_loi(db, world, folder):
    row = folder_access_grant_service.grant(
        db, folder, _single_grant_in(SUBJECT_EMPLOYEE, world.emp["a1"], level=VIEW), 0)
    folder_access_grant_service.revoke(db, folder, row.id, "thu hồi để kiểm", 0)

    with pytest.raises(HTTPException) as exc:
        folder_access_bulk_service.update_level(db, folder, row.id, CONTRIBUTE, 0)
    assert exc.value.status_code == 400


def test_update_level_khong_thuoc_thu_muc_nay_ra_404(db, world, roots, folder):
    other = folder_service.create_folder(
        db, FolderCreate(parent_id=roots[world.co["A"]].id, name="Thư mục khác"), 0)
    row = folder_access_grant_service.grant(
        db, folder, _single_grant_in(SUBJECT_EMPLOYEE, world.emp["a1"], level=VIEW), 0)

    with pytest.raises(HTTPException) as exc:
        folder_access_bulk_service.update_level(db, other, row.id, CONTRIBUTE, 0)
    assert exc.value.status_code == 404


def test_update_level_qua_controller_thanh_cong(db, world, folder):
    world.grant("a1", "doc_folder", scope="all", actions=("read", "write"))
    a1 = world.actor("a1")
    row = folder_access_grant_service.grant(
        db, folder, _single_grant_in(SUBJECT_EMPLOYEE, world.emp["a2"], level=VIEW), 0)

    response = folder_access_controller.update_access_level(
        folder.id, row.id, FolderAccessLevelPatchIn(level=CONTRIBUTE), db, a1.user)
    body = _payload(response)
    assert body["level"] == CONTRIBUTE
    assert body["id"] == row.id


def _single_grant_in(subject_kind, subject_id, **kw):
    from app.modules.doc_catalog.folder_access_schema import FolderAccessGrantIn

    return FolderAccessGrantIn(subject_kind=subject_kind, subject_id=subject_id, **kw)
