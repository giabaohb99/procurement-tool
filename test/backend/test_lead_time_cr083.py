"""Tra số ngày QĐ KHÔNG phân biệt hoa/thường — CR-083.

Phân loại trên sản phẩm là chuỗi tự do nhiều đợt nhập liệu để lại nên hay lệch cách viết so với
danh mục ("Nhãn thùng" vs "Nhãn Thùng"). Trước CR-083 tra khớp tuyệt đối nên các dòng đó âm thầm
rơi về 15 ngày -> sai Ngày QĐ và sai cờ Đơn gấp.
"""
import unicodedata

from app.modules.catalog import lead_time
from app.modules.catalog.model import ItemGroup
from app.modules.purchase_order.model import PODelivery, PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn
from app.modules.purchase_order.service import _save_items, recompute_effects
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.purchase_request.schema import PRItemIn
from app.modules.purchase_request import service as pr_service


def _cat(db):
    db.add_all([ItemGroup(code="PL3", name="Nhãn Thùng", std_days="7", std_days_unavail="7"),
                ItemGroup(code="PL8", name="NL", std_days="10", std_days_unavail="14")])
    db.commit()
    return lead_time.std_days_map(db)


def test_viet_thuong_van_ra_dung_so_ngay(db):
    m = _cat(db)
    assert lead_time.std_days_of(m, "Nhãn thùng") == 7
    assert lead_time.std_days_of(m, "nhãn thùng") == 7
    assert lead_time.std_days_of(m, "NHÃN THÙNG") == 7


def test_dau_cach_thua_khong_lam_lech(db):
    m = _cat(db)
    assert lead_time.std_days_of(m, "  Nhãn   Thùng ") == 7


def test_unicode_to_hop_va_dung_san_cung_mot_khoa(db):
    m = _cat(db)
    assert lead_time.std_days_of(m, unicodedata.normalize("NFD", "Nhãn thùng")) == 7


def test_phan_loai_ngoai_danh_muc_van_ve_moc_mac_dinh(db):
    m = _cat(db)
    assert lead_time.std_days_of(m, "Chai") == lead_time.DEFAULT_STD_DAYS
    assert lead_time.std_days_of(m, "") == lead_time.DEFAULT_STD_DAYS


def test_ngay_qd_tinh_theo_phan_loai_viet_lech(db):
    m = _cat(db)
    assert lead_time.regulated_date(m, "nl", "2026-08-01") == "2026-08-15"   # 14 ngày, không phải 15


def test_don_mua_hang_lay_dung_so_ngay_khi_viet_lech(db):
    _cat(db)
    po = PurchaseOrder(code="PO1", status="draft", order_date="2026-08-01")
    db.add(po)
    db.commit()
    _save_items(db, po, [POItemIn(product_code="SP1", product_name="Hàng A", qty_order=10,
                                  item_group="nhãn thùng",
                                  deliveries=[DeliveryIn(delivery_no=1, ship_qty=10)])], user_id=1)
    recompute_effects(db, po, user_id=1)
    db.commit()
    d = db.query(PODelivery).filter(PODelivery.po_id == po.id).one()
    assert d.std_days == 7 and d.regulated_date == "2026-08-08"


def test_don_gap_tinh_theo_phan_loai_viet_lech(db):
    """Cần hàng sau 10 ngày, phân loại NL quy định 14 -> gấp (trước đây tưởng 15 nên cũng gấp,
    nhưng mốc lấy sai; ở đây kiểm mốc đúng bằng ca cần sau 8 ngày với 'nhãn thùng' 7 ngày)."""
    _cat(db)
    pr = PurchaseRequest(code="PYC1", status="draft", created_by=1, request_date="2026-08-01")
    db.add(pr)
    db.commit()
    pr_service._save_items(db, pr.id, [PRItemIn(product_code="SP1", product_name="Hàng A", qty=1,
                                                item_group="nhãn thùng",
                                                required_date="2026-08-09")], user_id=1)
    db.refresh(pr)
    assert pr.is_urgent is False       # 01/08 + 7 = 08/08 <= 09/08 -> đúng hạn
    pr_service._save_items(db, pr.id, [PRItemIn(product_code="SP1", product_name="Hàng A", qty=1,
                                                item_group="nhãn thùng",
                                                required_date="2026-08-07")], user_id=1)
    db.refresh(pr)
    assert pr.is_urgent is True        # sớm hơn ngày QĐ 1 ngày -> gấp
