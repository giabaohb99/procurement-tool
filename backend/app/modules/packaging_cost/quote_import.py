"""Nhập BÁO GIÁ VTBB hàng loạt từ Excel (duoc-CR-784) — chạy trong tác vụ nền `import_tool.run_import`, module 5.

Khuôn tệp (tải ở `import_templates.build_quote_template`): sheet đầu, dòng tiêu đề nằm trong 6 dòng đầu, nhận cột theo CHỮ
tiêu đề (không theo vị trí): **Mã VTBB** · **Đơn giá** · **Ngày hiệu lực** (bắt buộc) · Mã NCC · VAT (%) · Ghi chú.
Đơn giá VNĐ chưa VAT theo ĐVT danh mục; VAT ghi 8 (= 8%), không ghi 0,08.

Khóa một báo giá = (mã VTBB, mã NCC, ngày hiệu lực): có rồi thì cập nhật đơn giá / VAT / ghi chú (chạy thử liệt kê cũ → mới),
chưa có thì thêm. Báo giá trên hệ thống không có trong tệp GIỮ NGUYÊN. Mã VTBB phải có trong danh mục sản phẩm (cùng luật với
hộp Báo giá mới). Chạy thử thì lùi toàn bộ; không hỗ trợ hoàn tác (sửa / xóa báo giá ở màn Báo giá VTBB).
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.modules.import_tool.catalog_import import ImportValidationError, _persist
from app.modules.import_tool.model import ImportBatch, LogLevel
from app.modules.product.model import Product
from app.modules.product_price.model import ProductPriceQuote
from app.modules.product_price.schema import MAX_YEAR, MIN_YEAR

from .bom_import import clean
from .import_log_collector import ImportLogCollector

MAX_ROWS = 20000
MAX_PRICE = Decimal("1000000000000")
CODE_LEN, NOTE_LEN = 50, 500
#  Khóa cột → các chữ tiêu đề nhận được (so đầu chuỗi, không dấu cách thừa, không phân biệt hoa thường).
COLUMNS = {
    "code": ("mã vtbb", "mã hàng", "mã vật tư"),
    "price": ("đơn giá",),
    "valid_from": ("ngày hiệu lực", "hiệu lực từ", "ngày báo giá"),
    "supplier": ("mã ncc", "mã nhà cung cấp"),
    "vat": ("vat",),
    "note": ("ghi chú",),
}
REQUIRED = ("code", "price", "valid_from")
LABELS = {"code": "Mã VTBB", "price": "Đơn giá", "valid_from": "Ngày hiệu lực"}


def _norm(v) -> str:
    return " ".join(str(v or "").split()).casefold()


def find_header(ws, columns: dict, required: tuple, scan: int = 6) -> tuple[int, dict]:
    """(số dòng tiêu đề, {khóa: chỉ số cột}) — dòng đầu tiên trong `scan` dòng có đủ cột bắt buộc."""
    for i, row in enumerate(ws.iter_rows(values_only=True, max_row=scan), start=1):
        heads = [_norm(c) for c in row]
        idx = {key: next((j for j, h in enumerate(heads) if any(h.startswith(w) for w in words)), -1)
               for key, words in columns.items()}
        if all(idx[k] >= 0 for k in required):
            return i, idx
    return 0, {}


def _sheet(wb):
    return wb.worksheets[0] if wb.worksheets else None


def precheck(wb) -> None:
    ws = _sheet(wb)
    if ws is None or not find_header(ws, COLUMNS, REQUIRED)[0]:
        raise ImportValidationError("Không thấy dòng tiêu đề có đủ cột Mã VTBB, Đơn giá, Ngày hiệu lực trong 6 dòng đầu "
                                    "— dùng tệp mẫu Nhập báo giá VTBB.")


def parse_date(v) -> date | None:
    """Ô ngày: kiểu ngày của Excel, chuỗi dd/mm/yyyy hoặc yyyy-mm-dd; ngoài năm 2000–2100 coi như sai."""
    if isinstance(v, datetime):
        d = v.date()
    elif isinstance(v, date):
        d = v
    else:
        s = clean(v)
        d = None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                d = datetime.strptime(s[:10], fmt).date()
                break
            except ValueError:
                continue
    return d if d is not None and MIN_YEAR <= d.year <= MAX_YEAR else None


def parse_decimal(v, places: str) -> Decimal | None:
    """Số trong ô: số Excel, hoặc chữ kiểu Việt (1.234,5) / kiểu Anh (1,234.5). Rỗng / sai → None."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float, Decimal)):
        raw = str(v)
    else:
        s = clean(v).replace(" ", "")
        if not s:
            return None
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".") if len(s.split(",")[-1]) != 3 else s.replace(",", "")
        elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[-1]) == 3 and len(s) > 4):
            s = s.replace(".", "")
        raw = s
    try:
        n = Decimal(raw)
    except (InvalidOperation, ValueError):
        return None
    return n.quantize(Decimal(places)) if n.is_finite() else None


def format_vn_number(n: Decimal) -> str:
    """Số kiểu Việt cho nhật ký: 1234567.5 -> "1.234.567,5"; số tròn không có phần lẻ."""
    text = f"{n:,.4f}".rstrip("0").rstrip(".")
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def _show(v) -> str:
    if isinstance(v, Decimal):
        return format_vn_number(v)
    return str(v) if v not in (None, "") else "(trống)"


def run(db: Session, batch: ImportBatch, wb, apply: bool) -> None:
    precheck(wb)
    ws = _sheet(wb)
    if (ws.max_row or 0) > MAX_ROWS + 6:
        raise ImportValidationError(f"Sheet có {ws.max_row:,} dòng, vượt trần {MAX_ROWS:,} dòng — tách tệp rồi nhập lại.")
    head_row, idx = find_header(ws, COLUMNS, REQUIRED)
    out = ImportLogCollector(ws.title)
    uid = batch.created_by

    def cell(row, key):
        j = idx.get(key, -1)
        return row[j] if 0 <= j < len(row) else None

    parsed: dict[tuple, tuple[int, dict]] = {}
    total = 0
    for i, row in enumerate(ws.iter_rows(values_only=True, min_row=head_row + 1), start=head_row + 1):
        if not any(clean(c) for c in row):
            continue
        total += 1
        code = clean(cell(row, "code")).upper()
        ref = code or f"dòng {i}"
        price = parse_decimal(cell(row, "price"), "0.0001")
        day = parse_date(cell(row, "valid_from"))
        missing = [LABELS[k] for k, bad in (("code", not code), ("price", price is None or price <= 0),
                                             ("valid_from", day is None)) if bad]
        if missing:
            out.log(i, LogLevel.ERROR, "bad_row", f"Thiếu hoặc sai: {', '.join(missing)} — bỏ dòng", ref)
            continue
        if len(code) > CODE_LEN or price > MAX_PRICE:
            out.log(i, LogLevel.ERROR, "out_of_range", f"Mã dài hơn {CODE_LEN} ký tự hoặc đơn giá quá lớn — bỏ dòng", ref)
            continue
        supplier = clean(cell(row, "supplier")).upper()[:CODE_LEN]
        vat = parse_decimal(cell(row, "vat"), "0.01")
        if vat is not None and 0 < vat < 1:
            vat = (vat * 100).quantize(Decimal("0.01"))      # ghi 0,08 thì hiểu là 8%
        if vat is None or not (0 <= vat < 100):
            if clean(cell(row, "vat")):
                out.log(i, LogLevel.WARNING, "bad_vat", f"VAT '{clean(cell(row, 'vat'))}' không hợp lệ — đặt 0", ref)
            vat = Decimal("0.00")
        note = clean(cell(row, "note"))
        if len(note) > NOTE_LEN:
            note = note[:NOTE_LEN]
            out.log(i, LogLevel.WARNING, "note_cut", f"Ghi chú dài hơn {NOTE_LEN} ký tự — đã cắt", ref)
        key = (code, supplier, day)
        if key in parsed:
            out.log(i, LogLevel.WARNING, "duplicate", f"Trùng mã, NCC, ngày hiệu lực với dòng {parsed[key][0]} — lấy dòng sau", ref)
        parsed[key] = (i, {"product_code": code, "supplier_code": supplier, "price": price, "vat": vat,
                           "valid_from": day, "note": note})
    if not total:
        raise ImportValidationError("Tệp không có dòng báo giá nào dưới dòng tiêu đề.")

    codes = {k[0] for k in parsed}
    in_catalog = {c.upper() for (c,) in db.query(Product.code).filter(Product.code.in_(codes)).all()} if codes else set()
    existing = {}
    if codes:
        for q in db.query(ProductPriceQuote).filter(ProductPriceQuote.product_code.in_(codes)).all():
            existing.setdefault((q.product_code.upper(), (q.supplier_code or "").upper(), q.valid_from), q)
    for key, (i, vals) in parsed.items():
        code = key[0]
        if code not in in_catalog:
            out.log(i, LogLevel.ERROR, "code_not_in_catalog", f"Mã {code} chưa có trong danh mục sản phẩm — bỏ dòng", code)
            continue
        old = existing.get(key)
        label = f"{code} · NCC {vals['supplier_code'] or '(trống)'} · từ {vals['valid_from']:%d/%m/%Y}"
        if old is None:
            out.counts["created"] += 1
            out.log(i, LogLevel.INFO, "quote_new", f"Thêm báo giá {label}: {format_vn_number(vals['price'])}", code)
            if apply:
                db.add(ProductPriceQuote(created_by=uid, updated_by=uid, **vals))
            continue
        diffs = [f"{name}: {_show(getattr(old, col))} → {_show(vals[col])}" for col, name in
                 (("price", "Đơn giá"), ("vat", "VAT"), ("note", "Ghi chú")) if getattr(old, col) != vals[col]]
        if not diffs:
            out.counts["skipped"] += 1
            continue
        out.counts["updated"] += 1
        out.log(i, LogLevel.INFO, "quote_update", f"Cập nhật báo giá {label}: " + "; ".join(diffs), code)
        if apply:
            for col in ("price", "vat", "note"):
                setattr(old, col, vals[col])
            old.updated_by = uid
    out.note_dropped()
    if not apply:
        db.rollback()
    _persist(db, batch, out.counts, out.logs, [], total, ws.title[:40])
