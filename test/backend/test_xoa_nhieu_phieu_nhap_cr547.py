"""bao-CR-547 — chọn nhiều rồi xóa: CHỈ phiếu Nháp, và kiểm CẢ LÔ trước khi xóa phiếu nào.

Đại ca chốt 01/10/2026:
  · YCBG, YCMH, ĐMH, YCTT cho chọn nhiều rồi xóa, nhưng chỉ khi tất cả đang Nháp;
  · YCTT siết cả xóa TỪNG phiếu về Nháp — trước đây phiếu chờ duyệt / đã duyệt mà chưa chi
    vẫn xóa được, mở xóa nhiều là xóa cả loạt phiếu đã duyệt.

Lỗi cũ được canh ở đây: đường xóa nhiều lặp từng phiếu, gặp phiếu không xóa được thì dừng
nhưng các phiếu ĐÃ xóa trước đó vẫn mất — lô bị xóa dở mà người bấm không biết.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.bulk_delete import ensure_all_draft


def _doc(pid, status, code=""):
    return SimpleNamespace(id=pid, status=status, code=code)


# ── Hàm kiểm dùng chung ─────────────────────────────────────────────────────

def test_all_draft_passes():
    ensure_all_draft([_doc(1, "draft", "PYC01"), _doc(2, "draft", "PYC02")], "phiếu")


def test_any_non_draft_blocks_and_names_the_codes():
    with pytest.raises(HTTPException) as err:
        ensure_all_draft([_doc(1, "draft", "PYC01"), _doc(2, "submitted", "PYC02"),
                          _doc(3, "rejected", "PYC03")], "phiếu yêu cầu mua hàng")
    assert err.value.status_code == 400
    msg = err.value.detail
    assert "chưa xóa phiếu nào" in msg and "PYC02, PYC03" in msg and "PYC01" not in msg


def test_empty_status_and_missing_code_are_handled():
    """Trạng thái rỗng KHÔNG phải Nháp; phiếu chưa có mã thì nêu bằng id."""
    with pytest.raises(HTTPException) as err:
        ensure_all_draft([_doc(9, "", "")], "đơn mua hàng")
    assert "#9" in err.value.detail


def test_long_lists_are_cut_after_ten_codes():
    rows = [_doc(i, "approved", f"PO{i:03d}") for i in range(15)]
    with pytest.raises(HTTPException) as err:
        ensure_all_draft(rows, "đơn mua hàng")
    assert "PO009" in err.value.detail and "PO010" not in err.value.detail
    assert "và 5 phiếu khác" in err.value.detail


# ── Qua đường API thật ──────────────────────────────────────────────────────

def _add(db, model, **kw):
    row = model(**kw)
    db.add(row)
    db.flush()
    db.commit()
    return row


def test_payment_request_single_delete_only_draft(world):
    from app.modules.payment_request.controller import delete_
    from app.modules.payment_request.model import PaymentRequest

    a1 = world.grant("a1", "payment_request", scope="company", actions=("read", "delete"))
    for status in ("submitted", "approved", "rejected"):
        req = _add(world.db, PaymentRequest, code=f"YCTT_{status}", company_id=world.co["A"],
                   status=status, total=100)
        with pytest.raises(HTTPException) as err:
            delete_(rid=req.id, db=world.db, user=a1.user)
        assert err.value.status_code == 400, f"phiếu {status} không được xóa"
        world.db.expire_all()
        assert world.db.get(PaymentRequest, req.id) is not None

    nhap = _add(world.db, PaymentRequest, code="YCTT_NHAP", company_id=world.co["A"],
                status="draft", total=100)
    delete_(rid=nhap.id, db=world.db, user=a1.user)
    world.db.expire_all()
    assert world.db.get(PaymentRequest, nhap.id) is None


def test_payment_request_bulk_is_all_or_nothing(world):
    from app.modules.payment_request.controller import bulk_delete_requests
    from app.modules.payment_request.model import PaymentRequest

    a1 = world.grant("a1", "payment_request", scope="company", actions=("read", "delete"))
    nhap = _add(world.db, PaymentRequest, code="YCTT_N1", company_id=world.co["A"], status="draft", total=1)
    duyet = _add(world.db, PaymentRequest, code="YCTT_D1", company_id=world.co["A"], status="approved", total=1)

    with pytest.raises(HTTPException) as err:
        bulk_delete_requests(ids=f"{nhap.id},{duyet.id}", db=world.db, user=a1.user)
    assert err.value.status_code == 400 and "YCTT_D1" in err.value.detail
    world.db.expire_all()
    assert world.db.get(PaymentRequest, nhap.id) is not None, "phiếu Nháp đứng trước cũng KHÔNG được xóa"
    assert world.db.get(PaymentRequest, duyet.id) is not None


def test_purchase_order_bulk_only_draft_but_single_delete_keeps_old_rule(world):
    """Xóa nhiều chỉ Nháp; xóa TỪNG đơn vẫn cho Bị từ chối như cũ (đại ca chỉ siết đường nhiều)."""
    from app.modules.purchase_order.controller import bulk_delete_pos, delete_po
    from app.modules.purchase_order.model import PurchaseOrder

    a1 = world.grant("a1", "purchase_order", scope="company", actions=("read", "delete"))
    nhap = _add(world.db, PurchaseOrder, code="PO_N1", company_id=world.co["A"], status="draft")
    tu_choi = _add(world.db, PurchaseOrder, code="PO_R1", company_id=world.co["A"], status="rejected")

    with pytest.raises(HTTPException) as err:
        bulk_delete_pos(ids=f"{nhap.id},{tu_choi.id}", db=world.db, user=a1.user)
    assert err.value.status_code == 400 and "PO_R1" in err.value.detail
    world.db.expire_all()
    assert {p.id for p in world.db.query(PurchaseOrder).filter(
        PurchaseOrder.id.in_([nhap.id, tu_choi.id]))} == {nhap.id, tu_choi.id}

    bulk_delete_pos(ids=str(nhap.id), db=world.db, user=a1.user)
    delete_po(pid=tu_choi.id, db=world.db, user=a1.user)
    world.db.expire_all()
    assert world.db.query(PurchaseOrder).filter(PurchaseOrder.id.in_([nhap.id, tu_choi.id])).count() == 0


def test_purchase_request_bulk_rejects_cancelled_and_deletes_drafts(world):
    from app.modules.purchase_request.controller import bulk_delete_prs
    from app.modules.purchase_request.model import PurchaseRequest

    a1 = world.grant("a1", "purchase_request", scope="company", actions=("read", "delete"))
    n1 = _add(world.db, PurchaseRequest, code="PYC_N1", company_id=world.co["A"], requester_id=0, status="draft")
    n2 = _add(world.db, PurchaseRequest, code="PYC_N2", company_id=world.co["A"], requester_id=0, status="draft")
    huy = _add(world.db, PurchaseRequest, code="PYC_H1", company_id=world.co["A"], requester_id=0,
               status="cancelled")

    with pytest.raises(HTTPException) as err:
        bulk_delete_prs(ids=f"{n1.id},{n2.id},{huy.id}", db=world.db, user=a1.user)
    assert "PYC_H1" in err.value.detail
    world.db.expire_all()
    assert not any(world.db.get(PurchaseRequest, i).is_deleted for i in (n1.id, n2.id, huy.id))

    bulk_delete_prs(ids=f"{n1.id},{n2.id}", db=world.db, user=a1.user)
    world.db.expire_all()
    assert world.db.get(PurchaseRequest, n1.id).is_deleted and world.db.get(PurchaseRequest, n2.id).is_deleted
