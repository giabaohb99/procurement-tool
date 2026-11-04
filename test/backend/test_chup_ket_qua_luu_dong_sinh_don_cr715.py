"""bao-CR-715 — bài kiểm CHỤP KẾT QUẢ trước khi tách hai hàm rối nhất cụm thu mua.

Đợt R3 tách `purchase_order.service._save_items` (F 53) và
`purchase_request.option_service.generate_purchase_orders` (F 52) theo bước kiểm -> tính -> ghi.
Refactor KHÔNG được đổi hành vi, nên bài này chụp lại đầu ra của mã CŨ trên dữ liệu mẫu phủ mọi
nhánh rồi so nguyên khối: giá trị từng cột ghi xuống, câu báo lỗi, thứ tự dòng, và SỐ CÂU TRUY VẤN
(tách hàm mà lỡ gọi truy vấn trong vòng lặp là bài này đỏ).

Số liệu trong các hằng `EXPECTED_*` lấy từ lần chạy trên mã trước khi tách (erp-v2 6a3ef106).
Đổi hành vi có chủ đích thì sửa hằng kèm mã CR, đừng nới phép so.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import event

from app.modules.catalog.model import ItemGroup
from app.modules.product.model import Product
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import OrderType, PODelivery, POItem, PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn
from app.modules.purchase_request import option_service as OS
from app.modules.purchase_request.constants import PR_OPT_MANUAL
from app.modules.purchase_request.model import (PurchaseRequest, PurchaseRequestItem,
                                                PurchaseRequestItemOption)
from app.modules.supplier.model import Supplier


class _QueryCounter:
    """Đếm số câu SQL chạy trong khối `with` (gắn vào engine của phiên)."""

    def __init__(self, db):
        self.engine = db.get_bind()
        self.count = 0

    def _on(self, *_a, **_k):
        self.count += 1

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self._on)
        return self

    def __exit__(self, *_exc):
        event.remove(self.engine, "before_cursor_execute", self._on)


ITEM_COLS = ("product_code", "product_name", "invoice_name", "item_group", "spec", "unit",
             "qty_order", "price", "vat", "currency", "exchange_rate", "expected_date",
             "progress_status", "note")


def _items_snapshot(db, po_id):
    rows = db.query(POItem).filter(POItem.po_id == po_id).order_by(POItem.id).all()
    out = []
    for r in rows:
        d = {}
        for c in ITEM_COLS:
            v = getattr(r, c)
            d[c] = float(v) if c in ("qty_order", "price", "vat", "exchange_rate") else (v or "")
        out.append(d)
    return out


def _deliveries_snapshot(db, po_id):
    rows = db.query(PODelivery).filter(PODelivery.po_id == po_id).order_by(PODelivery.id).all()
    return [{"ship_qty": float(d.ship_qty or 0), "promised_date": d.promised_date or "",
             "invoice_no": d.invoice_no or ""} for d in rows]


# ── purchase_order.service._save_items ──────────────────────────────────────────

@pytest.fixture
def masters(db):
    db.add_all([
        Product(code="SP1", name="Hàng một", specs="Thép 304", invoice_name="Tên HĐ một"),
        Product(code="SP2", name="Hàng hai", specs="", invoice_name=""),
        ItemGroup(code="G1", name="Nhóm G1", std_days="7", std_days_unavail="10"),
    ])
    pr = PurchaseRequest(code="PYC-715", status="dispatched", created_by=1)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP1", product_name="Hàng một",
                               qty=5, expected_date="2026-12-01", created_by=1))
    db.commit()
    return pr


def _po(db, **kw):
    base = dict(code="PO-715", pr_code="PYC-715", status="draft", currency="USD",
                exchange_rate=25000, order_date="2026-11-01", supplier_code="", supplier_name="")
    base.update(kw)
    po = PurchaseOrder(**base)
    db.add(po)
    db.commit()
    return po


EXPECTED_CREATE_ITEMS = [
    {"product_code": "SP1", "product_name": "Hàng một", "invoice_name": "Tên HĐ một", "item_group": "",
     "spec": "Thép 304", "unit": "Cái", "qty_order": 5.0, "price": 10.0, "vat": 8.0, "currency": "USD",
     "exchange_rate": 25000.0, "expected_date": "2026-12-01", "progress_status": "not_ordered", "note": ""},
    {"product_code": "SP2", "product_name": "Hàng hai", "invoice_name": "", "item_group": "G1",
     "spec": "", "unit": "Bộ", "qty_order": 2.0, "price": 300000.0, "vat": 10.0, "currency": "VND",
     "exchange_rate": 1.0, "expected_date": "", "progress_status": "not_ordered", "note": ""},
    {"product_code": "SP1", "product_name": "Hàng một lô 2", "invoice_name": "Tự gõ", "item_group": "",
     "spec": "Gõ tay", "unit": "Cái", "qty_order": 1.0, "price": 11.0, "vat": 8.0, "currency": "EUR",
     "exchange_rate": 27000.0, "expected_date": "2026-12-20", "progress_status": "not_ordered",
     "note": ""},
]
EXPECTED_CREATE_DELIVERIES = [{"ship_qty": 2.0, "promised_date": "2026-11-16", "invoice_no": ""}]
EXPECTED_CREATE_QUERIES = 14
EXPECTED_UPDATE_ITEMS = [{'product_code': 'SP1',
  'product_name': 'Hàng một',
  'invoice_name': 'Tên HĐ một',
  'item_group': '',
  'spec': '',
  'unit': 'Cái',
  'qty_order': 6.0,
  'price': 12.0,
  'vat': 8.0,
  'currency': 'USD',
  'exchange_rate': 25000.0,
  'expected_date': '2026-12-01',
  'progress_status': 'not_ordered',
  'note': ''},
 {'product_code': 'SP1',
  'product_name': 'Hàng một lô 2',
  'invoice_name': 'Tự gõ',
  'item_group': '',
  'spec': 'Gõ tay',
  'unit': 'Cái',
  'qty_order': 1.0,
  'price': 11.0,
  'vat': 8.0,
  'currency': 'EUR',
  'exchange_rate': 27000.0,
  'expected_date': '2026-12-20',
  'progress_status': 'completed',
  'note': ''},
 {'product_code': '',
  'product_name': 'Hàng lẻ',
  'invoice_name': '',
  'item_group': 'G1',
  'spec': '',
  'unit': 'Cái',
  'qty_order': 1.0,
  'price': 5.0,
  'vat': 0.0,
  'currency': 'USD',
  'exchange_rate': 25000.0,
  'expected_date': '',
  'progress_status': 'not_ordered',
  'note': ''},
 {'product_code': 'SP2',
  'product_name': 'Hàng hai',
  'invoice_name': '',
  'item_group': '',
  'spec': '',
  'unit': 'Bộ',
  'qty_order': 3.0,
  'price': 1.0,
  'vat': 0.0,
  'currency': 'USD',
  'exchange_rate': 25000.0,
  'expected_date': '',
  'progress_status': 'not_ordered',
  'note': ''}]
EXPECTED_UPDATE_QUERIES = 20
EXPECTED_IMPORT_ITEMS = [{'product_code': 'SP2',
  'product_name': 'Hàng hai',
  'invoice_name': '',
  'item_group': 'G1',
  'spec': '',
  'unit': 'Bộ',
  'qty_order': 1.0,
  'price': 50.0,
  'vat': 0.0,
  'currency': 'VND',
  'exchange_rate': 1.0,
  'expected_date': '2026-11-16',
  'progress_status': 'not_ordered',
  'note': ''},
 {'product_code': 'SP3',
  'product_name': 'Hàng ba',
  'invoice_name': '',
  'item_group': 'Nhóm lạ',
  'spec': '',
  'unit': 'Bộ',
  'qty_order': 1.0,
  'price': 50.0,
  'vat': 0.0,
  'currency': 'VND',
  'exchange_rate': 1.0,
  'expected_date': '2027-01-01',
  'progress_status': 'not_ordered',
  'note': ''}]


def _create_payload():
    return [
        POItemIn(product_code="SP1", product_name="Hàng một", unit="Cái", qty_order=5, price=10, vat=8),
        POItemIn(product_code="SP2", product_name="Hàng hai", item_group="G1", unit="Bộ", qty_order=2,
                 price=300000, vat=10, currency="VND",
                 deliveries=[DeliveryIn(ship_qty=2)]),
        POItemIn(product_code="SP1", product_name="Hàng một lô 2", unit="Cái", qty_order=1, price=11,
                 vat=8, spec="Gõ tay", invoice_name="Tự gõ", currency="EUR", exchange_rate=27000,
                 expected_date="2026-12-20"),
    ]


def test_luu_dong_moi_chup_ket_qua(db, masters):
    po = _po(db)
    with _QueryCounter(db) as qc:
        po_service._save_items(db, po, _create_payload(), user_id=7)
    db.commit()
    assert _items_snapshot(db, po.id) == EXPECTED_CREATE_ITEMS
    assert _deliveries_snapshot(db, po.id) == EXPECTED_CREATE_DELIVERIES
    assert qc.count == EXPECTED_CREATE_QUERIES


def test_items_none_khong_dong_gi(db, masters):
    po = _po(db)
    with _QueryCounter(db) as qc:
        assert po_service._save_items(db, po, None, user_id=7) is None
    assert qc.count == 0


def test_sua_khoa_xoa_dong_chup_ket_qua(db, masters):
    po = _po(db)
    po_service._save_items(db, po, _create_payload(), user_id=7)
    db.commit()
    a, b, c = db.query(POItem).filter(POItem.po_id == po.id).order_by(POItem.id).all()
    c.progress_status = po_service.PROG_COMPLETED      # dòng đã Hoàn thành -> khóa
    db.commit()
    payload = [
        # dòng a: sửa giá, xóa trắng spec (dòng cũ thì giữ trắng), bỏ trống tên HĐ (điền lại từ master)
        POItemIn(id=a.id, product_code="SP1", product_name="Hàng một", unit="Cái", qty_order=6, price=12,
                 vat=8, spec="", currency="USD", exchange_rate=25000),
        # dòng c bị khóa: gửi giá trị khác vẫn giữ nguyên
        POItemIn(id=c.id, product_code="SP9", product_name="Đổi tên", unit="Cái", qty_order=99, price=1),
        # dòng mới không mã hàng, ĐMH có YCMH -> không tự tính ngày QĐ
        POItemIn(product_code="", product_name="Hàng lẻ", item_group="G1", unit="Cái", qty_order=1,
                 price=5),
        # id lạ (không thuộc đơn) -> coi như dòng mới
        POItemIn(id=999999, product_code="SP2", product_name="Hàng hai", unit="Bộ", qty_order=3, price=1),
    ]
    with _QueryCounter(db) as qc:
        po_service._save_items(db, po, payload, user_id=8)
    db.commit()
    snap = _items_snapshot(db, po.id)
    assert db.get(POItem, b.id) is None                  # dòng b không còn trong payload -> xóa
    assert db.query(PODelivery).filter(PODelivery.po_id == po.id).count() == 0   # kèm lần giao
    assert snap == EXPECTED_UPDATE_ITEMS
    assert qc.count == EXPECTED_UPDATE_QUERIES


def test_don_nhap_khau_doc_lap_chup_ket_qua(db, masters):
    po = _po(db, code="PO-715-NK", pr_code="", order_type=int(OrderType.IMPORT), currency="",
             exchange_rate=0)
    payload = [
        POItemIn(product_code="SP2", product_name="Hàng hai", item_group="G1", unit="Bộ", qty_order=1,
                 price=50, vat=10),
        POItemIn(product_code="SP3", product_name="Hàng ba", item_group="Nhóm lạ", unit="Bộ",
                 qty_order=1, price=50, vat=5, expected_date="2027-01-01"),
    ]
    po_service._save_items(db, po, payload, user_id=7)
    db.commit()
    snap = _items_snapshot(db, po.id)
    assert all(r["vat"] == 0.0 for r in snap)            # đơn nhập khẩu: VAT dòng luôn 0
    assert snap == EXPECTED_IMPORT_ITEMS


def test_dong_da_nhan_hang_khong_doi_ma(db, masters):
    po = _po(db)
    po_service._save_items(db, po, _create_payload(), user_id=7)
    db.commit()
    a = db.query(POItem).filter(POItem.po_id == po.id).order_by(POItem.id).first()
    a.qty_received = 1
    db.commit()
    payload = [POItemIn(id=a.id, product_code="SP1", product_name="Hàng một", unit="Thùng", qty_order=5)]
    with pytest.raises(HTTPException) as e:
        po_service._save_items(db, po, payload, user_id=7)
    assert e.value.status_code == 400
    assert e.value.detail == ("Dòng 'Hàng một' đã nhận hàng — không đổi được ĐVT ('Cái' → 'Thùng'). "
                              "Hãy hủy dòng này rồi thêm dòng mới.")


# ── purchase_request.option_service.generate_purchase_orders ────────────────────

def _opt(db, item, supplier_code="", supplier_name="", price=0, vat=0, unit="", delivery_time="",
         delivery_place="", chosen=True):
    o = PurchaseRequestItemOption(pr_item_id=item.id, source=PR_OPT_MANUAL, is_chosen=chosen,
                                  supplier_code=supplier_code, supplier_name=supplier_name,
                                  snap_price_by_volume=price, snap_vat=vat, snap_quote_unit=unit,
                                  snap_delivery_time=delivery_time, snap_delivery_place=delivery_place)
    db.add(o)
    return o


@pytest.fixture
def pr_options(db):
    db.add(Supplier(code="NX", name="NCC Nam Xuân"))
    pr = PurchaseRequest(code="PYC-715G", status="dispatched", company_id=0, department="Phòng A",
                         department_id=0, vat_rate=0, is_urgent=True, created_by=1)
    db.add(pr)
    db.flush()

    def line(code, name, qty, vat_pct=8, status="no_po", unit="cái"):
        it = PurchaseRequestItem(pr_id=pr.id, product_code=code, product_name=name, item_group="Nhãn",
                                 qty=qty, unit=unit, vat_pct=vat_pct, line_status=status,
                                 required_date="2026-12-01", expected_date="2026-12-05", created_by=1)
        db.add(it)
        db.flush()
        return it

    a = line("SP-A", "Hàng A", 10)
    b = line("SP-B", "Hàng B", 3)
    c = line("SP-C", "Hàng C", 4)
    d = line("SP-D", "Hàng D", 1, status="cancelled")
    e = line("SP-E", "Hàng E", 1, status="not_ordered")
    f = line("SP-F", "Hàng F", 2)
    g = line("", "Hàng chưa mã", 2)
    h = line("SP-H", "Hàng H", 6, vat_pct=10)
    _opt(db, a, supplier_code="NX", price=4500, vat=8, unit="cuộn", delivery_time="7 ngày",
         delivery_place="Kho Bình Dương")
    _opt(db, b, supplier_code="NX", price=100, vat=0)                       # VAT trống -> lấy vat_pct dòng
    _opt(db, c, supplier_name="NCC ngoài danh mục", price=50, vat=5)       # chỉ có tên
    _opt(db, d, supplier_code="NX", price=1)
    _opt(db, e, supplier_code="NX", price=1)
    _opt(db, f, supplier_code="NX", price=1, chosen=False)                 # bỏ chốt hết
    _opt(db, g, supplier_code="NX", price=1)
    _opt(db, h, price=70, vat=0, delivery_place="Nhà máy")                  # chưa có NCC
    db.commit()
    return pr


EXPECTED_GEN = {'orders': [{'code': 'PO00001', 'supplier_code': 'NX', 'supplier_name': 'NCC Nam Xuân', 'line_count': 2},
            {'code': 'PO00002', 'supplier_code': '', 'supplier_name': 'NCC ngoài danh mục', 'line_count': 1},
            {'code': 'PO00003', 'supplier_code': '', 'supplier_name': '', 'line_count': 1}],
 'skipped': {'no_chosen': 1, 'already_ordered': 1, 'cancelled': 1, 'no_code': 1}}
EXPECTED_GEN_LINES = {'PO00001': {'header': {'supplier_code': 'NX',
                        'supplier_name': 'NCC Nam Xuân',
                        'note': 'Sinh tự động từ Yêu cầu mua hàng PYC-715G theo phương án đã chốt.',
                        'vat_rate': 0.08,
                        'is_urgent': True,
                        'status': 'draft',
                        'pr_code': 'PYC-715G'},
             'items': [{'product_code': 'SP-A',
                        'product_name': 'Hàng A',
                        'invoice_name': '',
                        'item_group': 'Nhãn',
                        'spec': '',
                        'unit': 'cuộn',
                        'qty_order': 10.0,
                        'price': 4500.0,
                        'vat': 8.0,
                        'currency': 'VND',
                        'exchange_rate': 1.0,
                        'expected_date': '2026-12-05',
                        'progress_status': 'not_ordered',
                        'note': 'Cam kết giao: 7 ngày; Nơi giao: Kho Bình Dương'},
                       {'product_code': 'SP-B',
                        'product_name': 'Hàng B',
                        'invoice_name': '',
                        'item_group': 'Nhãn',
                        'spec': '',
                        'unit': 'cái',
                        'qty_order': 3.0,
                        'price': 100.0,
                        'vat': 8.0,
                        'currency': 'VND',
                        'exchange_rate': 1.0,
                        'expected_date': '2026-12-05',
                        'progress_status': 'not_ordered',
                        'note': ''}]},
 'PO00002': {'header': {'supplier_code': '',
                        'supplier_name': 'NCC ngoài danh mục',
                        'note': 'Sinh tự động từ Yêu cầu mua hàng PYC-715G theo phương án đã chốt.',
                        'vat_rate': 0.08,
                        'is_urgent': True,
                        'status': 'draft',
                        'pr_code': 'PYC-715G'},
             'items': [{'product_code': 'SP-C',
                        'product_name': 'Hàng C',
                        'invoice_name': '',
                        'item_group': 'Nhãn',
                        'spec': '',
                        'unit': 'cái',
                        'qty_order': 4.0,
                        'price': 50.0,
                        'vat': 5.0,
                        'currency': 'VND',
                        'exchange_rate': 1.0,
                        'expected_date': '2026-12-05',
                        'progress_status': 'not_ordered',
                        'note': ''}]},
 'PO00003': {'header': {'supplier_code': '',
                        'supplier_name': '',
                        'note': 'Sinh tự động từ Yêu cầu mua hàng PYC-715G theo phương án đã chốt. Chưa có nhà '
                                'cung cấp — bổ sung trước khi gửi duyệt.',
                        'vat_rate': 0.08,
                        'is_urgent': True,
                        'status': 'draft',
                        'pr_code': 'PYC-715G'},
             'items': [{'product_code': 'SP-H',
                        'product_name': 'Hàng H',
                        'invoice_name': '',
                        'item_group': 'Nhãn',
                        'spec': '',
                        'unit': 'cái',
                        'qty_order': 6.0,
                        'price': 70.0,
                        'vat': 10.0,
                        'currency': 'VND',
                        'exchange_rate': 1.0,
                        'expected_date': '2026-12-05',
                        'progress_status': 'not_ordered',
                        'note': 'Nơi giao: Nhà máy'}]}}
EXPECTED_GEN_QUERIES = 137


def test_sinh_don_theo_phuong_an_chup_ket_qua(db, pr_options):
    pr = pr_options
    with _QueryCounter(db) as qc:
        out = OS.generate_purchase_orders(db, pr, user_id=5)
    gen = {"orders": [{k: v for k, v in o.items() if k != "id"} for o in out["orders"]],
           "skipped": out["skipped"]}
    lines = {}
    for o in out["orders"]:
        po = db.get(PurchaseOrder, o["id"])
        lines[o["code"]] = {
            "header": {"supplier_code": po.supplier_code, "supplier_name": po.supplier_name,
                       "note": po.note, "vat_rate": float(po.vat_rate), "is_urgent": bool(po.is_urgent),
                       "status": po.status, "pr_code": po.pr_code},
            "items": _items_snapshot(db, po.id),
        }
    assert gen == EXPECTED_GEN
    assert lines == EXPECTED_GEN_LINES
    assert qc.count == EXPECTED_GEN_QUERIES


def test_sinh_don_khong_con_dong_nao(db):
    pr = PurchaseRequest(code="PYC-715X", status="dispatched", created_by=1)
    db.add(pr)
    db.flush()
    it = PurchaseRequestItem(pr_id=pr.id, product_code="", product_name="Chưa mã", qty=1, created_by=1)
    db.add(it)
    db.flush()
    _opt(db, it, supplier_code="NX", price=1)
    db.commit()
    with pytest.raises(HTTPException) as e:
        OS.generate_purchase_orders(db, pr, user_id=5)
    assert e.value.status_code == 400
    assert e.value.detail == ("Còn 1 dòng đã chốt phương án nhưng chưa có mã VTBB — nhân sự thu mua gắn mã "
                              "ở chi tiết dòng rồi mới tạo đơn.")
    it.product_code = "SP-X"
    it.line_status = "cancelled"
    db.commit()
    with pytest.raises(HTTPException) as e:
        OS.generate_purchase_orders(db, pr, user_id=5)
    assert e.value.detail == ("Không còn dòng nào tạo được đơn: các dòng hoặc chưa chốt phương án, hoặc đã "
                              "nằm trên đơn mua hàng rồi.")
