"""Đồng bộ SỔ GIÁ (`tab_product_price_ledger`) từ lịch sử mua hàng + dòng ĐMH (duoc-CR-784, phase 02).

Luật sổ giá:
- Nguồn 1 (`PURCHASE_HISTORY`): MỖI dòng `tab_purchase_history` một dòng sổ, chỉ chèn, không sửa. Ngoại lệ duy nhất: dòng
  lịch sử bị xóa (nạp lại dữ liệu cũ) thì dòng sổ mồ côi bị xóa theo (`sync_history_ledger`).
- Nguồn 2 (`PO_LINE`): dòng có trong sổ KHI VÀ CHỈ KHI ĐMH được tính (đã duyệt trở đi, chưa xóa mềm — cùng hai hằng của
  đồng bộ YCMH) VÀ dòng chưa hủy VÀ `product_code` khác rỗng VÀ CHƯA có dòng lịch sử cho `po_item_id` đó. Đổi giá / SL /
  VAT / NCC / ngày / tỉ giá thì cập nhật đúng dòng sổ (id giữ nguyên). Dòng vào lịch sử thì dòng nguồn 2 của nó bị xóa.
- Giá sổ = giá dòng x tỉ giá (VNĐ, chưa VAT). Lịch sử cũ coi là VNĐ. Dòng giá 0 vẫn ghi (đếm "số lần mua"), tầng tính giá
  (`price_state_service`) bỏ qua.
- Thành tiền `amount` (VNĐ, chưa VAT): nguồn 1 = `tab_purchase_history.amount` (đã gồm VAT, tính theo SL thực nhận lúc dòng hoàn
  thành) bỏ VAT rồi x tỉ giá; = 0 / trống thì NULL. Nguồn 2 luôn NULL: `tab_po_item.amount` chỉ tính trên SL ĐÃ NHẬN nên với đơn
  đang mở nó lệch với SL đặt đang hiện — màn hình dùng giá x SL đặt. Nguồn 3 (Misa) lấy từ cột "Giá trị" của tệp.

Lỗi ở hook KHÔNG được chặn luồng mua hàng: `sync_po_price_ledger` bọc try / except + log, giống `_sync_pr`.
"""
import json
import logging
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, aliased

from app.core.packaging_price_codes import PriceSourceType
from app.modules.catalog.model import Warehouse
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_order.model import POItem, PurchaseOrder

from .model import ProductPriceLedger

log = logging.getLogger(__name__)

PROG_CANCELLED = "cancelled"          # trùng `purchase_order.base_service.PROG_CANCELLED` (không import để khỏi vòng)
MIN_YEAR, MAX_YEAR = 1990, 2100       # ngày ngoài dải này coi là ngày hỏng, bỏ dòng
MAX_WAREHOUSE_NAME = 200              # cột `warehouse_name` String(200); tên kho trong danh mục được tới 255
MAX_PRICE = Decimal("9999999999999")  # cột Numeric(18,4): quá trần thì bỏ dòng thay vì làm nổ cả lượt lưu ĐMH
BATCH = 1000
_Q4 = Decimal("0.0001")
_Q2 = Decimal("0.01")
MAX_AMOUNT = Decimal("9999999999999999")   # cột Numeric(18,2): quá trần thì để NULL (màn hình dùng giá x SL)


def parse_ledger_date(text: str | None) -> date | None:
    """Chuỗi 'YYYY-MM-DD' -> ngày hợp lệ trong dải 1990..2100; còn lại None (ngày hỏng)."""
    try:
        d = datetime.strptime((text or "").strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    return d if MIN_YEAR <= d.year <= MAX_YEAR else None


def _rate(value) -> Decimal:
    """Tỉ giá nhân được: trống / 0 đọc thành 1 (cùng luật `normalize_rate` của ĐMH)."""
    r = Decimal(str(value or 0))
    return r if r > 0 else Decimal(1)


def _to_vnd(price, rate) -> Decimal:
    return (Decimal(str(price or 0)) * _rate(rate)).quantize(_Q4)


def history_amount(ph: PurchaseHistory, rate) -> Decimal | None:
    """Thành tiền VNĐ CHƯA VAT của dòng lịch sử = tiền dòng (đã gồm VAT) / (1 + VAT%) x tỉ giá; 0 / trống / quá trần -> None."""
    gross = Decimal(str(ph.amount or 0))
    if gross == 0:
        return None
    value = (gross / (1 + Decimal(str(ph.vat or 0)) / 100) * _rate(rate)).quantize(_Q2)
    return value if abs(value) < MAX_AMOUNT else None


def warehouse_label(code: str | None, names: dict[str, str] | None = None) -> str | None:
    """Tên kho hiện ra trên sổ giá: tên trong danh mục kho theo mã; mã không có trong danh mục thì giữ chính mã; trống -> None."""
    code = (code or "").strip()
    if not code:
        return None
    return ((names or {}).get(code) or code).strip()[:MAX_WAREHOUSE_NAME] or None


def load_warehouse_names(db: Session) -> dict[str, str]:
    """`{mã kho: tên kho}` — MỘT truy vấn, bảng danh mục nhỏ (kho đang dùng thắng khi trùng mã)."""
    rows = db.query(Warehouse.code, Warehouse.name).order_by(Warehouse.is_active.asc(), Warehouse.id.desc()).all()
    return {(c or "").strip(): (n or "").strip() for c, n in rows if (c or "").strip()}


def history_warehouse_code(ph: PurchaseHistory) -> str:
    """Mã kho của dòng lịch sử: nằm trong JSON `extra` (khóa `warehouse_code`); JSON hỏng / thiếu khóa -> rỗng."""
    try:
        data = json.loads(ph.extra or "{}")
    except (TypeError, ValueError):
        return ""
    value = data.get("warehouse_code") if isinstance(data, dict) else ""
    return value.strip() if isinstance(value, str) else ""


def values_from_history(ph: PurchaseHistory, rate, warehouse_names: dict[str, str] | None = None) -> dict | None:
    """Giá trị dòng sổ nguồn 1 từ một dòng lịch sử; None nếu thiếu mã hàng / ngày hỏng / giá quá trần."""
    price_date = parse_ledger_date(ph.order_date)
    price = _to_vnd(ph.price, rate)
    if not (ph.product_code or "").strip() or price_date is None or abs(price) > MAX_PRICE:
        return None
    return {"source_type": int(PriceSourceType.PURCHASE_HISTORY), "source_id": ph.id, "doc_id": ph.po_id or 0,
            "product_code": ph.product_code.strip(), "supplier_code": ph.supplier_code or "",
            "company_id": ph.company_id or 0, "price_date": price_date, "price": price,
            "vat": Decimal(str(ph.vat or 0)), "qty": Decimal(str(ph.qty_order or 0)), "unit": ph.unit or "",
            "amount": history_amount(ph, rate) if price > 0 else None,
            "warehouse_name": warehouse_label(history_warehouse_code(ph), warehouse_names)}


def values_from_line(po: PurchaseOrder, item: POItem, warehouse_name: str | None = None) -> dict | None:
    """Giá trị dòng sổ nguồn 2 từ một dòng ĐMH; None nếu dòng không đủ điều kiện vào sổ.

    `warehouse_name` = tên kho trong danh mục ứng với `item.warehouse_code` (nơi gọi nối sẵn, không tra từng dòng).
    """
    price_date = parse_ledger_date(po.order_date)
    price = _to_vnd(item.price, item.exchange_rate)
    if not (item.product_code or "").strip() or price_date is None or abs(price) > MAX_PRICE:
        return None
    if (item.progress_status or "") == PROG_CANCELLED:
        return None
    return {"source_type": int(PriceSourceType.PO_LINE), "source_id": item.id, "doc_id": po.id,
            "product_code": item.product_code.strip(), "supplier_code": po.supplier_code or "",
            "company_id": po.company_id or 0, "price_date": price_date, "price": price,
            "vat": Decimal(str(item.vat or 0)), "qty": Decimal(str(item.qty_order or 0)), "unit": item.unit or "",
            "warehouse_name": warehouse_label(item.warehouse_code, {(item.warehouse_code or "").strip(): warehouse_name or ""})}


def po_counts_in_ledger(po: PurchaseOrder) -> bool:
    """ĐMH có được tính vào sổ giá không: đã duyệt trở đi, chưa xóa mềm (cùng hằng với đồng bộ YCMH)."""
    from app.modules.purchase_request.line_status_service import PO_DEAD_STATUSES, PO_PENDING_STATUSES
    return (not po.is_deleted) and (po.status or "") not in (*PO_PENDING_STATUSES, *PO_DEAD_STATUSES)


def _same(row: ProductPriceLedger, values: dict) -> bool:
    return all(getattr(row, k) == v for k, v in values.items())


def record_history_row(db: Session, ph: PurchaseHistory, exchange_rate=1) -> bool:
    """Chèn dòng sổ nguồn 1 cho một dòng lịch sử MỚI + xóa dòng nguồn 2 cùng `po_item_id`. Không commit.

    Gọi từ `snapshot_line` SAU `db.add(ph)` + `db.flush()` (có id). Kiểm tồn tại TRƯỚC khi chèn (không dựa vào lỗi unique:
    một lần flush hỏng giữa `auto_advance_line` làm hỏng cả phiên). Trả True nếu chèn dòng mới.
    """
    code = history_warehouse_code(ph)
    #  Một truy vấn theo khóa duy nhất, chỉ khi dòng có mã kho (mỗi dòng lịch sử mới chỉ ghi một lần, lúc dòng ĐMH hoàn thành)
    found = db.query(Warehouse.name).filter(Warehouse.code == code).first() if code else None
    names = {code: (found[0] or "").strip()} if found else {}
    values = values_from_history(ph, exchange_rate, names)
    if values is None:
        #  Dòng lịch sử hỏng (ngày sai / mã trống / giá quá trần) KHÔNG vào được sổ — giữ nguyên dòng nguồn 2 để giá
        #  không biến mất; `sync_history_ledger` đếm dòng này ở `skipped_bad_row` / `skipped_bad_date`.
        return False
    if ph.po_item_id:
        db.execute(delete(ProductPriceLedger).where(
            ProductPriceLedger.source_type == int(PriceSourceType.PO_LINE),
            ProductPriceLedger.source_id == ph.po_item_id))
    exists = db.query(ProductPriceLedger.id).filter(
        ProductPriceLedger.source_type == int(PriceSourceType.PURCHASE_HISTORY),
        ProductPriceLedger.source_id == ph.id).first()
    if exists:
        return False
    db.add(ProductPriceLedger(**values))
    return True


def sync_po_price_ledger(db: Session, po: PurchaseOrder, commit: bool = True) -> dict:
    """Dựng lại tập dòng sổ nguồn 2 của MỘT đơn rồi chèn / cập nhật / xóa phần chênh lệch.

    BA truy vấn cố định mỗi đơn (dòng ĐMH, id lịch sử, dòng sổ hiện có) — không phụ thuộc số dòng. Lỗi không ném ra
    (không được chặn luồng mua hàng): ghi log, và khi `commit=True` thì lùi phần của mình. Trả `{inserted, updated, deleted}`.
    """
    stats = {"inserted": 0, "updated": 0, "deleted": 0}
    try:
        db.flush()   # session autoflush=False ở vài nơi: dòng vừa sửa phải xuống DB trước khi đọc lại
        desired: dict[int, dict] = {}
        if po_counts_in_ledger(po):
            #  Tên kho nối thẳng vào truy vấn dòng ĐMH (không thêm truy vấn): `warehouse_code` trùng danh mục thì lấy tên
            rows = (db.query(POItem, Warehouse.name).outerjoin(Warehouse, Warehouse.code == POItem.warehouse_code)
                    .filter(POItem.po_id == po.id).all())
            items = [it for it, _ in rows]
            wh_names = {it.id: name for it, name in rows}
            #  "đã có lịch sử" CHỈ tính dòng lịch sử đã vào được sổ giá (nguồn 1) — lịch sử hỏng ngày thì dòng ĐMH ở lại
            covered = {r[0] for r in db.query(PurchaseHistory.po_item_id).join(
                ProductPriceLedger, (ProductPriceLedger.source_type == int(PriceSourceType.PURCHASE_HISTORY))
                & (ProductPriceLedger.source_id == PurchaseHistory.id)).filter(
                PurchaseHistory.po_item_id.in_([i.id for i in items] or [0])).all()}
            for it in items:
                if it.id in covered:
                    continue
                values = values_from_line(po, it, wh_names.get(it.id))
                if values is not None:
                    desired[it.id] = values
        existing = {r.source_id: r for r in db.query(ProductPriceLedger).filter(
            ProductPriceLedger.source_type == int(PriceSourceType.PO_LINE), ProductPriceLedger.doc_id == po.id)}
        for sid, row in existing.items():
            if sid not in desired:
                db.delete(row)
                stats["deleted"] += 1
        for sid, values in desired.items():
            row = existing.get(sid)
            if row is None:
                db.add(ProductPriceLedger(**values))
                stats["inserted"] += 1
            elif not _same(row, values):
                for k, v in values.items():
                    setattr(row, k, v)
                row.synced_at = datetime.utcnow()
                stats["updated"] += 1
        if commit:
            db.commit()
    except Exception:  # noqa: BLE001 — hook không được làm hỏng thao tác chính
        log.exception("Không đồng bộ được sổ giá cho ĐMH id=%s", getattr(po, "id", None))
        if commit:
            db.rollback()
    return stats


def _refresh_history_warehouse(db: Session, wh_names: dict[str, str]) -> int:
    """Điền / sửa `warehouse_name` cho dòng sổ nguồn 1 ĐÃ CÓ (chèn từ trước khi sổ có cột kho, hoặc đổi tên kho trong danh mục).

    Chỉ quét dòng lịch sử có mã kho khác rỗng trong `extra` (vài chục / vài trăm dòng), theo lô khóa id — không truy vấn từng dòng.
    """
    src1, count, last_id = int(PriceSourceType.PURCHASE_HISTORY), 0, 0
    L, PH = ProductPriceLedger, PurchaseHistory
    while True:
        rows = (db.query(PH, L).join(L, (L.source_type == src1) & (L.source_id == PH.id))
                .filter(PH.id > last_id, PH.extra.contains('"warehouse_code": "'), ~PH.extra.contains('"warehouse_code": ""'))
                .order_by(PH.id.asc()).limit(BATCH).all())
        if not rows:
            return count
        for ph, row in rows:
            last_id = max(last_id, ph.id)
            wanted = warehouse_label(history_warehouse_code(ph), wh_names)
            if row.warehouse_name != wanted:
                row.warehouse_name = wanted
                row.synced_at = datetime.utcnow()
                count += 1
        db.flush()


def _refresh_history_amount(db: Session) -> int:
    """Điền `amount` cho dòng sổ nguồn 1 ĐÃ CÓ mà chưa có thành tiền (chèn từ trước khi sổ có cột này).

    Chỉ quét dòng sổ `amount IS NULL` mà dòng lịch sử có tiền khác 0, theo lô khóa id; tỉ giá lấy LEFT JOIN `tab_po_item`
    (thiếu -> 1) như lúc chèn. Dòng tính ra None (tiền 0 / quá trần) vẫn NULL và không bị quét lại trong cùng lượt.
    """
    src1, count, last_id = int(PriceSourceType.PURCHASE_HISTORY), 0, 0
    L, PH = ProductPriceLedger, PurchaseHistory
    while True:
        rows = (db.query(PH, L, POItem.exchange_rate).join(L, (L.source_type == src1) & (L.source_id == PH.id))
                .outerjoin(POItem, POItem.id == PH.po_item_id)
                .filter(PH.id > last_id, L.amount.is_(None), PH.amount != 0).order_by(PH.id.asc()).limit(BATCH).all())
        if not rows:
            return count
        for ph, row, rate in rows:
            last_id = max(last_id, ph.id)
            wanted = history_amount(ph, rate) if row.price > 0 else None
            if wanted is not None:
                row.amount = wanted
                row.synced_at = datetime.utcnow()
                count += 1
        db.flush()


def sync_history_ledger(db: Session, dry_run: bool = False) -> dict:
    """Toàn bảng: xóa dòng sổ nguồn 1 mồ côi, chèn dòng lịch sử còn thiếu (lô 1000), xóa nguồn 2 đã có lịch sử.

    Tỉ giá lấy LEFT JOIN `tab_po_item` (dòng cũ / thiếu ĐMH → 1, có đếm). `dry_run=True` vẫn ghi vào phiên để đếm đúng
    rồi `rollback` — nơi gọi không phải commit. Không commit khi không phải dry-run; nơi gọi tự commit.
    """
    from app.modules.product_price import ledger_stats
    stats = ledger_stats.new_stats()
    src1, src2 = int(PriceSourceType.PURCHASE_HISTORY), int(PriceSourceType.PO_LINE)
    L, PH = ProductPriceLedger, PurchaseHistory

    # 1) mồ côi: dòng sổ nguồn 1 mà dòng lịch sử đã biến mất (nạp lại dữ liệu cũ)
    orphan_ids = [r[0] for r in db.query(L.id).outerjoin(PH, PH.id == L.source_id)
                  .filter(L.source_type == src1, PH.id.is_(None)).all()]
    for i in range(0, len(orphan_ids), BATCH):
        db.execute(delete(L).where(L.id.in_(orphan_ids[i:i + BATCH])))
    stats["deleted_orphans"] = len(orphan_ids)

    # 3) dòng lịch sử còn thiếu trong sổ (danh mục kho nạp MỘT lần cho cả lượt, tra mã -> tên trong bộ nhớ)
    wh_names = load_warehouse_names(db)
    last_id = 0
    while True:
        rows = (db.query(PH, POItem.exchange_rate, POItem.id)
                .outerjoin(L, (L.source_type == src1) & (L.source_id == PH.id))
                .outerjoin(POItem, POItem.id == PH.po_item_id)
                .filter(L.id.is_(None), PH.id > last_id).order_by(PH.id.asc()).limit(BATCH).all())
        if not rows:
            break
        for ph, rate, item_id in rows:
            last_id = max(last_id, ph.id)
            ledger_stats.count_history_row(stats, ph, rate, item_id)
            values = values_from_history(ph, rate, wh_names)
            if values is None:
                stats["skipped_bad_row"] += 1
                if parse_ledger_date(ph.order_date) is None:
                    stats["skipped_bad_date"] += 1
                continue
            db.add(L(**values))
            stats["inserted"] += 1
        db.flush()
    db.flush()
    stats["updated_warehouse"] = _refresh_history_warehouse(db, wh_names)
    stats["updated_amount"] = _refresh_history_amount(db)
    # 4) dòng nguồn 2 mà `po_item_id` đã có dòng lịch sử TRONG SỔ -> xóa (lịch sử là bản chốt cuối). Chạy SAU bước 3 để lịch sử
    #    vừa chèn đã có mặt; dòng lịch sử hỏng (không vào sổ) thì KHÔNG xóa dòng ĐMH — giá không được biến mất.
    hist = aliased(L)
    covered_ids = [r[0] for r in db.query(L.id).join(PH, PH.po_item_id == L.source_id)
                   .join(hist, (hist.source_type == src1) & (hist.source_id == PH.id))
                   .filter(L.source_type == src2).all()]
    for i in range(0, len(covered_ids), BATCH):
        db.execute(delete(L).where(L.id.in_(covered_ids[i:i + BATCH])))
    stats["deleted_covered_po_lines"] = len(covered_ids)

    stats["ledger_rows"] = db.query(func.count(L.id)).scalar() or 0
    if dry_run:
        db.rollback()
    return stats


def eligible_po_ids(db: Session) -> list[int]:
    """Id ĐMH cần dựng lại nguồn 2: đơn được tính HOẶC đơn còn dòng sổ nguồn 2 (có thể đã hết đủ điều kiện)."""
    from app.modules.purchase_request.line_status_service import PO_DEAD_STATUSES, PO_PENDING_STATUSES
    live = select(PurchaseOrder.id).where(PurchaseOrder.is_deleted.is_(False),
                                          PurchaseOrder.status.notin_([*PO_PENDING_STATUSES, *PO_DEAD_STATUSES]))
    stale = select(ProductPriceLedger.doc_id).where(
        ProductPriceLedger.source_type == int(PriceSourceType.PO_LINE)).distinct()
    return sorted({r[0] for r in db.execute(live).all()} | {r[0] for r in db.execute(stale).all()})
