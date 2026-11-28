"""duoc-CR-803 — trả YCMH Đang mua hàng về người yêu cầu CHỈ để sửa Công ty nhận hóa đơn.

Luật anh Được chốt 28/11/2026: chỉ phiếu Đang mua hàng; mọi dòng ĐMH liên quan chưa nhận hàng; ĐMH đã có
YCTT / công nợ cũng chặn. Trả về xong chỉ sửa được công ty, các ĐMH khóa mọi thao tác ghi; trưởng phòng duyệt
lại thì công ty chép xuống ĐMH, mở khóa, phiếu về lại mốc Đang mua hàng.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.core.pr_return_codes import PrReturnMode
from app.modules.company.model import Company
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.purchase_order import serializer as po_ser
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_request import access as pr_access
from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ApproveIn, PRUpdate, ReasonIn

USER = SimpleNamespace(id=1)


@pytest.fixture(autouse=True)
def _world(monkeypatch, cap_quyen):
    monkeypatch.setattr(pr_ctl, "trigger_notification", lambda **kw: None)
    monkeypatch.setattr(pr_service, "notify_users", lambda *a, **kw: None)
    monkeypatch.setattr(pr_access, "_in_approve_scope", lambda db, user, pid: True)
    monkeypatch.setattr(pr_ctl, "_in_approve_scope", lambda db, user, pid: True)
    for entity in ("purchase_request", "purchase_order"):
        cap_quyen(USER.id, entity, scope="all", read=True, write=True, approve=True, cancel=True, delete=True)


def _world_pr(db, seed, *, status="purchasing", progress="ordered", qty_received=0):
    """YCMH hai dòng; ĐMH đã nhập MISA phủ dòng SP01 → phiếu đúng mốc Đang mua hàng (phủ một phần)."""
    pr = PurchaseRequest(code="PYC-803", company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test", purpose="Mua nhãn",
                         status=status, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    for code, line in (("SP01", "ordered"), ("SP02", "no_po")):
        db.add(PurchaseRequestItem(pr_id=pr.id, product_code=code, product_name=code, item_group="Nhãn", qty=1,
                                   unit="cái", price=1, line_status=line, assignee="DEMONV",
                                   created_by=seed.u_req_id, updated_by=seed.u_req_id))
    po = PurchaseOrder(code="PO-803", pr_code=pr.code, company_id=seed.company_id, status="approved",
                       misa_code="MS-1", created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(po)
    db.flush()
    db.add(POItem(po_id=po.id, product_code="SP01", product_name="SP01", qty_order=1, price=1,
                  progress_status=progress, qty_received=qty_received,
                  created_by=seed.u_req_id, updated_by=seed.u_req_id))
    other = Company(name="Cty Khác", code="CT02", is_active=True)
    db.add(other)
    db.commit()
    return pr, po, other


def _return(db, pr):
    return pr_ctl.return_pr(pr.id, ReasonIn(reason="Sai pháp nhân"), BackgroundTasks(), db=db, user=USER)


def test_purchasing_pr_returns_keeping_po_and_lines(db, seed):
    pr, po, _ = _world_pr(db, seed)
    assert pr_ctl._out(db, pr, USER)["can_return"] is True
    _return(db, pr)
    db.refresh(pr)
    assert (pr.status, pr.return_mode) == ("rejected", PrReturnMode.INVOICE_COMPANY)
    lines = {it.product_code: it for it in pr_service.items_of(db, pr.id)}
    assert lines["SP01"].line_status == "ordered" and lines["SP01"].assignee == "DEMONV"
    out = pr_ctl._out(db, pr, USER)
    assert out["invoice_company_only"] is True and out["return_mode"] == 1
    assert po_ser._out(db, po)["locked_by_pr_return"] is True


@pytest.mark.parametrize("progress,qty", [("received", 0), ("doc_sent", 0), ("completed", 0), ("ordered", 1)])
def test_received_po_line_blocks_return(db, seed, progress, qty):
    pr, _, _ = _world_pr(db, seed, progress=progress, qty_received=qty)
    assert pr_ctl._out(db, pr, USER)["can_return"] is False
    with pytest.raises(HTTPException) as error:
        _return(db, pr)
    assert error.value.status_code == 400 and "nhận hàng" in error.value.detail
    db.refresh(pr)
    assert (pr.status, pr.return_mode) == ("purchasing", 0)


def test_payment_request_blocks_return(db, seed):
    pr, po, _ = _world_pr(db, seed)
    req = PaymentRequest(code="YCTT-803", status="submitted")
    db.add(req)
    db.flush()
    db.add(PaymentRequestLine(request_id=req.id, po_code=po.code, amount=1))
    db.commit()
    with pytest.raises(HTTPException) as error:
        _return(db, pr)
    assert "YCTT-803" in error.value.detail


def test_cancelled_payment_request_does_not_block(db, seed):
    pr, po, _ = _world_pr(db, seed)
    req = PaymentRequest(code="YCTT-803", status="cancelled")
    db.add(req)
    db.flush()
    db.add(PaymentRequestLine(request_id=req.id, po_code=po.code, amount=1))
    db.commit()
    assert pr_service.can_return_requester(db, pr) is True


def test_payable_blocks_return(db, seed):
    pr, po, _ = _world_pr(db, seed)
    db.add(Payable(po_code=po.code, company_id=seed.company_id))
    db.commit()
    assert pr_service.find_invoice_company_return_blocker(db, pr) != ""


@pytest.mark.parametrize("status", ["processing", "purchased", "completed"])
def test_only_purchasing_status_can_use_invoice_company_return(db, seed, status):
    pr, _, _ = _world_pr(db, seed, status=status)
    with pytest.raises(HTTPException) as error:
        _return(db, pr)
    assert error.value.status_code == 400
    db.refresh(pr)
    assert pr.return_mode == 0


def test_update_only_changes_invoice_company(db, seed):
    pr, _, other = _world_pr(db, seed)
    _return(db, pr)
    pr_ctl.update_pr(pr.id, PRUpdate(company_id=other.id, purpose="Đổi mục đích", items=[]), db=db, user=USER)
    db.refresh(pr)
    assert pr.company_id == other.id
    assert pr.purpose == "Mua nhãn"
    assert len(pr_service.items_of(db, pr.id)) == 2


def test_update_rejects_inactive_company(db, seed):
    pr, _, other = _world_pr(db, seed)
    other.is_active = False
    db.commit()
    _return(db, pr)
    with pytest.raises(HTTPException) as error:
        pr_ctl.update_pr(pr.id, PRUpdate(company_id=other.id), db=db, user=USER)
    assert error.value.status_code == 400


def test_approval_copies_company_to_po_and_unlocks(db, seed):
    pr, po, other = _world_pr(db, seed)
    _return(db, pr)
    pr_ctl.update_pr(pr.id, PRUpdate(company_id=other.id), db=db, user=USER)
    pr_service.set_status(db, pr.id, "submitted", USER.id)
    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)
    db.refresh(po)
    assert po.company_id == other.id
    assert (pr.status, pr.return_mode) == ("purchasing", 0)
    assert pr_service.items_of(db, pr.id)[0].assignee == "DEMONV"
    assert po_ser._out(db, po)["locked_by_pr_return"] is False


def test_return_again_from_submitted_keeps_mode_and_lines(db, seed):
    pr, _, _ = _world_pr(db, seed)
    _return(db, pr)
    pr_service.set_status(db, pr.id, "submitted", USER.id)
    _return(db, pr)
    db.refresh(pr)
    assert (pr.status, pr.return_mode) == ("rejected", PrReturnMode.INVOICE_COMPANY)
    assert {it.line_status for it in pr_service.items_of(db, pr.id)} == {"ordered", "no_po"}


def test_delete_and_urgent_blocked_while_returned(db, seed):
    pr, _, _ = _world_pr(db, seed)
    _return(db, pr)
    with pytest.raises(HTTPException):
        pr_service.delete_pr(db, pr.id, USER.id)
    with pytest.raises(HTTPException):
        pr_service.set_urgent(db, pr.id, True, USER.id)


@pytest.mark.parametrize("action", ["write", "approve", "cancel", "delete"])
def test_po_write_routes_locked_while_returned(db, seed, action):
    from app.modules.purchase_order import controller as po_ctl
    pr, po, _ = _world_pr(db, seed)
    _return(db, pr)
    with pytest.raises(HTTPException) as error:
        po_ctl._in_scope(db, po.id, USER, action)
    assert error.value.status_code == 400 and "khóa" in error.value.detail
    assert po_ctl._in_scope(db, po.id, USER, "read").id == po.id     # vẫn xem / in được


def test_po_service_update_locked_while_returned(db, seed):
    from app.modules.purchase_order import edit_service as po_edit
    from app.modules.purchase_order.schema import POUpdate
    pr, po, _ = _world_pr(db, seed)
    _return(db, pr)
    with pytest.raises(HTTPException):
        po_edit.update_po(db, po.id, POUpdate(), USER.id)    # đường AI / nhập liệu gọi thẳng service


def test_auto_progress_frozen_while_returned(db, seed):
    from app.modules.purchase_order import progress_service
    pr, po, _ = _world_pr(db, seed)
    _return(db, pr)
    assert progress_service.apply_auto_progress(db, po, USER.id) is False


def test_approve_while_still_rejected_is_refused(db, seed):
    #  Bấm Duyệt trên trang cũ lúc phiếu đã bị trả về lần nữa: phải chặn, không rơi xuống luồng duyệt thường.
    pr, po, _ = _world_pr(db, seed)
    _return(db, pr)
    with pytest.raises(HTTPException) as error:
        pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 400
    db.refresh(pr)
    assert (pr.status, pr.return_mode) == ("rejected", PrReturnMode.INVOICE_COMPANY)


def test_cancel_blocked_while_returned(db, seed):
    pr, po, _ = _world_pr(db, seed)
    _return(db, pr)
    pr_service.set_status(db, pr.id, "submitted", USER.id)
    with pytest.raises(HTTPException) as error:
        pr_ctl.cancel_pr(pr.id, ReasonIn(reason="Bỏ"), BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 400
    db.refresh(pr)
    assert pr.status == "submitted" and pr_service.is_po_locked_by_pr_return(db, po) is True


def test_payment_request_created_during_lock_blocks_approval(db, seed):
    pr, po, other = _world_pr(db, seed)
    _return(db, pr)
    pr_ctl.update_pr(pr.id, PRUpdate(company_id=other.id), db=db, user=USER)
    pr_service.set_status(db, pr.id, "submitted", USER.id)
    req = PaymentRequest(code="YCTT-803B", status="draft")
    db.add(req)
    db.flush()
    db.add(PaymentRequestLine(request_id=req.id, po_code=po.code, amount=1))
    db.commit()
    with pytest.raises(HTTPException) as error:
        pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)
    assert "YCTT-803B" in error.value.detail
    db.refresh(po)
    assert po.company_id == seed.company_id


def test_dispatch_blocked_while_returned(db, seed):
    pr, _, _ = _world_pr(db, seed)
    _return(db, pr)
    with pytest.raises(HTTPException):
        pr_service.dispatch_pr(db, pr.id, USER.id)


def test_misa_code_editable_while_locked_other_fields_ignored(db, seed):
    #  Đổi công ty thường phải lập lại đơn trên MISA dưới pháp nhân mới → màn Sửa ĐMH vẫn nhập lại được mã.
    from app.modules.purchase_order import controller as po_ctl
    from app.modules.purchase_order.schema import POUpdate
    pr, po, _ = _world_pr(db, seed)
    _return(db, pr)
    po_ctl.update_po(po.id, POUpdate(misa_code="MS-2", payment_terms="Đổi điều khoản"), db=db, user=USER)
    db.refresh(po)
    assert po.misa_code == "MS-2" and (po.payment_terms or "") != "Đổi điều khoản"


def test_misa_code_cannot_be_blanked_while_locked_when_lines_advanced(db, seed):
    from app.modules.purchase_order import controller as po_ctl
    from app.modules.purchase_order.schema import POUpdate
    pr, po, _ = _world_pr(db, seed)
    _return(db, pr)
    with pytest.raises(HTTPException):
        po_ctl.update_po(po.id, POUpdate(misa_code=""), db=db, user=USER)
