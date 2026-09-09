"""bao-CR-321 — điều khoản in trên Đơn đặt hàng khai theo NCC.

Bản in từng chốt cứng "15 ngày · 07 ngày · Chậm nhất 24h". Giờ số này đi theo NCC và
chép xuống đơn. Điểm cần canh: ba mức lùi (đơn -> NCC -> mặc định) phải đúng thứ tự,
và 0 / rỗng phải được coi là CHƯA KHAI chứ không phải "0 ngày" — nếu không, mọi đơn cũ
(cột mới thêm, server_default 0) sẽ in "kiểm tra hàng trong vòng 00 ngày".
"""
from types import SimpleNamespace

import pytest

from app.modules.purchase_order import service
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_order.schema import POCreate, POUpdate
from app.modules.supplier.model import Supplier
from app.modules.supplier.schema import SupplierCreate, SupplierUpdate


def _po(**kw):
    return SimpleNamespace(**{"inspection_days": 0, "return_days": 0, "invoice_deadline": "", **kw})


_sup = _po


# ── resolve_print_terms: ba mức lùi ──────────────────────────────────────────────
def test_khong_ai_khai_thi_ve_mac_dinh_cu():
    t = service.resolve_print_terms(_po(), _sup())
    assert t["inspection_days"] == 15
    assert t["return_days"] == 7
    assert t["return_days_label"] == "07"          # bản in ghi "trong vòng 07 ngày"
    assert t["invoice_deadline"] == "Chậm nhất 24h kể từ khi nhận hàng"


def test_khong_co_ncc_van_khong_no():
    """Đơn mất NCC (NCC bị xóa) vẫn phải in được."""
    t = service.resolve_print_terms(_po(), None)
    assert t["inspection_days"] == 15


def test_ncc_khai_thi_lay_cua_ncc():
    t = service.resolve_print_terms(_po(), _sup(inspection_days=30, return_days=10,
                                                 invoice_deadline="Trong 3 ngày làm việc"))
    assert (t["inspection_days"], t["return_days"]) == (30, 10)
    assert t["return_days_label"] == "10"
    assert t["invoice_deadline"] == "Trong 3 ngày làm việc"


def test_don_khai_thi_thang_ncc():
    t = service.resolve_print_terms(_po(inspection_days=5, invoice_deadline="Cuối tháng"),
                                    _sup(inspection_days=30, return_days=10, invoice_deadline="X"))
    assert t["inspection_days"] == 5
    assert t["invoice_deadline"] == "Cuối tháng"
    assert t["return_days"] == 10                   # ô đơn để trống -> vẫn lùi về NCC


def test_chuoi_toan_khoang_trang_coi_nhu_chua_khai():
    t = service.resolve_print_terms(_po(invoice_deadline="   "), _sup(invoice_deadline="  "))
    assert t["invoice_deadline"] == "Chậm nhất 24h kể từ khi nhận hàng"


def test_doi_tuong_cu_chua_co_cot():
    """Đơn / NCC nạp từ dữ liệu trước migration không có thuộc tính -> không nổ AttributeError."""
    t = service.resolve_print_terms(object(), object())
    assert t["inspection_days"] == 15


# ── Schema: chặn số ngày vô lý ───────────────────────────────────────────────────
@pytest.mark.parametrize("cls", [SupplierCreate, POCreate])
def test_mac_dinh_schema_la_chua_khai(cls):
    kw = {"code": "X", "name": "NCC"} if cls is SupplierCreate else {}
    obj = cls(**kw)
    assert (obj.inspection_days, obj.return_days, obj.invoice_deadline) == (0, 0, "")


@pytest.mark.parametrize("cls", [SupplierUpdate, POUpdate])
@pytest.mark.parametrize("field, value", [("inspection_days", -1), ("return_days", 366)])
def test_schema_chan_so_ngay_ngoai_khoang(cls, field, value):
    with pytest.raises(Exception):
        cls(**{field: value})


# ── Chảy xuống DB: tạo đơn + nhân bản giữ nguyên điều khoản ─────────────────────
def test_tao_don_va_nhan_ban_giu_dieu_khoan(db, seed):
    data = POCreate(company_id=seed.company_id, supplier_code="NX", supplier_name=seed.sup_name,
                    order_date="2026-09-09", inspection_days=20, return_days=5,
                    invoice_deadline="  Trong 48h  ")
    po = service.create_po(db, data, user_id=1)
    db.flush()
    saved = db.get(PurchaseOrder, po.id)
    assert (saved.inspection_days, saved.return_days) == (20, 5)
    assert saved.invoice_deadline == "Trong 48h"

    clone = service.copy_po(db, po.id, user_id=1)
    assert (clone.inspection_days, clone.return_days, clone.invoice_deadline) == (20, 5, "Trong 48h")


def test_ncc_luu_duoc_dieu_khoan(db, seed):
    sup = db.query(Supplier).filter(Supplier.code == "NX").first()
    sup.inspection_days, sup.return_days, sup.invoice_deadline = 25, 3, "Theo hợp đồng"
    db.flush()
    t = service.resolve_print_terms(_po(), sup)
    assert (t["inspection_days"], t["return_days_label"], t["invoice_deadline"]) == (25, "03", "Theo hợp đồng")
