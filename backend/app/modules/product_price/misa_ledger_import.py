"""Nạp TẠM sổ chi tiết mua hàng Misa (báo cáo HTML của chủ dự án) vào sổ giá làm nguồn giá đúng (duoc-CR-784).

Nguồn: tệp HTML `Bao cao gia NVL san xuat - 11.2026.html` (một tệp tự chứa, `window.VTBB_DEMO = {...}` trong thẻ script) hoặc tệp
JSON cùng cấu trúc: `vtbb` {mã: [tên, nhóm, ĐVT]} · `mua` [[id, ngày YYYY-MM-DD, tên NCC, mã VTBB, số lượng, đơn giá (VNĐ, chưa
VAT; None / 0 = chưa có giá), mã NCC, kho, thành tiền]]. Mỗi dòng `mua` thành MỘT dòng sổ giá `source_type = MISA (3)`,
`source_id = id dòng Misa`, `doc_id = 0`, `vat = NULL` (Misa không có VAT: NULL = không biết, giao diện hiện trống), `warehouse_name` = kho (chỉ số 7), `amount` = thành tiền (chỉ số 8, chỉ khi dòng có
giá và thành tiền khác 0 — như bản mẫu HTML; thiếu thì NULL, màn hình dùng giá x số lượng). Giá 0 vẫn vào sổ (đếm số lần mua như các nguồn khác, không xếp hạng).

Idempotent: có `(source_type, source_id)` rồi thì cập nhật nếu khác, chưa có thì chèn; dòng Misa nằm trong sổ mà tệp không còn thì
xóa (tệp là nguồn đúng). Nạp xong ghi MỐC = ngày lớn nhất của dòng Misa vào `tab_setting` (`misa_cutoff.py`) để nguồn 1 / 2 chỉ còn
được tính SAU mốc — không đếm trùng. Gỡ hẳn: `purge_misa_rows` (xóa dòng nguồn 3 + mốc), sổ giá trở về hành vi cũ.

KHÔNG TRỘN với module 6 (nạp xlsx từ màn Quản lý Import): script này dùng id dòng Misa làm `source_id` và XÓA mọi dòng Misa không có trong
tệp, còn module 6 tự đánh `source_id = max + 1` — chạy script sau module 6 là mất dòng xlsx. `import_misa_rows` vì thế TỪ CHỐI khi sổ đã có
dòng Misa mà module 6 từng nạp thật (`ensure_no_xlsx_misa_rows`). Muốn nạp lại từ HTML thì gỡ sạch bằng `purge_misa_rows` rồi nạp.

Hàm ở đây chỉ `flush`, KHÔNG commit — nơi gọi (`scripts/import_misa_price_ledger.py`) quyết định commit hay lùi.
"""
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.packaging_price_codes import LedgerLineStage, PriceSourceType
from app.modules.import_tool.model import ImportBatch, ImportMode, ImportModule, ImportStatus

from .misa_cutoff import set_misa_cutoff
from .model import ProductPriceLedger as L

SOURCE = int(PriceSourceType.MISA)
FINAL_STAGE = int(LedgerLineStage.FINAL)   # dòng Misa luôn là dòng đã chốt
BATCH = 1000
_MARKER = re.compile(r"window\.VTBB_DEMO\s*=\s*")
_VTBB_SUFFIX = re.compile(r"\s*-\s*VTBB\s*$", re.IGNORECASE)
MAX_CODE, MAX_SUPPLIER_CODE, MAX_SUPPLIER_NAME, MAX_WAREHOUSE_NAME, MAX_UNIT = 50, 50, 200, 200, 25
MAX_DECIMAL = Decimal("1e13")      # Numeric(18,4) / (18,3) chứa được, chặn số rác từ tệp


class MisaSourceError(ValueError):
    """Tệp nguồn không đọc được hoặc sai cấu trúc — câu tiếng Việt cho người chạy script."""


def load_misa_source(path: str | Path) -> dict:
    """Đọc `{vtbb, mua}` từ tệp HTML (cụm `window.VTBB_DEMO = {...}`) hoặc JSON."""
    p = Path(path)
    if not p.is_file():
        raise MisaSourceError(f"Không thấy tệp nguồn: {p}")
    text = p.read_text(encoding="utf-8")
    try:
        if p.suffix.lower() == ".json" or text.lstrip().startswith("{"):
            data = json.loads(text)
        else:
            found = _MARKER.search(text)
            if found is None:
                raise MisaSourceError("Tệp HTML không có cụm window.VTBB_DEMO — không phải báo cáo giá NVL")
            data, _ = json.JSONDecoder().raw_decode(text, found.end())
    except json.JSONDecodeError as exc:
        raise MisaSourceError(f"Dữ liệu trong tệp không phải JSON hợp lệ: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("mua"), list) or not isinstance(data.get("vtbb"), dict):
        raise MisaSourceError("Thiếu khóa vtbb (từ điển mã) hoặc mua (danh sách dòng mua hàng)")
    return data


def _decimal(value, *, places: str) -> Decimal | None:
    """`Decimal` đã làm tròn theo `places`; None khi không phải số hợp lệ / vượt trần."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or abs(number) >= MAX_DECIMAL:
        return None
    return number.quantize(Decimal(places))


def _clean_text(value, limit: int) -> str:
    return (str(value).strip() if value is not None else "")[:limit]


def build_misa_rows(data: dict, company_id: int) -> tuple[list[dict], dict]:
    """`(các dòng sổ giá dạng dict xếp theo id Misa tăng dần, số liệu)`. Dòng hỏng bị bỏ và đếm, không làm hỏng cả lô."""
    stats = {"file_rows": len(data["mua"]), "skipped_bad_row": 0, "skipped_duplicate_id": 0, "zero_price": 0,
             "min_date": None, "max_date": None}
    units = {code: _clean_text(info[2], MAX_UNIT) if isinstance(info, list) and len(info) > 2 else ""
             for code, info in data["vtbb"].items()}
    out: dict[int, dict] = {}
    for raw in data["mua"]:
        if not isinstance(raw, list) or len(raw) < 7 or isinstance(raw[0], bool) or not isinstance(raw[0], int) or raw[0] <= 0:
            stats["skipped_bad_row"] += 1
            continue
        misa_id, day, name, code, qty, price, supplier_code = raw[:7]
        warehouse = raw[7] if len(raw) > 7 else None           # chỉ số 7 = kho (tệp cũ không có thì để trống)
        amount_raw = raw[8] if len(raw) > 8 else None          # chỉ số 8 = thành tiền (tệp cũ không có thì NULL)
        try:
            price_date = date.fromisoformat(str(day).strip()[:10])
        except ValueError:
            price_date = None
        code = _clean_text(code, MAX_CODE)
        qty_value = _decimal(0 if qty is None else qty, places="0.001")
        price_value = _decimal(0 if price is None else price, places="0.0001")
        if price_date is None or not code or qty_value is None or price_value is None:
            stats["skipped_bad_row"] += 1
            continue
        if misa_id in out:
            stats["skipped_duplicate_id"] += 1
            continue
        if price_value <= 0:
            price_value = Decimal("0.0000")
            stats["zero_price"] += 1
        amount = _decimal(amount_raw, places="0.01") if price_value > 0 else None
        out[misa_id] = {"source_type": SOURCE, "source_id": misa_id, "line_stage": FINAL_STAGE, "doc_id": 0, "product_code": code,
                        "supplier_code": _clean_text(supplier_code, MAX_SUPPLIER_CODE),
                        "supplier_name": _VTBB_SUFFIX.sub("", _clean_text(name, MAX_SUPPLIER_NAME + 20))[:MAX_SUPPLIER_NAME] or None,
                        "warehouse_name": _clean_text(warehouse, MAX_WAREHOUSE_NAME) or None,
                        "company_id": company_id, "price_date": price_date, "price": price_value, "vat": None,
                        "qty": qty_value, "amount": amount or None, "unit": units.get(code, "")}
    rows = [out[k] for k in sorted(out)]
    if rows:
        stats["min_date"] = min(r["price_date"] for r in rows)
        stats["max_date"] = max(r["price_date"] for r in rows)
    return rows, stats


def _differs(row: L, values: dict) -> bool:
    return any(getattr(row, k) != v for k, v in values.items() if k not in ("source_type", "source_id"))


XLSX_GUARD_MESSAGE = ("Sổ giá đang có dòng Misa do màn Quản lý Import (module 6, nạp xlsx) nạp. Script HTML dùng id dòng Misa làm "
                      "source_id và xóa mọi dòng Misa không có trong tệp nên sẽ làm mất các dòng đó. Dùng module 6 để nạp tiếp, "
                      "hoặc gỡ sạch nguồn Misa (--purge --apply) rồi mới nạp lại từ tệp HTML.")


def ensure_no_xlsx_misa_rows(db: Session) -> None:
    """Từ chối (MisaSourceError) khi sổ có dòng Misa VÀ module 6 từng nạp thật (lô ghi thật, xong) — hai đường tự đánh `source_id`
    khác nhau nên không trộn được. Sổ chưa có dòng Misa nào (kể cả sau `--purge`) thì cho qua dù lô cũ còn trong lịch sử.

    Chưa phân biệt được TỪNG dòng Misa thuộc lô nào (sổ giá không lưu id lô; `source_id` của module 6 chỉ là số thứ tự) — việc đó
    thuộc phase 07 ("xóa theo lô"). Đủ cho chốt chặn này vì nó chỉ cần biết module 6 có từng ghi vào sổ hay chưa."""
    has_misa_rows = db.execute(select(L.id).where(L.source_type == SOURCE).limit(1)).first() is not None
    if not has_misa_rows:
        return
    applied = db.execute(select(ImportBatch.id).where(
        ImportBatch.module == int(ImportModule.PACKAGING_MISA), ImportBatch.mode == int(ImportMode.APPLY),
        ImportBatch.status == int(ImportStatus.DONE)).limit(1)).first() is not None
    if applied:
        raise MisaSourceError(XLSX_GUARD_MESSAGE)


def import_misa_rows(db: Session, rows: list[dict]) -> dict:
    """Upsert theo `(source_type, source_id)`, xóa dòng Misa không còn trong tệp, đặt mốc = ngày lớn nhất. Không commit.

    Từ chối khi sổ đã có dòng Misa do module 6 nạp (`ensure_no_xlsx_misa_rows`)."""
    ensure_no_xlsx_misa_rows(db)
    existing = {r.source_id: r for r in db.query(L).filter(L.source_type == SOURCE).all()}
    stats = {"inserted": 0, "updated": 0, "unchanged": 0, "deleted_stale": 0}
    keep = {r["source_id"] for r in rows}
    stale = [r.id for sid, r in existing.items() if sid not in keep]
    for i in range(0, len(stale), BATCH):
        db.execute(delete(L).where(L.id.in_(stale[i:i + BATCH])))
    stats["deleted_stale"] = len(stale)
    for n, values in enumerate(rows, 1):            # đã xếp theo id Misa tăng → id sổ giá tăng cùng chiều (hòa ngày thì dòng Misa sau là mới hơn)
        row = existing.get(values["source_id"])
        if row is None:
            db.add(L(**values))
            stats["inserted"] += 1
        elif _differs(row, values):
            for key, value in values.items():
                setattr(row, key, value)
            row.synced_at = func.now()
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1
        if n % BATCH == 0:
            db.flush()
    db.flush()
    cutoff = max((r["price_date"] for r in rows), default=None)
    set_misa_cutoff(db, cutoff)
    stats["cutoff"] = cutoff
    return stats


def purge_misa_rows(db: Session) -> dict:
    """Xóa mọi dòng sổ giá nguồn Misa và mốc — sổ giá trở về hành vi trước khi nạp. Không commit."""
    deleted = db.execute(delete(L).where(L.source_type == SOURCE)).rowcount or 0
    set_misa_cutoff(db, None)
    db.flush()
    return {"deleted": int(deleted)}
