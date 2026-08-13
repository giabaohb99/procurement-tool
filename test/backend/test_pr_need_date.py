"""Test đồng bộ và hiển thị Ngày cần hàng (need_date) trên YCMH."""
import pytest
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.schema import PRItemIn


def test_pr_need_date_synced_from_items(db, seed):
    pr = PurchaseRequest(code="PYC-NEED-01", is_urgent=False, status="draft",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.commit()
    db.refresh(pr)

    items = [
        PRItemIn(product_code="VT01", product_name="Sản phẩm 1", qty=10, price=1000,
                 required_date="2026-08-20", line_status="Chưa đặt hàng"),
        PRItemIn(product_code="VT02", product_name="Sản phẩm 2", qty=5, price=2000,
                 required_date="2026-08-15", line_status="Chưa đặt hàng"),
    ]
    pr_service._save_items(db, pr.id, items, seed.u_req_id)
    db.refresh(pr)

    assert pr.need_date == "2026-08-15"


def test_pr_need_date_ignores_cancelled_lines(db, seed):
    pr = PurchaseRequest(code="PYC-NEED-02", is_urgent=False, status="draft",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.commit()
    db.refresh(pr)

    items = [
        PRItemIn(product_code="VT01", product_name="Sản phẩm 1", qty=10, price=1000,
                 required_date="2026-08-10", line_status="Hủy đơn"),
        PRItemIn(product_code="VT02", product_name="Sản phẩm 2", qty=5, price=2000,
                 required_date="2026-08-18", line_status="Chưa đặt hàng"),
    ]
    pr_service._save_items(db, pr.id, items, seed.u_req_id)
    db.refresh(pr)

    # Dòng bị Hủy đơn ngày 10/08 bị bỏ qua -> lấy ngày sớm nhất của dòng còn hiệu lực (18/08)
    assert pr.need_date == "2026-08-18"
