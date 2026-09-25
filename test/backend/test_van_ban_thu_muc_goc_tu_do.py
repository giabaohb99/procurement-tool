"""THƯ MỤC TỰ DO Ở GỐC CÂY (mở 24/09/2026) — `folder_free_root_service`.

Trước đó `parent_id = 0` bị chặn hẳn ("thư mục thường không tạo ngang hàng
gốc"). Nay tạo được, với ba luật canh ở đây: người tạo tự nhận Quản lý, người
khác (kể cả người đọc văn bản toàn hệ) KHÔNG tự thấy, và thư mục nhận văn bản
của mọi pháp nhân nhưng KHÔNG mở quyền đọc văn bản.
"""
import pytest
from fastapi import HTTPException

from app.core.subject_match import SUBJECT_EMPLOYEE
from app.modules.doc_catalog import (folder_access_grant_service, folder_access_service,
                                     folder_free_root_service, folder_link_service,
                                     folder_root_service, folder_service)
from app.modules.doc_catalog.folder_access_schema import FolderAccessGrantIn
from app.modules.doc_catalog.folder_constants import FolderAccessLevel, FolderKind
from app.modules.doc_catalog.folder_schema import FolderCreate
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

VIEW = int(FolderAccessLevel.VIEW)
MANAGE = int(FolderAccessLevel.MANAGE)


@pytest.fixture()
def roots(db, world):
    created = folder_root_service.ensure_company_roots(db)
    return {f.company_id: f for f in created}


def _create_root(db, world, key="a1", name="Hồ sơ dự án"):
    #  Ngoài đời chỉ ai có `doc_folder.create` mới tạo được thư mục — thiếu dòng
    #  này thì trần theo vai trò (`role_level_cap`) hạ người tạo về mức Xem.
    world.grant(key, "doc_folder", scope="company", actions=("read", "create"))
    a = world.actor(key)
    return folder_free_root_service.create_free_root_folder(
        db, FolderCreate(parent_id=0, name=name), a.user.id, a.employee.id)


def _levels(db, world, key):
    a = world.actor(key)
    return folder_access_service.effective_levels(db, a.user, a.profile())


def test_schema_accepts_parent_zero_but_rejects_negative():
    assert FolderCreate(parent_id=0, name="x").parent_id == 0
    with pytest.raises(ValueError):
        FolderCreate(parent_id=-1, name="x")


def test_free_root_folder_sits_at_root_without_company(db, world, roots):
    folder = _create_root(db, world)
    assert folder.parent_id == 0
    assert folder.company_id == 0
    assert folder.kind == int(FolderKind.NORMAL)
    assert folder.path == f"/{folder.id}/"
    assert folder.depth == 1


def test_creator_gets_manage_on_the_new_folder(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read",))
    folder = _create_root(db, world)
    assert _levels(db, world, "a1").get(folder.id) == MANAGE


def test_other_user_does_not_see_it_even_with_document_read_all(db, world, roots):
    """`company_id = 0` + `default_access = PRIVATE` — người đọc văn bản TOÀN
    HỆ cũng không tự thấy thư mục riêng của người khác. Thiếu `PRIVATE` là
    thư mục này lộ cho mọi người có scope `all`."""
    folder = _create_root(db, world, "a1")
    world.grant("b1", "document", scope="all", actions=("read",))
    assert folder.id not in _levels(db, world, "b1")


def test_sharing_opens_it_to_another_user(db, world, roots):
    folder = _create_root(db, world, "a1")
    b = world.actor("b1")
    folder_access_grant_service.grant(
        db, folder, FolderAccessGrantIn(subject_kind=SUBJECT_EMPLOYEE, subject_id=b.employee.id, level=VIEW), 0)
    assert _levels(db, world, "b1").get(folder.id) == VIEW


def test_subfolder_inherits_company_zero_and_creator_access(db, world, roots):
    folder = _create_root(db, world, "a1")
    child = folder_service.create_folder(db, FolderCreate(parent_id=folder.id, name="Con"), 0)
    assert child.company_id == 0
    assert child.path == f"/{folder.id}/{child.id}/"
    assert _levels(db, world, "a1").get(child.id) == MANAGE
    world.grant("b1", "document", scope="all", actions=("read",))
    assert child.id not in _levels(db, world, "b1")


def test_blank_and_duplicate_names_are_rejected(db, world, roots):
    with pytest.raises(HTTPException):
        _create_root(db, world, name="   ")
    _create_root(db, world, name="Hợp đồng")
    with pytest.raises(HTTPException):
        _create_root(db, world, name="hop dong")   # gập dấu + hoa/thường vẫn trùng


def test_account_without_employee_cannot_create_orphan_root(db, world, roots):
    """Không có nhân sự = không có chủ thể để cấp Quản lý → thư mục mồ côi."""
    a = world.actor("a1")
    with pytest.raises(HTTPException):
        folder_free_root_service.create_free_root_folder(db, FolderCreate(parent_id=0, name="X"), a.user.id, 0)


def test_free_folder_accepts_documents_of_any_company(db, world, roots):
    folder = _create_root(db, world)
    for company_id in (world.co["A"], world.co["B"]):
        assert folder_link_service.validate_folder_for_company(db, folder.id, company_id).id == folder.id


def test_moving_free_folder_back_to_root_keeps_mover_access(db, world, roots):
    """Thư mục tự do con → chuyển ra gốc thì mất quyền kế thừa từ cha cũ; người
    chuyển phải GIỮ được mức Quản lý, không thì thư mục biến mất khỏi mắt họ."""
    from app.modules.doc_catalog import folder_move_service

    parent = _create_root(db, world, "a1", name="Cha")
    child = folder_service.create_folder(db, FolderCreate(parent_id=parent.id, name="Con"), 0)
    a = world.actor("a1")
    folder_move_service.move_folder(db, child, 0, a.user.id, a.employee.id)
    assert _levels(db, world, "a1").get(child.id) == MANAGE
    world.grant("b1", "document", scope="all", actions=("read",))
    assert child.id not in _levels(db, world, "b1")
