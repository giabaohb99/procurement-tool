"""Đơn mua hàng: lưu header + dòng hàng + các lần giao; mỗi lần lưu reconcile side-effect
(phiếu nhập kho ngầm, tồn kho, công nợ 2 luồng). Idempotent theo id của dòng giao."""
import json
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.status_codes import PO_DELIVERY_STATUS, PO_DOCUMENT_STATUS, PO_PROGRESS_STATUS
from app.modules.catalog import lead_time
from app.modules.department.service import sync_department_ref
from app.modules.employee.service import sync_employee_ref
from app.modules.goods_receipt import service as gr_service
from app.modules.inventory import service as inv_service
from app.modules.payable import service as pay_service
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.supplier.model import Supplier

from .model import (ALLOCATION_METHOD_LABELS, AllocationMethod, DEFAULT_CURRENCY, IMPORT_COST_TYPE_LABELS,
                    ImportCostStatus, ImportCostType, OrderType, PODelivery, POImportCost, POItem,
                    PurchaseOrder)
from .schema import POCreate, POUpdate


def rate_of(obj) -> float:
    """Tỷ giá dùng để quy đổi về đồng tiền hạch toán.

    bao-CR-319. Dòng cũ (trước khi có cột) và dòng VNĐ đều để trống hoặc 0 — phải đọc
    thành 1, vì nhân với 0 sẽ biến cả đơn hàng thành 0 đồng mà không báo lỗi ở đâu cả.
    """
    return float(getattr(obj, "exchange_rate", 0) or 0) or 1.0


# bao-CR-321 — mặc định của ba điều khoản in trên Đơn đặt hàng (mục 2 và mục 5 của
# "Thoả thuận khác"). Đây là các số từng chốt cứng trong bản in, giữ nguyên để đơn cũ và
# NCC chưa khai in ra y hệt trước.
DEFAULT_INSPECTION_DAYS = 15
DEFAULT_RETURN_DAYS = 7
DEFAULT_INVOICE_DEADLINE = "Chậm nhất 24h kể từ khi nhận hàng"


def resolve_print_terms(po, sup=None) -> dict:
    """Điều khoản in trên đơn: ưu tiên giá trị trên ĐƠN, trống thì lấy của NCC, vẫn trống thì
    mặc định. Ba mức để đơn cũ (chưa có cột) và NCC chưa khai vẫn in đúng như trước.
    `days` trả về dạng chuỗi hai chữ số ("07") vì bản in ghi "trong vòng 07 ngày".
    """
    def _pick(field: str, default):
        for obj in (po, sup):
            v = getattr(obj, field, None) if obj is not None else None
            if isinstance(v, str):
                v = v.strip()
            if v:
                return v
        return default

    inspection = int(_pick("inspection_days", DEFAULT_INSPECTION_DAYS))
    return_ = int(_pick("return_days", DEFAULT_RETURN_DAYS))
    return {
        "inspection_days": inspection,
        "return_days": return_,
        "inspection_days_label": f"{inspection:02d}",
        "return_days_label": f"{return_:02d}",
        "invoice_deadline": str(_pick("invoice_deadline", DEFAULT_INVOICE_DEADLINE)),
    }


def _pdate(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date() if s else None
    except ValueError:
        return None


def _days(a: str, b: str) -> int:
    """Số ngày = (a − b). a,b là 'YYYY-MM-DD'. Trả 0 nếu thiếu."""
    da, db_ = _pdate(a), _pdate(b)
    return (da - db_).days if da and db_ else 0

# order_date nằm trong whitelist để BỘ LỌC ĐIỀU KIỆN lọc theo ngày (order_date__between/gte…).
# Lọc khoảng kiểu cũ (order_date_from/_to của thanh lọc cơ bản) vẫn do apply_range_filters lo.
FILTERABLE = ["code", "status", "supplier_code", "pr_code", "misa_code", "nspt", "is_urgent",
              "department", "document_status", "order_date", "order_type",
              "nspt_id", "department_id", "company_id"]
ENTITY = "purchase_order"

# ── Mã trạng thái của cụm ĐMH (B-06) ─────────────────────────────────────────────────────
# Đặt tên cho mã thay vì gõ chuỗi trần ở từng chỗ: `_recalc` ghi bốn cột này, còn hơn chục chỗ
# khác trong ba phân hệ đọc chúng. Gõ thẳng chuỗi là lần sau đổi mã sẽ sót đúng một chỗ, mà chỗ
# sót đó im lặng cho ra trạng thái sai chứ không nổ.
DELIV_PENDING = "pending"
DELIV_SHORT = "short"
DELIV_DEFECT = "defect"
DELIV_RECEIVED = "received"

LINE_NOT_DELIVERED = "not_delivered"
LINE_PARTIAL = "partial"
LINE_FULL = "full"

# Tiến độ dòng — xem thêm PROGRESS_ORDER / PROGRESS_EXCEPTIONS ở giữa tệp.
PROG_NOT_ORDERED = "not_ordered"
PROG_ORDERED = "ordered"
PROG_RECEIVED = "received"
PROG_DOC_PENDING = "doc_pending"
PROG_DOC_SENT = "doc_sent"
PROG_COMPLETED = "completed"
PROG_PAUSED = "paused"
PROG_CANCELLED = "cancelled"


def get_po(db: Session, pid: int) -> PurchaseOrder:
    obj = db.get(PurchaseOrder, pid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy đơn mua hàng")
    return obj


def items_of(db: Session, po_id: int):
    return db.query(POItem).filter(POItem.po_id == po_id).order_by(POItem.id.asc()).all()


def deliveries_of(db: Session, item_id: int):
    return (db.query(PODelivery).filter(PODelivery.po_item_id == item_id)
            .order_by(PODelivery.id.asc()).all())


def list_po(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(PurchaseOrder.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def _supplier_map(db: Session) -> dict:
    return {s.code: s for s in db.query(Supplier).all()}


def _product_specs_map(db: Session, items) -> dict:
    """Thông số kỹ thuật của các SP xuất hiện trong payload (1 query, không N+1).
    Dùng để tự điền "Xuất xứ / TSKT / chất liệu" cho dòng hàng MỚI còn bỏ trống."""
    from app.modules.product.model import Product
    codes = {(getattr(r, "product_code", "") or "").strip() for r in (items or [])}
    codes.discard("")
    if not codes:
        return {}
    rows = db.query(Product.code, Product.specs).filter(Product.code.in_(codes)).all()
    return {c: (s or "") for c, s in rows if s}


def pr_expected_map(db: Session, pr_code: str) -> dict[str, str]:
    """{mã hàng -> thời gian dự kiến có hàng} của phiếu YCMH nguồn.

    Không có khóa ngoại giữa dòng YCMH và dòng ĐMH: cầu nối duy nhất là
    `PurchaseOrder.pr_code` + `product_code`. Mã hàng là DUY NHẤT trên phiếu YCMH
    (app/core/utils.assert_unique_product_codes) nên map theo mã trỏ đúng một dòng nguồn.
    Phía ĐMH được phép trùng mã (bao-CR-308) — các dòng trùng cùng chiếu về một dòng YCMH,
    cùng nhận một ngày dự kiến là đúng nghiệp vụ.
    """
    if not (pr_code or "").strip():
        return {}
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code).first()
    if not pr:
        return {}
    rows = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
    return {(r.product_code or "").strip(): (r.expected_date or "").strip()
            for r in rows if (r.product_code or "").strip() and (r.expected_date or "").strip()}


def pr_items_for_po(pr_data: dict, po_items) -> dict:
    """Cắt phiếu YCMH (đã serialize) còn ĐÚNG các dòng hàng có trên đơn mua hàng — bao-CR-314.

    Một phiếu YCMH được chia cho nhiều NSTM phụ trách rồi tách thành nhiều đơn, nên bản in
    kèm theo một đơn chỉ được mang phần hàng của đơn đó. Ghép bằng `product_code` vì giữa
    hai bảng dòng KHÔNG có khóa ngoại — cùng cầu nối `pr_expected_map` đang dùng. Mã hàng là
    duy nhất trên YCMH (`assert_unique_product_codes`) nên tra ngược trúng đúng một dòng;
    ĐMH được phép trùng mã (bao-CR-308) thì các dòng trùng cùng chiếu về một dòng nguồn và
    chỉ in một lần.

    Tổng tiền tính LẠI tại đây: `_out` của YCMH cộng từ danh sách dòng chứ không đọc cột lưu
    sẵn, nên cắt dòng mà giữ nguyên tổng là in ra 3 dòng kèm tổng của 10 dòng.

    `po_lines_unmatched` = số dòng trên ĐƠN không đối chiếu được (bỏ trống mã hàng, hoặc mã
    không có trên phiếu). Giao diện báo con số này ở thanh công cụ, KHÔNG in vào tờ giấy —
    người in phải biết bản in thiếu, nhưng tờ phiếu thì giữ nguyên khuôn cũ.
    """
    pr_codes = {(i.get("product_code") or "").strip() for i in pr_data.get("items", [])}
    pr_codes.discard("")
    keep, unmatched = set(), 0
    for it in po_items or []:
        code = (getattr(it, "product_code", "") or "").strip()
        if code and code in pr_codes:
            keep.add(code)
        else:
            unmatched += 1
    items = [i for i in pr_data.get("items", [])
             if (i.get("product_code") or "").strip() in keep]
    subtotal = round(sum(i["qty"] * i["price"] for i in items), 2)   # chưa VAT
    total = round(sum(i["amount"] for i in items), 2)                # gồm VAT
    pr_data["items"] = items
    pr_data["subtotal"] = subtotal
    pr_data["vat"] = round(total - subtotal, 2)
    pr_data["total"] = total
    pr_data["po_lines_unmatched"] = unmatched
    return pr_data


def _save_items(db: Session, po: PurchaseOrder, items, user_id: int):
    """Upsert dòng hàng + các lần giao theo id (giữ id ổn định để side-effect idempotent)."""
    if items is None:
        return
    existing_items = {it.id: it for it in items_of(db, po.id)}
    # bao-CR-308: ĐMH ĐƯỢC PHÉP trùng mã hàng (mua theo bộ chứng từ: cùng mã, khác lô /
    # khác Tên trên hóa đơn). An toàn vì đồng bộ về YCMH cộng GỘP theo mã
    # (sync_from_purchase_orders), còn nhận hàng/công nợ/lịch sử đi theo ID dòng.
    # YCMH vẫn chặn trùng (assert_unique_product_codes) — trùng bên đó mới làm tiến độ
    # nhân đôi. Giao diện hỏi xác nhận trước khi lưu để chặn gõ nhầm.
    keep_item_ids = set()
    specs_by_code = _product_specs_map(db, items)
    std_map = lead_time.std_days_map(db)          # số ngày QĐ theo phân loại (mốc dài nhất)
    # Dự kiến có hàng: chép XUỐNG từ dòng YCMH nguồn, CHỈ khi ô trên ĐMH còn trống.
    # Đặt ở backend (không chỉ ở nút "Tạo ĐMH" bên giao diện) để nhập khẩu và dòng thêm sau
    # cũng được điền. Dòng không gắn YCMH, hoặc mã hàng không có trên YCMH: nhập tay bình thường.
    pr_expected = pr_expected_map(db, po.pr_code)
    for raw in items:
        delivs = raw.deliveries or []
        data = raw.model_dump(exclude={"deliveries"})
        # bao-CR-367: bỏ nhịp "có Số hóa đơn mà trống Ngày hóa đơn -> lấy ngày hôm nay".
        # Cùng lý do với `_save_deliveries`: ngày hóa đơn là ngày in trên tờ giấy, đoán hộ
        # bằng ngày nhập liệu là ghi một con số sai mà không ai phát hiện ra.
        # Dòng MỚI chưa có "Xuất xứ / TSKT / chất liệu" -> lấy Thông số kỹ thuật của SP.
        # Chỉ điền lúc TẠO dòng: dòng đang sửa mà người dùng cố ý xóa trắng thì giữ trắng.
        if not (data.get("spec") or "").strip() and not data.get("id"):
            data["spec"] = specs_by_code.get((data.get("product_code") or "").strip(), "")
        # bao-CR-319: dòng không khai loại tiền / tỷ giá thì lấy theo ĐƠN. Không để trống hay
        # để 0 nằm trong CSDL — nhân với 0 là mất trắng số tiền mà không báo lỗi.
        if not (data.get("currency") or "").strip():
            data["currency"] = (po.currency or "").strip() or DEFAULT_CURRENCY
        if not float(data.get("exchange_rate") or 0):
            data["exchange_rate"] = rate_of(po) if data["currency"] == (po.currency or DEFAULT_CURRENCY) else 1
        # bao-CR-319 P3 — ĐƠN NHẬP KHẨU: VAT dòng hàng luôn 0, khóa ở BACKEND.
        # Hóa đơn của NCC nước ngoài không có thuế GTGT Việt Nam; thuế GTGT hàng nhập nộp
        # cho ngân sách nhà nước theo tờ khai và đã khai thành một dòng ở bảng chi phí nhập
        # khẩu. Để người dùng gõ VAT ở dòng hàng nữa là cộng thuế HAI LẦN, đồng thời sinh
        # công nợ thuế cho chính NCC bán hàng — người không hề nhận khoản đó.
        if int(po.order_type or OrderType.DOMESTIC) == int(OrderType.IMPORT):
            data["vat"] = 0
        if not (data.get("expected_date") or "").strip():
            exp_from_pr = pr_expected.get((data.get("product_code") or "").strip(), "")
            if exp_from_pr:
                data["expected_date"] = exp_from_pr
            elif not data.get("id") and not (po.pr_code or "").strip() and (data.get("item_group") or "").strip():
                # Dòng MỚI trên ĐMH độc lập (không gắn YCMH) -> tự tính theo ngày QĐ phân loại
                _base = (po.order_date or "").strip() or date.today().isoformat()
                data["expected_date"] = lead_time.regulated_date(std_map, data.get("item_group") or "", _base)
        iid = data.pop("id", None)
        if iid and iid in existing_items:
            it = existing_items[iid]
            # Dòng đã Hoàn thành / Hủy đơn → KHÓA: giữ nguyên, không cho sửa (kể cả lần giao)
            if (it.progress_status or "") in (PROG_COMPLETED, PROG_CANCELLED):
                keep_item_ids.add(it.id)
                continue
            # Dòng ĐÃ NHẬN HÀNG → khóa nhận diện sản phẩm. Đổi mã hàng/tên hàng/ĐVT lúc này
            # sẽ dời phiếu nhập kho + tồn kho đã ghi nhận sang hàng khác (sai số liệu kho).
            if float(it.qty_received or 0) > 0:
                line_name = (it.product_name or "").strip() or (it.product_code or "").strip() or f"#{it.id}"
                for f, label in (("product_code", "Mã hàng"), ("product_name", "Tên hàng"), ("unit", "ĐVT")):
                    new_v = (data.get(f) or "").strip()
                    old_v = (getattr(it, f, "") or "").strip()
                    if new_v != old_v:
                        raise HTTPException(
                            400,
                            f"Dòng '{line_name}' đã nhận hàng — không đổi được {label} "
                            f"('{old_v}' → '{new_v}'). Hãy hủy dòng này rồi thêm dòng mới.",
                        )
            for k, v in data.items():
                setattr(it, k, v)
            it.updated_by = user_id
        else:
            it = POItem(po_id=po.id, created_by=user_id, updated_by=user_id, **data)
            db.add(it)
        db.flush()
        keep_item_ids.add(it.id)
        _save_deliveries(db, po, it, delivs, user_id, std_map)

    # Xóa dòng hàng (và lần giao + side-effect) không còn trong payload
    for old_id, it in existing_items.items():
        if old_id not in keep_item_ids:
            for d in deliveries_of(db, old_id):
                _cleanup_delivery(db, d.id)
                db.delete(d)
            db.delete(it)
    db.flush()


# ───────────────────────── Chi phí lô hàng nhập khẩu (bao-CR-319 P3) ─────────────────────────
def import_costs_of(db: Session, po_id: int):
    return (db.query(POImportCost).filter(POImportCost.po_id == po_id)
            .order_by(POImportCost.id.asc()).all())


def import_cost_base(row) -> float:
    """Tổng một khoản chi phí, ĐÃ gồm VAT, quy về đồng tiền hạch toán.

    Cùng quy ước với dòng hàng: số nguyên tệ nằm ở `amount`, số quy đổi nằm ở
    `base_amount`. Mọi nơi cộng tiền ngoài phân hệ này chỉ được đọc bản quy đổi.
    """
    return round(float(getattr(row, "amount", 0) or 0)
                 * (1 + float(getattr(row, "vat", 0) or 0) / 100)
                 * rate_of(row), 2)


def is_actual_cost(row) -> bool:
    """Khoản chi phí này là số THỰC TẾ chứ không phải dự toán (bao-CR-347).

    Dòng cũ (trước khi có cột) và mọi giá trị lạ đọc thành Thực tế — cột mặc định là
    Thực tế, và đoán nhầm theo chiều đó chỉ làm khoản nợ hiện ra sớm, còn đoán nhầm
    theo chiều kia thì khoản nợ có thật biến mất khỏi công nợ mà không báo gì.
    """
    return int(getattr(row, "cost_status", 0) or 0) != int(ImportCostStatus.ESTIMATED)


def actual_costs(rows: list[dict]) -> list[dict]:
    """Lọc lấy dòng chi phí THỰC TẾ từ danh sách đã tuần tự hóa (bao-CR-347)."""
    return [r for r in rows if int(r.get("cost_status") or 0) != int(ImportCostStatus.ESTIMATED)]


# ───────────────────────── Công nợ chi phí lô hàng (bao-CR-319 P5) ─────────────────────────
# Mỗi dòng chi phí là MỘT khoản nợ riêng trên `tab_payable`: source_type = ref_type =
# "import_cost", ref_id = id dòng chi phí. Đi chung bảng với goods/shipping để Yêu cầu
# thanh toán, màn Công nợ và tuổi nợ dùng lại y nguyên, không phải dựng luồng thứ hai.
IMPORT_COST_SOURCE = "import_cost"
# Đơn ở các trạng thái này mới sinh nợ cho dòng chi phí. Nháp / chờ duyệt là số ước tính,
# hủy / từ chối thì không còn gì phải trả (khớp REAL_PO_STATUSES của báo cáo).
IMPORT_COST_PAYABLE_STATUSES = frozenset({"approved", "partial", "received", "completed"})


def import_cost_payables_of(db: Session, po_id: int) -> dict[int, Payable]:
    """Khoản nợ chi phí của một đơn, khóa theo id dòng chi phí."""
    rows = db.query(Payable).filter(Payable.po_id == po_id,
                                    Payable.ref_type == IMPORT_COST_SOURCE).all()
    return {int(p.ref_id or 0): p for p in rows}


def sync_import_cost_payables(db: Session, po: PurchaseOrder, user_id: int,
                              suppliers: dict | None = None) -> None:
    """Đồng bộ công nợ cho TOÀN BỘ dòng chi phí của đơn — idempotent, gọi sau mỗi lần lưu
    bảng chi phí và mỗi lần đơn đổi trạng thái.

    Đơn chưa duyệt / đã hủy: gỡ khoản nợ chưa chi đồng nào; khoản đã chi một phần thì giữ
    lại (tiền đã ra khỏi két, xóa dấu vết là mất đối chiếu — cùng cách đối xử với nợ hàng
    khi hủy đơn). Dòng chi phí 0 đồng hoặc chưa khai NCC thì không thành nợ.

    bao-CR-347: dòng DỰ KIẾN cũng không thành nợ — đó là số dự toán để chốt giá bán, chưa
    có hóa đơn nên chưa nợ ai cả. Đổi dòng sang Thực tế là nợ hiện ra ngay ở lần lưu kế
    tiếp; đổi ngược lại thì nợ chưa chi bị gỡ, y như lúc bỏ NCC.
    """
    rows = import_costs_of(db, po.id)
    if not rows:
        return
    existing = import_cost_payables_of(db, po.id)
    active = po.status in IMPORT_COST_PAYABLE_STATUSES
    suppliers = suppliers if suppliers is not None else _supplier_map(db)
    for row in rows:
        base_total = import_cost_base(row)
        has_supplier = bool((row.supplier_code or "").strip() or (row.supplier_name or "").strip())
        if not active or base_total <= 0 or not has_supplier or not is_actual_cost(row):
            old = existing.get(row.id)
            if old and float(old.paid_amount or 0) <= 0:
                db.delete(old)
                db.flush()
            continue
        # Cùng quy ước với nợ hàng: `amount` là gốc trước VAT đã quy đổi, `vat` là tiền thuế.
        base_before_vat = round(float(row.amount or 0) * rate_of(row), 2)
        sup = suppliers.get((row.supplier_code or "").strip())
        pay_service.upsert(
            db, source_type=IMPORT_COST_SOURCE, ref_type=IMPORT_COST_SOURCE, ref_id=row.id,
            company_id=po.company_id, supplier_code=(row.supplier_code or "").strip(),
            supplier_name=(row.supplier_name or "").strip() or (sup.name if sup else ""),
            po_id=po.id, po_code=po.code, invoice_no=(row.invoice_no or "").strip(),
            incur_date=(row.invoice_date or "").strip() or po.order_date or "",
            amount=base_before_vat, vat=round(base_total - base_before_vat, 2),
            due_days=pay_service.debt_days(sup.payment_terms if sup else ""),
            due_date=(row.payment_due_date or "").strip(), user_id=user_id)


def block_complete_unpaid_import_costs(db: Session, po: PurchaseOrder) -> None:
    """Đơn NHẬP KHẨU chỉ được Hoàn thành khi MỌI khoản chi phí lô hàng đã trả đủ (09/09/2026,
    khách chốt mức chặt, chỉ áp cho đơn nhập khẩu).

    Tiến độ dòng hàng chỉ xét nợ HÀNG (`is_line_paid`), nên không có chốt này thì đơn nhập khẩu
    vẫn "Hoàn thành" trong khi cước tàu, thuế nộp ngân sách, phí lưu bãi chưa trả đồng nào — mà
    Hoàn thành xong là khóa sửa đơn, muốn khai thêm chi phí phải Mở lại. Dòng chi phí có tiền
    nhưng chưa thành công nợ (chưa chọn NCC) cũng chặn: khoản đó không có đường nào để trả.
    Đơn trong nước không đổi luật.

    bao-CR-347: dòng DỰ KIẾN đứng ngoài chốt này. Đó là số dự toán, không sinh công nợ, nên
    nếu xét thì đơn nào cũng kẹt ở "chưa thành công nợ" và không bao giờ Hoàn thành được.
    """
    if int(po.order_type or OrderType.DOMESTIC) != int(OrderType.IMPORT):
        return
    rows = import_costs_of(db, po.id)
    if not rows:
        return
    pays = import_cost_payables_of(db, po.id)
    problems: list[str] = []
    for row in rows:
        if import_cost_base(row) <= 0 or not is_actual_cost(row):
            continue
        try:
            cost_type = ImportCostType(int(row.cost_type or 0))
        except ValueError:
            cost_type = ImportCostType.OTHER
        label = (row.description or "").strip() or IMPORT_COST_TYPE_LABELS.get(cost_type, "Chi phí")
        pay = pays.get(row.id)
        if not pay:
            problems.append(f"{label}: chưa thành công nợ (chưa chọn NCC hoặc chưa Lưu đơn)")
            continue
        # Tính từ total - paid (như YCTT) thay vì đọc cột `remaining` tính sẵn, để không lệ thuộc
        # vào việc cột đó đã được cập nhật hay chưa.
        remaining = round(float(pay.total or 0) - float(pay.paid_amount or 0), 2)
        if remaining > 0.01:
            who = (pay.supplier_name or pay.supplier_code or "").strip()
            problems.append(f"{label} ({who}): còn {remaining:,.0f} đ")
    if problems:
        raise HTTPException(
            400, f"Đơn nhập khẩu chỉ Hoàn thành khi đã trả đủ chi phí lô hàng. Còn {len(problems)} khoản: "
                 + "; ".join(problems) + ". Tạo và chi Yêu cầu thanh toán cho các khoản này trước.")


def block_delete_paid_import_cost(db: Session, row: POImportCost) -> None:
    """Dòng chi phí đã có tiền chi thì không xóa được — xóa là mất chỗ để đối chiếu số đã trả."""
    pay = db.query(Payable).filter(Payable.ref_type == IMPORT_COST_SOURCE,
                                   Payable.ref_id == row.id).first()
    if pay and float(pay.paid_amount or 0) > 0:
        raise HTTPException(
            400, f"Dòng chi phí '{row.description or row.supplier_name or row.id}' đã chi "
                 f"{float(pay.paid_amount):,.0f} đ, không xóa được. Sửa số tiền hoặc ghi chú thay vì xóa.")
    if pay:
        db.delete(pay)
        db.flush()


# ───────────────────────── Phân bổ chi phí về dòng hàng (bao-CR-319 P4) ─────────────────────────
# Kết quả chia CHỈ ĐỂ XEM: tính lúc xem / lúc in, không ghi xuống cột nào, không đẩy vào
# giá tồn kho. Vì vậy hàm nhận/trả dict thuần (đúng dạng `_item` / `_import_cost` của
# controller) để màn hình, bản in và P5 cùng đọc một con số — giao diện tự cộng là lệch.
EQUAL_SHARE_LABEL = "Chia đều"
# Cách 5 "Nhập tay": tổng số gõ được phép lệch tối đa chừng này so với số quy đổi của khoản
# (số quy đổi là số thập phân sau nhân tỷ giá, người gõ số tròn đồng).
MANUAL_ALLOCATION_TOLERANCE = 1.0


def parse_manual_allocation(raw) -> dict[str, float]:
    """Đọc cột / payload `manual_allocation` thành {"<id dòng hàng>": số tiền VNĐ}.

    Nhận cả chuỗi JSON (từ DB) lẫn dict (từ payload); giá trị hỏng, khóa rỗng, số âm hay
    không phải số đều bị bỏ chứ không làm đổ cả đơn — cột này chỉ là dữ liệu phụ của khoản.
    """
    if not raw:
        return {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in raw.items():
        key = str(key).strip()
        if not key:
            continue
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            continue
        if amount > 0:
            out[key] = round(amount, 2)
    return out


def _line_goods_base(line: dict) -> float:
    """Tiền hàng QUY ĐỔI của một dòng theo SL đặt (cùng cách tính `goods_base` ở controller)."""
    return float(line.get("order_total") or 0) * float(line.get("exchange_rate") or 1)


def _basis_goods_base(line: dict) -> float:
    """Tiền hàng của một DÒNG ĐÃ CHUẨN HÓA trong `allocate_import_costs` (khóa `goods_base`)."""
    return float(line.get("goods_base") or 0)


def _allocation_basis(method: AllocationMethod, target: str, lines: list[dict],
                      manual: dict[str, float] | None = None, amount: float = 0.0):
    """Trả (cơ sở chia từng dòng, cách chia THỰC TẾ, lời cảnh báo nếu phải đổi cách).

    Cơ sở nào cộng lại bằng 0 (chưa ai gõ kg, SL đặt toàn 0...) thì không chia được;
    lùi về theo giá trị, giá trị cũng 0 thì chia đều — và NÓI RÕ ra chứ không im lặng
    đổi cách, vì người xem sẽ tưởng số kg của họ đã được dùng.

    Cách "Nhập tay": cơ sở chính là số tiền đã gõ cho từng dòng (`manual`, khóa = id dòng
    hàng). Lúc lưu đã chặn tổng lệch, nhưng dòng hàng có thể bị xóa / số tiền khoản đổi sau
    đó nên lúc xem vẫn kiểm lại: lệch quá `MANUAL_ALLOCATION_TOLERANCE` thì lùi về giá trị
    và nói rõ.
    """
    if method == AllocationMethod.MANUAL:
        manual = manual or {}
        basis = [float(manual.get(str(line.get("item_id") or ""), 0) or 0) for line in lines]
        entered = round(sum(basis), 2)
        if entered > 0 and abs(entered - float(amount or 0)) <= MANUAL_ALLOCATION_TOLERANCE:
            return basis, method, ""
        warning = (f"chọn nhập tay nhưng tổng đã gõ {entered:,.0f} đ lệch số tiền khoản {float(amount or 0):,.0f} đ"
                   if entered > 0 else "chọn nhập tay nhưng chưa gõ số tiền dòng nào")
        return _allocation_basis(AllocationMethod.BY_VALUE, "", lines)[0], AllocationMethod.BY_VALUE, \
            warning + " — đã chia theo giá trị"

    if method == AllocationMethod.BY_PRODUCT:
        code = (target or "").strip()
        matched = [(line.get("product_code") or "").strip() == code for line in lines]
        if code and any(matched):
            # Dòng ĐMH được phép trùng mã: mọi dòng cùng mã chia nhau khoản này theo giá trị,
            # giá trị trống thì theo SL đặt, cũng trống thì chia đều.
            for pick in (_basis_goods_base, lambda l: float(l.get("qty_order") or 0), lambda l: 1.0):
                basis = [pick(line) if hit else 0.0 for line, hit in zip(lines, matched)]
                if sum(basis) > 0:
                    return basis, method, ""
        warning = (f"Khoản chỉ định cho mã '{code}' nhưng đơn không có dòng hàng mã này"
                   if code else "Khoản chọn chỉ định mã hàng nhưng chưa ghi mã")
        return _allocation_basis(AllocationMethod.BY_VALUE, "", lines)[0], AllocationMethod.BY_VALUE, \
            warning + " — đã chia theo giá trị"

    if method == AllocationMethod.BY_WEIGHT:
        basis = [float(line.get("weight_kg") or 0) for line in lines]
        if sum(basis) > 0:
            return basis, method, ""
        warning = "chọn chia theo khối lượng nhưng chưa dòng nào có số kg"
    elif method == AllocationMethod.BY_QUANTITY:
        basis = [float(line.get("qty_order") or 0) for line in lines]
        if sum(basis) > 0:
            return basis, method, ""
        warning = "chọn chia theo số lượng nhưng SL đặt của mọi dòng đều bằng 0"
    else:
        warning = ""

    basis = [_basis_goods_base(line) for line in lines]
    if sum(basis) > 0:
        return basis, AllocationMethod.BY_VALUE, (warning + " — đã chia theo giá trị") if warning else ""
    return [1.0] * len(lines), None, (warning + " — đã chia đều") if warning else ""


def allocate_import_costs(items: list[dict], costs: list[dict]) -> dict:
    """Chia từng khoản chi phí về các dòng hàng theo `allocation_method` của khoản đó.

    Vào: `items` đúng dạng `_item()` và `costs` đúng dạng `_import_cost()` của controller
    (đã quy đổi VNĐ). Ra: mỗi dòng hàng là CHA, bên trong liệt kê từng khoản đã gánh kèm cách
    chia + tỷ lệ, cuối cùng là tổng toàn đơn — đúng chiều lồng đại ca chốt cho màn hình.

    Làm tròn: phần lệch DỒN VÀO DÒNG CUỐI (dòng cuối trong số các dòng có nhận khoản đó)
    để tổng các phần luôn bằng đúng số tiền khoản chi — kế toán đối chiếu là phải khớp.
    """
    lines = [{"item_id": it.get("id"), "product_code": it.get("product_code") or "",
              "product_name": it.get("product_name") or "", "unit": it.get("unit") or "",
              "qty_order": float(it.get("qty_order") or 0), "weight_kg": float(it.get("weight_kg") or 0),
              "goods_base": round(_line_goods_base(it), 2), "cost_base": 0.0, "landed_base": 0.0,
              "costs": []} for it in items]
    warnings: list[str] = []
    if not lines:
        if costs:
            warnings.append("Đơn chưa có dòng hàng nên chưa chia được chi phí")
        goods_total = 0.0
        cost_total = round(sum(float(c.get("base_amount") or 0) for c in costs), 2)
        return {"lines": [], "goods_base_total": goods_total, "cost_total": cost_total,
                "landed_total": cost_total, "warnings": warnings}

    for cost in costs:
        try:
            method = AllocationMethod(int(cost.get("allocation_method") or 0))
        except ValueError:
            method = AllocationMethod.BY_VALUE
        amount = float(cost.get("base_amount") or 0)
        basis, effective, warning = _allocation_basis(
            method, cost.get("allocation_target") or "", lines,
            manual=parse_manual_allocation(cost.get("manual_allocation")), amount=amount)
        if warning:
            warnings.append(f"Khoản '{cost.get('description') or cost.get('cost_type_label') or ''}': {warning}")
        total_basis = sum(basis)
        receivers = [i for i, b in enumerate(basis) if b > 0]
        last = receivers[-1]
        allocated = 0.0
        for i in receivers:
            ratio = basis[i] / total_basis
            share = round(amount - allocated, 2) if i == last else round(amount * ratio, 2)
            allocated = round(allocated + share, 2)
            lines[i]["costs"].append({
                "cost_id": cost.get("id"), "cost_type": cost.get("cost_type"),
                "cost_type_label": cost.get("cost_type_label") or "",
                "description": cost.get("description") or "",
                "supplier_code": cost.get("supplier_code") or "", "supplier_name": cost.get("supplier_name") or "",
                "allocation_method": int(method),
                "allocation_method_label": ALLOCATION_METHOD_LABELS.get(method, ""),
                # Cách chia THỰC TẾ đã dùng (khác cách chọn khi phải lùi về giá trị / chia đều)
                "effective_method": int(effective) if effective else 0,
                "effective_method_label": ALLOCATION_METHOD_LABELS.get(effective, "") if effective else EQUAL_SHARE_LABEL,
                "ratio": round(ratio, 6), "base_amount": share,
            })
            lines[i]["cost_base"] = round(lines[i]["cost_base"] + share, 2)

    for line in lines:
        line["landed_base"] = round(line["goods_base"] + line["cost_base"], 2)
    goods_total = round(sum(line["goods_base"] for line in lines), 2)
    cost_total = round(sum(line["cost_base"] for line in lines), 2)
    return {"lines": lines, "goods_base_total": goods_total, "cost_total": cost_total,
            "landed_total": round(goods_total + cost_total, 2), "warnings": warnings}


def _save_import_costs(db: Session, po: PurchaseOrder, costs, user_id: int):
    """Upsert bảng chi phí theo id, xóa dòng không còn trong payload.

    Không gửi khóa `import_costs` (costs is None) = màn hình không đụng tới bảng này,
    giữ nguyên. Gửi mảng rỗng = người dùng đã xóa hết dòng.
    """
    if costs is None:
        return
    existing = {c.id: c for c in import_costs_of(db, po.id)}
    # `_save_items` chạy trước nên id dòng hàng đã có; số nhập tay chỉ giữ khóa của dòng còn tồn tại.
    item_ids = {str(it.id) for it in items_of(db, po.id)}
    keep = set()
    for raw in costs:
        data = raw.model_dump()
        manual = {k: v for k, v in parse_manual_allocation(data.pop("manual_allocation", None)).items()
                  if k in item_ids}
        # Mã lạ (payload cũ, hoặc gõ tay qua API) không được rơi vào cột theo kiểu im lặng.
        try:
            data["cost_type"] = int(ImportCostType(int(data.get("cost_type") or 0)))
        except ValueError:
            data["cost_type"] = int(ImportCostType.OTHER)
        if not (data.get("currency") or "").strip():
            data["currency"] = (po.currency or "").strip() or DEFAULT_CURRENCY
        if not float(data.get("exchange_rate") or 0):
            # Chi phí ghi bằng đúng đồng tiền của đơn thì theo tỷ giá đơn; khác đồng tiền
            # (cước nội địa trả bằng VNĐ trong đơn USD) thì để 1 chứ không mượn tỷ giá đơn.
            data["exchange_rate"] = rate_of(po) if data["currency"] == (po.currency or DEFAULT_CURRENCY) else 1
        # Chia theo chỉ định mà không chọn mã hàng thì không chia được — về mặc định theo giá trị.
        if int(data.get("allocation_method") or 0) == int(AllocationMethod.BY_PRODUCT) \
                and not (data.get("allocation_target") or "").strip():
            data["allocation_method"] = int(AllocationMethod.BY_VALUE)
        cid = data.pop("id", None)
        if cid and cid in existing:
            row = existing[cid]
            for k, v in data.items():
                setattr(row, k, v)
            row.updated_by = user_id
        else:
            row = POImportCost(po_id=po.id, created_by=user_id, updated_by=user_id, **data)
            db.add(row)
        row.base_amount = import_cost_base(row)
        # Nhập tay: tổng các dòng phải bằng đúng số quy đổi của khoản — chặn ngay lúc lưu chứ
        # không im lặng lùi về giá trị, vì thu mua gõ tay là để cân số với chứng từ.
        if int(data.get("allocation_method") or 0) == int(AllocationMethod.MANUAL):
            label = (data.get("description") or "").strip() or "chi phí"
            if not manual:
                raise HTTPException(400, f"Khoản '{label}' chọn nhập tay nhưng chưa nhập số tiền dòng nào")
            entered = round(sum(manual.values()), 2)
            target_amount = float(row.base_amount or 0)
            if abs(entered - target_amount) > MANUAL_ALLOCATION_TOLERANCE:
                raise HTTPException(
                    400, f"Khoản '{label}' chọn nhập tay: tổng đã nhập {entered:,.0f} đ, "
                         f"phải bằng {target_amount:,.0f} đ (lệch {entered - target_amount:,.0f} đ)")
            row.manual_allocation = json.dumps(manual)
        else:
            row.manual_allocation = ""
        db.flush()
        keep.add(row.id)

    for old_id, row in existing.items():
        if old_id not in keep:
            block_delete_paid_import_cost(db, row)
            db.delete(row)
    db.flush()
    # bao-CR-319 P5 — bảng chi phí đổi là công nợ chi phí đổi theo, cùng một lần lưu.
    sync_import_cost_payables(db, po, user_id)


def _save_deliveries(db: Session, po: PurchaseOrder, item: POItem, delivs, user_id: int,
                     std_map: dict[str, int] | None = None):
    existing = {d.id: d for d in deliveries_of(db, item.id)}
    if std_map is None:
        std_map = lead_time.std_days_map(db)
    # Ngày QĐ có hàng của dòng = Ngày đặt hàng + số ngày QĐ của phân loại
    qd_date = lead_time.regulated_date(std_map, item.item_group, (po.order_date or "").strip())
    keep = set()
    for raw in delivs:
        data = raw.model_dump()
        inv_no = (data.get("invoice_no") or "").strip() or (item.invoice_no or "").strip()
        inv_date = (data.get("invoice_date") or "").strip() or (item.invoice_date or "").strip()
        # bao-CR-367: KHÔNG tự gán ngày hôm nay khi có số hóa đơn mà trống ngày. Câu đó biến
        # "thiếu dữ liệu" thành "dữ liệu sai" — trống thì người dùng còn nhìn ra mà điền, chứ
        # điền bừa ngày hôm nay thì không ai biết đó là ngày bịa. Ghép với lỗi giao diện quên
        # gửi `invoice_date` (PurchaseOrderDetail.tsx), nó đã dập ngày thật của 90/96 dòng
        # giao hàng trên hệ thật. Đừng khôi phục lại.
        if inv_no:
            data["invoice_no"] = inv_no
        if inv_date:
            data["invoice_date"] = inv_date
        did = data.pop("id", None)
        if did and did in existing:
            d = existing[did]
            for k, v in data.items():
                setattr(d, k, v)
            d.updated_by = user_id
        else:
            # Cam kết giao mặc định = NGÀY QĐ CÓ HÀNG theo phân loại (Ngày đặt hàng + số ngày QĐ).
            # CHỈ điền lúc TẠO lần giao (kể cả lần giao sinh từ nhập khẩu/copy đơn, không riêng nút
            # "Thêm lần giao"); lần giao đã có thì tôn trọng giá trị người dùng nhập, xóa trắng vẫn trắng.
            if not (data.get("promised_date") or "").strip():
                data["promised_date"] = qd_date
            d = PODelivery(po_id=po.id, po_item_id=item.id, created_by=user_id, updated_by=user_id, **data)
            db.add(d)
        db.flush()
        keep.add(d.id)
    for old_id, d in existing.items():
        if old_id not in keep:
            _cleanup_delivery(db, old_id)
            db.delete(d)
    db.flush()


def _cleanup_delivery(db: Session, delivery_id: int):
    """Gỡ side-effect của 1 lần giao (khi xóa dòng giao)."""
    gr_service.remove_for_delivery(db, delivery_id)
    inv_service.remove_delivery(db, delivery_id)
    pay_service.remove(db, "goods", delivery_id)
    pay_service.remove(db, "shipping", delivery_id)


def recompute_effects(db: Session, po: PurchaseOrder, user_id: int):
    """Tính lại tổng dòng + sinh/cập nhật phiếu nhập kho ngầm, tồn kho, công nợ 2 luồng."""
    suppliers = _supplier_map(db)
    goods_sup = suppliers.get(po.supplier_code)
    goods_days = pay_service.debt_days(po.payment_terms or (goods_sup.payment_terms if goods_sup else ""))

    std_map = lead_time.std_days_map(db)   # số ngày QĐ theo phân loại (mốc dài nhất, thiếu -> 15)

    total_order = total_received = 0.0
    for it in items_of(db, po.id):
        qty_order = float(it.qty_order or 0)
        vat = float(it.vat or 0)
        # bao-CR-319: đơn giá ghi theo đồng tiền của dòng. Công nợ, tồn kho và mọi báo cáo
        # đều không có khái niệm loại tiền nên phải nhận GIÁ ĐÃ QUY ĐỔI. Đơn VNĐ có tỷ giá 1
        # nên số liệu cũ không đổi một đồng nào.
        rate = rate_of(it)
        base_price = float(it.price or 0) * rate

        recv_sum = 0.0
        for d in deliveries_of(db, it.id):
            recv = float(d.received_qty or 0)
            recv_sum += recv
            wh = d.warehouse_code or it.warehouse_code
            if recv > 0:
                # Phiếu nhập kho ngầm + tồn kho
                gr_service.upsert_for_delivery(
                    db, po_id=po.id, po_code=po.code, delivery_id=d.id, company_id=po.company_id,
                    warehouse_code=wh, product_code=it.product_code, product_name=it.product_name,
                    unit=it.unit, qty_received=recv, received_date=d.received_date,
                    qc_result=d.qc_result, user_id=user_id)
                inv_service.apply_delivery(
                    db, delivery_id=d.id, company_id=po.company_id, warehouse_code=wh,
                    product_code=it.product_code, product_name=it.product_name, unit=it.unit,
                    qty=recv, price=base_price, user_id=user_id)
                # Công nợ hàng (NCC bán) — số HĐ lấy theo sản phẩm (po_item)
                amt = recv * base_price
                pay_service.upsert(
                    db, source_type="goods", ref_id=d.id, company_id=po.company_id,
                    supplier_code=po.supplier_code, supplier_name=po.supplier_name,
                    po_id=po.id, po_code=po.code, invoice_no=(d.invoice_no or it.invoice_no or "").strip(),
                    incur_date=d.received_date or po.order_date, amount=amt, vat=amt * vat / 100,
                    due_days=goods_days, user_id=user_id)
                # Công nợ vận chuyển (carrier riêng) — chỉ khi có carrier + cước > 0
                ship_amt = float(d.shipping_amount or 0)
                if d.carrier_code and ship_amt > 0:
                    carrier = suppliers.get(d.carrier_code)
                    c_days = pay_service.debt_days(carrier.payment_terms if carrier else "")
                    # Vận chuyển không có hóa đơn riêng → số HĐ tạm = Mã MISA + Mã SP
                    ship_inv = f"{po.misa_code}-{it.product_code}".strip("-")
                    pay_service.upsert(
                        db, source_type="shipping", ref_id=d.id, company_id=po.company_id,
                        supplier_code=d.carrier_code,
                        supplier_name=d.carrier_name or (carrier.name if carrier else ""),
                        po_id=po.id, po_code=po.code, invoice_no=ship_inv,
                        incur_date=d.received_date or po.order_date, amount=ship_amt, vat=0,
                        due_days=c_days, user_id=user_id)
                else:
                    pay_service.remove(db, "shipping", d.id)
            else:
                _cleanup_delivery(db, d.id)

            # Tiến độ giao: số ngày QĐ → ngày QĐ → chênh lệch.
            # Số ngày QĐ ĐƯỢC SỬA TAY: đã có số trên dòng giao thì giữ nguyên, chỉ dòng còn trống
            # mới lấy mặc định theo phân loại (mốc dài nhất — KHÔNG còn phụ thuộc "NCC có sẵn hàng").
            std = int(d.std_days or 0) or lead_time.std_days_of(std_map, it.item_group)
            d.std_days = std
            od = _pdate(po.order_date)
            d.regulated_date = (od + timedelta(days=std)).strftime("%Y-%m-%d") if (od and std) else ""
            d.diff_promise = _days(d.promised_date, d.received_date) if (d.promised_date and d.received_date) else 0
            d.diff_regulated = _days(d.regulated_date, d.received_date) if (d.regulated_date and d.received_date) else 0
            d.diff_required = _days(d.regulated_date, it.required_date) if (d.regulated_date and it.required_date) else 0
            ship_q = float(d.ship_qty or 0)
            # Mã B-06, xem PO_DELIVERY_STATUS. `qc_result` KHÔNG thuộc bộ mã nào — nó là ô chữ
            # tự do người dùng gõ, chỉ tình cờ cũng mang chữ "Lỗi"; đừng gộp hai thứ làm một.
            if recv <= 0:
                d.status = DELIV_PENDING
            elif d.qc_result == "Lỗi":
                d.status = DELIV_DEFECT
            elif ship_q > 0 and recv + 0.001 < ship_q:
                d.status = DELIV_SHORT
            else:
                d.status = DELIV_RECEIVED

        it.qty_received = round(recv_sum, 3)
        it.qty_remaining = round(qty_order - recv_sum, 3)
        # Thành tiền đơn hàng = SL THỰC NHẬN × đơn giá × (1+VAT) (đã chốt) — NGUYÊN TỆ
        it.amount = round(recv_sum * float(it.price or 0) * (1 + vat / 100), 2)
        it.base_amount = round(it.amount * rate, 2)   # bao-CR-319: bản quy đổi cho báo cáo
        # Mã B-06, xem PO_ITEM_LINE_STATUS. Là HÀM của hai con số nên `LINE_FULL` không phải
        # trạng thái kết: tăng SL đặt của một dòng đã đủ là nó tự lùi về `LINE_PARTIAL`.
        if recv_sum <= 0:
            it.line_status = LINE_NOT_DELIVERED
        elif recv_sum + 0.001 < qty_order:
            it.line_status = LINE_PARTIAL
        else:
            it.line_status = LINE_FULL
        total_order += qty_order
        total_received += recv_sum

    # CR-268 — nhận hàng sinh/cập nhật công nợ xong thì TỰ ĐỘNG đối trừ tiền treo
    # (phiếu THANH TOÁN TRƯỚC gắn đúng đơn này, đã chi). Phải chạy TRƯỚC
    # apply_auto_progress (gọi ngay sau recompute_effects) vì is_line_paid đọc
    # paid_amount của công nợ. Treo CẤP NCC (không gắn đơn) KHÔNG tự trừ — kế toán
    # bấm tay, xem payment_request.service.
    from app.modules.payment_request import service as prq_service   # LAZY: tránh circular
    prq_service.apply_prepay_offsets(db, po.code, po.supplier_code, user_id)

    # Trạng thái PO theo tiến độ nhận (không hạ cấp khi chưa duyệt)
    if po.status in ("approved", "partial", "received") and total_order > 0:
        if total_received <= 0:
            po.status = "approved"
        elif total_received + 0.001 < total_order:
            po.status = "partial"
        else:
            po.status = "received"
    db.flush()


# Các cột dòng hàng được sao chép khi Nhân bản (KHÔNG copy số đã nhận / lần giao / trạng thái;
# KHÔNG copy Số hóa đơn / Ngày hóa đơn — chứng từ riêng từng đơn, phải nhập lại ở bản sao)
_ITEM_COPY_FIELDS = ["product_code", "product_name", "invoice_name", "item_group", "spec",
                     "fg_code", "fg_name", "supplier_ready", "required_date", "unit",
                     "qty_request", "qty_order", "price", "vat", "warehouse_code", "note",
                     "currency", "exchange_rate", "weight_kg", "dimension"]


def copy_po(db: Session, pid: int, user_id: int) -> PurchaseOrder:
    """Nhân bản đơn thành 1 đơn Nháp mới: giữ dòng hàng, bỏ lần giao/số đã nhận, reset mã/MISA/trạng thái."""
    src = get_po(db, pid)
    po = PurchaseOrder(
        code="", misa_code="", pr_code=src.pr_code, survey_code=src.survey_code,
        company_id=src.company_id, supplier_code=src.supplier_code, supplier_name=src.supplier_name,
        department=src.department, department_id=src.department_id,
        nspt=src.nspt, nspt_id=src.nspt_id, order_date=src.order_date, vat_rate=src.vat_rate,
        payment_terms=src.payment_terms, is_urgent=src.is_urgent, note=src.note,
        status="draft", created_by=user_id, updated_by=user_id,
        # bao-CR-319: nhân bản giữ loại đơn + tiền tệ; KHÔNG chép số tờ khai hải quan,
        # cũng KHÔNG chép bảng chi phí nhập khẩu (mỗi lô hàng một tờ khai và một bộ hóa
        # đơn cước riêng — chép sang là gán chứng từ của lô này cho lô khác).
        order_type=src.order_type or int(OrderType.DOMESTIC),
        currency=(src.currency or "").strip() or DEFAULT_CURRENCY,
        exchange_rate=rate_of(src),
        # bao-CR-321: điều khoản in đi theo NCC nên nhân bản giữ nguyên
        inspection_days=src.inspection_days or 0, return_days=src.return_days or 0,
        invoice_deadline=src.invoice_deadline or "",
    )
    sync_department_ref(db, po)     # CR-086
    sync_employee_ref(db, po, "nspt_id", "nspt")    # CR-087
    db.add(po)
    db.flush()
    po.code = f"PO{po.id:05d}"
    for it in items_of(db, src.id):
        data = {k: getattr(it, k) for k in _ITEM_COPY_FIELDS}
        data["amount"] = round((float(data.get("qty_order") or 0)) * (float(data.get("price") or 0)) * (1 + (float(data.get("vat") or 0)) / 100), 2)
        db.add(POItem(po_id=po.id, created_by=user_id, updated_by=user_id, **data))
    db.commit()
    db.refresh(po)
    record(db, user_id, ENTITY, po.id, "create", f"Nhân bản từ {src.code}")
    return po


def _default_nspt(db: Session, data: POCreate, user_id: int) -> tuple[str, int]:
    """NSPT mặc định khi tạo ĐMH — trả về `(tên, id nhân sự)`:
    - Tạo TỪ YCMH (pr_code): lấy người phụ trách (assignee) của dòng trong đơn.
    - Không qua YCMH: người tạo đơn.

    CR-087: ở đây đã cầm sẵn bản ghi nhân sự nên trả luôn id, khỏi tra ngược lại theo tên
    (tra theo tên là chỗ trùng tên gây sai).
    """
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
    if data.pr_code:
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == data.pr_code).first()
        if pr:
            po_codes = {(it.product_code or "").strip() for it in (data.items or []) if (it.product_code or "").strip()}
            rows = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
            emp_code = ""
            for r in rows:   # ưu tiên dòng khớp sản phẩm trong đơn
                if (r.assignee or "").strip() and (not po_codes or (r.product_code or "").strip() in po_codes):
                    emp_code = r.assignee.strip(); break
            if not emp_code:   # fallback: bất kỳ dòng nào có người phụ trách
                for r in rows:
                    if (r.assignee or "").strip():
                        emp_code = r.assignee.strip(); break
            if emp_code:
                emp = db.query(Employee).filter(Employee.code == emp_code).first()
                if emp:
                    return emp.full_name, emp.id
    u = db.query(User).filter(User.id == user_id).first()   # người tạo
    if u and u.employee_id:
        emp = db.query(Employee).filter(Employee.id == u.employee_id).first()
        if emp:
            return emp.full_name, emp.id
    return "", 0


def _ensure_pr_dispatched(db: Session, pr_code: str) -> None:
    """CR-034 — chỉ tạo được ĐMH từ YCMH ĐÃ ĐIỀU PHỐI trở đi.
    Chặn ở đây chứ không chỉ ẩn nút bên giao diện: form ĐMH cho gõ thẳng mã YCMH.
    Mã không khớp phiếu nào (dữ liệu cũ / nhập tay) thì bỏ qua, không chặn."""
    if not pr_code:
        return
    from app.modules.purchase_request.model import PurchaseRequest
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code,
                                          PurchaseRequest.is_deleted == False).first()
    if not pr:
        return
    # Công tắc điều phối TẮT → không còn bước duyệt lần 2, phiếu "Đã duyệt" (phiếu cũ còn kẹt lại
    # từ lúc công tắc còn bật) coi như làm việc được, nếu không sẽ không ai gỡ được cho nó.
    from app.modules.purchase_request.service import dispatch_enabled
    not_actionable_statuses = ["draft", "submitted", "rejected"]
    if dispatch_enabled():
        not_actionable_statuses.append("approved")
    if pr.status in not_actionable_statuses:
        raise HTTPException(400, f"YCMH {pr_code} chưa được điều phối (chưa có nhân sự phụ trách) "
                                 f"— chưa tạo được đơn mua hàng.")
    if pr.status == "cancelled":
        raise HTTPException(400, f"YCMH {pr_code} đã bị từ chối — không tạo được đơn mua hàng.")


def create_po(db: Session, data: POCreate, user_id: int) -> PurchaseOrder:
    _ensure_pr_dispatched(db, (data.pr_code or "").strip())
    nspt, nspt_id = (data.nspt or "").strip(), data.nspt_id
    if not nspt and not nspt_id:
        nspt, nspt_id = _default_nspt(db, data, user_id)
    po = PurchaseOrder(
        code=data.code or "", misa_code=data.misa_code, pr_code=data.pr_code,
        survey_code=data.survey_code, company_id=data.company_id, supplier_code=data.supplier_code,
        supplier_name=data.supplier_name, department=data.department,
        department_id=data.department_id, nspt=nspt, nspt_id=nspt_id,
        order_date=data.order_date, vat_rate=data.vat_rate, payment_terms=data.payment_terms,
        is_urgent=data.is_urgent, note=data.note, status="draft", created_by=user_id, updated_by=user_id,
        order_type=data.order_type or int(OrderType.DOMESTIC),
        currency=(data.currency or "").strip() or DEFAULT_CURRENCY,
        exchange_rate=float(data.exchange_rate or 0) or 1,
        customs_decl_no=data.customs_decl_no, customs_decl_date=data.customs_decl_date,
        inspection_days=data.inspection_days or 0, return_days=data.return_days or 0,
        invoice_deadline=(data.invoice_deadline or "").strip(),
    )
    sync_department_ref(db, po)     # CR-086: neo phòng ban bằng id ngay từ lúc lập đơn
    sync_employee_ref(db, po, "nspt_id", "nspt")    # CR-087: NSPT cũng neo bằng id
    db.add(po)
    db.flush()
    if not po.code:
        po.code = f"PO{po.id:05d}"
    _save_items(db, po, data.items, user_id)
    _save_import_costs(db, po, data.import_costs, user_id)
    recompute_effects(db, po, user_id)
    db.commit()
    db.refresh(po)
    # CR-074: dòng YCMH phải đổi sang `not_ordered` NGAY khi đơn vừa được lập, kể cả đơn Nháp.
    _sync_pr(db, po.pr_code)
    record(db, user_id, ENTITY, po.id, "create")
    return po


# ───────────────────── Đơn ĐÃ DUYỆT: khóa phần đã được duyệt ─────────────────────
# CR-108 (phiếu hỗ trợ TK19082604): 'approved' không nằm trong danh sách khóa nên duyệt
# xong vẫn đổi được mã hàng, số lượng, đơn giá — trưởng phòng ký một đằng, đơn gửi nhà
# cung cấp một nẻo mà không để lại dấu vết nào. Từ nay đơn đã duyệt chỉ còn sửa được các
# ô PHÁT SINH SAU KHI DUYỆT; muốn đổi phần đã duyệt thì bấm "Hủy duyệt" (đơn về Nháp)
# rồi gửi duyệt lại — đi qua đúng cổng kiểm tra CR-095 một lần nữa.
APPROVED_STATUSES = ("approved", "partial", "received")

# Ô của DÒNG HÀNG còn sửa được sau khi duyệt (đúng các ô khoanh đỏ trong phiếu hỗ trợ).
LINE_FIELDS_EDITABLE_AFTER_APPROVAL = {
    "invoice_name",            # Tên trên hóa đơn — kế toán chốt sau khi có hóa đơn thật
    "expected_date",           # Ngày dự kiến có hàng — NCC hẹn lại liên tục
    "warehouse_code",          # Kho nhận mặc định
    "note",                    # Ghi chú
    # Ngày giao chứng từ cho KT: KHÔNG có trong phiếu hỗ trợ nhưng bắt buộc phải để mở.
    # Nó là điều kiện của bước tiến độ `doc_sent` (xem _step_ok) mà bước đó chỉ
    # xảy ra SAU khi duyệt — khóa lại thì mọi dòng đều kẹt tiến độ, không đơn nào xong.
    "document_delivery_date",
}

# Nhãn tiếng Việt để câu báo lỗi gọi đúng tên ô người dùng nhìn thấy trên màn hình.
LINE_FIELD_LABELS = {
    "product_code": "Mã hàng", "product_name": "Tên hàng", "item_group": "Phân loại",
    "spec": "Xuất xứ / TSKT / chất liệu", "fg_code": "Mã HH (thành phẩm)",
    "fg_name": "Tên HH (thành phẩm)", "invoice_no": "Số hóa đơn", "invoice_date": "Ngày hóa đơn",
    "supplier_ready": "NCC có sẵn hàng", "required_date": "Ngày yêu cầu có hàng",
    "unit": "ĐVT", "qty_request": "SL yêu cầu", "qty_order": "SL đặt NCC",
    "price": "Đơn giá", "vat": "VAT (%)",
    "currency": "Đồng tiền", "exchange_rate": "Tỷ giá",
    "weight_kg": "Khối lượng (kg)", "dimension": "Quy cách / kích thước",
}
ORDER_FIELD_LABELS = {
    "misa_code": "Số hóa đơn (MISA)", "pr_code": "Mã YCMH nguồn", "survey_code": "Mã YCBG nguồn",
    "company_id": "Pháp nhân", "supplier_code": "Nhà cung cấp", "supplier_name": "Tên NCC",
    "department": "Bộ phận", "nspt": "NSPT phụ trách", "order_date": "Ngày đặt hàng",
    "vat_rate": "VAT chung", "payment_terms": "Điều khoản thanh toán", "is_urgent": "Đơn gấp",
    "note": "Ghi chú đơn",
    "order_type": "Loại đơn", "currency": "Đồng tiền đơn hàng", "exchange_rate": "Tỷ giá",
    "customs_decl_no": "Số tờ khai hải quan", "customs_decl_date": "Ngày tờ khai",
    # bao-CR-321 — điều khoản in; là nội dung đã duyệt nên KHÔNG nằm trong danh sách sửa sau duyệt
    "inspection_days": "Số ngày kiểm tra hàng", "return_days": "Số ngày đổi trả",
    "invoice_deadline": "Hạn xuất hóa đơn",
}
# Ô của ĐƠN còn sửa được sau khi duyệt: hồ sơ chứng từ (đã có endpoint riêng, cập nhật
# được cả khi đơn Hoàn thành) và mã đơn MISA (kế toán nhập/sửa sau khi đã duyệt trên phần
# mềm MISA) — mọi ô còn lại là nội dung đã được duyệt.
# bao-CR-319: tờ khai hải quan cũng nằm ở đây — tờ khai chỉ có SAU khi hàng thông quan,
# mà lúc đó đơn đã duyệt từ lâu. Khóa lại thì không đơn nhập khẩu nào ghi được số tờ khai.
ORDER_FIELDS_EDITABLE_AFTER_APPROVAL = {"document_status", "misa_code",
                            "customs_decl_no", "customs_decl_date"}

_EDIT_HINT = "Bấm 'Hủy duyệt' để đưa đơn về Nháp, chỉnh rồi gửi duyệt lại."


def _differs(old, new) -> bool:
    """So sánh giá trị cũ (DB) với giá trị gửi lên, bỏ qua khác biệt kiểu Decimal/float
    và None/chuỗi rỗng — nếu không thì lần lưu nào cũng báo 'đã sửa' dù không ai chạm vào."""
    if isinstance(old, bool) or isinstance(new, bool):
        return bool(old) != bool(new)
    if isinstance(old, (int, float, Decimal)) or isinstance(new, (int, float, Decimal)):
        try:
            return abs(float(old or 0) - float(new or 0)) > 1e-6
        except (TypeError, ValueError):
            pass
    return (str(old or "").strip()) != (str(new or "").strip())


def block_edit_approved_order(db: Session, po: PurchaseOrder, data: POUpdate) -> None:
    """Chặn mọi thay đổi ngoài danh sách cho phép khi đơn đã duyệt. So theo GIÁ TRỊ chứ
    không theo 'có gửi lên hay không': màn hình luôn gửi nguyên cả đơn mỗi lần Lưu."""
    if po.status not in APPROVED_STATUSES:
        return
    payload = data.model_dump(exclude_unset=True)
    for k, v in payload.items():
        # bao-CR-319 P3: bảng chi phí nhập khẩu KHÔNG bị khóa sau khi duyệt — hóa đơn cước,
        # tờ khai thuế, phí lưu bãi đều về sau ngày duyệt đơn hàng cả tháng. Khóa lại thì
        # không đơn nhập khẩu nào ghi được chi phí thật.
        if k in ("items", "import_costs") or k in ORDER_FIELDS_EDITABLE_AFTER_APPROVAL:
            continue
        if _differs(getattr(po, k, None), v):
            raise HTTPException(400, f"Đơn đã duyệt — không sửa được '{ORDER_FIELD_LABELS.get(k, k)}'. {_EDIT_HINT}")

    rows = payload.get("items")
    if rows is None:
        return
    existing = {it.id: it for it in items_of(db, po.id)}
    if any(not r.get("id") for r in rows):
        raise HTTPException(400, f"Đơn đã duyệt — không thêm dòng hàng mới. {_EDIT_HINT}")
    submitted_ids = {r.get("id") for r in rows}
    if set(existing) - submitted_ids:
        raise HTTPException(400, f"Đơn đã duyệt — không xóa dòng hàng. {_EDIT_HINT}")
    for r in rows:
        it = existing.get(r.get("id"))
        if it is None:
            raise HTTPException(400, "Dòng hàng không thuộc đơn này.")
        # Dòng Hoàn thành / Hủy đơn: _save_items đã bỏ qua nguyên dòng, không cần chặn thêm.
        if (it.progress_status or "") in (PROG_COMPLETED, PROG_CANCELLED):
            continue
        line_name = (it.product_name or "").strip() or (it.product_code or "").strip() or f"#{it.id}"
        for k, v in r.items():
            if k in ("id", "deliveries") or k in LINE_FIELDS_EDITABLE_AFTER_APPROVAL:
                continue
            if _differs(getattr(it, k, None), v):
                label = LINE_FIELD_LABELS.get(k, k)
                raise HTTPException(400, f"Đơn đã duyệt — dòng '{line_name}' không sửa được '{label}'. {_EDIT_HINT}")


def block_clear_misa_in_use(db: Session, po: PurchaseOrder, data: POUpdate) -> None:
    """Chặn XÓA TRẮNG Mã đơn MISA khi đã có dòng tiến qua bước cần mã đó.

    Bước 1 của máy trạng thái tiến độ dòng đòi đơn phải có mã MISA (xem `_step_ok`), mà
    `auto_advance_line` chỉ TIẾN chứ không bao giờ lùi. Nên xóa trắng ô này xong là dòng
    kẹt lại ở bậc cao trong khi điều kiện của bậc đó đã hết đúng — trên màn hiện ra cảnh
    "chưa có mã MISA mà đã Chưa gửi ĐMH cho KT".

    Sửa mã thành mã KHÁC thì vẫn cho: điều kiện "có mã" vẫn thỏa, gõ nhầm phải sửa được.
    """
    payload = data.model_dump(exclude_unset=True)
    if "misa_code" not in payload:
        return
    if (payload.get("misa_code") or "").strip():
        return
    if not (po.misa_code or "").strip():
        return

    def advanced(item: POItem) -> bool:
        #  Dòng Tạm ngưng giữ bậc cũ ở `status_before_pause` và sẽ quay lại đó khi tiếp tục.
        for value in (item.progress_status or "", item.status_before_pause or ""):
            if value in PROGRESS_ORDER and PROGRESS_ORDER.index(value) >= 1:
                return True
        return False

    stuck = [it for it in items_of(db, po.id) if advanced(it)]
    if stuck:
        names = ", ".join((it.product_code or it.product_name or f"#{it.id}") for it in stuck[:3])
        more = f" và {len(stuck) - 3} dòng nữa" if len(stuck) > 3 else ""
        raise HTTPException(400, f"Không xóa trắng được Mã đơn MISA: {len(stuck)} dòng đã tiến qua bước "
                                 f"cần mã này ({names}{more}). Nhập mã khác thì được.")


def unapprove_po(db: Session, pid: int, user_id: int, reason: str = "") -> PurchaseOrder:
    """Hủy duyệt: đưa đơn ĐÃ DUYỆT về Nháp để sửa rồi gửi duyệt lại (CR-108).

    Về Nháp chứ không về Chờ duyệt: ở Nháp màn hình mở khóa sẵn theo luồng đang có, và
    lần Gửi duyệt sau sẽ chạy lại cổng kiểm tra đủ trường (CR-095) — sửa xong mà thiếu ô
    thì không lọt lên người duyệt được.
    """
    po = get_po(db, pid)
    if po.status not in APPROVED_STATUSES:
        raise HTTPException(400, "Chỉ hủy duyệt được đơn đang ở trạng thái Đã duyệt / Nhận một phần / Đã nhận.")
    items = items_of(db, pid)
    if any(float(i.qty_received or 0) > 0 for i in items):
        raise HTTPException(400, "Đơn đã nhận hàng — không hủy duyệt được. Hàng đã vào kho và đã sinh công nợ; "
                                 "muốn dừng thì hủy từng dòng ở cột Trạng thái.")
    if any((i.progress_status or "") == PROG_COMPLETED for i in items):
        raise HTTPException(400, "Đơn có dòng đã Hoàn thành — không hủy duyệt được.")
    linked_payment_lines = db.query(PaymentRequestLine.id).join(
        PaymentRequest, PaymentRequest.id == PaymentRequestLine.request_id
    ).filter(
        PaymentRequestLine.po_code == (po.code or ""),
        PaymentRequest.status != "cancelled",
    ).first()
    if linked_payment_lines:
        raise HTTPException(400, "Đơn đã có yêu cầu thanh toán — không hủy duyệt được. "
                                 "Hủy phiếu thanh toán liên quan trước.")
    return set_status(db, pid, "draft", user_id, reason)


def update_po(db: Session, pid: int, data: POUpdate, user_id: int) -> PurchaseOrder:
    po = get_po(db, pid)
    if po.status in ("completed", "cancelled"):
        raise HTTPException(400, "Đơn đã hoàn thành/đã hủy — không sửa được. Dùng 'Nhân bản' để tạo đơn mới.")
    block_edit_approved_order(db, po, data)
    block_clear_misa_in_use(db, po, data)
    _new_pr_code = (data.model_dump(exclude_unset=True).get("pr_code") or "").strip()
    if _new_pr_code and _new_pr_code != (po.pr_code or ""):
        _ensure_pr_dispatched(db, _new_pr_code)   # CR-034: đổi sang YCMH khác cũng phải đã điều phối
    old_urgent = bool(po.is_urgent)
    for k, v in data.model_dump(exclude_unset=True, exclude={"items", "import_costs"}).items():
        setattr(po, k, v)
    # CR-086: FE cũ chỉ gửi TÊN phòng → bỏ id cũ rồi tra lại từ tên; gửi kèm id thì id thắng.
    if data.department is not None or data.department_id is not None:
        if data.department_id is None:
            po.department_id = 0
        sync_department_ref(db, po)
    # CR-087: y hệt vậy cho ô NSPT.
    if data.nspt is not None or data.nspt_id is not None:
        if data.nspt_id is None:
            po.nspt_id = 0
        sync_employee_ref(db, po, "nspt_id", "nspt")
    po.updated_by = user_id
    _save_items(db, po, data.items, user_id)
    _save_import_costs(db, po, data.import_costs, user_id)
    recompute_effects(db, po, user_id)
    db.commit()
    db.refresh(po)
    # Cờ Đơn gấp đổi → đồng bộ ngược về YCMH + các ĐMH anh em cùng pr_code (hai chiều)
    if bool(po.is_urgent) != old_urgent and po.pr_code:
        sync_urgent_group(db, po.pr_code, bool(po.is_urgent), exclude_po_id=po.id)
    record(db, user_id, ENTITY, pid, "update")
    try:
        apply_auto_progress(db, po, user_id)   # tự tiến trạng thái dòng + đồng bộ YCMH (chỉ khi có đổi)
    except Exception:
        db.rollback()   # auto-progress không được phép làm hỏng thao tác chính (đã commit)
    # LUÔN đồng bộ lại YCMH sau khi lưu ĐMH — kể cả khi trạng thái dòng KHÔNG đổi nhưng
    # SL đặt/nhận thay đổi (vd sửa SL nhận 1800→1900). apply_auto_progress chỉ sync khi có
    # đổi trạng thái nên nếu thiếu bước này, tiến độ SL bên YCMH sẽ bị cũ.
    _sync_pr(db, po.pr_code)
    db.refresh(po)
    return po


# B-06: mã cố định, xem PO_DOCUMENT_STATUS. Trước đây là ba chuỗi tiếng Việt VIẾT THƯỜNG gõ tay.
DOCUMENT_STATUSES = tuple(PO_DOCUMENT_STATUS.ordered_values)


def set_document_status(db: Session, pid: int, value: str, user_id: int) -> PurchaseOrder:
    """Task 10b: cập nhật TAY trạng thái hồ sơ chứng từ. Cho phép cả khi đơn đã hoàn thành
    (chứng từ có thể bổ sung sau khi đơn xong)."""
    value = (value or "").strip()
    if value not in DOCUMENT_STATUSES:
        raise HTTPException(400, "Trạng thái hồ sơ chứng từ không hợp lệ")
    po = get_po(db, pid)
    po.document_status = value
    po.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "document_status", value)
    db.refresh(po)
    return po


def delete_po(db: Session, pid: int, user_id: int):
    po = get_po(db, pid)
    if po.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ xóa được đơn ở trạng thái Nháp hoặc Bị từ chối. Đơn đã duyệt/xử lý hãy dùng Hủy đơn.")
    from app.modules.attachment.service import delete_attachments_for
    pairs = [("purchase_order", pid)]
    for it in items_of(db, pid):
        for d in deliveries_of(db, it.id):
            pairs.append(("delivery", d.id))
            _cleanup_delivery(db, d.id)
            db.delete(d)
        db.delete(it)
    for row in import_costs_of(db, pid):
        # Đơn nháp/từ chối chưa từng sinh nợ chi phí; có sót thì gỡ theo (chặn nếu đã chi).
        block_delete_paid_import_cost(db, row)
        db.delete(row)
    delete_attachments_for(db, pairs)
    _pr_code = po.pr_code
    db.delete(po)
    db.commit()
    # CR-074: xóa đơn xong thì dòng YCMH phải quay lại `no_po` nếu không còn
    # đơn nào khác — nên phải đồng bộ lại, lấy mã YCMH trước khi xóa.
    _sync_pr(db, _pr_code)
    record(db, user_id, ENTITY, pid, "delete")


def reopen_po(db: Session, pid: int, user_id: int) -> PurchaseOrder:
    """Mở lại đơn (từ Hoàn thành) để xử lý tiếp — trả về trạng thái theo TIẾN ĐỘ NHẬN,
    KHÔNG hạ về Nháp (giữ 'đã duyệt' để sửa/nhập Số HĐ + cập nhật tiến độ dòng ngay)."""
    po = get_po(db, pid)
    if po.status != "completed":
        raise HTTPException(400, "Chỉ mở lại đơn đã Hoàn thành.")
    items = items_of(db, pid)
    total_order = sum(float(i.qty_order or 0) for i in items)
    total_recv = sum(float(i.qty_received or 0) for i in items)
    if total_order > 0 and total_recv + 0.001 >= total_order:
        st = "received"
    elif total_recv > 0:
        st = "partial"
    else:
        st = "approved"
    return set_status(db, pid, st, user_id)


def set_status(db: Session, pid: int, status: str, user_id: int, message: str = "") -> PurchaseOrder:
    po = get_po(db, pid)
    po.status = status
    if message:
        po.approve_note = message
    po.updated_by = user_id
    # bao-CR-319 P5 — duyệt xong thì chi phí đã khai lúc lập đơn thành nợ; hủy/từ chối thì gỡ.
    sync_import_cost_payables(db, po, user_id)
    db.commit()
    record(db, user_id, ENTITY, pid, status, message)
    # Mọi đổi trạng thái ĐƠN đều ảnh hưởng việc đơn có được TÍNH vào YCMH hay không
    # (duyệt → bắt đầu tính; hủy/từ chối → thôi tính) nên luôn đồng bộ lại tiến độ dòng YCMH.
    _sync_pr(db, po.pr_code)
    db.refresh(po)
    return po


# ───────────────────────── Trường BẮT BUỘC trước khi GỬI DUYỆT ─────────────────────────
# CR-095 (phiếu hỗ trợ TK19082601): khách chốt danh sách ô phải điền xong mới được
# trình đơn. Trước đây chỉ chặn thiếu NCC và thiếu dòng hàng (CR-073), nên đơn gửi lên
# vẫn có thể trống ĐVT, kho nhận, đơn giá — người duyệt không có gì để duyệt.
#
# Chặn ở lúc GỬI DUYỆT chứ không chặn lúc LƯU: người lập thường lưu nháp nhiều lần rồi
# mới điền đủ (chờ NCC báo giá, chờ kho xác nhận). Chặn lúc lưu là ép nhập một lượt.
#
# KHÔNG có VAT trong danh sách dù khách liệt kê: cột lưu số, giá trị 0 vừa nghĩa là
# "chưa nhập" vừa nghĩa là "hàng không chịu thuế / thuế suất 0%" — hai thứ đó không phân
# biệt được, chặn thì khóa luôn mặt hàng 0% hợp lệ. Ô nào để trống KHÔNG bắt buộc thì
# giữ nguyên: xuất xứ/TSKT, mã & tên HH thành phẩm, ngày giao chứng từ cho KT, ghi chú.
REQUIRED_LINE_FIELDS: list[tuple[str, str]] = [
    ("product_code", "Mã hàng"),
    ("item_group", "Phân loại"),
    ("product_name", "Tên hàng"),
    ("invoice_name", "Tên trên hóa đơn"),
    ("required_date", "Ngày yêu cầu có hàng"),
    ("expected_date", "Ngày dự kiến có hàng"),
    ("unit", "ĐVT"),
    ("warehouse_code", "Kho nhận mặc định"),
    ("qty_request", "SL yêu cầu"),
    ("qty_order", "SL đặt NCC"),
    ("price", "Đơn giá"),
]
# Ô số: 0 ở đây là "chưa nhập" thật — dòng hàng không có số lượng hoặc không có giá thì
# không phải là dòng để đặt mua.
_NUMERIC_FIELDS = {"qty_request", "qty_order", "price"}


def missing_line_fields(item: POItem) -> list[str]:
    """Nhãn các ô còn trống của MỘT dòng hàng, theo thứ tự hiện trên màn Chi tiết dòng."""
    missing = []
    for field, label in REQUIRED_LINE_FIELDS:
        value = getattr(item, field, None)
        is_empty = float(value or 0) <= 0 if field in _NUMERIC_FIELDS else not str(value or "").strip()
        if is_empty:
            missing.append(label)
    return missing


# ───────────────────────── Máy trạng thái TIẾN ĐỘ của DÒNG ĐMH (progress_status) ─────────────────────────
# Luồng chính tuần tự; `paused`/`cancelled` là ngoại lệ bấm nút, cần lý do.
# Task 8: tách `doc_pending` (có số hóa đơn) → `doc_sent` (có ngày giao chứng từ).
#
# B-06: hai list này KHÔNG còn gõ tay — sinh từ PO_PROGRESS_STATUS để không thể lệch với bộ mã.
# `ordered_values` đã loại sẵn hai mã `is_exception`, nên `PROGRESS_ORDER.index(...)` vẫn cho đúng
# số bước như trước; `PROGRESS_EXCEPTIONS` chính là phần bị loại ra đó.
PROGRESS_ORDER = list(PO_PROGRESS_STATUS.ordered_values)
PROGRESS_EXCEPTIONS = [c.value for c in PO_PROGRESS_STATUS.codes if c.is_exception]


def is_line_paid(db: Session, po: PurchaseOrder, item: POItem) -> bool:
    """Điều kiện 'đã thanh toán dòng' = MỌI khoản nợ HÀNG (goods, không tính vận chuyển)
    của các lần giao đã nhận của dòng đều đã trả đủ (còn lại ≈ 0)."""
    from app.modules.payable.model import Payable
    ref_ids = [d.id for d in deliveries_of(db, item.id) if float(d.received_qty or 0) > 0]
    if not ref_ids:
        return False   # chưa nhận hàng thì chưa thể 'đã trả đủ'
    pays = (db.query(Payable)
            .filter(Payable.source_type == "goods", Payable.ref_type == "delivery",
                    Payable.ref_id.in_(ref_ids)).all())
    if not pays:
        return False
    return all(float(p.remaining or 0) <= 0.01 for p in pays)


# Tên trường hiển thị còn thiếu cho từng bước tiến độ (index theo PROGRESS_ORDER)
_STEP_MISSING = {
    1: "Mã đơn MISA (trên phiếu)",
    2: "Có nhận hàng (số lượng nhận > 0)",
    3: "Số hóa đơn",
    4: "Ngày giao chứng từ cho KT",
    5: "Thanh toán cho dòng (NCC sản phẩm)",
}


def _step_ok(db: Session, po: PurchaseOrder, item: POItem, ti: int) -> bool:
    """Điều kiện ĐỦ để dòng đạt bước index ti (dùng chung cho auto-advance + validate_progress)."""
    if ti <= 0:
        return True
    if ti == 1:
        return bool((po.misa_code or "").strip())
    if ti == 2:
        return float(item.qty_received or 0) > 0
    if ti == 3:   # Chưa gửi ĐMH cho KT — đã có số hóa đơn (ở lần giao hoặc ở dòng sản phẩm)
        has_deliv_inv = any(bool((d.invoice_no or "").strip()) for d in deliveries_of(db, item.id))
        return has_deliv_inv or bool((item.invoice_no or "").strip())
    if ti == 4:   # Đã gửi ĐMH cho KT — đã có ngày giao chứng từ
        return bool((item.document_delivery_date or "").strip())
    if ti == 5:   # Hoàn thành — đã thanh toán dòng
        return is_line_paid(db, po, item)
    return False


def validate_progress(db: Session, po: PurchaseOrder, item: POItem, target: str):
    """Trả (ok, missing[]): missing là TÊN TRƯỜNG hiển thị còn thiếu. Điều kiện CỘNG DỒN theo bước."""
    if target not in PROGRESS_ORDER:
        return True, []
    ti = PROGRESS_ORDER.index(target)
    missing = [_STEP_MISSING[s] for s in range(1, ti + 1) if not _step_ok(db, po, item, s)]
    return (len(missing) == 0), missing


def highest_satisfied_step(db: Session, po: PurchaseOrder, item: POItem) -> int:
    """Bước cao nhất LIÊN TỤC thỏa (dừng ở bước hụt đầu tiên — gate cộng dồn)."""
    ti = 0
    for s in range(1, len(PROGRESS_ORDER)):
        if _step_ok(db, po, item, s):
            ti = s
        else:
            break
    return ti


def auto_advance_line(db: Session, po: PurchaseOrder, item: POItem) -> bool:
    """Chỉ TIẾN (forward-only). Bỏ qua dòng ở điểm cuối/tạm ngưng. Trả True nếu có đổi."""
    if item.progress_status in (PROG_COMPLETED, PROG_CANCELLED, PROG_PAUSED):
        return False
    cur = PROGRESS_ORDER.index(item.progress_status) if item.progress_status in PROGRESS_ORDER else 0
    target = highest_satisfied_step(db, po, item)
    if target > cur:
        item.progress_status = PROGRESS_ORDER[target]
        if item.progress_status == PROG_COMPLETED:
            # Chốt LỊCH SỬ MUA HÀNG: đây là chỗ DUY NHẤT dòng vào `completed`
            # (set_item_progress chặn set tay các trạng thái trong PROGRESS_ORDER), và hàm này
            # bỏ qua dòng đã ở điểm cuối → mỗi dòng chỉ ghi snapshot đúng 1 lần.
            # Chỉ add(), caller commit cùng transaction với việc đổi progress_status.
            from app.modules.purchase_history.service import snapshot_line_safe
            snapshot_line_safe(db, po, item)
        return True
    return False


def apply_auto_progress(db: Session, po: PurchaseOrder, user_id: int | None = None) -> bool:
    """Duyệt mọi dòng → auto tiến; nếu có đổi thì commit + đồng bộ YCMH. Trả True nếu có đổi."""
    changed = False
    for item in db.query(POItem).filter(POItem.po_id == po.id).all():
        if auto_advance_line(db, po, item):
            changed = True
            record(db, user_id or 0, ENTITY, po.id, "item_progress_auto",
                   f"{item.product_name}: {item.progress_status}")
    if changed:
        db.commit()
        _sync_pr(db, po.pr_code)
    return changed


def set_item_progress(db: Session, pid: int, item_id: int, target: str, reason: str, user_id: int) -> PurchaseOrder:
    po = get_po(db, pid)
    if po.status not in ("approved", "partial", "received", "processing", "completed"):
        raise HTTPException(400, "Chỉ cập nhật tiến độ dòng khi đơn đã được duyệt.")
    item = db.query(POItem).filter(POItem.id == item_id, POItem.po_id == pid).first()
    if not item:
        raise HTTPException(404, "Không tìm thấy dòng hàng.")
    if item.progress_status in (PROG_CANCELLED, PROG_COMPLETED):
        done = "hoàn thành" if item.progress_status == PROG_COMPLETED else "hủy"
        raise HTTPException(400, f"Dòng đã {done} — không thể đổi trạng thái (điểm cuối).")

    if target == "__resume__":
        # Tiếp tục đơn từ Tạm ngưng → khôi phục trạng thái trước đó
        if item.progress_status != PROG_PAUSED:
            raise HTTPException(400, "Dòng không ở trạng thái Tạm ngưng.")
        item.progress_status = item.status_before_pause or PROG_NOT_ORDERED
        item.status_before_pause = ""
    elif target in PROGRESS_EXCEPTIONS:
        if not (reason or "").strip():
            raise HTTPException(400, f"Cần nhập lý do {PO_PROGRESS_STATUS.label_of(target).lower()}.")
        if target == PROG_PAUSED:
            item.status_before_pause = item.progress_status
        item.pause_reason = reason.strip()
        item.progress_status = target
    elif target in PROGRESS_ORDER:
        raise HTTPException(400, "Trạng thái tiến độ tự động theo dữ liệu — không đặt tay. Chỉ dùng Tạm ngưng/Hủy đơn/Tiếp tục.")
    else:
        raise HTTPException(400, "Trạng thái không hợp lệ.")

    item.updated_by = user_id
    db.commit()
    label = "Tiếp tục" if target == "__resume__" else PO_PROGRESS_STATUS.label_of(target, target)
    record(db, user_id, ENTITY, pid, "item_progress", f"{item.product_name}: {label}")
    _sync_pr(db, po.pr_code)   # đồng bộ tiến độ sang YCMH nguồn
    db.refresh(po)
    return po


def sync_urgent_group(db: Session, pr_code: str, is_urgent: bool, *, exclude_po_id: int | None = None) -> None:
    """Đồng bộ cờ Đơn gấp cho cả NHÓM: YCMH + mọi ĐMH cùng pr_code = is_urgent.

    Dùng UPDATE trực tiếp (không đi qua endpoint) nên không gây vòng lặp sync.
    exclude_po_id: bỏ qua chính ĐMH vừa lưu (đã set giá trị rồi)."""
    if not pr_code:
        return
    from app.modules.purchase_request.model import PurchaseRequest
    q = db.query(PurchaseOrder).filter(PurchaseOrder.pr_code == pr_code)
    if exclude_po_id:
        q = q.filter(PurchaseOrder.id != exclude_po_id)
    q.update({PurchaseOrder.is_urgent: is_urgent}, synchronize_session=False)
    db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code).update(
        {PurchaseRequest.is_urgent: is_urgent}, synchronize_session=False)
    db.commit()


def _sync_pr(db: Session, pr_code: str) -> None:
    """Đồng bộ tiến độ dòng ĐMH → dòng YCMH nguồn (khớp product_code) + suy lại trạng thái phiếu."""
    if not pr_code:
        return
    try:
        from app.modules.purchase_request import service as pr_service
        pr_service.sync_from_purchase_orders(db, pr_code)
    except Exception:
        pass  # sync không được phép làm hỏng thao tác chính
