"""Đồng bộ SỔ GIÁ (`tab_product_price_ledger`) từ lịch sử mua hàng + dòng ĐMH (duoc-CR-784, phase 02 + gộp nguồn `srcmerge784`).

Luật sổ giá (một lần mua của hệ thống = MỘT dòng sổ theo `po_item_id` suốt đời, id giữ nguyên):
- Dòng ĐMH (`PO_LINE`, `source_id` = `tab_po_item.id`): có trong sổ KHI VÀ CHỈ KHI ĐMH được tính (đã duyệt trở đi, chưa xóa mềm — cùng hai
  hằng của đồng bộ YCMH) VÀ dòng chưa hủy VÀ `product_code` khác rỗng. Giai đoạn `OPEN`: đổi giá / SL / VAT / NCC / ngày / tỉ giá thì cập
  nhật đúng dòng sổ (`sync_po_price_ledger`). Dòng hoàn thành (`snapshot_line` -> `record_history_row`) được cập nhật bằng số CHỤP của lịch
  sử rồi đặt `FINAL` — không xóa, không chèn lại. Dòng `FINAL` là bản chốt: đồng bộ theo ĐMH bỏ qua hẳn (không cập nhật, không xóa),
  kể cả khi ĐMH sau đó bị hủy / xóa mềm.
- Lịch sử cũ nạp từ Excel (`PURCHASE_HISTORY`, `source_id` = `tab_purchase_history.id`, `po_item_id` trống): chỉ chèn, luôn `FINAL`. Ngoại
  lệ duy nhất: dòng lịch sử bị xóa (nạp lại dữ liệu cũ) thì dòng sổ mồ côi bị xóa theo (`sync_history_ledger`).
- bao-CR-790: lịch sử mua hàng nay có bản ghi ĐANG MỞ từ lúc nhận hàng (`tab_purchase_history.line_stage = 1`). Bản ghi đó KHÔNG
  chốt dòng sổ: dòng sổ vẫn đang mở và đi theo ĐMH; chỉ bản ghi lịch sử ĐÃ CHỐT (dòng hoàn thành, dữ liệu cũ) mới chốt dòng sổ.
- Giá sổ = giá dòng x tỉ giá (VNĐ, chưa VAT). Lịch sử cũ coi là VNĐ. Dòng giá 0 vẫn ghi (đếm "số lần mua"), tầng tính giá
  (`price_state_service`) bỏ qua.
- Thành tiền `amount` (VNĐ, chưa VAT): dòng chốt từ lịch sử = `tab_purchase_history.amount` (đã gồm VAT, tính theo SL thực nhận lúc dòng hoàn
  thành) bỏ VAT rồi x tỉ giá; = 0 / trống thì NULL. Dòng ĐMH đang mở luôn NULL: `tab_po_item.amount` chỉ tính trên SL ĐÃ NHẬN nên với đơn
  đang mở nó lệch với SL đặt đang hiện — màn hình dùng giá x SL đặt. Nguồn 3 (Misa) lấy từ cột "Giá trị" của tệp.

Lỗi ở hook KHÔNG được chặn luồng mua hàng: `sync_po_price_ledger` bọc try / except + log, giống `_sync_pr`.
"""
import json
import logging
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import and_, case, delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.core.packaging_price_codes import LedgerLineStage, PriceSourceType
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
SRC_HISTORY, SRC_PO = int(PriceSourceType.PURCHASE_HISTORY), int(PriceSourceType.PO_LINE)
OPEN, FINAL = int(LedgerLineStage.OPEN), int(LedgerLineStage.FINAL)


def history_ledger_key(ph: PurchaseHistory) -> tuple[int, int]:
    """`(source_type, source_id)` của dòng sổ ứng với một dòng lịch sử: có ĐMH thì là dòng ĐMH, lịch sử cũ thì là chính nó."""
    return (SRC_PO, ph.po_item_id) if ph.po_item_id is not None else (SRC_HISTORY, ph.id)


def history_join(L, PH):
    """Điều kiện nối dòng sổ `L` với dòng lịch sử `PH` — cùng luật khóa với `history_ledger_key`, viết bằng SQL."""
    return and_(L.source_type == case((PH.po_item_id.is_(None), SRC_HISTORY), else_=SRC_PO),
                L.source_id == func.coalesce(PH.po_item_id, PH.id))


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
    """Giá trị dòng sổ CHỐT (`FINAL`) từ một dòng lịch sử: dòng ĐMH (có `po_item_id`) hoặc lịch sử cũ; None nếu thiếu mã hàng / ngày hỏng / giá quá trần."""
    price_date = parse_ledger_date(ph.order_date)
    price = _to_vnd(ph.price, rate)
    if not (ph.product_code or "").strip() or price_date is None or abs(price) > MAX_PRICE:
        return None
    source_type, source_id = history_ledger_key(ph)
    return {"source_type": source_type, "source_id": source_id, "line_stage": FINAL, "doc_id": ph.po_id or 0,
            "product_code": ph.product_code.strip(), "supplier_code": ph.supplier_code or "",
            "company_id": ph.company_id or 0, "price_date": price_date, "price": price,
            "vat": Decimal(str(ph.vat or 0)), "qty": Decimal(str(ph.qty_order or 0)), "unit": ph.unit or "",
            "amount": history_amount(ph, rate) if price > 0 else None,
            "warehouse_name": warehouse_label(history_warehouse_code(ph), warehouse_names)}


def values_from_line(po: PurchaseOrder, item: POItem, warehouse_name: str | None = None) -> dict | None:
    """Giá trị dòng sổ ĐANG MỞ (`OPEN`) từ một dòng ĐMH; None nếu dòng không đủ điều kiện vào sổ.

    `warehouse_name` = tên kho trong danh mục ứng với `item.warehouse_code` (nơi gọi nối sẵn, không tra từng dòng).
    """
    price_date = parse_ledger_date(po.order_date)
    price = _to_vnd(item.price, item.exchange_rate)
    if not (item.product_code or "").strip() or price_date is None or abs(price) > MAX_PRICE:
        return None
    if (item.progress_status or "") == PROG_CANCELLED:
        return None
    return {"source_type": SRC_PO, "source_id": item.id, "line_stage": OPEN, "doc_id": po.id,
            "product_code": item.product_code.strip(), "supplier_code": po.supplier_code or "",
            "company_id": po.company_id or 0, "price_date": price_date, "price": price,
            "vat": Decimal(str(item.vat or 0)), "qty": Decimal(str(item.qty_order or 0)), "unit": item.unit or "",
            "amount": None,   # đang mở: thành tiền chỉ có khi chốt (dòng trả về OPEN từ FINAL cũng được xóa số chốt)
            "warehouse_name": warehouse_label(item.warehouse_code, {(item.warehouse_code or "").strip(): warehouse_name or ""})}


def po_counts_in_ledger(po: PurchaseOrder) -> bool:
    """ĐMH có được tính vào sổ giá không: đã duyệt trở đi, chưa xóa mềm (cùng hằng với đồng bộ YCMH)."""
    from app.modules.purchase_request.line_status_service import PO_DEAD_STATUSES, PO_PENDING_STATUSES
    return (not po.is_deleted) and (po.status or "") not in (*PO_PENDING_STATUSES, *PO_DEAD_STATUSES)


def _same(row: ProductPriceLedger, values: dict) -> bool:
    return all(getattr(row, k) == v for k, v in values.items())


def _apply(row: ProductPriceLedger, values: dict) -> None:
    """Ghi `values` lên một dòng sổ ĐÃ CÓ (id giữ nguyên) và đóng dấu giờ đồng bộ."""
    for k, v in values.items():
        setattr(row, k, v)
    row.synced_at = func.now()


def record_history_row(db: Session, ph: PurchaseHistory, exchange_rate=1) -> bool:
    """Chốt dòng sổ cho một dòng lịch sử MỚI. Không commit. Trả True nếu chèn dòng mới hoặc nâng dòng đang mở lên `FINAL`.

    Gọi từ `snapshot_line` SAU `db.add(ph)` + `db.flush()` (có id). Dòng ĐMH (có `po_item_id`): cập nhật ĐÚNG dòng sổ `(PO_LINE, po_item_id)`
    bằng số chụp của lịch sử rồi đặt `FINAL` (id giữ nguyên); ĐMH chưa từng vào sổ thì chèn dòng `FINAL`. Kiểm tồn tại TRƯỚC khi chèn
    (không dựa vào lỗi unique: một lần flush hỏng giữa `auto_advance_line` làm hỏng cả phiên). Dòng đã `FINAL` thì giữ nguyên.
    """
    code = history_warehouse_code(ph)
    #  Một truy vấn theo khóa duy nhất, chỉ khi dòng có mã kho (mỗi dòng lịch sử mới chỉ ghi một lần, lúc dòng ĐMH hoàn thành)
    found = db.query(Warehouse.name).filter(Warehouse.code == code).first() if code else None
    names = {code: (found[0] or "").strip()} if found else {}
    values = values_from_history(ph, exchange_rate, names)
    if values is None:
        #  Dòng lịch sử hỏng (ngày sai / mã trống / giá quá trần) KHÔNG vào được sổ — giữ nguyên dòng đang mở để giá
        #  không biến mất; `sync_history_ledger` đếm dòng này ở `skipped_bad_row` / `skipped_bad_date`.
        return False
    row = db.query(ProductPriceLedger).filter(ProductPriceLedger.source_type == values["source_type"],
                                              ProductPriceLedger.source_id == values["source_id"]).first()
    if row is None:
        db.add(ProductPriceLedger(**values))
        return True
    if row.line_stage == FINAL:
        return False
    _apply(row, values)
    return True


def sync_po_price_ledger(db: Session, po: PurchaseOrder, commit: bool = True) -> dict:
    """Dựng lại tập dòng sổ ĐANG MỞ của MỘT đơn rồi chèn / cập nhật / xóa phần chênh lệch; dòng `FINAL` bị bỏ qua hẳn.

    HAI truy vấn cố định mỗi đơn (dòng ĐMH kèm tên kho, dòng sổ hiện có) — không phụ thuộc số dòng. Lỗi không ném ra
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
            for it, wh_name in rows:
                values = values_from_line(po, it, wh_name)
                if values is not None:
                    desired[it.id] = values
        existing = {r.source_id: r for r in db.query(ProductPriceLedger).filter(
            ProductPriceLedger.source_type == SRC_PO, ProductPriceLedger.doc_id == po.id)}
        for sid, row in existing.items():
            if row.line_stage == OPEN and sid not in desired:
                db.delete(row)
                stats["deleted"] += 1
        for sid, values in desired.items():
            row = existing.get(sid)
            if row is None:
                db.add(ProductPriceLedger(**values))
                stats["inserted"] += 1
            elif row.line_stage == OPEN and not _same(row, values):
                _apply(row, values)
                stats["updated"] += 1
        if commit:
            db.commit()
    except Exception:  # noqa: BLE001 — hook không được làm hỏng thao tác chính
        log.exception("Không đồng bộ được sổ giá cho ĐMH id=%s", getattr(po, "id", None))
        if commit:
            db.rollback()
    return stats


def _refresh_history_warehouse(db: Session, wh_names: dict[str, str]) -> int:
    """Điền / sửa `warehouse_name` cho dòng sổ CHỐT từ lịch sử ĐÃ CÓ (chèn từ trước khi sổ có cột kho, hoặc đổi tên kho trong danh mục).

    Chỉ quét dòng lịch sử có mã kho khác rỗng trong `extra` (vài chục / vài trăm dòng), theo lô khóa id — không truy vấn từng dòng.
    """
    count, last_id = 0, 0
    L, PH = ProductPriceLedger, PurchaseHistory
    while True:
        rows = (db.query(PH, L).join(L, history_join(L, PH))
                .filter(L.line_stage == FINAL, PH.id > last_id, PH.extra.contains('"warehouse_code": "'),
                        ~PH.extra.contains('"warehouse_code": ""'))
                .order_by(PH.id.asc()).limit(BATCH).all())
        if not rows:
            return count
        for ph, row in rows:
            last_id = max(last_id, ph.id)
            wanted = warehouse_label(history_warehouse_code(ph), wh_names)
            if row.warehouse_name != wanted:
                row.warehouse_name = wanted
                row.synced_at = func.now()
                count += 1
        db.flush()


def _refresh_history_amount(db: Session) -> int:
    """Điền `amount` cho dòng sổ CHỐT từ lịch sử ĐÃ CÓ mà chưa có thành tiền (chèn từ trước khi sổ có cột này).

    Chỉ quét dòng sổ `amount IS NULL` mà dòng lịch sử có tiền khác 0, theo lô khóa id; tỉ giá lấy LEFT JOIN `tab_po_item`
    (thiếu -> 1) như lúc chèn. Dòng tính ra None (tiền 0 / quá trần) vẫn NULL và không bị quét lại trong cùng lượt.
    """
    count, last_id = 0, 0
    L, PH = ProductPriceLedger, PurchaseHistory
    while True:
        rows = (db.query(PH, L, POItem.exchange_rate).join(L, history_join(L, PH))
                .outerjoin(POItem, POItem.id == PH.po_item_id)
                .filter(L.line_stage == FINAL, PH.id > last_id, L.amount.is_(None), PH.amount != 0)
                .order_by(PH.id.asc()).limit(BATCH).all())
        if not rows:
            return count
        for ph, row, rate in rows:
            last_id = max(last_id, ph.id)
            wanted = history_amount(ph, rate) if row.price > 0 else None
            if wanted is not None:
                row.amount = wanted
                row.synced_at = func.now()
                count += 1
        db.flush()


def sync_history_ledger(db: Session, dry_run: bool = False) -> dict:
    """Toàn bảng: dọn dòng sổ mồ côi, chốt dòng lịch sử còn thiếu / còn đang mở (lô 1000), điền kho + thành tiền cho dòng chốt.

    Tỉ giá lấy LEFT JOIN `tab_po_item` (dòng cũ / thiếu ĐMH → 1, có đếm). `dry_run=True` vẫn ghi vào phiên để đếm đúng
    rồi `rollback` — nơi gọi không phải commit. Không commit khi không phải dry-run; nơi gọi tự commit.
    """
    from app.modules.product_price import ledger_stats
    stats = ledger_stats.new_stats()
    L, PH = ProductPriceLedger, PurchaseHistory

    # 1) mồ côi: dòng sổ lịch sử cũ mà dòng lịch sử đã biến mất (nạp lại dữ liệu cũ), hoặc trỏ vào dòng lịch sử đã có ĐMH (sai dạng)
    orphan_ids = [r[0] for r in db.query(L.id).outerjoin(PH, PH.id == L.source_id)
                  .filter(L.source_type == SRC_HISTORY, or_(PH.id.is_(None), PH.po_item_id.is_not(None))).all()]
    for i in range(0, len(orphan_ids), BATCH):
        db.execute(delete(L).where(L.id.in_(orphan_ids[i:i + BATCH])))
    stats["deleted_orphans"] = len(orphan_ids)

    # 2) dòng ĐMH đã chốt mà không còn dòng lịch sử ĐÃ CHỐT nào trỏ `po_item_id` đó (hiếm: hoàn tác nhập ĐMH) -> trả về đang mở,
    #    để `sync_po_price_ledger` quyết giữ hay bỏ theo ĐMH
    reopen_ids = [r[0] for r in db.query(L.id).filter(
        L.source_type == SRC_PO, L.line_stage == FINAL,
        ~select(PH.id).where(PH.po_item_id == L.source_id, PH.line_stage == FINAL).exists()).all()]
    for i in range(0, len(reopen_ids), BATCH):
        db.execute(update(L).where(L.id.in_(reopen_ids[i:i + BATCH])).values(line_stage=OPEN, amount=None, synced_at=func.now()))
    stats["reopened"] = len(reopen_ids)

    # 3) dòng lịch sử ĐÃ CHỐT chưa có dòng sổ (chèn `FINAL`) hoặc dòng sổ còn đang mở (nâng lên `FINAL` bằng số chụp). Bản ghi lịch
    #    sử đang mở (bao-CR-790: đã nhận hàng, chưa hoàn thành) bị bỏ qua — dòng sổ của nó do `sync_po_price_ledger` giữ. Danh mục
    #    kho nạp MỘT lần cho cả lượt, tra mã -> tên trong bộ nhớ
    wh_names = load_warehouse_names(db)
    last_id = 0
    while True:
        rows = (db.query(PH, POItem.exchange_rate, POItem.id, L)
                .outerjoin(L, history_join(L, PH))
                .outerjoin(POItem, POItem.id == PH.po_item_id)
                .filter(or_(L.id.is_(None), L.line_stage != FINAL), PH.line_stage == FINAL, PH.id > last_id)
                .order_by(PH.id.asc()).limit(BATCH).all())
        if not rows:
            break
        for ph, rate, item_id, row in rows:
            last_id = max(last_id, ph.id)
            ledger_stats.count_history_row(stats, ph, rate, item_id)
            values = values_from_history(ph, rate, wh_names)
            if values is None:
                stats["skipped_bad_row"] += 1
                if parse_ledger_date(ph.order_date) is None:
                    stats["skipped_bad_date"] += 1
                continue
            if row is None:
                db.add(L(**values))
                stats["inserted"] += 1
            else:
                _apply(row, values)
                stats["finalized"] += 1
        db.flush()
    db.flush()
    stats["updated_warehouse"] = _refresh_history_warehouse(db, wh_names)
    stats["updated_amount"] = _refresh_history_amount(db)

    stats["ledger_rows"] = db.query(func.count(L.id)).scalar() or 0
    if dry_run:
        db.rollback()
    return stats


def eligible_po_ids(db: Session) -> list[int]:
    """Id ĐMH cần dựng lại dòng đang mở: đơn được tính HOẶC đơn còn dòng sổ đang mở (có thể đã hết đủ điều kiện)."""
    from app.modules.purchase_request.line_status_service import PO_DEAD_STATUSES, PO_PENDING_STATUSES
    live = select(PurchaseOrder.id).where(PurchaseOrder.is_deleted.is_(False),
                                          PurchaseOrder.status.notin_([*PO_PENDING_STATUSES, *PO_DEAD_STATUSES]))
    stale = select(ProductPriceLedger.doc_id).where(
        ProductPriceLedger.source_type == SRC_PO, ProductPriceLedger.line_stage == OPEN).distinct()
    return sorted({r[0] for r in db.execute(live).all()} | {r[0] for r in db.execute(stale).all()})
