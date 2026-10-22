"""duoc-CR-663 (kh-NT1-4) — (a) «Tên trên hóa đơn» của dòng ĐMH GHI vào cột lúc lưu;
(b) N-008: báo cáo mua hàng gom theo ID phòng ban, hiển thị tên hiện hành — đổi tên phòng
không làm lệch số."""
from types import SimpleNamespace

import pytest

from app.core.report_period import parse_period
from app.modules.department.model import Department
from app.modules.product.model import Product
from app.modules.purchase_order import service
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.schema import POItemIn
from app.modules.report import service as report_service
from app.modules.report.procurement_summary_service import compute_procurement_summary


# --- (a) Tên trên hóa đơn ------------------------------------------------------------

def _po(db, seed, **kw):
    po = PurchaseOrder(code="PO663%d" % (db.query(PurchaseOrder).count() + 1), status="draft",
                       supplier_code="NX", company_id=seed.company_id, **kw)
    db.add(po)
    db.commit()
    return po


def _line(**kw):
    base = dict(product_code="SP663", product_name="Hàng 663", qty_order=1, price=10, unit="Cái")
    return POItemIn(**{**base, **kw})


def _items(db, po):
    return db.query(POItem).filter(POItem.po_id == po.id).order_by(POItem.id).all()


@pytest.fixture
def master(db):
    db.add(Product(code="SP663", name="Hàng 663", invoice_name="Tên HĐ master"))
    db.commit()


def test_dong_moi_trong_ten_hoa_don_duoc_ghi_tu_master(db, seed, master):
    po = _po(db, seed)
    service._save_items(db, po, [_line()], 1)
    assert _items(db, po)[0].invoice_name == "Tên HĐ master"   # nằm trong CỘT, không chỉ suy lúc trả


def test_nguoi_dung_da_go_ten_thi_giu_nguyen(db, seed, master):
    po = _po(db, seed)
    service._save_items(db, po, [_line(invoice_name="Tên kế toán gõ")], 1)
    assert _items(db, po)[0].invoice_name == "Tên kế toán gõ"


def test_master_khong_co_ten_thi_de_trong(db, seed):
    db.add(Product(code="SP663", name="Hàng 663", invoice_name=""))
    db.commit()
    po = _po(db, seed)
    service._save_items(db, po, [_line()], 1)
    assert _items(db, po)[0].invoice_name == ""


def test_luu_lai_dong_cu_dang_trong_cung_duoc_bu(db, seed, master):
    po = _po(db, seed)
    service._save_items(db, po, [_line()], 1)
    it = _items(db, po)[0]
    it.invoice_name = ""
    db.commit()
    service._save_items(db, po, [_line(id=it.id)], 1)
    assert _items(db, po)[0].invoice_name == "Tên HĐ master"


# --- (b) Báo cáo theo ID phòng ---------------------------------------------------------

@pytest.fixture
def phong(db, seed):
    dept = Department(code="PB663", name="Phòng cũ", company_id=seed.company_id, is_active=True)
    db.add(dept)
    db.commit()
    return dept


def _dmh(db, seed, dept, order_date, snapshot_name, urgent=False):
    po = PurchaseOrder(code=f"PO-{order_date}-{snapshot_name}-{db.query(PurchaseOrder).count()}",
                       company_id=seed.company_id, order_date=order_date, status="approved",
                       supplier_code="NX", supplier_name="NX", department=snapshot_name,
                       department_id=dept.id if dept else 0, is_urgent=urgent)
    db.add(po)
    db.flush()
    db.add(POItem(po_id=po.id, product_code="SP1", item_group="Nhãn", qty_order=1, price=100,
                  vat=0, exchange_rate=1))
    return po


def test_doi_ten_phong_van_gom_chung_mot_dong_theo_ma_ma_tran(db, seed, phong):
    _dmh(db, seed, phong, "2026-09-05", "Phòng cũ")          # bản chụp tên CŨ
    phong.name = "Phòng mới"                                  # đổi tên trong Danh mục
    db.commit()
    _dmh(db, seed, phong, "2026-10-05", "Phòng mới")         # bản chụp tên MỚI
    db.commit()
    rows = report_service.compute(db, "2026", seed.company_id)["department"]
    assert [(r["key"], r["orders"], r["department_id"]) for r in rows] == [("Phòng mới", 2, phong.id)]


def test_khoang_ngay_gom_theo_id(db, seed, phong):
    _dmh(db, seed, phong, "2026-09-05", "Phòng cũ", urgent=True)
    phong.name = "Phòng mới"
    db.commit()
    _dmh(db, seed, phong, "2026-09-06", "Phòng mới")
    db.commit()
    rows = report_service.compute_dept_range(db, "2026-09-01", "2026-09-30", seed.company_id)
    assert [(r["key"], r["orders"], r["urgent"]) for r in rows] == [("Phòng mới", 2, 1)]


def test_phieu_chua_co_id_thi_lui_ve_ban_chup_ten(db, seed, phong):
    _dmh(db, seed, None, "2026-09-05", "Phòng ngoài danh mục")
    db.commit()
    rows = report_service.compute_dept_range(db, "2026-09-01", "2026-09-30", seed.company_id)
    assert [(r["key"], r["department_id"]) for r in rows] == [("Phòng ngoài danh mục", 0)]


def test_hai_phong_khac_id_khong_tron_voi_nhau(db, seed, phong):
    khac = Department(code="PB663B", name="Phòng khác", company_id=seed.company_id, is_active=True)
    db.add(khac)
    db.commit()
    _dmh(db, seed, phong, "2026-09-05", "Phòng cũ")
    _dmh(db, seed, khac, "2026-09-06", "Phòng khác")
    db.commit()
    rows = report_service.compute_dept_range(db, "2026-09-01", "2026-09-30", seed.company_id)
    assert {r["key"]: r["orders"] for r in rows} == {"Phòng cũ": 1, "Phòng khác": 1}


def test_bao_cao_theo_ky_chieu_bo_phan_dung_ten_hien_hanh(db, seed, phong, monkeypatch):
    monkeypatch.setattr(report_service, "report_dept_scope", lambda db, user: None)
    _dmh(db, seed, phong, "2026-09-05", "Phòng cũ")
    phong.name = "Phòng mới"
    db.commit()
    _dmh(db, seed, phong, "2026-09-06", "Phòng mới")
    db.commit()
    period = parse_period({"preset": "custom", "date_from": "2026-09-01", "date_to": "2026-09-30",
                           "compare": "none"})
    data = compute_procurement_summary(db, SimpleNamespace(id=0), period, seed.company_id,
                                       "department", show_ncc=True)
    text = str(data["groups"])
    assert "Phòng mới" in text and "Phòng cũ" not in text
    assert data["totals"]["current"]["po_count"] == 2


# --- Các đường tạo dòng khác: sao chép + nhập Excel ------------------------------------------

def test_sao_chep_dmh_bu_ten_hoa_don_dong_cu_dang_trong(db, seed, master):
    po = _po(db, seed)
    db.add(POItem(po_id=po.id, product_code="SP663", product_name="Hàng 663", invoice_name="",
                  qty_order=1, price=10, unit="Cái"))
    db.commit()
    ban = service.copy_po(db, po.id, 1)
    assert _items(db, ban)[0].invoice_name == "Tên HĐ master"


def test_sao_chep_dmh_giu_ten_da_co(db, seed, master):
    po = _po(db, seed)
    db.add(POItem(po_id=po.id, product_code="SP663", product_name="Hàng 663",
                  invoice_name="Tên kế toán", qty_order=1, price=10, unit="Cái"))
    db.commit()
    assert _items(db, service.copy_po(db, po.id, 1))[0].invoice_name == "Tên kế toán"


def test_helper_dung_cho_nhap_excel_chi_dien_khi_trong(db, master):
    cache = {}
    assert service.fill_blank_invoice_name(db, {"product_code": "SP663", "invoice_name": ""}, cache)[
        "invoice_name"] == "Tên HĐ master"
    assert cache == {"SP663": "Tên HĐ master"}
    assert service.fill_blank_invoice_name(db, {"product_code": "SP663", "invoice_name": "Gõ tay"})[
        "invoice_name"] == "Gõ tay"
    assert service.fill_blank_invoice_name(db, {"product_code": "", "invoice_name": ""})["invoice_name"] == ""
    assert service.fill_blank_invoice_name(db, {"product_code": "KHONGCO", "invoice_name": ""})[
        "invoice_name"] == ""


def test_nhap_excel_goi_helper_dien_ten(db):
    """Khóa dây: đường nhập ĐMH phải gọi helper (đọc mã nguồn — dựng file Excel đầy đủ quá nặng)."""
    import inspect
    from app.modules.import_tool import po_import
    assert "fill_blank_invoice_name" in inspect.getsource(po_import)
