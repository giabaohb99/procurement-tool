"""Ghi một lô tệp GTT02 xuống DB — chạy trong tác vụ nền `import_tool.run_import` (bao-CR-470).

Lô nạp dùng lại `tab_import_batch` (`ImportModule.CUSTOMS_DECLARATION`), chế độ
`DRY_RUN` (chạy thử, không ghi gì) hoặc `APPLY`. Thiết kế:
`doc/erp/hai-quan/02-thiet-ke-ky-thuat.md` §3.1 + §4.

⚠️ **Nạp theo LÔ, thay theo KHOẢNG NGÀY — không "có rồi thì cập nhật".** Dữ liệu
không có số tờ khai, so đủ 32 cột vẫn còn 806 dòng trùng khít: không dựng được
khóa duy nhất. Lô mới phủ khoảng ngày nào thì dòng của lô KHÁC trong khoảng đó bị
xóa rồi mới chèn — nạp lại một tệp không bao giờ nhân đôi dữ liệu.

⚠️ **Ghi dòng hàng bằng lệnh chèn hàng loạt, không `db.add` từng dòng.** Một lần
kết xuất hàng chục nghìn dòng; `db.add` còn kích hoạt nhật ký trước/sau của
`change_tracker` cho từng dòng (hai bảng này đã vào `NO_LOG_TABLES`, nhưng chèn
hàng loạt còn nhanh hơn nhiều).
"""
import json
from datetime import datetime

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.modules.import_tool.model import ImportBatch, ImportStatus, LogLevel
from app.modules.import_tool.service import add_log

from . import reader
from .constants import INSERT_CHUNK, PartyType
from .ingredient import load_tagger
from .model import CustomsLine, CustomsParty

SHEET = "GTT02"

_PARTY_KEYS = ("importer_tax_code", "importer_name", "partner_name")


def run(db: Session, batch: ImportBatch, raw: bytes, apply: bool) -> None:
    """Đọc tệp của lô, ghi số liệu vào lô; `apply=True` mới ghi dòng hàng thật."""
    res = reader.parse(raw, batch.filename or "")
    for row_no, level, message in res.logs:
        add_log(db, batch, SHEET, row_no, level, "customs", message)

    rows = res.rows
    date_from = min((r["reg_date"] for r in rows), default=None)
    date_to = max((r["reg_date"] for r in rows), default=None)
    #  Số dòng cũ (của lô KHÁC) nằm trong khoảng ngày của lô này — lượt chạy thử
    #  báo trước con số này để người nạp biết lần này sẽ xóa bao nhiêu dòng cũ.
    replaced = _count_in_range(db, batch.id, date_from, date_to)

    batch.total_rows = len(rows) + res.skipped
    batch.skipped_count = res.skipped
    batch.created_count = len(rows)
    batch.deleted_count = replaced
    batch.sheet_info = json.dumps({
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
        "date_fixed": sum(r["date_fixed"] for r in rows),
        "date_swap_detected": res.date_swap,
    }, ensure_ascii=False)

    if apply and rows:
        #  HQ4 — gắn hoạt chất + hàm lượng ngay lúc nạp (danh mục nạp một lần cho cả lô).
        tagger = load_tagger(db)
        cache: dict[str, tuple[str, str]] = {}
        for r in rows:
            name = r["product_name"]
            if name not in cache:
                cache[name] = tagger.tag(name)
            r["active_ingredient"], r["formulation"] = cache[name]
        importer_ids = _upsert_parties(db, PartyType.DOMESTIC, rows)
        partner_ids = _upsert_parties(db, PartyType.FOREIGN, rows)
        if replaced:
            _delete_in_range(db, batch.id, date_from, date_to)
            add_log(db, batch, SHEET, 0, LogLevel.INFO, "customs_replace",
                    f"Đã thay {replaced} dòng cũ trong khoảng {date_from:%d/%m/%Y} → {date_to:%d/%m/%Y}")
        _insert_lines(db, batch.id, rows, importer_ids, partner_ids)

    batch.status = ImportStatus.DONE
    batch.finished_at = datetime.utcnow()
    db.commit()


def revert(db: Session, batch: ImportBatch) -> dict:
    """Hoàn tác một lô đã ghi: xóa mọi dòng hàng mang `batch_id` của nó.

    ⚠️ **Chặn nếu lô đã THAY dữ liệu cũ** (`deleted_count > 0`). Dòng cũ đã xóa lúc
    thay và không có bản chụp để dựng lại — hoàn tác lúc đó là để trống cả khoảng
    ngày mà không ai hay. Nạp nhầm tệp thì cách sửa là nạp lại tệp đúng (nó tự thay
    khoảng ngày đó), không phải hoàn tác.
    """
    if batch.deleted_count:
        return {"ok": False,
                "message": f"Lô này đã thay {batch.deleted_count} dòng cũ nên không hoàn tác được — "
                           "hoàn tác sẽ để trống cả khoảng ngày đó. Nếu nạp nhầm, hãy nạp lại tệp đúng "
                           "cho khoảng ngày này."}
    deleted = (db.query(CustomsLine).filter(CustomsLine.batch_id == batch.id)
               .delete(synchronize_session=False))
    return {"ok": True, "deleted": deleted, "restored": 0,
            "message": f"Đã hoàn tác: xóa {deleted} dòng hàng của lô này"}


# ── Nội bộ ─────────────────────────────────────────────────────────────────
def _range_query(db: Session, batch_id: int, date_from, date_to):
    return db.query(CustomsLine).filter(CustomsLine.reg_date >= date_from,
                                        CustomsLine.reg_date <= date_to,
                                        CustomsLine.batch_id != batch_id)


def _count_in_range(db: Session, batch_id: int, date_from, date_to) -> int:
    if date_from is None:
        return 0
    return _range_query(db, batch_id, date_from, date_to).count()


def _delete_in_range(db: Session, batch_id: int, date_from, date_to) -> None:
    _range_query(db, batch_id, date_from, date_to).delete(synchronize_session=False)


def _party_key(party_type: PartyType, row: dict) -> tuple[str, str, str] | None:
    """→ (khóa chống trùng, mã số thuế, tên), hoặc None nếu dòng không có đối tượng này."""
    if party_type == PartyType.DOMESTIC:
        tax = row["importer_tax_code"]
        return (tax, tax, row["importer_name"]) if tax else None
    name = row["partner_name"]
    return (reader.hash_name(name), "", name) if name else None


def _upsert_parties(db: Session, party_type: PartyType, rows: list[dict]) -> dict[str, int]:
    """Tra hoặc tạo đối tượng cho CẢ LÔ trong vài truy vấn, không truy vấn từng dòng.

    → map khóa chống trùng → id. Tên lấy của lần nạp MỚI NHẤT (dòng cuối cùng gặp).
    """
    wanted: dict[str, tuple[str, str]] = {}
    for r in rows:
        k = _party_key(party_type, r)
        if k:
            wanted[k[0]] = (k[1], k[2])
    ids: dict[str, int] = {}
    keys = list(wanted)
    for i in range(0, len(keys), 1000):
        chunk = keys[i:i + 1000]
        for p in db.query(CustomsParty).filter(CustomsParty.party_type == int(party_type),
                                               CustomsParty.dedupe_key.in_(chunk)):
            ids[p.dedupe_key] = p.id
            if wanted[p.dedupe_key][1] and p.name != wanted[p.dedupe_key][1]:
                p.name = wanted[p.dedupe_key][1]
    new = [{"party_type": int(party_type), "dedupe_key": k, "tax_code": wanted[k][0],
            "name": wanted[k][1]} for k in keys if k not in ids]
    if new:
        db.execute(insert(CustomsParty), new)
        db.flush()
        for i in range(0, len(new), 1000):
            chunk = [n["dedupe_key"] for n in new[i:i + 1000]]
            for pid, key in db.query(CustomsParty.id, CustomsParty.dedupe_key).filter(
                    CustomsParty.party_type == int(party_type), CustomsParty.dedupe_key.in_(chunk)):
                ids[key] = pid
    return ids


def _insert_lines(db: Session, batch_id: int, rows: list[dict],
                  importer_ids: dict[str, int], partner_ids: dict[str, int]) -> None:
    payload = []
    for r in rows:
        line = {k: v for k, v in r.items() if k not in _PARTY_KEYS}
        imp = _party_key(PartyType.DOMESTIC, r)
        par = _party_key(PartyType.FOREIGN, r)
        line.update(batch_id=batch_id,
                    importer_id=importer_ids.get(imp[0], 0) if imp else 0,
                    partner_id=partner_ids.get(par[0], 0) if par else 0)
        payload.append(line)
    for i in range(0, len(payload), INSERT_CHUNK):
        db.execute(insert(CustomsLine), payload[i:i + INSERT_CHUNK])
