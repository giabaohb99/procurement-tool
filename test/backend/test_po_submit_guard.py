"""CR-073: chốt trạng thái + dữ liệu bắt buộc của Đơn mua hàng nằm ở BACKEND.

`service.set_status` chỉ GÁN trạng thái, không kiểm gì. Trước CR-073 các endpoint
submit / approve / reject / return / cancel gọi thẳng vào đó, nên gọi API trực tiếp là
gửi duyệt được đơn chưa có nhà cung cấp, chưa có dòng hàng, hoặc kéo đơn đã Hoàn thành
ngược về Chờ duyệt. Giao diện có ẩn nút, nhưng ẩn nút không phải là chốt chặn.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.modules.purchase_order import controller, service
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.schema import RejectIn

USER = SimpleNamespace(id=1)


@pytest.fixture(autouse=True)
def _khong_gui_thong_bao(monkeypatch):
    """Chặn gửi thông báo — bài test này chỉ quan tâm tới chốt trạng thái."""
    monkeypatch.setattr(controller, "trigger_notification", lambda **kw: None)


def _po(db, status="draft", supplier_code="NX", co_dong_hang=True, progress="Chưa đặt hàng"):
    code = "PO%d" % (db.query(PurchaseOrder).count() + 1)   # tab_purchase_order.code là UNIQUE
    po = PurchaseOrder(code=code, status=status, supplier_code=supplier_code,
                       supplier_name="NCC Nam Xuân" if supplier_code else "")
    db.add(po)
    db.commit()
    db.refresh(po)
    if co_dong_hang:
        # CR-095: dòng hàng phải ĐỦ bộ trường bắt buộc, nếu không chốt mới sẽ chặn và các
        # bài "đơn đủ thông tin thì qua" ở dưới hỏng oan. Bộ trường: xem `dong_day_du`.
        db.add(POItem(po_id=po.id, progress_status=progress, **dong_day_du()))
        db.commit()
    return po


def dong_day_du(**doi) -> dict:
    """Một dòng hàng điền đủ mọi ô bắt buộc; `doi` để bỏ trống/đổi từng ô khi cần."""
    return {"product_code": "SP001", "product_name": "Hàng A", "item_group": "Nguyên liệu",
            "invoice_name": "Hàng A (hóa đơn)", "required_date": "2026-08-25",
            "expected_date": "2026-08-25", "unit": "Cái", "warehouse_code": "KHO1",
            "qty_request": 10, "qty_order": 10, "price": 670, **doi}


def _submit(db, po):
    return controller.submit_po(po.id, BackgroundTasks(), db=db, user=USER)


# --- Gửi duyệt -------------------------------------------------------------------

def test_gui_duyet_khi_chua_chon_ncc_bi_chan(db):
    """Ca người dùng báo: DEMONV bấm Gửi duyệt trên đơn chưa có nhà cung cấp."""
    po = _po(db, supplier_code="")
    with pytest.raises(HTTPException) as e:
        _submit(db, po)
    assert e.value.status_code == 400
    assert "nhà cung cấp" in e.value.detail
    db.refresh(po)
    assert po.status == "draft"


def test_gui_duyet_khi_khong_co_dong_hang_bi_chan(db):
    po = _po(db, co_dong_hang=False)
    with pytest.raises(HTTPException) as e:
        _submit(db, po)
    assert e.value.status_code == 400
    assert "dòng hàng" in e.value.detail


def test_gui_duyet_thieu_ca_hai_thi_bao_ca_hai(db):
    po = _po(db, supplier_code="", co_dong_hang=False)
    with pytest.raises(HTTPException) as e:
        _submit(db, po)
    assert "nhà cung cấp" in e.value.detail and "dòng hàng" in e.value.detail


@pytest.mark.parametrize("status", ["submitted", "approved", "partial", "received",
                                    "completed", "cancelled"])
def test_gui_duyet_don_khong_phai_nhap_bi_chan(db, status):
    po = _po(db, status=status)
    with pytest.raises(HTTPException) as e:
        _submit(db, po)
    assert e.value.status_code == 400
    assert "Nháp" in e.value.detail


@pytest.mark.parametrize("status", ["draft", "rejected"])
def test_gui_duyet_don_du_thong_tin_thi_qua(db, status):
    """Đơn Nháp / Bị trả lại có đủ NCC + dòng hàng thì không được báo lỗi oan."""
    po = _po(db, status=status)
    _submit(db, po)
    db.refresh(po)
    assert po.status == "submitted"


# --- CR-095: bộ trường bắt buộc của TỪNG dòng hàng -------------------------------
# Phiếu hỗ trợ TK19082601: đơn gửi lên vẫn có thể trống ĐVT / kho nhận / đơn giá, người
# duyệt không có gì để duyệt. Chặn ở lúc GỬI DUYỆT, không chặn lúc lưu nháp.

def _po_voi_dong(db, **doi):
    """Đơn Nháp có đúng 1 dòng hàng, `doi` để bỏ trống ô muốn thử."""
    po = _po(db, co_dong_hang=False)
    db.add(POItem(po_id=po.id, progress_status="Chưa đặt hàng", **dong_day_du(**doi)))
    db.commit()
    return po


@pytest.mark.parametrize("truong, nhan", [
    ("product_code", "Mã hàng"), ("item_group", "Phân loại"), ("product_name", "Tên hàng"),
    ("invoice_name", "Tên trên hóa đơn"), ("required_date", "Ngày yêu cầu có hàng"),
    ("expected_date", "Ngày dự kiến có hàng"), ("unit", "ĐVT"),
    ("warehouse_code", "Kho nhận mặc định"),
])
def test_dong_thieu_truong_chu_thi_bi_chan(db, truong, nhan):
    po = _po_voi_dong(db, **{truong: ""})
    with pytest.raises(HTTPException) as e:
        _submit(db, po)
    assert e.value.status_code == 400
    assert nhan in e.value.detail
    db.refresh(po)
    assert po.status == "draft"          # không được nhích trạng thái khi đã chặn


@pytest.mark.parametrize("truong, nhan", [
    ("qty_request", "SL yêu cầu"), ("qty_order", "SL đặt NCC"), ("price", "Đơn giá"),
])
def test_dong_co_o_so_bang_0_thi_bi_chan(db, truong, nhan):
    """Ô số: 0 ở đây là 'chưa nhập' thật — không có SL / không có giá thì không phải dòng để đặt."""
    po = _po_voi_dong(db, **{truong: 0})
    with pytest.raises(HTTPException) as e:
        _submit(db, po)
    assert nhan in e.value.detail


def test_vat_bang_0_van_gui_duyet_duoc(db):
    """VAT KHÔNG nằm trong bộ bắt buộc: 0 vừa là 'chưa nhập' vừa là 'hàng không chịu thuế'."""
    po = _po_voi_dong(db, vat=0)
    _submit(db, po)
    db.refresh(po)
    assert po.status == "submitted"


def test_o_khong_bat_buoc_de_trong_van_gui_duyet_duoc(db):
    """Xuất xứ/TSKT, mã & tên HH thành phẩm, ngày giao chứng từ cho KT, ghi chú — để trống là hợp lệ."""
    po = _po_voi_dong(db, spec="", fg_code="", fg_name="", document_delivery_date=None, note="")
    _submit(db, po)
    db.refresh(po)
    assert po.status == "submitted"


def test_bao_dich_danh_dong_nao_thieu_o_nao(db):
    """Báo chung chung thì người lập phải mở lần lượt từng dòng để dò."""
    po = _po(db, co_dong_hang=False)
    db.add(POItem(po_id=po.id, progress_status="Chưa đặt hàng", **dong_day_du()))
    db.add(POItem(po_id=po.id, progress_status="Chưa đặt hàng",
                  **dong_day_du(product_code="SP002", unit="", price=0)))
    db.commit()
    with pytest.raises(HTTPException) as e:
        _submit(db, po)
    assert "dòng 2" in e.value.detail and "SP002" in e.value.detail
    assert "ĐVT" in e.value.detail and "Đơn giá" in e.value.detail
    assert "dòng 1" not in e.value.detail       # dòng đủ thông tin thì đừng réo tên


def test_thieu_truong_dong_tra_ve_dung_nhan(db):
    assert service.thieu_truong_dong(POItem(**dong_day_du())) == []
    assert service.thieu_truong_dong(POItem(**dong_day_du(unit="", qty_order=0))) \
        == ["ĐVT", "SL đặt NCC"]                # đúng thứ tự hiện trên màn Chi tiết dòng


# --- Duyệt / Từ chối / Trả về ----------------------------------------------------

@pytest.mark.parametrize("status", ["draft", "approved", "partial", "received",
                                    "completed", "cancelled", "rejected"])
def test_duyet_don_khong_o_cho_duyet_bi_chan(db, status):
    po = _po(db, status=status)
    with pytest.raises(HTTPException) as e:
        controller.approve_po(po.id, BackgroundTasks(), db=db, user=USER)
    assert e.value.status_code == 400
    assert "Chờ duyệt" in e.value.detail
    db.refresh(po)
    assert po.status == status


@pytest.mark.parametrize("status", ["draft", "approved", "completed", "cancelled"])
def test_tu_choi_don_khong_o_cho_duyet_bi_chan(db, status):
    po = _po(db, status=status)
    with pytest.raises(HTTPException) as e:
        controller.reject_po(po.id, RejectIn(reason="x"), BackgroundTasks(), db=db, user=USER)
    assert e.value.status_code == 400


@pytest.mark.parametrize("status", ["draft", "approved", "completed", "cancelled"])
def test_tra_ve_don_khong_o_cho_duyet_bi_chan(db, status):
    po = _po(db, status=status)
    with pytest.raises(HTTPException) as e:
        controller.return_po(po.id, RejectIn(reason="x"), BackgroundTasks(), db=db, user=USER)
    assert e.value.status_code == 400


def test_don_cho_duyet_van_duyet_tu_choi_tra_ve_binh_thuong(db):
    po = _po(db, status="submitted")
    controller.approve_po(po.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(po)
    assert po.status == "approved"

    po2 = _po(db, status="submitted")
    controller.return_po(po2.id, RejectIn(reason="thiếu báo giá"), BackgroundTasks(),
                         db=db, user=USER)
    db.refresh(po2)
    assert po2.status == "rejected"

    po3 = _po(db, status="submitted")
    controller.reject_po(po3.id, RejectIn(reason="không mua nữa"), BackgroundTasks(),
                         db=db, user=USER)
    db.refresh(po3)
    assert po3.status == "cancelled"


# --- Hủy đơn ---------------------------------------------------------------------

@pytest.mark.parametrize("status", ["cancelled", "completed"])
def test_huy_don_da_o_diem_cuoi_bi_chan(db, status):
    po = _po(db, status=status)
    with pytest.raises(HTTPException) as e:
        controller.cancel_po(po.id, RejectIn(reason="hủy"), db=db, user=USER)
    assert e.value.status_code == 400
    assert "không hủy lại được" in e.value.detail


def test_huy_don_dang_chay_van_huy_duoc(db):
    po = _po(db, status="approved")
    controller.cancel_po(po.id, RejectIn(reason="NCC báo hết hàng"), db=db, user=USER)
    db.refresh(po)
    assert po.status == "cancelled"
