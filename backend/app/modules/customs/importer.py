"""Ghi một lô tệp GTT02 xuống DB — chạy trong tác vụ nền `import_tool.run_import` (bao-CR-470).

Lô nạp dùng lại `tab_import_batch` (`ImportModule.CUSTOMS_DECLARATION`), chế độ
`DRY_RUN` (chạy thử, không ghi gì) hoặc `APPLY`. Thiết kế:
`doc/erp/hai-quan/02-thiet-ke-ky-thuat.md` §3.1 + §4.

⚠️ **Nạp theo LÔ, CHỈ THÊM dòng chưa có — không ghi đè, không thay theo khoảng ngày**
(bao-CR-541, đại ca chốt 01/10/2026). Mỗi dòng mang mã băm đủ các cột dữ liệu
(`dedupe.py`); dòng giống hệt một dòng đã lưu hoặc một dòng phía trên trong cùng tệp thì
BỎ QUA, nên nạp lại một tệp không nhân đôi dữ liệu. Bản trước (bao-CR-470) xóa mọi dòng
của lô khác trong khoảng ngày của tệp rồi chèn lại — tệp mới xuất thiếu là mất dữ liệu cũ
đúng mà không ai hay (rủi ro R1), và lô đã thay thì không hoàn tác được.

⚠️ **Ghi dòng hàng bằng lệnh chèn hàng loạt, không `db.add` từng dòng.** Một lần
kết xuất hàng chục nghìn dòng; `db.add` còn kích hoạt nhật ký trước/sau của
`change_tracker` cho từng dòng (hai bảng này đã vào `NO_LOG_TABLES`, nhưng chèn
hàng loạt còn nhanh hơn nhiều).
"""
import json
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import insert, text
from sqlalchemy.orm import Session

from app.modules.import_tool.model import ImportBatch, ImportStatus, LogLevel
from app.modules.import_tool.service import add_log

from . import dedupe, reader, row_log
from .constants import INSERT_CHUNK, PartyType
from .ingredient import load_kind_tagger, load_tagger
from .model import CustomsLine, CustomsParty

SHEET = "GTT02"

_PARTY_KEYS = ("importer_tax_code", "importer_name", "partner_name")
_LOCK_NAME = "customs_declaration_import"
_LOCK_WAIT_SECONDS = 300


class CustomsImportBusyError(reader.CustomsFileError):
    """Lượt nạp khác giữ khóa quá lâu — từ chối lô này bằng câu đọc được (không kèm traceback)."""


@contextmanager
def _import_lock(db: Session):
    """Cho từng lô ghi LẦN LƯỢT — kể cả khác tiến trình Celery (khóa có tên của MySQL).

    Hai lô chứa cùng một dòng mà ghi song song thì cả hai cùng thấy «chưa có» và cùng chèn:
    chống trùng thủng đúng ở chỗ nó cần nhất. Khóa giữ trên một kết nối RIÊNG (khóa MySQL gắn
    với kết nối, kết nối của `db` có thể trả về pool giữa chừng). SQLite (pytest) bỏ qua.
    """
    bind = db.get_bind()
    if bind.dialect.name != "mysql":
        yield
        return
    with bind.connect() as conn:
        got = conn.execute(text("SELECT GET_LOCK(:n, :w)"),
                           {"n": _LOCK_NAME, "w": _LOCK_WAIT_SECONDS}).scalar()
        if got != 1:
            raise CustomsImportBusyError("Đang có lượt nạp dữ liệu thị trường khác chạy quá lâu — thử lại sau")
        try:
            yield
        finally:
            conn.execute(text("SELECT RELEASE_LOCK(:n)"), {"n": _LOCK_NAME})


def run(db: Session, batch: ImportBatch, raw: bytes, apply: bool) -> None:
    """Đọc tệp của lô, ghi số liệu vào lô; `apply=True` mới ghi dòng hàng thật."""
    res = reader.parse(raw, batch.filename or "")
    for row_no, level, message in res.logs:
        add_log(db, batch, SHEET, row_no, level, "customs", message)
    with _import_lock(db):
        _classify_and_write(db, batch, res, apply)


def _classify_and_write(db: Session, batch: ImportBatch, res: reader.ParseResult, apply: bool) -> None:
    rows = res.rows
    date_from = min((r["reg_date"] for r in rows), default=None)
    date_to = max((r["reg_date"] for r in rows), default=None)
    #  bao-CR-541: so trùng bằng mã băm với dòng đã lưu trong khoảng ngày của tệp (dòng cũ
    #  chưa có mã thì tính luôn), rồi chỉ giữ dòng thật sự mới. Chạy thử cũng so — người nạp
    #  thấy trước bao nhiêu dòng mới, bao nhiêu dòng đã có, bao nhiêu dòng trùng trong tệp.
    identities = dedupe.stamp_rows(rows)
    existing = dedupe.load_existing(db, date_from, date_to, exclude_batch_id=batch.id)
    statuses, to_insert, suspect = row_log.classify_rows(res, identities, existing)
    #  bao-CR-496: mỗi dòng dữ liệu một dòng nhật ký mang kết cục — ghi ở CẢ chạy thử lẫn ghi thật.
    row_counts = row_log.write_row_logs(db, batch, statuses)

    batch.total_rows = len(rows) + res.skipped
    batch.skipped_count = res.skipped
    batch.created_count = len(to_insert)
    batch.deleted_count = 0                     # bao-CR-541: không còn thay dòng cũ
    batch.sheet_info = json.dumps({
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
        "date_fixed": sum(r["date_fixed"] for r in rows),
        "date_swap_detected": res.date_swap,
        "duplicate_rows": row_counts["duplicate"],     # trùng trong tệp — bỏ qua
        "existing_rows": row_counts["existing"],       # bao-CR-541: đã có trong bảng giá — bỏ qua
        "suspect_rows": suspect,                       # bao-CR-541: thêm mới nhưng nghi sửa giá
    }, ensure_ascii=False)

    if apply and to_insert:
        #  HQ4 — gắn hoạt chất + hàm lượng ngay lúc nạp (danh mục nạp một lần cho cả lô).
        tagger = load_tagger(db)
        kinds = load_kind_tagger(db)          # bao-CR-494: nhãn Thành phẩm / Nguyên liệu
        cache: dict[str, tuple[str, str, int]] = {}
        for r in to_insert:
            name = r["product_name"]
            if name not in cache:
                active, form = tagger.tag(name)
                cache[name] = (active, form, kinds.tag(name))
            r["active_ingredient"], r["formulation"], r["product_kind"] = cache[name]
        importer_ids = _upsert_parties(db, PartyType.DOMESTIC, to_insert)
        partner_ids = _upsert_parties(db, PartyType.FOREIGN, to_insert)
        _insert_lines(db, batch.id, to_insert, importer_ids, partner_ids)

    batch.status = ImportStatus.DONE
    batch.finished_at = datetime.utcnow()
    db.commit()


def revert(db: Session, batch: ImportBatch) -> dict:
    """Hoàn tác một lô đã ghi: xóa mọi dòng hàng mang `batch_id` của nó.

    Từ bao-CR-541 lô chỉ THÊM dòng chưa có nên hoàn tác luôn an toàn — kể cả để sửa số liệu:
    hoàn tác lô sai rồi nạp lại tệp đúng.
    ⚠️ **Vẫn chặn lô CŨ đã thay dữ liệu** (`deleted_count > 0`, nạp trước bao-CR-541). Dòng cũ
    đã xóa lúc thay và không có bản chụp để dựng lại — hoàn tác lúc đó là để trống cả khoảng
    ngày mà không ai hay.
    """
    if batch.deleted_count:
        return {"ok": False,
                "message": f"Lô này nạp theo cách cũ, đã thay {batch.deleted_count} dòng cũ nên không "
                           "hoàn tác được — hoàn tác sẽ để trống cả khoảng ngày đó."}
    deleted = (db.query(CustomsLine).filter(CustomsLine.batch_id == batch.id)
               .delete(synchronize_session=False))
    return {"ok": True, "deleted": deleted, "restored": 0,
            "message": f"Đã hoàn tác: xóa {deleted} dòng hàng của lô này"}


# ── Nội bộ ─────────────────────────────────────────────────────────────────
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
