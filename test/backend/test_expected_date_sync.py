"""Test "Dự kiến có hàng" đồng bộ hai chiều giữa dòng YCMH và dòng ĐMH.

Luật:
- Chép XUỐNG (YCMH -> ĐMH): chỉ điền khi ô trên dòng ĐMH còn TRỐNG.
- Cuộn NGƯỢC (ĐMH -> YCMH): lấy ngày MUỘN NHẤT của các dòng ĐMH liên kết (bỏ ô trống).
  Ô trên YCMH trống  -> ghi thẳng.
  Ô trên YCMH đã có và LỆCH -> KHÔNG ghi đè và KHÔNG báo gì (người sửa ĐMH đã thấy popup
  cảnh báo ngay trên màn hình đơn; đổi ngày trên YCMH là quyền của NSTM và phải kèm lý do).
- Dòng ĐMH không gắn YCMH, hoặc mã hàng không có trên YCMH: nhập tay tự do, không cuộn.
- NSTM đổi ngày TRÊN YCMH -> báo cho NGƯỜI YÊU CẦU biết hàng của họ đổi ngày.
"""
import pytest
from fastapi import HTTPException

from app.modules.notification.model import Notification
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.schema import POItemIn
from app.modules.purchase_order.service import _save_items, pr_expected_map
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ItemStatusIn
from app.modules.purchase_request.service import sync_from_purchase_orders, update_item_status


def _pr(db, expected="", assignee="DEMONV", code="PYC1", product="SP1",
        created_by=1, requester_id=0):
    pr = PurchaseRequest(code=code, status="approved", created_by=created_by,
                         requester_id=requester_id)
    db.add(pr)
    db.flush()
    it = PurchaseRequestItem(pr_id=pr.id, product_code=product, product_name="Hàng A",
                             qty=10, expected_date=expected, assignee=assignee)
    db.add(it)
    db.commit()
    return pr, it


def _po_line(db, pr_code, product, expected, po_code="PO1", status="approved",
             progress="Đã đặt hàng"):
    po = PurchaseOrder(code=po_code, pr_code=pr_code, status=status)
    db.add(po)
    db.flush()
    it = POItem(po_id=po.id, product_code=product, product_name="Hàng A", qty_order=5,
                expected_date=expected, progress_status=progress)
    db.add(it)
    db.commit()
    return po, it


# ── Cuộn ngược: lấy ngày MUỘN NHẤT ────────────────────────────────────────────
def test_cuon_nguoc_lay_ngay_muon_nhat(db, seed):
    pr, pr_it = _pr(db, expected="")
    _po_line(db, "PYC1", "SP1", "2026-07-20", po_code="PO1")
    _po_line(db, "PYC1", "SP1", "2026-07-25", po_code="PO2")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(pr_it)
    assert pr_it.expected_date == "2026-07-25"   # muộn nhất, không phải sớm nhất


def test_o_trong_khong_tinh_vao_max(db, seed):
    pr, pr_it = _pr(db, expected="")
    _po_line(db, "PYC1", "SP1", "2026-07-20", po_code="PO1")
    _po_line(db, "PYC1", "SP1", "", po_code="PO2")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(pr_it)
    assert pr_it.expected_date == "2026-07-20"


def test_moi_dong_dmh_deu_trong_thi_giu_nguyen(db, seed):
    pr, pr_it = _pr(db, expected="")
    _po_line(db, "PYC1", "SP1", "", po_code="PO1")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(pr_it)
    assert pr_it.expected_date == ""


def test_dong_huy_don_khong_tinh(db, seed):
    pr, pr_it = _pr(db, expected="")
    _po_line(db, "PYC1", "SP1", "2026-07-20", po_code="PO1")
    _po_line(db, "PYC1", "SP1", "2026-09-30", po_code="PO2", progress="Hủy đơn")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(pr_it)
    assert pr_it.expected_date == "2026-07-20"   # dòng hủy không kéo ngày ra xa


# ── Đã có giá trị: KHÔNG ghi đè, và KHÔNG báo chuông ──────────────────────────
def test_da_co_gia_tri_thi_khong_ghi_de(db, seed):
    pr, pr_it = _pr(db, expected="2026-07-20")
    _po_line(db, "PYC1", "SP1", "2026-07-25", po_code="PO1")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(pr_it)
    assert pr_it.expected_date == "2026-07-20"   # giữ nguyên


def test_lech_ngay_thi_khong_bao_chuong(db, seed):
    """Lệch ngày chỉ hiện popup ở màn hình ĐMH — backend không được sinh thông báo nào."""
    pr, pr_it = _pr(db, expected="2026-07-20", assignee="DEMONV")
    _po_line(db, "PYC1", "SP1", "2026-07-25", po_code="PO1")
    sync_from_purchase_orders(db, "PYC1")
    sync_from_purchase_orders(db, "PYC1")   # sync chạy lại ở mọi thao tác ĐMH
    assert db.query(Notification).filter(Notification.title.like("%dự kiến có hàng%")).count() == 0


def test_dmh_thay_duoc_ngay_ycmh_de_bat_popup(db, seed):
    """FE so ô trên đơn với ngày YCMH nguồn để bật popup — map phải trả đúng mã hàng."""
    _pr(db, expected="2026-07-20", product="SP1")
    assert pr_expected_map(db, "PYC1") == {"SP1": "2026-07-20"}
    assert pr_expected_map(db, "") == {}
    assert pr_expected_map(db, "PYC-KHONG-CO") == {}


# ── Đổi ngày TRÊN YCMH: báo cho người yêu cầu ─────────────────────────────────
def _doi_ngay(db, pr, item, new, reason="", user_id=None, emp_code="DEMONV"):
    return update_item_status(
        db, pr.id, ItemStatusIn(items=[{"id": item.id, "expected_date": new,
                                        "expected_date_reason": reason}]),
        user_id=user_id if user_id is not None else 999, emp_code=emp_code, is_manager=True)


def test_doi_ngay_tren_ycmh_bao_cho_nguoi_yeu_cau(db, seed):
    pr, pr_it = _pr(db, expected="2026-07-20", requester_id=seed.emp_req_id)
    _doi_ngay(db, pr, pr_it, "2026-08-15", reason="NCC báo trễ")
    notis = db.query(Notification).filter(Notification.title.like("%Điều chỉnh ngày%")).all()
    assert len(notis) == 1
    assert notis[0].user_id == seed.u_req_id                 # NGƯỜI YÊU CẦU, không phải NSTM
    assert "2026-07-20" in notis[0].body and "2026-08-15" in notis[0].body
    assert "NCC báo trễ" in notis[0].body
    assert notis[0].link == f"/purchase-requests/{pr.id}"


def test_dien_ngay_lan_dau_cung_bao(db, seed):
    """Ô đang trống thì điền tự do (không cần lý do) — người yêu cầu vẫn cần biết."""
    pr, pr_it = _pr(db, expected="", requester_id=seed.emp_req_id)
    _doi_ngay(db, pr, pr_it, "2026-08-15")
    assert db.query(Notification).filter(Notification.title.like("%Điều chỉnh ngày%")).count() == 1


def test_khong_doi_ngay_thi_khong_bao(db, seed):
    pr, pr_it = _pr(db, expected="2026-07-20", requester_id=seed.emp_req_id)
    _doi_ngay(db, pr, pr_it, "2026-07-20", reason="không đổi gì")
    assert db.query(Notification).filter(Notification.title.like("%Điều chỉnh ngày%")).count() == 0


def test_doi_ngay_da_co_ma_thieu_ly_do_thi_chan(db, seed):
    """Luật cũ phải còn nguyên: đổi giá trị đã có mà không kèm lý do -> 400, không báo gì."""
    pr, pr_it = _pr(db, expected="2026-07-20", requester_id=seed.emp_req_id)
    with pytest.raises(HTTPException) as e:
        _doi_ngay(db, pr, pr_it, "2026-08-15")
    assert e.value.status_code == 400
    db.rollback()
    assert db.query(Notification).filter(Notification.title.like("%Điều chỉnh ngày%")).count() == 0


def test_khong_tu_bao_cho_chinh_minh(db, seed):
    """Người yêu cầu tự sửa ngày trên phiếu của mình thì không cần thông báo lại."""
    pr, pr_it = _pr(db, expected="2026-07-20", requester_id=seed.emp_req_id)
    _doi_ngay(db, pr, pr_it, "2026-08-15", reason="tự dời", user_id=seed.u_req_id)
    assert db.query(Notification).filter(Notification.title.like("%Điều chỉnh ngày%")).count() == 0


def test_khong_co_nguoi_yeu_cau_thi_bao_nguoi_tao(db, seed):
    pr, pr_it = _pr(db, expected="2026-07-20", requester_id=0, created_by=seed.u_req_id)
    _doi_ngay(db, pr, pr_it, "2026-08-15", reason="NCC báo trễ")
    notis = db.query(Notification).filter(Notification.title.like("%Điều chỉnh ngày%")).all()
    assert len(notis) == 1 and notis[0].user_id == seed.u_req_id


# ── Chép xuống khi lưu ĐMH ────────────────────────────────────────────────────
def test_chep_xuong_khi_o_dmh_trong(db, seed):
    _pr(db, expected="2026-07-20")
    po = PurchaseOrder(code="PO1", pr_code="PYC1", status="draft")
    db.add(po)
    db.commit()
    _save_items(db, po, [POItemIn(product_code="SP1", product_name="Hàng A", qty_order=5)], user_id=1)
    db.commit()
    line = db.query(POItem).filter(POItem.po_id == po.id).one()
    assert line.expected_date == "2026-07-20"


def test_khong_ghi_de_ngay_da_nhap_tay_tren_dmh(db, seed):
    _pr(db, expected="2026-07-20")
    po = PurchaseOrder(code="PO1", pr_code="PYC1", status="draft")
    db.add(po)
    db.commit()
    _save_items(db, po, [POItemIn(product_code="SP1", product_name="Hàng A", qty_order=5,
                                  expected_date="2026-08-01")], user_id=1)
    db.commit()
    line = db.query(POItem).filter(POItem.po_id == po.id).one()
    assert line.expected_date == "2026-08-01"


def test_don_khong_gan_ycmh_van_nhap_binh_thuong(db, seed):
    po = PurchaseOrder(code="PO1", pr_code="", status="draft")
    db.add(po)
    db.commit()
    _save_items(db, po, [POItemIn(product_code="SPX", product_name="Hàng lẻ", qty_order=5,
                                  expected_date="2026-08-01")], user_id=1)
    db.commit()
    line = db.query(POItem).filter(POItem.po_id == po.id).one()
    assert line.expected_date == "2026-08-01"


def test_ma_hang_khong_co_tren_ycmh_thi_de_trong(db, seed):
    _pr(db, expected="2026-07-20", product="SP1")
    po = PurchaseOrder(code="PO1", pr_code="PYC1", status="draft")
    db.add(po)
    db.commit()
    _save_items(db, po, [POItemIn(product_code="SP-MUA-THEM", product_name="Hàng thêm", qty_order=5)],
                user_id=1)
    db.commit()
    line = db.query(POItem).filter(POItem.po_id == po.id).one()
    assert line.expected_date == ""


def test_ycmh_khac_khong_bi_anh_huong(db, seed):
    _pr(db, expected="", code="PYC1", product="SP1")
    pr2, pr2_it = _pr(db, expected="", code="PYC2", product="SP1")
    _po_line(db, "PYC1", "SP1", "2026-07-25", po_code="PO1")
    sync_from_purchase_orders(db, "PYC1")
    db.refresh(pr2_it)
    assert pr2_it.expected_date == ""
