"""Nhập ĐỊNH MỨC BAO BÌ từ tệp `DATA_CHAI.xlsx` (duoc-CR-784, phase 03) — chạy trong tác vụ nền `import_tool.run_import`.

Đúng logic `importExcel()` của bản mẫu `Bao cao gia NVL san xuat - 11.2026.html`, hai khuôn tệp:
- **MAP_SP** (ưu tiên): bỏ 4 dòng đầu, lấy dòng có cột C. A chai · B nắp · C mã HH · D tên HH · E tên pháp lý ·
  F quy cách thùng (số) · I nhãn · J nhãn thùng · K thùng. Ô bắt đầu bằng `#` (lỗi công thức Excel) coi là rỗng.
- **data** + **DATA CHUNG** (khi không có MAP_SP): sheet `data` cùng cột A–F; `DATA CHUNG` (bỏ 2 dòng đầu; cột C mã, cột F
  mã HH) gán nhãn / nhãn thùng theo tiền tố mã (NHG / NHD / NTN → nhãn, NDT → nhãn thùng); một HH nhiều mã thì chọn mã có
  LẦN MUA CÓ GIÁ GẦN NHẤT trong sổ giá. Khớp HH bỏ số 0 đầu (`HH0417.1` = `HH417.1`).

Có rồi (theo `hh_code`, không phân biệt hoa thường) thì cập nhật, chưa có thì tạo; dòng trên DB không có trong tệp GIỮ NGUYÊN
(chỉ báo số đếm). Chạy thử liệt kê ô sẽ đổi (cũ → mới). Không hỗ trợ hoàn tác đợt đầu.
"""
import re
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.packaging_price_codes import PackagingRole

from app.modules.import_tool.catalog_import import ImportValidationError, _persist
from app.modules.import_tool.model import ImportBatch, LogLevel
from app.modules.product.model import Product
from app.modules.product_price.model import ProductPriceLedger

from .bom_parts_service import codes_from_fields, current_codes, set_bom_codes
from .model import PackagingBom, role_field
from .schema import CARTON_QTY_MAX

SHEET_MAP, SHEET_DATA, SHEET_COMMON = "MAP_SP", "data", "DATA CHUNG"
MAX_ROWS = 20000                      # trần số dòng một tệp (chặn tệp khổng lồ / nhầm tệp)
CODE_LEN, NAME_LEN = 50, 255
#  Chữ mong đợi ở 4 dòng tiêu đề của tệp thật — không thấy chữ nào là gần như chắc chắn nhầm tệp.
HEADER_HINTS = ("chai", "nắp", "nhãn", "thùng", "hh", "quy cách", "mã")
#  tiền tố mã ở DATA CHUNG → cột định mức
PREFIX_COLUMN = {"NHG": "label_code", "NHD": "label_code", "NTN": "label_code", "NDT": "carton_label_code"}
FIELD_LABELS = {"hh_name": "Tên HH", "legal_name": "Tên pháp lý", "bottle_code": "Chai", "cap_code": "Nắp",
                "label_code": "Nhãn", "carton_label_code": "Nhãn thùng", "carton_code": "Thùng",
                "carton_qty": "Quy cách thùng"}
#  Trường phẳng của tệp nhập: ba trường đầu phiếu + một trường mã cho MỖI loại thành phần (dựng từ `PackagingRole`).
HEADER_FIELDS = ("hh_name", "legal_name", "carton_qty")
CODE_FIELDS = tuple(role_field(role) for role in PackagingRole)
_HH_KEY = re.compile(r"^HH0*(\d+(?:\.\d+)?)$")


ROLE_FIELDS = tuple((role, role_field(role)) for role in PackagingRole)


def _flat_values(bom: PackagingBom) -> dict:
    """Trường phẳng của một định mức đã có (ba trường đầu phiếu + mã mỗi loại thành phần) — để so với giá trị trong tệp."""
    codes = current_codes(bom)
    return {**{f: getattr(bom, f) for f in HEADER_FIELDS}, **{f: codes.get(int(role), "") for role, f in ROLE_FIELDS}}


def clean(v) -> str:
    """Giá trị ô → chuỗi gọn; rỗng / lỗi công thức (`#N/A`…) → ''; số nguyên dạng float (40.0) → '40'."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip()
    return "" if s.startswith("#") else s


def hh_key(code: str) -> str:
    """Khóa so khớp HH bỏ số 0 đầu: `HH0417.1` và `HH417.1` cùng khóa."""
    c = (code or "").strip().upper()
    m = _HH_KEY.match(c)
    return m.group(1) if m else c


def _sheet(wb, name: str):
    return next((ws for ws in wb.worksheets if ws.title.strip().casefold() == name.casefold()), None)


def _rows(ws, skip: int) -> list[tuple[int, tuple]]:
    """[(số dòng Excel, giá trị 11 cột đầu)] — bỏ `skip` dòng đầu. Chặn trần TRƯỚC khi đọc (tệp khổng lồ không nạp vào bộ nhớ)."""
    if (ws.max_row or 0) > MAX_ROWS + skip:
        raise ImportValidationError(f"Sheet '{ws.title}' có {ws.max_row:,} dòng, vượt trần {MAX_ROWS:,} dòng — tách tệp rồi nhập lại.")
    out = []
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if i > skip:
            out.append((i, tuple(row[:11]) + (None,) * max(0, 11 - len(row))))
    return out


def precheck(wb) -> None:
    """Chặn sớm lúc tải lên: phải có sheet MAP_SP hoặc data, và 4 dòng đầu có chữ nhận ra được."""
    ws = _sheet(wb, SHEET_MAP) or _sheet(wb, SHEET_DATA)
    if ws is None:
        raise ImportValidationError(f"Không thấy sheet '{SHEET_MAP}' hoặc '{SHEET_DATA}' — kiểm tra lại tệp DATA_CHAI.xlsx.")
    head = " ".join(clean(c).lower() for _, r in _rows_upto(ws, 4) for c in r)
    if not any(h in head for h in HEADER_HINTS):
        raise ImportValidationError("4 dòng đầu của sheet không có tiêu đề cột định mức (Chai / Nắp / Nhãn / Thùng / Mã HH) "
                                    "— có thể nhầm tệp.")


def _rows_upto(ws, n: int):
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if i > n:
            break
        yield i, row


def _common_links(db: Session, wb) -> dict[str, dict[str, str]]:
    """`{khóa HH: {cột: mã}}` từ DATA CHUNG; nhiều mã cùng cột thì giữ mã có lần mua có giá gần nhất (hòa → mã đầu)."""
    ws = _sheet(wb, SHEET_COMMON)
    if ws is None:
        return {}
    cands: list[tuple[str, str, str]] = []
    for _, r in _rows(ws, 2):
        code, hh = clean(r[2]).upper(), clean(r[5])
        col = PREFIX_COLUMN.get(code[:3])
        if col and hh:
            cands.append((hh_key(hh), col, code))
    last = {}
    if cands:
        last = dict(db.query(ProductPriceLedger.product_code, func.max(ProductPriceLedger.price_date))
                    .filter(ProductPriceLedger.product_code.in_({c[2] for c in cands}), ProductPriceLedger.price > 0)
                    .group_by(ProductPriceLedger.product_code).all())
    links: dict[str, dict[str, str]] = {}
    for key, col, code in cands:
        slot = links.setdefault(key, {})
        if col not in slot or (last.get(code) or date.min) > (last.get(slot[col]) or date.min):
            slot[col] = code
    return links


def _parse_qty(raw, warn) -> int:
    if raw is None or clean(raw) == "":
        return 0
    try:
        n = int(round(float(str(raw).replace(",", ".").strip())))
    except ValueError:
        warn(f"Quy cách thùng '{clean(raw)}' không phải số — đặt 0")
        return 0
    if not 0 <= n <= CARTON_QTY_MAX:
        warn(f"Quy cách thùng {n} ngoài khoảng 0–{CARTON_QTY_MAX} — đặt 0")
        return 0
    return n


def run(db: Session, batch: ImportBatch, wb, apply: bool) -> None:
    precheck(wb)
    is_map = _sheet(wb, SHEET_MAP) is not None
    ws = _sheet(wb, SHEET_MAP) or _sheet(wb, SHEET_DATA)
    rows = [(i, r) for i, r in _rows(ws, 4) if r[2] not in (None, "")]
    if not rows:
        raise ImportValidationError("Sheet không có dòng dữ liệu nào (cột C — Mã HH — đều trống).")
    uid = batch.created_by
    counts = {"created": 0, "updated": 0, "skipped": 0, "warning": 0, "review": 0, "error": 0}
    logs: list[dict] = []

    def log(row_no, level, category, message, ref=""):
        logs.append({"sheet": ws.title[:40], "row_no": row_no, "level": int(level), "category": category,
                     "message": message, "ref_key": ref, "target_code": ref[:50]})
        key = {LogLevel.WARNING: "warning", LogLevel.REVIEW: "review", LogLevel.ERROR: "error"}.get(level)
        if key:
            counts[key] += 1

    existing = {b.hh_code.casefold(): b for b in db.query(PackagingBom).options(selectinload(PackagingBom.parts)).all()}
    links = {} if is_map else _common_links(db, wb)
    parsed: dict[str, tuple[int, dict]] = {}     # casefold(hh) -> (dòng, giá trị)
    for i, r in rows:
        hh = clean(r[2])
        if not hh:
            log(i, LogLevel.ERROR, "missing_hh", "Mã HH trống hoặc là lỗi công thức — bỏ dòng")
            continue
        vals = {"hh_code": hh, "hh_name": clean(r[3]), "legal_name": clean(r[4]), "bottle_code": clean(r[0]),
                "cap_code": clean(r[1]),
                "carton_qty": _parse_qty(r[5], lambda m, i=i, hh=hh: log(i, LogLevel.WARNING, "bad_qty", m, hh))}
        old = existing.get(hh.casefold())
        old_codes = current_codes(old) if old else {}
        if is_map:
            vals.update(label_code=clean(r[8]), carton_label_code=clean(r[9]), carton_code=clean(r[10]))
        else:
            lk = links.get(hh_key(hh), {})
            kept = {f: old_codes.get(int(role), "") for role, f in ROLE_FIELDS}
            vals.update(label_code=lk.get("label_code") or kept["label_code"],
                        carton_label_code=lk.get("carton_label_code") or kept["carton_label_code"],
                        carton_code=kept["carton_code"])
        if not vals["bottle_code"]:
            log(i, LogLevel.ERROR, "missing_bottle", "Thiếu mã chai — bỏ dòng", hh)
            continue
        too_long = [c for c in ("hh_code", *CODE_FIELDS) if len(vals[c]) > CODE_LEN]
        if too_long:
            log(i, LogLevel.ERROR, "too_long", f"Mã dài hơn {CODE_LEN} ký tự ({', '.join(too_long)}) — bỏ dòng", hh)
            continue
        for c in ("hh_name", "legal_name"):
            if len(vals[c]) > NAME_LEN:
                vals[c] = vals[c][:NAME_LEN]
                log(i, LogLevel.WARNING, "name_cut", f"{FIELD_LABELS[c]} dài hơn {NAME_LEN} ký tự — đã cắt", hh)
        if hh.casefold() in parsed:
            log(i, LogLevel.WARNING, "duplicate_hh", f"Mã HH {hh} trùng dòng {parsed[hh.casefold()][0]} — lấy dòng sau", hh)
        parsed[hh.casefold()] = (i, vals)

    part_codes = {v[c] for _, v in parsed.values() for c in CODE_FIELDS if v[c]}
    in_catalog = ({c for (c,) in db.query(Product.code).filter(Product.code.in_(part_codes)).all()}
                  if part_codes else set())
    for key, (i, vals) in parsed.items():
        missing = sorted(c for c in {vals[f] for f in CODE_FIELDS} if c and c not in in_catalog)
        if missing:
            log(i, LogLevel.WARNING, "code_not_in_catalog",
                f"Mã thành phần chưa có trong danh mục sản phẩm: {', '.join(missing)} (vẫn nhận)", vals["hh_code"])
        old = existing.get(key)
        if old is None:
            counts["created"] += 1
            log(i, LogLevel.INFO, "bom_new", f"Thêm định mức {vals['hh_code']}", vals["hh_code"])
            if apply:
                bom = PackagingBom(hh_code=vals["hh_code"], created_by=uid, updated_by=uid, **{f: vals[f] for f in HEADER_FIELDS})
                set_bom_codes(bom, codes_from_fields(vals))
                db.add(bom)
            continue
        before = _flat_values(old)
        diffs = [f"{FIELD_LABELS[c]}: {before[c] or '(trống)'} → {vals[c] or '(trống)'}"
                 for c in FIELD_LABELS if before[c] != vals[c]]
        if not diffs:
            counts["skipped"] += 1
            continue
        counts["updated"] += 1
        log(i, LogLevel.INFO, "bom_update", f"Cập nhật {old.hh_code}: " + "; ".join(diffs), old.hh_code)
        if apply:
            for c in HEADER_FIELDS:
                setattr(old, c, vals[c])
            set_bom_codes(old, codes_from_fields(vals))
            old.updated_by = uid
    kept = len(set(existing) - set(parsed))
    if kept:
        log(0, LogLevel.INFO, "bom_kept", f"{kept} định mức có trên hệ thống nhưng không có trong tệp — giữ nguyên")
    if not apply:
        db.rollback()
    _persist(db, batch, counts, logs, [], len(rows), ws.title[:40])
