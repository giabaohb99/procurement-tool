"""Nạp SỔ CHI TIẾT MUA HÀNG MISA (.xlsx) vào sổ giá từ màn hình (duoc-CR-784) — module 6 của Quản lý Import.

Đọc tệp đúng luật `importExcel()` của báo cáo giá NVL bản HTML: quét MỌI sheet, tìm dòng tiêu đề trong 6 dòng đầu, nhận cột
theo CHỮ tiêu đề (Ngày · Mã nhà cung cấp · Tên nhà cung cấp · Tên kho · Mã hàng · Tên hàng · ĐVT · Số lượng · Đơn giá · Giá
trị; bắt buộc Ngày, Mã hàng, Số lượng, Đơn giá). Bỏ dòng không có mã, không có ngày, số lượng 0, và mã đầu PPA / CKC / CPM /
CPN (không phải vật tư bao bì). Đơn giá trống / 0 vẫn nhận (đếm số lần mua, không làm giá).

AN TOÀN KHI NẠP TỪNG PHẦN: chỉ đụng dòng Misa có ngày NẰM TRONG khoảng ngày của tệp; dòng Misa ngoài khoảng giữ nguyên. Trong
khoảng, so theo nội dung (ngày, mã, NCC, kho, ĐVT, số lượng, đơn giá): dòng trùng khớp giữ nguyên (giữ id), dòng mới thêm, dòng
trên sổ không còn trong tệp thì bỏ. Nạp lại cùng tệp lần hai là "không đổi gì". Xong cập nhật MỐC = ngày lớn nhất của mọi dòng
Misa (`misa_cutoff.py`): tới mốc chỉ dùng Misa, sau mốc chỉ dùng đơn mua hàng ERP. Chạy thử thì lùi toàn bộ; chưa có hoàn tác
(nạp lại tệp đúng để sửa).
"""
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.import_tool.catalog_import import ImportValidationError, _persist
from app.modules.import_tool.model import ImportBatch, LogLevel
from app.modules.product_price.misa_cutoff import get_misa_cutoff, set_misa_cutoff
from app.modules.product_price.misa_ledger_import import (MAX_CODE, MAX_DECIMAL, MAX_SUPPLIER_CODE, MAX_SUPPLIER_NAME,
                                                          MAX_UNIT, MAX_WAREHOUSE_NAME, SOURCE, _VTBB_SUFFIX)
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.product_price.schema import MAX_YEAR, MIN_YEAR

from .bom_import import clean
from .import_log_collector import ImportLogCollector
from .quote_import import find_header, parse_date, parse_decimal

MAX_ROWS = 100000                         # trần tổng số dòng mọi sheet (sổ Misa một năm ~ vài chục nghìn dòng)
EXCLUDED_PREFIXES = ("PPA", "CKC", "CPM", "CPN")
COLUMNS = {
    "date": ("ngày",),
    "supplier_code": ("mã nhà cung cấp", "mã ncc"),
    "supplier_name": ("tên nhà cung cấp", "nhà cung cấp"),
    "warehouse": ("tên kho", "kho"),
    "code": ("mã hàng", "mã vtbb"),
    "name": ("tên hàng", "tên vật tư"),
    "unit": ("đvt",),
    "qty": ("số lượng",),
    "price": ("đơn giá",),
    "amount": ("giá trị",),
}
REQUIRED = ("date", "code", "qty", "price")
EXCEL_EPOCH = date(1899, 12, 30)


def _vn(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _date(v) -> date | None:
    """Ngày Misa: ô ngày, chuỗi dd/mm/yyyy, hoặc số ngày kiểu Excel (ô không định dạng ngày)."""
    if isinstance(v, (int, float)) and not isinstance(v, bool) and 20000 < v < 80000:
        d = EXCEL_EPOCH + timedelta(days=int(v))
        return d if MIN_YEAR <= d.year <= MAX_YEAR else None
    return parse_date(v)


def _sheets_with_header(wb) -> list[tuple[int, object, int, dict]]:
    found = []
    for si, ws in enumerate(wb.worksheets):
        head_row, idx = find_header(ws, COLUMNS, REQUIRED)
        if head_row:
            found.append((si, ws, head_row, idx))
    return found


def precheck(wb) -> None:
    if not _sheets_with_header(wb):
        raise ImportValidationError("Không thấy sheet nào có dòng tiêu đề đủ cột Ngày, Mã hàng, Số lượng, Đơn giá trong 6 dòng "
                                    "đầu — dùng Sổ chi tiết mua hàng xuất từ Misa hoặc tệp mẫu Nạp sổ Misa.")


def _key(r) -> tuple:
    """Khóa so nội dung một lần mua (dict tệp hoặc dòng sổ giá)."""
    get = (lambda k: r[k]) if isinstance(r, dict) else (lambda k: getattr(r, k))
    return (get("price_date"), (get("product_code") or "").upper(), (get("supplier_code") or "").upper(),
            " ".join((get("warehouse_name") or "").split()).casefold(), (get("unit") or "").strip().casefold(),
            Decimal(get("qty")).quantize(Decimal("0.001")),
            Decimal(get("price")).quantize(Decimal("0.0001")))


def _company_id(db: Session) -> int:
    """Pháp nhân gán cho dòng Misa: theo dòng Misa đang có, chưa có thì 1 (cùng mặc định với script nạp)."""
    found = db.query(L.company_id).filter(L.source_type == SOURCE).limit(1).scalar()
    return int(found or 1)


def read_rows(wb, out: ImportLogCollector, company_id: int) -> tuple[list[dict], dict]:
    """Dòng sổ giá (dict, đã xếp ngày → sheet → dòng) + số đếm các dòng bị bỏ."""
    sheets = _sheets_with_header(wb)
    total = sum(max((ws.max_row or 0) - head, 0) for _, ws, head, _ in sheets)
    if total > MAX_ROWS:
        raise ImportValidationError(f"Tệp có {_vn(total)} dòng, vượt trần {_vn(MAX_ROWS)} dòng — tách theo năm rồi nạp từng tệp.")
    stats = {"no_code": 0, "excluded": 0, "zero_qty": 0, "bad_date": 0, "bad_number": 0, "zero_price": 0}
    found = []
    for si, ws, head, idx in sheets:
        def cell(row, key, idx=idx):
            j = idx.get(key, -1)
            return row[j] if 0 <= j < len(row) else None
        for ri, row in enumerate(ws.iter_rows(values_only=True, min_row=head + 1), start=head + 1):
            code = clean(cell(row, "code")).upper()
            if not code:
                stats["no_code"] += 1
                continue
            if code[:3] in EXCLUDED_PREFIXES:
                stats["excluded"] += 1
                continue
            qty = parse_decimal(cell(row, "qty"), "0.001")
            if qty is None or qty == 0:
                stats["zero_qty"] += 1
                continue
            day = _date(cell(row, "date"))
            if day is None:
                stats["bad_date"] += 1
                out.log(ri, LogLevel.WARNING, "bad_date", f"Sheet {ws.title}: ngày '{clean(cell(row, 'date'))}' không đọc được — bỏ dòng", code)
                continue
            price = parse_decimal(cell(row, "price"), "0.0001") or Decimal("0.0000")
            if abs(qty) >= MAX_DECIMAL or abs(price) >= MAX_DECIMAL or len(code) > MAX_CODE:
                stats["bad_number"] += 1
                out.log(ri, LogLevel.ERROR, "bad_number", f"Sheet {ws.title}: mã quá dài hoặc số quá lớn — bỏ dòng", code)
                continue
            if price <= 0:
                price = Decimal("0.0000")
                stats["zero_price"] += 1
            name = _VTBB_SUFFIX.sub("", clean(cell(row, "supplier_name")))[:MAX_SUPPLIER_NAME]
            found.append(((day, si, ri), {
                "source_type": SOURCE, "doc_id": 0, "product_code": code, "company_id": company_id,
                "supplier_code": clean(cell(row, "supplier_code")).upper()[:MAX_SUPPLIER_CODE],
                "supplier_name": name or None,
                "warehouse_name": clean(cell(row, "warehouse"))[:MAX_WAREHOUSE_NAME] or None,
                "price_date": day, "price": price, "vat": Decimal("0.00"), "qty": qty,
                "unit": clean(cell(row, "unit"))[:MAX_UNIT], "_row": ri, "_sheet": ws.title}))
    found.sort(key=lambda t: t[0])
    return [r for _, r in found], stats


def run(db: Session, batch: ImportBatch, wb, apply: bool) -> None:
    precheck(wb)
    out = ImportLogCollector(", ".join(ws.title for _, ws, _, _ in _sheets_with_header(wb)))
    rows, stats = read_rows(wb, out, _company_id(db))
    if not rows:
        raise ImportValidationError("Tệp không có dòng mua hàng nào đọc được (cần Mã hàng, Ngày, Số lượng khác 0).")
    lo, hi = rows[0]["price_date"], rows[-1]["price_date"]
    in_range = db.query(L).filter(L.source_type == SOURCE, L.price_date >= lo, L.price_date <= hi).all()
    existing = Counter(_key(r) for r in in_range)
    incoming = Counter(_key(r) for r in rows)
    to_delete = existing - incoming
    to_insert = incoming - existing
    old_cutoff = get_misa_cutoff(db)

    #  Bỏ dòng sổ không còn trong tệp (đúng số bản thừa của từng nội dung).
    deleted = 0
    for r in in_range:
        k = _key(r)
        if to_delete[k] > 0:
            to_delete[k] -= 1
            deleted += 1
            if apply:
                db.delete(r)
            out.log(0, LogLevel.INFO, "misa_remove",
                    f"Bỏ lần mua {r.price_date:%d/%m/%Y} {r.product_code} giá {r.price:,.0f} (không còn trong tệp)".replace(",", "."),
                    r.product_code)
    next_id = int(db.query(func.max(L.source_id)).filter(L.source_type == SOURCE).scalar() or 0)
    inserted = 0
    for r in rows:
        k = _key(r)
        if to_insert[k] <= 0:
            continue
        to_insert[k] -= 1
        inserted += 1
        next_id += 1
        out.log(r["_row"], LogLevel.INFO, "misa_add",
                f"Sheet {r['_sheet']}: thêm lần mua {r['price_date']:%d/%m/%Y} {r['product_code']} giá {r['price']:,.0f}"
                .replace(",", "."), r["product_code"])
        if apply:
            db.add(L(source_id=next_id, **{k2: v for k2, v in r.items() if not k2.startswith("_")}))
    kept = len(rows) - inserted
    if apply:
        db.flush()
    outside_max = (db.query(func.max(L.price_date)).filter(L.source_type == SOURCE, L.price_date > hi).scalar())
    new_cutoff = max(d for d in (hi, outside_max) if d is not None)
    if apply:
        set_misa_cutoff(db, new_cutoff)
    out.counts.update(created=inserted, deleted=deleted, skipped=kept)
    skipped = ", ".join(f"{label} {_vn(stats[k])}" for k, label in (
        ("no_code", "không có mã"), ("excluded", "mã PPA / CKC / CPM / CPN"), ("zero_qty", "số lượng 0"),
        ("bad_date", "sai ngày"), ("bad_number", "số / mã lỗi")) if stats[k])
    cutoff_text = (f"Mốc sổ Misa: {old_cutoff:%d/%m/%Y} → {new_cutoff:%d/%m/%Y}." if old_cutoff
                   else f"Mốc sổ Misa mới: {new_cutoff:%d/%m/%Y}.")
    summary = (f"Tệp có {_vn(len(rows))} lần mua từ {lo:%d/%m/%Y} đến {hi:%d/%m/%Y} "
               f"({_vn(len(rows) - stats['zero_price'])} có đơn giá). Trong khoảng ngày này: giữ {_vn(kept)}, thêm "
               f"{_vn(inserted)}, bỏ {_vn(deleted)}; dòng Misa ngoài khoảng giữ nguyên. {cutoff_text}"
               + (f" Đã bỏ qua: {skipped}." if skipped else ""))
    out.logs.insert(0, {"sheet": out.sheet, "row_no": 0, "level": int(LogLevel.INFO), "category": "misa_summary",
                        "message": summary, "ref_key": "", "target_code": ""})
    out.note_dropped()
    if not apply:
        db.rollback()
    _persist(db, batch, out.counts, out.logs, [], len(rows), out.sheet)
