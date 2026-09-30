"""bao-CR-527 — Phân công phụ trách: đúng 1 NSTM chính + tối đa 1 dự phòng, NSTM chính phải
«Chính thức» (khách chốt 30/09/2026).

Luật chốt ở MỘT chỗ (`category_assignee.service.validate_assignee_pair`) cho mọi cửa ghi — tạo,
sửa, gán hàng loạt:
  · NSTM chính BẮT BUỘC, phải «Chính thức» + đang hoạt động; sai → 400, câu nói rõ người + tình
    trạng;
  · dự phòng không bắt buộc; có thì phải khác người chính và cũng «Chính thức» + đang hoạt động.
Màn danh sách nhận cờ `primary_not_official` để gắn cảnh báo cho dòng có người chính NAY đã nghỉ.
Tự gán lúc duyệt/điều phối: người chính không còn «Chính thức» → dự phòng; không ai → để trống.
"""
import json

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.status_codes import EMPLOYEE_STATUS
from app.modules.catalog.model import ItemGroup
from app.modules.category_assignee import controller as ca_ctl
from app.modules.category_assignee import service as ca_service
from app.modules.category_assignee.model import CategoryAssignee
from app.modules.category_assignee.schema import CategoryAssigneeCreate, CategoryAssigneeUpdate
from app.modules.employee.model import Employee
from app.modules.employee.service import STATUS_OFFICIAL
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem

_n = {"i": 0}


def _emp(db, seed, status: str = "official", active: bool = True, name: str = "") -> Employee:
    _n["i"] += 1
    emp = Employee(code=f"T525{_n['i']:02d}", full_name=name or f"Người 525-{_n['i']}",
                   company_id=seed.company_id, department_id=seed.dept_id, status=status,
                   is_active=active)
    db.add(emp)
    db.commit()
    return emp


@pytest.fixture
def groups(db, seed):
    db.query(CategoryAssignee).delete()
    db.commit()
    nhan = db.query(ItemGroup).filter(ItemGroup.name == "Nhãn").one()
    thung = db.query(ItemGroup).filter(ItemGroup.name == "Thùng").one()
    return nhan.id, thung.id


def _create(db, seed, group_id: int, primary: int, backup: int = 0) -> CategoryAssignee:
    return ca_service.create(db, CategoryAssigneeCreate(item_group_id=group_id, primary_employee_id=primary,
                                                        backup_employee_id=backup), user_id=seed.u_req_id)


def test_official_code_is_the_catalog_code():
    assert STATUS_OFFICIAL in EMPLOYEE_STATUS.values
    assert EMPLOYEE_STATUS.label_of(STATUS_OFFICIAL) == "Chính thức"


def test_primary_is_required(db, seed, groups):
    with pytest.raises(HTTPException) as e:
        _create(db, seed, groups[0], 0)
    assert e.value.status_code == 400 and "NSTM chính" in e.value.detail
    assert db.query(CategoryAssignee).count() == 0


@pytest.mark.parametrize("status,active,label", [
    ("maternity_leave", True, "Nghỉ thai sản"),
    ("resigned", True, "Nghỉ việc"),
    ("collaborator", True, "Cộng tác viên"),
    ("official", False, "ngừng hoạt động"),
])
def test_primary_must_be_official_and_active(db, seed, groups, status, active, label):
    bad = _emp(db, seed, status=status, active=active, name="Trần Thị Bận")
    with pytest.raises(HTTPException) as e:
        _create(db, seed, groups[0], bad.id)
    assert e.value.status_code == 400
    assert "Trần Thị Bận" in e.value.detail and label in e.value.detail, "câu chặn phải nói rõ ai + vì sao"
    assert db.query(CategoryAssignee).count() == 0


def test_unknown_primary_id_is_rejected_not_stored(db, seed, groups):
    with pytest.raises(HTTPException) as e:
        _create(db, seed, groups[0], 987_654)
    assert e.value.status_code == 400


def test_backup_is_optional_but_must_differ_and_be_official(db, seed, groups):
    ok = _create(db, seed, groups[0], seed.emp_nstm_id)
    assert ok.backup_employee_id == 0
    with pytest.raises(HTTPException) as e:
        _create(db, seed, groups[1], seed.emp_nstm_id, seed.emp_nstm_id)
    assert "khác" in e.value.detail
    gone = _emp(db, seed, status="resigned", name="Lê Văn Đi")
    with pytest.raises(HTTPException) as e:
        _create(db, seed, groups[1], seed.emp_nstm_id, gone.id)
    assert "NSTM dự phòng" in e.value.detail and "Lê Văn Đi" in e.value.detail


def test_update_checks_the_resulting_pair_even_when_only_another_field_changes(db, seed, groups):
    primary = _emp(db, seed)
    row = _create(db, seed, groups[0], primary.id)
    primary.status = "maternity_leave"
    db.commit()
    with pytest.raises(HTTPException):
        ca_service.update(db, row.id, CategoryAssigneeUpdate(backup_employee_id=seed.emp_backup_id), seed.u_req_id)
    with pytest.raises(HTTPException):   # xóa trắng người chính cũng không được
        ca_service.update(db, row.id, CategoryAssigneeUpdate(primary_employee_id=0), seed.u_req_id)
    with pytest.raises(HTTPException):   # dự phòng trùng người chính mới
        ca_service.update(db, row.id, CategoryAssigneeUpdate(primary_employee_id=seed.emp_nstm_id,
                                                             backup_employee_id=seed.emp_nstm_id), seed.u_req_id)
    fixed = ca_service.update(db, row.id, CategoryAssigneeUpdate(primary_employee_id=seed.emp_nstm_id,
                                                                 backup_employee_id=seed.emp_backup_id), seed.u_req_id)
    assert (fixed.primary_employee_id, fixed.backup_employee_id) == (seed.emp_nstm_id, seed.emp_backup_id)


def test_bulk_assign_is_blocked_before_any_row_is_written(db, seed, groups):
    gone = _emp(db, seed, status="resigned")
    with pytest.raises(HTTPException):
        ca_service.bulk_upsert(db, list(groups), gone.id, 0, seed.u_req_id)
    with pytest.raises(HTTPException):
        ca_service.bulk_upsert(db, list(groups), 0, seed.emp_backup_id, seed.u_req_id)
    with pytest.raises(HTTPException):
        ca_service.bulk_upsert(db, list(groups), seed.emp_nstm_id, seed.emp_nstm_id, seed.u_req_id)
    assert db.query(CategoryAssignee).count() == 0
    assert ca_service.bulk_upsert(db, list(groups), seed.emp_nstm_id, seed.emp_backup_id, seed.u_req_id) == 2


def test_list_and_detail_flag_rows_whose_current_primary_is_no_longer_official(db, seed, groups):
    leaving = _emp(db, seed)
    stale = _create(db, seed, groups[0], leaving.id)
    fine = _create(db, seed, groups[1], seed.emp_nstm_id)
    leaving.status = "resigned"
    db.commit()

    req = Request({"type": "http", "query_string": b"", "headers": []})
    items = json.loads(ca_ctl.list_(req, "item_group_name", "asc", "", "", {"offset": 0, "limit": 50},
                                    db, None).body)["data"]["items"]
    by_id = {r["id"]: r for r in items}
    assert by_id[stale.id]["primary_not_official"] is True
    assert by_id[stale.id]["primary_status"] == "resigned"
    assert by_id[stale.id]["primary_status_label"] == "Nghỉ việc"
    assert by_id[fine.id]["primary_not_official"] is False
    detail = json.loads(ca_ctl.get_(stale.id, db, None).body)["data"]
    assert detail["primary_not_official"] is True


def _pr_with_line(db, seed, group_name: str) -> PurchaseRequest:
    pr = PurchaseRequest(code=f"PYC-525-{group_name}-{_n['i']}", company_id=seed.company_id,
                         department_id=seed.dept_id, status="approved", created_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_name="Hàng", item_group=group_name,
                               created_by=seed.u_req_id))
    db.commit()
    return pr


def test_auto_assign_falls_back_to_backup_when_primary_is_not_official(db, seed, groups):
    primary = _emp(db, seed)
    backup = _emp(db, seed)
    _create(db, seed, groups[0], primary.id, backup.id)
    primary.status = "maternity_leave"        # hồ sơ vẫn bật — trước CR-527 vẫn được gán việc
    db.commit()
    pr = _pr_with_line(db, seed, "Nhãn")
    assert ca_service.auto_assign_by_category(db, pr) == 1
    line = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).one()
    assert line.assignee == backup.code


def test_auto_assign_leaves_the_line_blank_when_neither_is_official(db, seed, groups):
    primary = _emp(db, seed)
    backup = _emp(db, seed)
    _create(db, seed, groups[0], primary.id, backup.id)
    primary.status = "resigned"
    backup.is_active = False                  # trước CR-527 dự phòng được trả thẳng dù đã tắt
    db.commit()
    pr = _pr_with_line(db, seed, "Nhãn")
    assert ca_service.auto_assign_by_category(db, pr) == 0
    line = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).one()
    assert line.assignee in ("", None)
    assert ca_service.resolve_for_group(db, "Nhãn") is None


def test_official_primary_is_still_picked_first(db, seed, groups):
    _create(db, seed, groups[0], seed.emp_nstm_id, seed.emp_backup_id)
    assert ca_service.resolve_for_group(db, "Nhãn").code == seed.emp_nstm_code
