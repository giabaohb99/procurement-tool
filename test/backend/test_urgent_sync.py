"""Test đồng bộ cờ Đơn gấp theo nhóm YCMH ↔ ĐMH (sync_urgent_group)."""
import pytest
from fastapi import HTTPException

from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.purchase_order.service import sync_urgent_group
from app.modules.purchase_request import service as pr_service


def _setup(db):
    pr = PurchaseRequest(code="PYC1", is_urgent=False, status="draft")
    po1 = PurchaseOrder(code="PO1", pr_code="PYC1", is_urgent=False, status="approved")
    po2 = PurchaseOrder(code="PO2", pr_code="PYC1", is_urgent=False, status="completed")
    other = PurchaseOrder(code="PO9", pr_code="PYC-KHAC", is_urgent=False, status="approved")
    db.add_all([pr, po1, po2, other])
    db.commit()
    for x in (pr, po1, po2, other):
        db.refresh(x)
    return pr, po1, po2, other


def test_sync_bat_ca_nhom(db):
    pr, po1, po2, other = _setup(db)
    sync_urgent_group(db, "PYC1", True)
    for x in (pr, po1, po2, other):
        db.refresh(x)
    assert pr.is_urgent is True
    assert po1.is_urgent is True and po2.is_urgent is True   # cả ĐMH đã duyệt/hoàn thành
    assert other.is_urgent is False                           # khác pr_code → không đụng


def test_sync_tat_ca_nhom(db):
    pr, po1, po2, _ = _setup(db)
    sync_urgent_group(db, "PYC1", True)
    sync_urgent_group(db, "PYC1", False)
    for x in (pr, po1, po2):
        db.refresh(x)
    assert pr.is_urgent is False and po1.is_urgent is False and po2.is_urgent is False


def test_exclude_po_giu_nguyen(db):
    pr, po1, po2, _ = _setup(db)
    sync_urgent_group(db, "PYC1", True)                       # tất cả True
    sync_urgent_group(db, "PYC1", False, exclude_po_id=po1.id)  # ĐMH nguồn giữ True
    for x in (pr, po1, po2):
        db.refresh(x)
    assert po1.is_urgent is True                              # bị loại → giữ nguyên
    assert po2.is_urgent is False and pr.is_urgent is False   # YCMH + anh em đổi theo


def test_pr_code_rong_khong_loi(db):
    sync_urgent_group(db, "", True)   # no-op, không raise


def test_set_urgent_phieu_da_duyet_sync_po(db):
    pr, po1, po2, other = _setup(db)
    pr.status = "approved"; db.commit()
    pr_service.set_urgent(db, pr.id, True, user_id=1)   # đổi cờ dù phiếu đã duyệt
    for x in (pr, po1, po2, other):
        db.refresh(x)
    assert pr.is_urgent is True
    assert po1.is_urgent is True and po2.is_urgent is True
    assert other.is_urgent is False


def test_set_urgent_phieu_da_huy_bao_loi(db):
    pr, *_ = _setup(db)
    pr.status = "cancelled"; db.commit()
    with pytest.raises(HTTPException):
        pr_service.set_urgent(db, pr.id, True, user_id=1)
