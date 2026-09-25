"""bao-CR-485 — Công tắc điều phối TẮT: sổ thao tác chỉ MỘT dòng «Duyệt» của trưởng phòng.

Đại ca soi dev 25/09/2026: anh Khôi (trưởng phòng nhà máy) duyệt YCMH xong, sổ hiện HAI dòng
dưới tên anh — «Duyệt» rồi «Điều phối — tự động phân bổ 1 dòng». Anh Khôi không bấm và không
có quyền Điều phối; dòng đó do đường duyệt gọi `dispatch_pr` khi công tắc `pr_dispatch_enabled`
tắt. Nay:
  · công tắc TẮT → một dòng `approved` duy nhất, ghi chú nói rõ hệ thống tự phân bổ;
  · công tắc BẬT → đường cũ y nguyên: `approved` lúc duyệt, `dispatched` lúc thu mua bấm nút;
  · bản in YCMH vẫn ra ô «TP/BP mua hàng» khi công tắc tắt: `_approval_signers` lùi người
    điều phối = người duyệt vì không còn dòng `dispatched` để tra.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks

from app.core.audit import record
from app.modules.audit.model import AuditLog
from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ApproveIn

USER = SimpleNamespace(id=1)


@pytest.fixture(autouse=True)
def _im_lang(monkeypatch, cap_quyen):
    monkeypatch.setattr(pr_ctl, "trigger_notification", lambda **kw: None)
    monkeypatch.setattr(pr_ctl, "_notify_assigned", lambda *a, **kw: None)
    monkeypatch.setattr(pr_ctl, "_in_approve_scope", lambda db, user, pid: True)
    cap_quyen(USER.id, "purchase_request", scope="all", read=True, approve=True, write=True)


def _ycmh(db, seed, code="PYC-CR485"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         head_of_dept_id=seed.emp_req_id, status="submitted",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP01", product_name="Hàng Nhãn",
                               item_group="Nhãn", qty=10, unit="cái", price=1000,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


def _rows(db, pr):
    return [(r.action, r.created_by, r.message) for r in
            db.query(AuditLog).filter(AuditLog.entity == "purchase_request",
                                      AuditLog.entity_id == pr.id).order_by(AuditLog.id).all()]


def test_switch_off_writes_exactly_one_approved_row_with_system_note(db, seed, monkeypatch):
    monkeypatch.setattr(pr_ctl.service, "dispatch_enabled", lambda: False)
    pr = _ycmh(db, seed)

    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)

    rows = _rows(db, pr)
    assert [a for a, _, _ in rows] == ["approved"], rows
    action, uid, message = rows[0]
    assert uid == USER.id
    assert message.startswith("Hệ thống tự phân bổ (công tắc điều phối tắt) 1 dòng")
    db.refresh(pr)
    assert pr.status == "dispatched", "luồng vẫn chạy trọn: phiếu sang Đã điều phối, có người phụ trách"
    assert [it.assignee for it in pr_ctl.service.items_of(db, pr.id)] == [seed.emp_nstm_code]


def test_switch_on_keeps_two_separate_rows(db, seed, monkeypatch):
    monkeypatch.setattr(pr_ctl.service, "dispatch_enabled", lambda: True)
    pr = _ycmh(db, seed, "PYC-CR485-ON")

    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)
    pr_ctl.service.dispatch_pr(db, pr.id, seed.u_nstm_id)

    rows = _rows(db, pr)
    assert [(a, u) for a, u, _ in rows] == [("approved", USER.id), ("dispatched", seed.u_nstm_id)]
    assert rows[1][2].startswith("Điều phối — tự động phân bổ 1 dòng")


def test_print_signers_fall_back_to_approver_when_switch_off(db, seed, monkeypatch):
    """Không còn dòng `dispatched` thì ô «TP/BP mua hàng» không được trống."""
    monkeypatch.setattr(pr_ctl.service, "dispatch_enabled", lambda: False)
    pr = _ycmh(db, seed, "PYC-CR485-IN")
    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)

    out = pr_ctl._approval_signers(db, pr)
    assert out["approver_name"] and out["dispatcher_name"] == out["approver_name"]
    assert out["purchasing_head_name"]


def test_print_signers_keep_real_dispatcher_when_row_exists(db, seed, monkeypatch):
    """Phiếu cũ (trước CR-485) vẫn có dòng `dispatched` → không lùi."""
    monkeypatch.setattr(pr_ctl.service, "dispatch_enabled", lambda: False)
    pr = _ycmh(db, seed, "PYC-CR485-OLD")
    pr.status = "dispatched"
    db.commit()
    record(db, USER.id, "purchase_request", pr.id, "approved")
    record(db, seed.u_nstm_id, "purchase_request", pr.id, "dispatched")

    out = pr_ctl._approval_signers(db, pr)
    assert out["dispatcher_name"] != out["approver_name"]
