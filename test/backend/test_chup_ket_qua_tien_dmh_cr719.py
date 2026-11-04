"""bao-CR-719 — bài kiểm CHỤP KẾT QUẢ trước khi tách các hàm tính tiền của Đơn mua hàng (đợt R3b).

Đợt R3b tách các hàm rối đụng tiền của `purchase_order`: lưu bảng chi phí thu mua (`_save_import_costs`),
tính lại phiếu nhập kho ngầm / tồn kho / công nợ (`recompute_effects`), chọn cơ sở chia (`_allocation_basis`),
phân bổ chi phí (`allocate_import_costs`), đồng bộ công nợ chi phí (`sync_import_cost_payables`), quyết toán nhiều
dòng (`finalize_cost_lines`) và hai hàm dựng kết quả chi phí ở serializer. Refactor KHÔNG được đổi một đồng nào, nên
bài này chụp đầu ra của mã CŨ trên dữ liệu mẫu phủ mọi nhánh rồi so nguyên khối:

- số tiền TỪNG DÒNG (ba giai đoạn, tỷ giá, số quy đổi, phần chia về dòng hàng, giá nhập tồn kho);
- công nợ sinh ra (nguồn, NCC, số tiền, thuế, hạn, trạng thái) và công nợ bị gỡ;
- dòng nhật ký (thứ tự + nội dung), câu báo lỗi;
- SỐ CÂU TRUY VẤN của từng thao tác (tách hàm mà lỡ truy vấn trong vòng lặp là bài này đỏ).

Số liệu trong các hằng `EXPECTED_*` (tệp `du_lieu_chup_tien_dmh_cr719.py`) lấy từ lần chạy trên mã trước khi tách
(erp-v2 c9c5c574).
Đổi hành vi có chủ đích thì sửa hằng kèm mã CR, đừng nới phép so.
"""
import json

from fastapi import HTTPException
from sqlalchemy import event

from app.modules.audit.model import AuditLog
from app.modules.goods_receipt.model import GoodsReceipt
from app.modules.inventory.model import Inventory, InventoryMove
from app.modules.payable.model import Payable
from app.modules.purchase_order import service
from app.modules.purchase_order.model import (AllocationMethod, CostStage, ImportCostType, OrderType,
                                              PODelivery, POCost, POCostType, POItem, PurchaseOrder)
from app.modules.purchase_order.schema import DeliveryIn, POImportCostIn, POItemIn
from app.modules.purchase_order.serializer import _out
from app.modules.supplier.model import Supplier
from du_lieu_chup_tien_dmh_cr719 import (EXPECTED_ALLOCATION_PURE, EXPECTED_LINE_FINALIZE_REOPEN,
                                        EXPECTED_PAYABLE_RULES, EXPECTED_RECOMPUTE_EFFECTS, EXPECTED_THREE_STAGES)

RATE = 25_000.0
REASON = "Hóa đơn hãng tàu về sai số, cần sửa lại"


# ───────────────────────────── công cụ chụp ─────────────────────────────

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


def _num(v):
    return None if v is None else float(v)


def _run(db, queries: dict, key: str, fn, *args, **kwargs):
    """Chạy một thao tác, ghi số câu truy vấn; thành công thì commit (như controller), lỗi thì
    rollback và trả `(mã lỗi, câu lỗi)`."""
    with _QueryCounter(db) as qc:
        try:
            result = fn(*args, **kwargs)
            error = None
        except HTTPException as exc:
            result = None
            error = (exc.status_code, exc.detail)
    queries[key] = qc.count
    if error:
        db.rollback()
        return error
    db.commit()
    return result


COST_COLS = ("cost_type", "description", "supplier_code", "supplier_name", "currency", "vat",
             "estimate_amount", "estimate_rate", "estimate_base", "provisional_amount", "provisional_rate",
             "provisional_base", "final_amount", "final_rate", "final_base", "line_stage",
             "allocation_method", "allocation_target", "manual_allocation", "invoice_no", "invoice_date",
             "payment_due_date")
_COST_NUMS = {"vat", "estimate_amount", "estimate_rate", "estimate_base", "provisional_amount",
              "provisional_rate", "provisional_base", "final_amount", "final_rate", "final_base"}


def _costs(db, po):
    rows = db.query(POCost).filter(POCost.po_id == po.id).order_by(POCost.id).all()
    out = []
    for r in rows:
        d = {"id": r.id}
        for c in COST_COLS:
            v = getattr(r, c)
            d[c] = _num(v) if c in _COST_NUMS else v
        out.append(d)
    return out


PAY_COLS = ("source_type", "ref_type", "ref_id", "company_id", "department_id", "supplier_code",
            "supplier_name", "po_code", "invoice_no", "incur_date", "period", "due_date", "amount", "vat",
            "total", "paid_amount", "remaining", "status")
_PAY_NUMS = {"amount", "vat", "total", "paid_amount", "remaining"}


def _payables(db, po):
    rows = db.query(Payable).filter(Payable.po_id == po.id).order_by(Payable.id).all()
    return [{c: (_num(getattr(p, c)) if c in _PAY_NUMS else getattr(p, c)) for c in PAY_COLS} for p in rows]


def _audit(db):
    rows = db.query(AuditLog).order_by(AuditLog.id).all()
    return [(a.entity, a.entity_id, a.action, a.message, a.doc_code) for a in rows]


def _cost_view(db, po):
    """Phần chi phí của `_out` (dựng bằng `_import_cost`, `_import_cost_summary`, `allocate_import_costs`)."""
    d = _out(db, po)
    return {k: d[k] for k in ("unpaid_total", "import_costs", "cost_stage", "cost_stage_label",
                              "import_cost_summary", "import_cost_allocation")}


def _mark_paid(db, payable, amount):
    payable.paid_amount = amount
    payable.remaining = float(payable.total) - amount
    payable.status = "partial"
    db.commit()


def _suppliers(db):
    db.add_all([
        Supplier(code="HANGTAU", name="Hãng tàu ABC", supplier_type="service", payment_terms="Công nợ 30 ngày",
                 is_active=True),
        Supplier(code="CANG", name="Cảng Cát Lái", supplier_type="service", payment_terms="", is_active=True),
        Supplier(code="VC01", name="Vận chuyển Một", supplier_type="carrier", payment_terms="Công nợ 15 ngày",
                 is_active=True),
    ])
    nx = db.query(Supplier).filter(Supplier.code == "NX").one()
    nx.payment_terms = "Công nợ 45 ngày"
    db.commit()


def _make_po(db, seed, code, items, **kw):
    kw.setdefault("status", "approved")
    kw.setdefault("order_type", int(OrderType.IMPORT))
    kw.setdefault("currency", "USD")
    kw.setdefault("exchange_rate", RATE)
    po = PurchaseOrder(code=code, company_id=seed.company_id, supplier_code="NX", supplier_name=seed.sup_name,
                       order_date="2026-09-22", misa_code="MS01", **kw)
    db.add(po)
    db.flush()
    service._save_items(db, po, items, user_id=1)
    db.commit()
    return po


def _three_items():
    return [
        POItemIn(product_code="SP01", product_name="Hàng một", item_group="Nhãn", unit="cái", qty_request=4,
                 qty_order=4, price=100, vat=0, weight_kg=12.5, required_date="2026-09-30", warehouse_code="KHO01"),
        POItemIn(product_code="SP02", product_name="Hàng hai", item_group="Nhãn", unit="cái", qty_request=3,
                 qty_order=3, price=33.33, vat=10, weight_kg=0, required_date="2026-09-30", warehouse_code="KHO01"),
        POItemIn(product_code="SP03", product_name="Hàng ba", item_group="Thùng", unit="bộ", qty_request=7,
                 qty_order=7, price=150_000, vat=8, currency="VND", exchange_rate=1, weight_kg=3,
                 required_date="2026-09-30", warehouse_code="KHO01"),
    ]


def _payload_from_rows(db, po, **override_by_index):
    """Dựng lại payload bảng chi phí y như màn hình gửi lên (gửi lại cả bảng), có thể đè vài ô của một dòng."""
    out = []
    for i, r in enumerate(db.query(POCost).filter(POCost.po_id == po.id).order_by(POCost.id).all()):
        data = dict(id=r.id, cost_type=r.cost_type, description=r.description, supplier_code=r.supplier_code,
                    supplier_name=r.supplier_name, currency=r.currency, vat=float(r.vat or 0),
                    estimate_amount=_num(r.estimate_amount), estimate_rate=float(r.estimate_rate or 0),
                    provisional_amount=_num(r.provisional_amount), provisional_rate=float(r.provisional_rate or 0),
                    final_amount=_num(r.final_amount), final_rate=float(r.final_rate or 0),
                    allocation_method=r.allocation_method, allocation_target=r.allocation_target,
                    manual_allocation=service.parse_manual_allocation(r.manual_allocation),
                    invoice_no=r.invoice_no, invoice_date=r.invoice_date, payment_due_date=r.payment_due_date)
        data.update(override_by_index.get(f"r{i}", {}))
        out.append(POImportCostIn(**data))
    return out


# ───────────────────── kịch bản A: ba giai đoạn, tỷ giá, phân bổ, công nợ ─────────────────────

def _scenario_three_stages(db, seed) -> dict:
    _suppliers(db)
    po = _make_po(db, seed, "PO-719-A", _three_items())
    item_ids = [it.id for it in service.items_of(db, po.id)]
    q: dict = {}
    snap: dict = {"queries": q}
    costs = [
        POImportCostIn(cost_type=int(ImportCostType.OCEAN_FREIGHT), description="Cước biển", supplier_code="HANGTAU",
                       supplier_name="", currency="USD", estimate_amount=1234.56, vat=10,
                       allocation_method=int(AllocationMethod.BY_VALUE), invoice_no="HD-01",
                       invoice_date="2026-09-25"),
        POImportCostIn(cost_type=int(ImportCostType.LOCAL_CHARGE), description="Phí cảng", supplier_code="CANG",
                       supplier_name="Cảng Cát Lái", currency="VND", estimate_amount=2_500_000, vat=8,
                       allocation_method=int(AllocationMethod.BY_QUANTITY), payment_due_date="2026-10-30"),
        POImportCostIn(cost_type=int(ImportCostType.CUSTOMS_SERVICE), description="Khai thuê", supplier_code="",
                       supplier_name="Đại lý khai thuê", currency="VND", estimate_amount=1_000_001, vat=0,
                       allocation_method=int(AllocationMethod.BY_WEIGHT)),
        POImportCostIn(cost_type=int(ImportCostType.IMPORT_DUTY), description="Thuế nhập khẩu", currency="VND",
                       estimate_amount=333_333, allocation_method=int(AllocationMethod.BY_PRODUCT),
                       allocation_target="SP02"),
        POImportCostIn(cost_type=int(ImportCostType.OTHER), description="Bảo hiểm", supplier_code="HANGTAU",
                       currency="USD", estimate_amount=10, estimate_rate=24_000,
                       allocation_method=int(AllocationMethod.MANUAL),
                       manual_allocation={str(item_ids[0]): 100_000, str(item_ids[1]): 140_000, "999999": 5}),
        POImportCostIn(cost_type=int(ImportCostType.OTHER), description="Khoản không số", supplier_code="CANG",
                       currency="VND", estimate_amount=0, allocation_method=int(AllocationMethod.BY_PRODUCT),
                       allocation_target=""),
        POImportCostIn(cost_type=int(ImportCostType.OTHER), description="Phí EUR", supplier_code="HANGTAU",
                       currency="EUR", estimate_amount=7, estimate_rate=27_123.45, vat=5,
                       allocation_method=int(AllocationMethod.BY_PRODUCT), allocation_target="SPXX"),
        POImportCostIn(cost_type=int(ImportCostType.OTHER), description="Phí trống tiền tệ", supplier_code="CANG",
                       currency="", estimate_amount=3, allocation_method=int(AllocationMethod.BY_VALUE)),
    ]
    _run(db, q, "save_estimate", service._save_import_costs, db, po, costs, 1)
    snap["estimate"] = {"costs": _costs(db, po), "payables": _payables(db, po), "view": _cost_view(db, po)}

    _run(db, q, "advance_provisional", service.advance_cost_stage, db, po, int(CostStage.PROVISIONAL), 1)
    # Gõ số Tạm tính riêng cho cước biển (tỷ giá riêng) và khai thuê (số lẻ).
    payload = _payload_from_rows(db, po, r0={"provisional_amount": 1300.01, "provisional_rate": 25_500},
                                 r2={"provisional_amount": 1_000_003})
    _run(db, q, "save_provisional", service._save_import_costs, db, po, payload, 1)
    snap["provisional"] = {"costs": _costs(db, po), "payables": _payables(db, po), "view": _cost_view(db, po)}

    _run(db, q, "advance_final", service.advance_cost_stage, db, po, int(CostStage.FINAL), 1)
    snap["final"] = {"costs": _costs(db, po), "payables": _payables(db, po), "view": _cost_view(db, po)}

    # Màn hình gửi lại cả bảng y nguyên: đi qua êm, không đổi gì.
    _run(db, q, "save_same_after_final", service._save_import_costs, db, po, _payload_from_rows(db, po), 1)
    snap["errors"] = {
        "edit_final": _run(db, q, "edit_final", service._save_import_costs, db, po,
                           _payload_from_rows(db, po, r1={"final_amount": 2_600_000}), 1),
        "delete_final": _run(db, q, "delete_final", service._save_import_costs, db, po,
                             _payload_from_rows(db, po)[1:], 1),
    }
    snap["after"] = {"costs": _costs(db, po), "payables": _payables(db, po)}
    snap["audit"] = _audit(db)
    return snap


# ───────────── kịch bản B: chốt từng dòng, mở lại, dòng đã chi không lùi, chặn Hoàn thành ─────────────

def _scenario_line_finalize_reopen(db, seed) -> dict:
    _suppliers(db)
    po = _make_po(db, seed, "PO-719-B", _three_items()[:2])
    q: dict = {}
    snap: dict = {"queries": q}
    costs = [
        POImportCostIn(cost_type=int(ImportCostType.OCEAN_FREIGHT), description="Cước biển", supplier_code="HANGTAU",
                       currency="VND", estimate_amount=1_000_000, vat=0),
        POImportCostIn(cost_type=int(ImportCostType.LOCAL_CHARGE), description="Phí cảng không dự toán",
                       supplier_code="CANG", currency="VND", provisional_amount=500_000, vat=10),
        POImportCostIn(cost_type=int(ImportCostType.CUSTOMS_SERVICE), description="", supplier_code="CANG",
                       currency="VND", estimate_amount=777_777, vat=10),
        POImportCostIn(cost_type=int(ImportCostType.OCEAN_FREIGHT), description="Cước USD", supplier_code="HANGTAU",
                       currency="USD", estimate_amount=200, final_amount=210, final_rate=25_100, vat=0),
    ]
    _run(db, q, "save", service._save_import_costs, db, po, costs, 1)
    ids = [c["id"] for c in _costs(db, po)]
    snap["errors"] = {
        "only_no_estimate": _run(db, q, "fin_only_no_estimate", service.finalize_cost_lines, db, po, [ids[1]], 1),
        "unknown_id": _run(db, q, "fin_unknown", service.finalize_cost_lines, db, po, [ids[0], 999_999], 1),
    }
    snap["missing_estimate_all"] = service.count_costs_missing_estimate(db, po)
    done = _run(db, q, "fin_three", service.finalize_cost_lines, db, po, [ids[0], ids[1], ids[2]], 1)
    snap["fin_three_ids"] = [r.id for r in done]
    snap["after_fin_three"] = {"costs": _costs(db, po), "payables": _payables(db, po)}
    snap["errors"]["fin_again"] = _run(db, q, "fin_again", service.finalize_cost_line, db, po, ids[0], 1)

    pay = db.query(Payable).filter(Payable.ref_type == service.IMPORT_COST_SOURCE, Payable.ref_id == ids[0]).one()
    _mark_paid(db, pay, 300_000)
    snap["errors"]["reopen_paid"] = _run(db, q, "reopen_paid", service.reopen_cost_line, db, po, ids[0], REASON, 1)
    snap["errors"]["reopen_short"] = _run(db, q, "reopen_short", service.reopen_cost_line, db, po, ids[2], "ngắn", 1)
    _run(db, q, "reopen_line", service.reopen_cost_line, db, po, ids[2], REASON, 1)
    snap["after_reopen_line"] = {"costs": _costs(db, po), "payables": _payables(db, po)}

    _run(db, q, "advance_final", service.advance_cost_stage, db, po, int(CostStage.FINAL), 1)
    snap["after_advance_final"] = {"costs": _costs(db, po), "payables": _payables(db, po),
                                   "view": _cost_view(db, po)}
    snap["errors"]["complete_unpaid"] = _run(db, q, "complete_unpaid", service.block_complete_unpaid_import_costs,
                                             db, po)
    _run(db, q, "reopen_stage", service.reopen_cost_stage, db, po, int(CostStage.ESTIMATE), REASON, 1)
    snap["after_reopen_stage"] = {"costs": _costs(db, po), "payables": _payables(db, po),
                                  "view": _cost_view(db, po)}
    snap["errors"]["complete_not_final"] = _run(db, q, "complete_not_final", service.block_complete_not_final_costs,
                                                db, po)
    snap["errors"]["delete_paid_final"] = _run(db, q, "delete_paid_final", service._save_import_costs, db, po,
                                               _payload_from_rows(db, po)[1:], 1)
    done = _run(db, q, "fin_all", service.finalize_cost_lines, db, po, None, 1)
    snap["fin_all_ids"] = [r.id for r in done]
    snap["errors"]["fin_nothing_left"] = _run(db, q, "fin_nothing_left", service.finalize_cost_lines, db, po, None, 1)
    snap["end"] = {"costs": _costs(db, po), "payables": _payables(db, po)}
    snap["audit"] = _audit(db)
    return snap


# ───────────── kịch bản C: sinh / không sinh công nợ theo trạng thái đơn và danh mục loại ─────────────

def _scenario_payable_rules(db, seed) -> dict:
    _suppliers(db)
    db.add_all([
        POCostType(code=int(ImportCostType.OCEAN_FREIGHT), name="Cước biển (danh mục)", creates_payable=True),
        POCostType(code=int(ImportCostType.LOCAL_CHARGE), name="Phí cảng (danh mục)", creates_payable=True),
        POCostType(code=int(ImportCostType.OTHER), name="Chi phí khác", creates_payable=False),
        POCostType(code=15, name="Phí nội bộ", creates_payable=False),
        POCostType(code=16, name="Phí ngừng dùng", creates_payable=True, is_active=False),
    ])
    db.commit()
    po = _make_po(db, seed, "PO-719-C", _three_items()[:1], status="draft", cost_stage=int(CostStage.FINAL))
    q: dict = {}
    snap: dict = {"queries": q}
    costs = [
        POImportCostIn(cost_type=int(ImportCostType.OCEAN_FREIGHT), description="Cước", supplier_code="HANGTAU",
                       currency="VND", final_amount=1_000_000, vat=10, invoice_date="2026-09-29"),
        POImportCostIn(cost_type=int(ImportCostType.OTHER), description="Khoản không sinh nợ",
                       supplier_code="HANGTAU", currency="VND", final_amount=500_000),
        POImportCostIn(cost_type=15, description="Nội bộ", supplier_code="CANG", currency="VND",
                       final_amount=70_000),
        POImportCostIn(cost_type=int(ImportCostType.OCEAN_FREIGHT), description="Số không", supplier_code="CANG",
                       currency="VND", final_amount=0),
        POImportCostIn(cost_type=int(ImportCostType.LOCAL_CHARGE), description="Thiếu NCC", currency="VND",
                       final_amount=90_000),
        POImportCostIn(cost_type=int(ImportCostType.LOCAL_CHARGE), description="Phí USD", supplier_code="CANG",
                       supplier_name="", currency="USD", final_amount=12.5, final_rate=0, vat=8,
                       payment_due_date="2026-12-31"),
    ]
    snap["errors"] = {
        "unknown_type": _run(db, q, "unknown_type", service._save_import_costs, db, po,
                             [POImportCostIn(cost_type=77, currency="VND", final_amount=1)], 1),
        "inactive_type": _run(db, q, "inactive_type", service._save_import_costs, db, po,
                              [POImportCostIn(cost_type=16, currency="VND", final_amount=1)], 1),
        "manual_empty": _run(db, q, "manual_empty", service._save_import_costs, db, po,
                             [POImportCostIn(cost_type=1, description="Tay", currency="VND", final_amount=100,
                                             allocation_method=int(AllocationMethod.MANUAL))], 1),
        "manual_mismatch": _run(db, q, "manual_mismatch", service._save_import_costs, db, po,
                                [POImportCostIn(cost_type=1, description="Tay lệch", currency="VND",
                                                final_amount=100_000, allocation_method=int(AllocationMethod.MANUAL),
                                                manual_allocation={"1": 98_000})], 1),
    }
    _run(db, q, "save_draft", service._save_import_costs, db, po, costs, 1)
    snap["draft"] = {"costs": _costs(db, po), "payables": _payables(db, po)}
    po.status = "approved"
    db.commit()
    _run(db, q, "sync_approved", service.sync_import_cost_payables, db, po, 1)
    snap["approved"] = {"payables": _payables(db, po), "view": _cost_view(db, po)}
    # Loại đang dùng bị ngừng sau đó: dòng cũ vẫn lưu được.
    db.query(POCostType).filter(POCostType.code == int(ImportCostType.LOCAL_CHARGE)).one().is_active = False
    po.cost_stage = int(CostStage.ESTIMATE)
    db.commit()
    snap["errors"]["inactive_kept_row"] = _run(db, q, "inactive_kept_row", service._save_import_costs, db, po,
                                               _payload_from_rows(db, po), 1)
    snap["after_inactive"] = {"costs": _costs(db, po), "payables": _payables(db, po)}
    po.cost_stage = int(CostStage.FINAL)
    db.commit()
    _run(db, q, "sync_final_again", service.sync_import_cost_payables, db, po, 1)
    first = db.query(Payable).filter(Payable.po_id == po.id).order_by(Payable.id).first()
    _mark_paid(db, first, 50_000)
    po.status = "cancelled"
    db.commit()
    _run(db, q, "sync_cancelled", service.sync_import_cost_payables, db, po, 1)
    snap["cancelled"] = {"payables": _payables(db, po)}
    snap["audit"] = _audit(db)
    return snap


# ───────────── kịch bản D: phân bổ thuần (mọi cách chia, lùi cách, làm tròn) ─────────────

def _scenario_allocation_pure() -> dict:
    lines = [
        {"id": 1, "product_code": "A", "product_name": "Hàng A", "unit": "cái", "qty_order": 1, "weight_kg": 0,
         "order_total": 1, "exchange_rate": 1},
        {"id": 2, "product_code": "B", "product_name": "Hàng B", "unit": "cái", "qty_order": 1, "weight_kg": 0,
         "order_total": 1, "exchange_rate": 1},
        {"id": 3, "product_code": "A", "product_name": "Hàng A lô 2", "unit": "cái", "qty_order": 1,
         "weight_kg": 0, "order_total": 1, "exchange_rate": 1},
    ]
    zero_lines = [dict(line, order_total=0, qty_order=0) for line in lines]
    mixed = [
        {"id": 11, "product_code": "X", "qty_order": 3, "weight_kg": 2.5, "order_total": 10.5, "exchange_rate": 25_000},
        {"id": 12, "product_code": "Y", "qty_order": 0, "weight_kg": 0, "order_total": 0, "exchange_rate": 1},
        {"id": 13, "product_code": "Z", "qty_order": 7, "weight_kg": 1.25, "order_total": 333_333.33,
         "exchange_rate": 1},
    ]

    def cost(i, method, base, **kw):
        c = {"id": i, "cost_type": 1, "cost_type_label": f"Loại {i}", "description": f"Khoản {i}",
             "supplier_code": "S", "supplier_name": "NCC S", "allocation_method": method,
             "allocation_target": "", "manual_allocation": {}, "base_amount": base}
        c.update(kw)
        return c

    costs_equal = [cost(1, 1, 100.0), cost(2, 3, 100.0), cost(3, 2, 100.0), cost(4, 4, 100.01, allocation_target="A"),
                   cost(5, 4, 50.0, allocation_target="Q"), cost(6, 4, 50.0), cost(7, 9, 10.0),
                   cost(8, 5, 99.99, manual_allocation={"1": 33.33, "3": 66.66}),
                   cost(9, 5, 100.0, manual_allocation={"1": 10}), cost(10, 5, 100.0)]
    staged = [cost(21, 1, None, effective_base=1000.0, estimate_base=900.0, provisional_base=None, final_base=1000.0),
              cost(22, 3, None, effective_base=0.07, estimate_base=0.07, provisional_base=0.08, final_base=None),
              cost(23, 2, None, effective_base=1_000_001.0, estimate_base=1_000_001.0, provisional_base=1_000_003.0,
                   final_base=1_000_003.0)]
    out = {
        "equal": service.allocate_import_costs(lines, costs_equal),
        "zero_goods": service.allocate_import_costs(zero_lines, costs_equal[:3]),
        "no_lines": service.allocate_import_costs([], costs_equal[:2]),
        "no_lines_no_costs": service.allocate_import_costs([], []),
        "mixed_effective": service.allocate_import_costs(mixed, staged),
        "mixed_effective_key": service.allocate_import_costs(mixed, staged, "effective"),
    }
    for stage in CostStage:
        out[f"mixed_stage_{int(stage)}"] = service.allocate_import_costs(mixed, staged, int(stage))
    norm = [{"item_id": line["id"], "product_code": line["product_code"], "qty_order": line["qty_order"],
             "weight_kg": line["weight_kg"], "goods_base": line["order_total"] * line["exchange_rate"]}
            for line in mixed]
    def basis(*args):
        values, method, warning = service._allocation_basis(*args)
        return [values, None if method is None else int(method), warning]

    out["basis"] = {f"{m.name}-{t}-{a}": basis(m, t, norm, man, a)
                    for m, t, man, a in [
                        (AllocationMethod.BY_VALUE, "", None, 0), (AllocationMethod.BY_WEIGHT, "", None, 0),
                        (AllocationMethod.BY_QUANTITY, "", None, 0), (AllocationMethod.BY_PRODUCT, "Y", None, 0),
                        (AllocationMethod.BY_PRODUCT, " Z ", None, 0), (AllocationMethod.BY_PRODUCT, "", None, 0),
                        (AllocationMethod.MANUAL, "", {"11": 5, "13": 5.5}, 10.5),
                        (AllocationMethod.MANUAL, "", {"11": 5}, 10.5), (AllocationMethod.MANUAL, "", {}, 10.5)]}
    out["basis_zero"] = {m.name: basis(m, "", [dict(n, qty_order=0, weight_kg=0, goods_base=0) for n in norm])
                         for m in AllocationMethod}
    return out


# ───────────── kịch bản E: tính lại nhận hàng, phiếu nhập kho ngầm, tồn kho, công nợ hàng + vận chuyển ─────────────

def _effects(db, po):
    items = db.query(POItem).filter(POItem.po_id == po.id).order_by(POItem.id).all()
    dels = db.query(PODelivery).filter(PODelivery.po_id == po.id).order_by(PODelivery.id).all()
    grs = db.query(GoodsReceipt).filter(GoodsReceipt.po_id == po.id).order_by(GoodsReceipt.id).all()
    return {
        "po_status": po.status,
        "items": [{"id": i.id, "qty_received": _num(i.qty_received), "qty_remaining": _num(i.qty_remaining),
                   "amount": _num(i.amount), "base_amount": _num(i.base_amount), "line_status": i.line_status}
                  for i in items],
        "deliveries": [{"id": d.id, "status": d.status, "std_days": d.std_days, "regulated_date": d.regulated_date,
                        "diff_promise": d.diff_promise, "diff_regulated": d.diff_regulated,
                        "diff_required": d.diff_required} for d in dels],
        "receipts": [{"delivery_id": g.delivery_id, "warehouse_code": g.warehouse_code,
                      "product_code": g.product_code, "qty_received": _num(g.qty_received),
                      "received_date": g.received_date, "qc_result": g.qc_result} for g in grs],
        "inventory": [{"warehouse_code": v.warehouse_code, "product_code": v.product_code, "qty": _num(v.qty),
                       "avg_cost": _num(v.avg_cost), "value": _num(v.value)}
                      for v in db.query(Inventory).order_by(Inventory.id).all()],
        "moves": [{"product_code": m.product_code, "qty": _num(m.qty), "unit_price": _num(m.unit_price),
                   "ref_type": m.ref_type, "ref_id": m.ref_id}
                  for m in db.query(InventoryMove).order_by(InventoryMove.id).all()],
        "payables": _payables(db, po),
    }


def _scenario_recompute_effects(db, seed) -> dict:
    _suppliers(db)
    items = [
        POItemIn(product_code="SP01", product_name="Hàng một", item_group="Nhãn", unit="cái", qty_request=10,
                 qty_order=10, price=12.345, vat=10, required_date="2026-10-03", warehouse_code="KHO01",
                 invoice_no="HD-DONG",
                 deliveries=[
                     DeliveryIn(delivery_no=1, ship_qty=6, received_qty=6, promised_date="2026-09-28",
                                received_date="2026-10-01", carrier_code="VC01", shipping_amount=150_000,
                                invoice_no="HD9"),
                     DeliveryIn(delivery_no=2, ship_qty=4, received_qty=3, received_date="2026-10-02",
                                qc_result="Lỗi", warehouse_code="KHO02"),
                     DeliveryIn(delivery_no=3, ship_qty=1, received_qty=0)]),
        POItemIn(product_code="SP02", product_name="Hàng hai", item_group="Thùng", unit="thùng", qty_request=5,
                 qty_order=5, price=200_000, vat=8, currency="VND", exchange_rate=1, required_date="2026-10-05",
                 warehouse_code="KHO01",
                 deliveries=[DeliveryIn(delivery_no=1, ship_qty=5, received_qty=5, received_date="2026-09-30",
                                        std_days=7, carrier_code="VC02", carrier_name="Xe ngoài",
                                        shipping_amount=0, promised_date="2026-10-01")]),
        POItemIn(product_code="SP03", product_name="Hàng ba", item_group="Nhãn", unit="cái", qty_request=2,
                 qty_order=2, price=1, vat=0, warehouse_code="KHO01"),
    ]
    po = _make_po(db, seed, "PO-719-E", items, order_type=int(OrderType.DOMESTIC))
    q: dict = {}
    snap: dict = {"queries": q}
    _run(db, q, "first", service.recompute_effects, db, po, 1)
    snap["first"] = _effects(db, po)

    d_all = db.query(PODelivery).filter(PODelivery.po_id == po.id).order_by(PODelivery.id).all()
    d_all[0].received_qty = 0          # bỏ nhận lần giao một: gỡ phiếu nhập, tồn, công nợ hàng + vận chuyển
    d_all[1].qc_result = ""
    d_all[1].received_qty = 4
    d_all[3].shipping_amount = 80_000  # vận chuyển của NCC chưa có trong danh mục
    db.commit()
    _run(db, q, "second", service.recompute_effects, db, po, 1)
    snap["second"] = _effects(db, po)

    d_all[0].received_qty = 6
    d_all[0].carrier_code = ""
    d_all[2].received_qty = 0.9995
    it3 = db.query(POItem).filter(POItem.po_id == po.id, POItem.product_code == "SP03").one()
    it3.qty_order = 0
    db.commit()
    _run(db, q, "third", service.recompute_effects, db, po, 1)
    snap["third"] = _effects(db, po)
    return snap


# ───────────────────────────── bài kiểm ─────────────────────────────

def _assert_same(actual: dict, expected: dict):
    """So từng khóa cấp một để chỗ lệch hiện rõ tên bước (khối chụp rất dài), rồi so cả khối — so thêm bản JSON để
    bắt cả THỨ TỰ KHÓA của dữ liệu trả về (`dict ==` của Python bỏ qua thứ tự)."""
    assert list(actual) == list(expected)
    for key in expected:
        assert actual[key] == expected[key], f"lệch ở bước '{key}'"
    assert actual == expected
    assert json.dumps(actual, ensure_ascii=False) == json.dumps(expected, ensure_ascii=False)


def test_chup_ket_qua_ba_giai_doan_ty_gia_phan_bo_cong_no(db, seed):
    _assert_same(_scenario_three_stages(db, seed), EXPECTED_THREE_STAGES)


def test_chup_ket_qua_chot_tung_dong_mo_lai_dong_da_chi(db, seed):
    _assert_same(_scenario_line_finalize_reopen(db, seed), EXPECTED_LINE_FINALIZE_REOPEN)


def test_chup_ket_qua_sinh_khong_sinh_cong_no(db, seed):
    _assert_same(_scenario_payable_rules(db, seed), EXPECTED_PAYABLE_RULES)


def test_chup_ket_qua_phan_bo_lam_tron(db):
    _assert_same(_scenario_allocation_pure(), EXPECTED_ALLOCATION_PURE)


def test_chup_ket_qua_tinh_lai_nhan_hang_ton_kho_cong_no(db, seed):
    _assert_same(_scenario_recompute_effects(db, seed), EXPECTED_RECOMPUTE_EFFECTS)
