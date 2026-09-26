"""bao-CR-497 — ĐIỀU KIỆN bỏ qua bước thu mua duyệt lần 2 (điều phối) cho một nhóm phiếu YCMH.

Đại ca chốt 25/09/2026 (đường A): giữ công tắc chung `pr_dispatch_enabled`, thêm ô điều kiện JSON
`pr_dispatch_skip_rules` cú pháp của bộ máy duyệt chung. Ba điều phải đúng:
  · ô điều kiện RỖNG → mọi thứ y như cũ (công tắc bật = hai bước, tắt = một bước);
  · có điều kiện «phiếu có phòng xử lý riêng» → phiếu nhà máy tự mua đi thẳng, nhân sự lấy theo bộ
    phân công RIÊNG của phòng (không rơi về Thu mua chung); phiếu thu mua chung vẫn chờ bước 2;
  · JSON gõ sai không được đổi luồng của cả công ty.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks

from app.modules.category_assignee.model import CategoryAssignee
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.catalog.model import ItemGroup
from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request import service as S
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ApproveIn

USER = SimpleNamespace(id=1)
FACTORY_RULE = '[{"field": "handler_dept_id", "op": "not_empty"}]'


@pytest.fixture(autouse=True)
def _quiet(monkeypatch, cap_quyen):
    monkeypatch.setattr(pr_ctl, "trigger_notification", lambda **kw: None)
    monkeypatch.setattr(pr_ctl, "_notify_assigned", lambda *a, **kw: None)
    monkeypatch.setattr(pr_ctl, "_in_approve_scope", lambda db, user, pid: True)
    cap_quyen(USER.id, "purchase_request", scope="all", read=True, approve=True, write=True)


@pytest.fixture
def settings(monkeypatch):
    """Giả lập hai ô ở màn Cấu hình hệ thống; không đụng DB cấu hình thật."""
    state = {"pr_dispatch_enabled": True, "pr_dispatch_skip_rules": ""}
    from app.core import app_settings
    monkeypatch.setattr(app_settings, "get", lambda key, *a, **kw: state.get(key))
    return state


@pytest.fixture
def factory(db, seed):
    """Nhà máy có bộ phân công riêng: phân loại «Nhãn» → nhân sự F1 của nhà máy."""
    dept = Department(code="NM497", name="Nhà máy", company_id=seed.company_id, is_active=True)
    db.add(dept)
    db.flush()
    buyer = Employee(code="F497", full_name="Thu mua nhà máy", company_id=seed.company_id,
                     department_id=dept.id, is_active=True)
    db.add(buyer)
    db.flush()
    nhan = db.query(ItemGroup).filter(ItemGroup.code == "NHAN").one()
    db.add(CategoryAssignee(item_group_id=nhan.id, department_id=dept.id,
                            primary_employee_id=buyer.id))
    db.commit()
    return SimpleNamespace(id=dept.id, buyer=buyer)


def _pr(db, seed, handler_dept_id: int, code: str):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         head_of_dept_id=seed.emp_req_id, handler_dept_id=handler_dept_id,
                         status="submitted", created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP01", product_name="Hàng Nhãn",
                               item_group="Nhãn", qty=10, unit="cái", price=1000,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


def _approve(db, pr):
    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)
    return pr


def test_empty_rules_keep_the_old_two_step_flow(db, seed, factory, settings):
    pr = _approve(db, _pr(db, seed, factory.id, "PYC-497-A"))
    assert pr.status == "approved", "ô điều kiện rỗng → nhà máy vẫn chờ thu mua duyệt lần 2 như trước"
    assert all(not it.assignee for it in S.items_of(db, pr.id))


def test_switch_off_still_skips_everything(db, seed, factory, settings):
    settings["pr_dispatch_enabled"] = False
    pr = _approve(db, _pr(db, seed, 0, "PYC-497-B"))
    assert pr.status == "dispatched", "công tắc tắt = luồng cũ CR-034, không phụ thuộc ô điều kiện"


def test_factory_rule_separates_self_purchasing_dept_from_central(db, seed, factory, settings):
    settings["pr_dispatch_skip_rules"] = FACTORY_RULE
    fac = _approve(db, _pr(db, seed, factory.id, "PYC-497-C"))
    assert fac.status == "dispatched", "phiếu nhà máy đi thẳng, không qua thu mua chung"
    assert [it.assignee for it in S.items_of(db, fac.id)] == [factory.buyer.code], \
        "nhân sự lấy theo bộ phân công RIÊNG của nhà máy"

    central = _approve(db, _pr(db, seed, 0, "PYC-497-D"))
    assert central.status == "approved", "phiếu thu mua chung vẫn chờ bước 2"


def test_factory_without_own_assignment_does_not_fall_back_to_central(db, seed, settings):
    """Bỏ qua điều phối để TÁCH nhà máy — không được lén đẩy việc sang tay thu mua chung."""
    dept = Department(code="NM497B", name="Nhà máy B", company_id=seed.company_id, is_active=True)
    db.add(dept)
    db.commit()
    settings["pr_dispatch_skip_rules"] = FACTORY_RULE
    pr = _approve(db, _pr(db, seed, dept.id, "PYC-497-E"))
    assert pr.status == "dispatched"
    assert all(not it.assignee for it in S.items_of(db, pr.id)), \
        "bộ chung (seed gán DEMONV cho «Nhãn») KHÔNG được dùng cho phiếu nhà máy"


def test_bad_json_or_non_list_is_treated_as_empty(db, seed, factory, settings):
    for raw in ('{"field": "handler_dept_id"}', "[{", "abc", "   "):
        settings["pr_dispatch_skip_rules"] = raw
        pr = _pr(db, seed, factory.id, f"PYC-497-{abs(hash(raw)) % 10000}")
        assert S.skip_dispatch_for(db, pr) is False, raw


def test_context_exposes_documented_fields_and_other_rules_work(db, seed, factory, settings):
    pr = _pr(db, seed, factory.id, "PYC-497-F")
    ctx = S.dispatch_context(db, pr)
    assert set(ctx) == {"handler_dept_id", "department_id", "company_id", "requester_id", "is_urgent", "line_count"}
    settings["pr_dispatch_skip_rules"] = '[{"field": "line_count", "op": "lte", "value": 1}, {"field": "is_urgent", "op": "eq", "value": false}]'
    assert S.skip_dispatch_for(db, pr) is True
    settings["pr_dispatch_skip_rules"] = '[{"field": "company_id", "op": "in", "value": [999]}]'
    assert S.skip_dispatch_for(db, pr) is False
