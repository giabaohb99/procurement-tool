"""bao-CR-794 — Sửa giá SAU DUYỆT trên đơn mua hàng (kể cả đơn đã nhận hàng). CHỈ kiểm phần vừa làm:

- người có quyền DUYỆT sửa đơn giá của dòng trên đơn Đã duyệt / Nhận một phần / Đã nhận, phải có lý do;
- sửa xong: thành tiền dòng, công nợ hàng, bản ghi lịch sử mua đang mở và sổ giá đi theo giá mới; nhật ký ghi giá cũ -> giá mới;
- chặn: đơn chưa duyệt / đã hoàn thành / đã hủy; đã có yêu cầu thanh toán gửi duyệt trở đi; công nợ hàng đã trả tiền;
  dòng đã hoàn thành / đã hủy; giá không dương; không dòng nào đổi; một dòng sai thì không dòng nào được ghi;
- yêu cầu thanh toán còn Nháp thì vẫn cho sửa nhưng trả tên phiếu để người dùng kiểm lại số tiền.
"""
import pytest
from fastapi import HTTPException

from app.core.packaging_price_codes import PriceSourceType
from app.modules.audit.model import AuditLog
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.product.model import Product
from app.modules.product_price.model import ProductPriceLedger
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn, POUpdate, PriceAdjustIn
from app.modules.purchase_order.serializer import _out
from app.modules.supplier.model import Supplier
from hdld_factory import client_as  # noqa: F401  (fixture)


@pytest.fixture
def order(db, seed):
    uid = seed.u_nstm_id
    db.add_all([Product(code="CHT0230", name="Chai HDPE 550ml", unit="Cái"), Product(code="NAP0136", name="Nắp 28", unit="Cái"),
                Supplier(code="PHL", name="Công ty Cổ phần PHL")])
    po = PurchaseOrder(code="PO00794", misa_code="MS794", supplier_code="PHL", supplier_name="Công ty Cổ phần PHL",
                       order_date="2026-11-19", status="approved", company_id=seed.company_id, created_by=uid, updated_by=uid,
                       currency="VND", exchange_rate=1)
    db.add(po)
    db.flush()
    for code, name, price in (("CHT0230", "Chai HDPE 550ml", 5105), ("NAP0136", "Nắp 28", 1000)):
        db.add(POItem(po_id=po.id, product_code=code, product_name=name, unit="Cái", item_group="Chai", qty_order=2000,
                      price=price, vat=8, warehouse_code="KHO1", currency="VND", exchange_rate=1, progress_status="ordered",
                      created_by=uid, updated_by=uid))
    db.commit()
    return po, uid


def _line(db, po, code="CHT0230") -> POItem:
    return db.query(POItem).filter(POItem.po_id == po.id, POItem.product_code == code).one()


def _receive(db, po, uid, qty=2048, code="CHT0230"):
    """Đúng cách màn web lưu lần nhận hàng: gửi lại nguyên đơn qua `update_po`, thêm một lần giao cho dòng `code`."""
    items = []
    for it in _out(db, db.get(PurchaseOrder, po.id))["items"]:
        deliveries = [dict(d) for d in it["deliveries"]]
        if it["product_code"] == code:
            deliveries.append({"delivery_no": len(deliveries) + 1, "ship_qty": qty, "received_qty": qty,
                               "received_date": "2026-11-24", "warehouse_code": "KHO1", "ship_unit": "Cái"})
        items.append(POItemIn.model_validate({**it, "deliveries": [DeliveryIn.model_validate(d) for d in deliveries]}))
    po_service.update_po(db, po.id, POUpdate(items=items), uid)


def _adjust(db, po, uid, prices: dict, reason="Nhà cung cấp báo lại giá"):
    body = PriceAdjustIn(reason=reason, items=[{"id": _line(db, po, code).id, "price": price} for code, price in prices.items()])
    return po_service.adjust_prices(db, po.id, body, uid)


def _goods_payables(db, po) -> list[Payable]:
    return db.query(Payable).filter(Payable.po_code == po.code, Payable.source_type == "goods").all()


def _payment_request(db, po, status="submitted", code="YCTT00794") -> PaymentRequest:
    request = PaymentRequest(code=code, status=status)
    db.add(request)
    db.flush()
    db.add(PaymentRequestLine(request_id=request.id, po_code=po.code, amount=1000))
    db.commit()
    return request


# ── Đường chính ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_sua_gia_don_da_nhan_hang_tinh_lai_tien_cong_no_lich_su_va_so_gia(db, order):
    po, uid = order
    _receive(db, po, uid)
    assert float(_goods_payables(db, po)[0].amount) == pytest.approx(2048 * 5105)

    result = _adjust(db, po, uid, {"CHT0230": 5000})

    line = _line(db, po)
    assert float(line.price) == 5000
    assert float(line.amount) == pytest.approx(2048 * 5000 * 1.08, abs=1)
    payable = _goods_payables(db, po)
    assert len(payable) == 1 and float(payable[0].amount) == pytest.approx(2048 * 5000)
    assert float(payable[0].vat) == pytest.approx(2048 * 5000 * 0.08, abs=1)
    history = db.query(PurchaseHistory).filter(PurchaseHistory.po_item_id == line.id).one()
    assert float(history.price) == 5000
    ledger = db.query(ProductPriceLedger).filter(ProductPriceLedger.source_type == int(PriceSourceType.PO_LINE),
                                                 ProductPriceLedger.source_id == line.id).one()
    assert float(ledger.price) == 5000
    assert result["changed"] == [{"id": line.id, "product_code": "CHT0230", "old_price": 5105.0, "new_price": 5000.0}]
    assert result["draft_requests"] == []
    assert db.get(PurchaseOrder, po.id).status in ("approved", "partial", "received")     # không tụt về Nháp


def test_nhat_ky_ghi_gia_cu_gia_moi_va_ly_do(db, order):
    po, uid = order
    _receive(db, po, uid)
    _adjust(db, po, uid, {"CHT0230": 5000}, reason="Nhà cung cấp giảm giá theo phụ lục 02")

    log = db.query(AuditLog).filter(AuditLog.entity == "purchase_order", AuditLog.entity_id == po.id,
                                    AuditLog.action == "adjust_price").one()
    assert "CHT0230" in log.message and "5.105" in log.message and "5.000" in log.message
    assert "Nhà cung cấp giảm giá theo phụ lục 02" in log.message


def test_don_da_duyet_chua_nhan_hang_cung_sua_duoc_va_chua_sinh_cong_no(db, order):
    po, uid = order
    _adjust(db, po, uid, {"CHT0230": 4900, "NAP0136": 950})
    assert (float(_line(db, po).price), float(_line(db, po, "NAP0136").price)) == (4900, 950)
    assert _goods_payables(db, po) == []


def test_gia_khong_doi_cua_dong_khac_bi_bo_qua(db, order):
    po, uid = order
    result = _adjust(db, po, uid, {"CHT0230": 5000, "NAP0136": 1000})
    assert [c["product_code"] for c in result["changed"]] == ["CHT0230"]


# ── Chặn ──────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("status", ["draft", "submitted", "rejected", "completed", "cancelled"])
def test_chi_don_da_duyet_tro_di_va_chua_dong_moi_sua_gia_sau_duyet(db, order, status):
    po, uid = order
    po.status = status
    db.commit()
    with pytest.raises(HTTPException) as error:
        _adjust(db, po, uid, {"CHT0230": 5000})
    assert error.value.status_code == 400
    assert float(_line(db, po).price) == 5105


def test_phai_co_ly_do(db, order):
    po, uid = order
    with pytest.raises(HTTPException) as error:
        _adjust(db, po, uid, {"CHT0230": 5000}, reason="   ")
    assert "lý do" in error.value.detail


@pytest.mark.parametrize("status", ["submitted", "approved", "paid"])
def test_da_co_yeu_cau_thanh_toan_gui_duyet_tro_di_thi_chan(db, order, status):
    po, uid = order
    _receive(db, po, uid)
    _payment_request(db, po, status)
    with pytest.raises(HTTPException) as error:
        _adjust(db, po, uid, {"CHT0230": 5000})
    assert "YCTT00794" in error.value.detail
    assert float(_line(db, po).price) == 5105


def test_yeu_cau_thanh_toan_con_nhap_thi_cho_sua_va_bao_ten_phieu(db, order):
    po, uid = order
    _receive(db, po, uid)
    _payment_request(db, po, "draft")
    result = _adjust(db, po, uid, {"CHT0230": 5000})
    assert result["draft_requests"] == ["YCTT00794"]
    assert float(_line(db, po).price) == 5000


@pytest.mark.parametrize("how", ["cancelled", "deleted"])
def test_yeu_cau_thanh_toan_da_huy_hoac_da_xoa_khong_chan(db, order, how):
    po, uid = order
    request = _payment_request(db, po, "cancelled" if how == "cancelled" else "submitted")
    if how == "deleted":
        request.is_deleted = True
        db.commit()
    result = _adjust(db, po, uid, {"CHT0230": 5000})
    assert result["draft_requests"] == [] and float(_line(db, po).price) == 5000


def test_cong_no_hang_da_tra_tien_thi_chan(db, order):
    po, uid = order
    _receive(db, po, uid)
    payable = _goods_payables(db, po)[0]
    payable.paid_amount = 1000
    db.commit()
    with pytest.raises(HTTPException) as error:
        _adjust(db, po, uid, {"CHT0230": 5000})
    assert "đã trả tiền" in error.value.detail


def test_cong_no_cu_chi_mang_ma_don_da_tra_tien_cung_chan(db, order):
    """Khoản nợ cũ có dòng `po_id = 0`, chỉ mang mã đơn — vẫn phải tính là công nợ của đơn."""
    po, uid = order
    db.add(Payable(source_type="goods", ref_id=987654, po_id=0, po_code=po.code, supplier_code="PHL", amount=1000, total=1000,
                   paid_amount=500))
    db.commit()
    with pytest.raises(HTTPException) as error:
        _adjust(db, po, uid, {"CHT0230": 5000})
    assert "đã trả tiền" in error.value.detail


@pytest.mark.parametrize("progress", ["completed", "cancelled"])
def test_dong_da_hoan_thanh_hoac_da_huy_khong_sua_gia(db, order, progress):
    po, uid = order
    line = _line(db, po)
    line.progress_status = progress
    db.commit()
    with pytest.raises(HTTPException) as error:
        _adjust(db, po, uid, {"CHT0230": 5000})
    assert "CHT0230" in error.value.detail or "Chai HDPE" in error.value.detail


@pytest.mark.parametrize("price", [0, -5])
def test_gia_phai_duong(db, order, price):
    po, uid = order
    with pytest.raises(Exception):      # noqa: B017, PT011 — schema (422) hoặc service (400) đều được, miễn không ghi
        _adjust(db, po, uid, {"CHT0230": price})
    assert float(_line(db, po).price) == 5105


def test_dong_khong_thuoc_don_thi_chan(db, order):
    po, uid = order
    with pytest.raises(HTTPException) as error:
        po_service.adjust_prices(db, po.id, PriceAdjustIn(reason="thử", items=[{"id": 999999, "price": 10}]), uid)
    assert error.value.status_code == 400


def test_khong_dong_nao_doi_gia_thi_bao_loi(db, order):
    po, uid = order
    with pytest.raises(HTTPException) as error:
        _adjust(db, po, uid, {"CHT0230": 5105})
    assert "Không có dòng nào đổi giá" in error.value.detail


def test_mot_dong_sai_thi_khong_dong_nao_duoc_ghi(db, order):
    po, uid = order
    blocked = _line(db, po, "NAP0136")
    blocked.progress_status = "completed"
    db.commit()
    with pytest.raises(HTTPException):
        _adjust(db, po, uid, {"CHT0230": 5000, "NAP0136": 900})
    db.rollback()
    assert (float(_line(db, po).price), float(_line(db, po, "NAP0136").price)) == (5105, 1000)


# ── Quyền: chỉ người có quyền DUYỆT ───────────────────────────────────────────────────────────────────────────────
def test_duong_api_can_quyen_duyet_khong_phai_quyen_sua(db, seed, order, cap_quyen, client_as):  # noqa: F811
    from app.modules.user.model import User

    po, uid = order
    body = {"reason": "Nhà cung cấp báo lại giá", "items": [{"id": _line(db, po).id, "price": 5000}]}
    editor = db.get(User, seed.u_req_id)
    cap_quyen(editor.id, "purchase_order", scope="all", read=True, write=True)
    assert client_as(editor).post(f"/api/purchase-orders/{po.id}/adjust-prices", json=body).status_code == 403

    approver = db.get(User, seed.u_nstm_id)
    cap_quyen(approver.id, "purchase_order", scope="all", read=True, approve=True)
    response = client_as(approver).post(f"/api/purchase-orders/{po.id}/adjust-prices", json=body)
    assert response.status_code == 200, response.text
    assert "Đã sửa giá 1 dòng" in response.json()["message"]
    assert float(_line(db, po).price) == 5000


def test_ma_hanh_dong_co_trong_bo_ma_nhat_ky():
    from app.core.action_catalog import ACTION_LABELS
    assert ACTION_LABELS["adjust_price"] == "Sửa giá sau duyệt"
