"""CR-074: dòng YCMH có nhãn riêng "Chưa tạo đơn mua hàng".

Trước CR-074 ba tình huống khác hẳn nhau lại chung một nhãn "Chưa đặt hàng":
chưa ai lập ĐMH, đã lập ĐMH còn Nháp/Chờ duyệt, và đơn đã duyệt nhưng chưa bấm đặt hàng.
Người yêu cầu nhìn vào phiếu không biết nhân sự thu mua đã bắt tay làm chưa.

Luật chốt: hễ có MỘT dòng ĐMH mang mã sản phẩm đó (kể cả đơn còn Nháp) thì dòng YCMH
chuyển sang "Chưa đặt hàng"; đơn đã Hủy không tính. Các mốc sau ("Đã đặt hàng" trở đi)
giữ nguyên luật cũ.
"""
import pytest

from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_order.schema import POCreate, POItemIn
from app.modules.purchase_order.service import create_po, delete_po
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.service import (LINE_STATUS_NOT_ORDERED, LINE_STATUS_NO_PO,
                                                  sync_from_purchase_orders)


def _pr(db, code="PYC1", products=("SP1",), status="dispatched"):
    pr = PurchaseRequest(code=code, status=status, created_by=1)
    db.add(pr)
    db.flush()
    rows = [PurchaseRequestItem(pr_id=pr.id, product_code=p, product_name="Hàng " + p,
                                qty=10, assignee="DEMONV") for p in products]
    db.add_all(rows)
    db.commit()
    return pr, rows


def _po(db, pr_code="PYC1", product="SP1", status="approved", progress="Đã đặt hàng",
        qty=10, po_code="PO1"):
    po = PurchaseOrder(code=po_code, pr_code=pr_code, status=status, supplier_code="NX",
                       supplier_name="NCC Nam Xuân")
    db.add(po)
    db.flush()
    it = POItem(po_id=po.id, product_code=product, product_name="Hàng " + product,
                unit="Cái", qty_order=qty, progress_status=progress)
    db.add(it)
    db.commit()
    return po, it


# --- Nhãn mặc định ---------------------------------------------------------------

def test_dong_ycmh_moi_mang_nhan_chua_tao_don(db):
    _, rows = _pr(db)
    assert rows[0].line_status == LINE_STATUS_NO_PO


def test_khong_co_dmh_nao_thi_van_la_chua_tao_don(db):
    _, rows = _pr(db)
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(rows[0])
    assert rows[0].line_status == LINE_STATUS_NO_PO


# --- Có ĐMH thì đổi nhãn ----------------------------------------------------------

@pytest.mark.parametrize("po_status", ["draft", "submitted", "rejected", "approved"])
def test_co_dong_dmh_chua_bam_dat_thi_thanh_chua_dat_hang(db, po_status):
    """Kể cả đơn còn Nháp — người dùng chốt "cứ tạo đơn là đổi nhãn"."""
    _, rows = _pr(db)
    _po(db, status=po_status, progress="Chưa đặt hàng")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(rows[0])
    assert rows[0].line_status == LINE_STATUS_NOT_ORDERED


def test_don_da_huy_thi_coi_nhu_chua_ai_lap(db):
    """Đơn Hủy là đơn chết — dòng YCMH phải quay về "Chưa tạo đơn mua hàng" để có người lập lại."""
    _, rows = _pr(db)
    _po(db, status="cancelled", progress="Chưa đặt hàng")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(rows[0])
    assert rows[0].line_status == LINE_STATUS_NO_PO


def test_san_pham_khac_trong_cung_phieu_khong_bi_lay_nhan(db):
    _, rows = _pr(db, products=("SP1", "SP2"))
    _po(db, product="SP1", status="draft", progress="Chưa đặt hàng")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(rows[0]); db.refresh(rows[1])
    assert rows[0].line_status == LINE_STATUS_NOT_ORDERED
    assert rows[1].line_status == LINE_STATUS_NO_PO


# --- Luật cũ từ "Đã đặt hàng" trở đi không đổi -------------------------------------

def test_da_bam_dat_hang_van_ra_da_dat_hang(db):
    _, rows = _pr(db)
    _po(db, progress="Đã đặt hàng")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(rows[0])
    assert rows[0].line_status == "Đã đặt hàng"


def test_da_nhan_hang_van_ra_da_nhan_hang(db):
    _, rows = _pr(db)
    po, po_it = _po(db, progress="Đã nhận hàng")
    db.add(PODelivery(po_id=po.id, po_item_id=po_it.id, delivery_no=1, received_qty=4))
    db.commit()
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(rows[0])
    assert rows[0].line_status == "Đã nhận hàng"


def test_moi_dong_dmh_hoan_thanh_van_ra_hoan_thanh(db):
    _, rows = _pr(db)
    _po(db, progress="Hoàn thành")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(rows[0])
    assert rows[0].line_status == "Hoàn thành"


def test_dong_dmh_bi_huy_van_ra_huy_don(db):
    _, rows = _pr(db)
    _po(db, progress="Hủy đơn")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(rows[0])
    assert rows[0].line_status == "Hủy đơn"


# --- Trạng thái PHIẾU giữ nguyên luật cũ -------------------------------------------

def test_moi_lap_don_nhap_thi_phieu_van_o_da_dieu_phoi(db):
    """Nhãn dòng đổi nhưng phiếu KHÔNG được nhảy sang "Đang xử lý" — chưa đặt hàng thật."""
    pr, _ = _pr(db)
    _po(db, status="draft", progress="Chưa đặt hàng")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(pr)
    assert pr.status == "dispatched"


def test_bam_dat_hang_roi_thi_phieu_sang_dang_xu_ly(db):
    pr, _ = _pr(db)
    _po(db, progress="Đã đặt hàng")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(pr)
    assert pr.status == "processing"


# --- Đi qua đường tạo/xóa đơn thật -------------------------------------------------

def test_tao_don_nhap_la_dong_ycmh_doi_nhan_ngay(db):
    """Không chờ tới lúc duyệt đơn — vừa bấm Lưu là dòng YCMH phải đổi."""
    _, rows = _pr(db)
    po = create_po(db, POCreate(pr_code="PYC1", supplier_code="NX", supplier_name="NCC Nam Xuân",
                                items=[POItemIn(product_code="SP1", product_name="Hàng SP1",
                                                unit="Cái", qty_order=10)]), user_id=1)
    assert po.status == "draft"
    db.refresh(rows[0])
    assert rows[0].line_status == LINE_STATUS_NOT_ORDERED


def test_xoa_don_nhap_thi_dong_ycmh_quay_lai_chua_tao_don(db):
    _, rows = _pr(db)
    po = create_po(db, POCreate(pr_code="PYC1", supplier_code="NX", supplier_name="NCC Nam Xuân",
                                items=[POItemIn(product_code="SP1", product_name="Hàng SP1",
                                                unit="Cái", qty_order=10)]), user_id=1)
    delete_po(db, po.id, user_id=1)
    db.refresh(rows[0])
    assert rows[0].line_status == LINE_STATUS_NO_PO
