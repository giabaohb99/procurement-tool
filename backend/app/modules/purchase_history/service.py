"""Lịch sử mua hàng — bản ghi có từ lúc dòng ĐMH NHẬN HÀNG, chốt khi dòng vào `completed` + truy vấn cho UI.

bao-CR-790 (chủ dự án 27/11/2026): trước đây chỉ ghi khi dòng `completed` (đã thanh toán đủ) nên phần lớn lần mua thật không có
lịch sử. Nay: hàng về kho (SL nhận > 0) là có bản ghi ĐANG MỞ, đồng bộ theo ĐMH (`sync_po_history`); dòng hoàn thành thì CHỐT
đúng bản ghi đó (`snapshot_line`), id giữ nguyên.
"""
import json
import logging
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.packaging_price_codes import LedgerLineStage

from .model import PurchaseHistory

log = logging.getLogger(__name__)

OPEN, FINAL = int(LedgerLineStage.OPEN), int(LedgerLineStage.FINAL)
PROG_CANCELLED, PROG_COMPLETED = "cancelled", "completed"   # trùng `purchase_order.base_service` (không import để khỏi vòng)


def _dec(value, places: int) -> Decimal:
    """Số về đúng độ lẻ của cột để so được với giá trị đọc từ DB (không báo "đã đổi" vì khác kiểu float / Decimal)."""
    return Decimal(str(value or 0)).quantize(Decimal(1).scaleb(-places))


def _company_name(db: Session, po) -> str:
    """Tên pháp nhân — denormalize để bảng lịch sử tự đứng được, không phụ thuộc tab_company sau này."""
    if not po.company_id:
        return ""
    from app.modules.company.model import Company
    row = db.query(Company.name).filter(Company.id == po.company_id).first()
    return row[0] if row else ""


def _line_values(po, item, company_name: str) -> dict:
    """Mọi cột của bản ghi lịch sử lấy từ ĐMH + dòng hàng (trừ giai đoạn và ngày chốt)."""
    return {
        "po_item_id": item.id,
        "po_id": po.id,
        "po_code": po.code or "",
        "product_code": item.product_code or "",
        "product_name": item.product_name or "",
        "supplier_code": po.supplier_code or "",
        "supplier_name": po.supplier_name or "",
        "company_id": po.company_id or 0,
        "company_name": company_name,
        "order_date": po.order_date or "",
        "unit": item.unit or "",
        "qty_order": _dec(item.qty_order, 3),
        "price": _dec(item.price, 4),
        "vat": _dec(item.vat, 2),
        "amount": _dec(item.amount, 2),
        "extra": json.dumps({
            # Phần "Thông tin chung" còn lại của ĐMH
            "pr_code": po.pr_code or "",
            "misa_code": po.misa_code or "",
            "nspt": po.nspt or "",
            "payment_terms": po.payment_terms or "",
            "is_urgent": bool(po.is_urgent),
            "po_note": po.note or "",
            "department": po.department or "",
            # Phần còn lại của dòng hàng
            "item_group": item.item_group or "",
            "spec": item.spec or "",
            "invoice_name": item.invoice_name or "",
            "fg_code": item.fg_code or "",
            "fg_name": item.fg_name or "",
            "qty_received": float(item.qty_received or 0),
            "required_date": item.required_date or "",
            "invoice_no": item.invoice_no or "",
            "invoice_date": item.invoice_date or "",
            "warehouse_code": item.warehouse_code or "",
            "item_note": item.note or "",
        }, ensure_ascii=False),
    }


def _apply(row: PurchaseHistory, values: dict) -> bool:
    """Ghi `values` lên bản ghi ĐÃ CÓ (id giữ nguyên). Trả True nếu có cột nào đổi."""
    changed = False
    for key, value in values.items():
        if getattr(row, key) != value:
            setattr(row, key, value)
            changed = True
    return changed


def snapshot_line(db: Session, po, item) -> PurchaseHistory | None:
    """CHỐT bản ghi lịch sử cho dòng vừa vào `completed`.

    Gọi từ `purchase_order.service.auto_advance_line` — chỉ `db.add()`, KHÔNG commit
    (caller commit trong cùng transaction với việc đổi `progress_status`).
    bao-CR-790: dòng đã có bản ghi ĐANG MỞ (sinh lúc nhận hàng) thì chụp lại số của ĐMH lên chính bản ghi đó rồi đặt ĐÃ CHỐT;
    chưa có thì chèn bản ghi đã chốt. Trả None nếu dòng này đã chốt rồi (idempotent).
    """
    obj = db.query(PurchaseHistory).filter(PurchaseHistory.po_item_id == item.id).first()
    if obj is not None and obj.line_stage == FINAL:
        return None
    values = _line_values(po, item, _company_name(db, po))
    today = date.today().strftime("%Y-%m-%d")
    if obj is None:
        obj = PurchaseHistory(**values, line_stage=FINAL, completed_at=today)
        db.add(obj)
    else:
        _apply(obj, values)
        obj.line_stage = FINAL
        obj.completed_at = today
    _record_in_price_ledger(db, obj, item)
    return obj


def _record_in_price_ledger(db: Session, history: PurchaseHistory, item) -> None:
    """duoc-CR-784: dòng lịch sử mới CHỐT dòng sổ giá của dòng ĐMH đó (cùng id, số chụp, giai đoạn `FINAL`) — không xóa / chèn lại.

    Cần `flush` để có `history.id`. Lỗi ở phần sổ giá chỉ ghi log — KHÔNG được làm mất dòng lịch sử hay chặn luồng
    tiến độ mua hàng (sổ giá dựng lại được bằng `scripts/backfill_product_price_ledger.py`).
    """
    db.flush()   # dòng lịch sử là việc chính: lỗi ở đây để luồng gọi tự xử lý như trước
    #  bao-CR-789: phần sổ giá chạy trong SAVEPOINT — lỗi CSDL giữa chừng chỉ lùi phần sổ giá, phiên vẫn dùng tiếp được
    #  (trước đây chỉ nuốt ngoại lệ, phiên có thể kẹt ở trạng thái lỗi làm hỏng luôn thao tác hoàn tất dòng ĐMH).
    savepoint = db.begin_nested()
    try:
        from app.modules.product_price.ledger_sync_service import record_history_row
        record_history_row(db, history, float(getattr(item, "exchange_rate", 0) or 0) or 1.0)
        db.flush()
        savepoint.commit()
    except Exception:
        savepoint.rollback()
        log.exception("Không ghi được sổ giá cho lịch sử mua hàng po_item_id=%s", getattr(item, "id", None))


def snapshot_line_safe(db: Session, po, item) -> None:
    """Bọc `snapshot_line` — lỗi ghi lịch sử KHÔNG được chặn luồng tiến độ mua hàng."""
    try:
        snapshot_line(db, po, item)
    except Exception:
        log.exception("Không ghi được lịch sử mua hàng cho po_item_id=%s", getattr(item, "id", None))


def line_in_history(po_counts: bool, item) -> bool:
    """Dòng ĐMH có mặt trong lịch sử mua hàng không: ĐMH được tính (đã duyệt trở đi, chưa xóa mềm), dòng chưa hủy và ĐÃ NHẬN HÀNG."""
    return po_counts and (item.progress_status or "") != PROG_CANCELLED and float(item.qty_received or 0) > 0


def sync_po_history(db: Session, po) -> dict:
    """Dựng lại các bản ghi lịch sử ĐANG MỞ của MỘT ĐMH theo đúng dòng hàng hiện tại (bao-CR-790). Không commit.

    - Dòng đủ điều kiện (`line_in_history`) chưa có bản ghi -> chèn bản ghi đang mở; có rồi mà số đã đổi (giá / SL / VAT / NCC /
      ngày / thông tin kèm) -> cập nhật đúng bản ghi đó.
    - Bản ghi đang mở mà dòng hết đủ điều kiện (dòng hủy, SL nhận về 0, dòng bị xóa, ĐMH hủy / bỏ duyệt / xóa mềm) -> xóa.
    - Bản ghi ĐÃ CHỐT không bao giờ bị đụng. Dòng đã `completed` mà chưa chốt (dữ liệu nạp thẳng tiến độ) -> chốt luôn.
    Ba truy vấn cố định mỗi đơn (dòng ĐMH, bản ghi hiện có, tên pháp nhân). Trả `{inserted, updated, deleted, finalized}`.
    """
    from app.modules.product_price.ledger_sync_service import po_counts_in_ledger
    from app.modules.purchase_order.model import POItem

    stats = {"inserted": 0, "updated": 0, "deleted": 0, "finalized": 0}
    db.flush()   # session autoflush=False ở vài nơi: dòng vừa sửa phải xuống DB trước khi đọc lại
    counts = po_counts_in_ledger(po)
    items = {it.id: it for it in db.query(POItem).filter(POItem.po_id == po.id).all()}
    existing = {r.po_item_id: r for r in db.query(PurchaseHistory).filter(
        PurchaseHistory.po_id == po.id, PurchaseHistory.po_item_id.isnot(None))}
    wanted = {item_id: it for item_id, it in items.items() if line_in_history(counts, it)}

    for item_id, row in existing.items():
        if row.line_stage == OPEN and item_id not in wanted:
            db.delete(row)
            stats["deleted"] += 1
    company_name = _company_name(db, po) if wanted else ""
    for item_id, it in wanted.items():
        row = existing.get(item_id)
        if row is not None and row.line_stage == FINAL:
            continue
        if (it.progress_status or "") == PROG_COMPLETED:
            if snapshot_line(db, po, it) is not None:
                stats["finalized"] += 1
            continue
        values = _line_values(po, it, company_name)
        if row is None:
            db.add(PurchaseHistory(**values, line_stage=OPEN, completed_at=""))
            stats["inserted"] += 1
        elif _apply(row, values):
            stats["updated"] += 1
    db.flush()
    return stats


def sync_po_history_safe(db: Session, po, commit: bool = True) -> dict:
    """Bọc `sync_po_history` trong SAVEPOINT — lỗi ở lịch sử KHÔNG được chặn hay làm hỏng thao tác chính trên ĐMH.

    `commit=True`: tự commit phần của mình (gọi sau khi thao tác chính đã commit); `commit=False`: để nơi gọi commit.
    """
    savepoint = db.begin_nested()
    try:
        stats = sync_po_history(db, po)
        savepoint.commit()
    except Exception:
        savepoint.rollback()
        log.exception("Không đồng bộ được lịch sử mua hàng cho ĐMH id=%s", getattr(po, "id", None))
        return {}
    if commit:
        db.commit()
    return stats


def list_history(db: Session, pg: dict, product_code: str = "", supplier_code: str = "",
                 search: str = "", search_by_supplier: bool = True) -> tuple[int, list]:
    """Danh sách lịch sử, mới nhất trước. Lọc theo mã SP hoặc mã NCC (dùng chung cho 2 màn).

    `search`: tìm gần đúng trên Mã PO / Tên NCC / Tên SP / Tên công ty — phục vụ ô tìm kiếm
    của popup chọn lịch sử khi lập ĐMH.

    `tim_theo_ncc=False`: BỎ tên NCC khỏi vế tìm kiếm — dùng cho người không có quyền
    `supplier.read`. Nếu vẫn cho tìm theo tên NCC thì dù đã ẩn cột, gõ tên một NCC rồi
    xem có ra dòng nào không là suy ra được ai bán mã hàng đó — che cột thôi chưa đủ.
    """
    query = db.query(PurchaseHistory)
    if product_code:
        query = query.filter(PurchaseHistory.product_code == product_code)
    if supplier_code:
        query = query.filter(PurchaseHistory.supplier_code == supplier_code)
    if search.strip():
        from sqlalchemy import or_
        kw = f"%{search.strip()}%"
        clauses = [PurchaseHistory.po_code.like(kw),
              PurchaseHistory.product_name.like(kw),
              PurchaseHistory.company_name.like(kw)]
        if search_by_supplier:
            clauses.append(PurchaseHistory.supplier_name.like(kw))
        query = query.filter(or_(*clauses))
    total = query.count()
    items = (query.order_by(PurchaseHistory.order_date.desc(), PurchaseHistory.id.desc())
             .offset(pg["offset"]).limit(pg["limit"]).all())
    return total, items


def attach_invoice_names(db: Session, rows: list[dict]) -> None:
    """Cột "Tên trên hóa đơn" của popup lịch sử (bao-CR-522); trợ lý dùng chung (bao-CR-769).

    `rows`: dict có `product_code` và `extra` (dict đã giải JSON).

    Lần mua đi qua ĐMH trên hệ chụp sẵn tên đó vào `extra.invoice_name`. Dòng DỮ LIỆU CŨ (nạp
    từ Excel, `source='legacy'`) không có cột này trong tệp gốc — lùi về tên trên hóa đơn đang khai
    ở DANH MỤC sản phẩm, gắn cờ `invoice_name_from_catalog` để giao diện ghi rõ là số danh mục
    chứ không phải tên đã xuất trên hóa đơn lần đó. MỘT truy vấn cho cả trang.
    """
    from app.modules.product.model import Product

    missing = {r["product_code"] for r in rows
               if not (r.get("extra") or {}).get("invoice_name") and r.get("product_code")}
    catalog = dict(db.query(Product.code, Product.invoice_name)
                   .filter(Product.code.in_(missing)).all()) if missing else {}
    for r in rows:
        own = ((r.get("extra") or {}).get("invoice_name") or "").strip()
        fallback = (catalog.get(r.get("product_code")) or "").strip()
        r["invoice_name"] = own or fallback
        r["invoice_name_from_catalog"] = bool(not own and fallback)
