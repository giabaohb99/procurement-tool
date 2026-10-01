"""Nhật ký TỪNG DÒNG của một lô nạp GTT02 — bao-CR-496 (F01, ghi chú 25/09 của chị Mi),
đổi luật trùng ở bao-CR-541.

Mỗi dòng dữ liệu trong tệp có đúng MỘT dòng nhật ký mang `row_status` (`ImportRowStatus`):

  · NEW       — đọc được và chưa có, ghi vào bảng giá. Trùng các cột nhận diện với một dòng
                đã có mà khác giá / lượng thì câu ghi «nghi sửa giá» để người nạp rà — vẫn
                THÊM, không ghi đè (xem `dedupe.py`: đo trên dữ liệu thật, đa số là lô thật);
  · ERROR     — bộ đọc bỏ dòng (hiện chỉ có một lý do: không đọc được Ngày đăng ký);
  · DUPLICATE — giống hệt một dòng ĐỨNG TRƯỚC trong cùng tệp → BỎ QUA;
  · EXISTING  — giống hệt một dòng đã lưu (lô khác) → BỎ QUA.

«Giống hệt» = cùng mã băm `row_hash` (đủ các cột dữ liệu sau chuẩn hóa). Đại ca chốt
01/10/2026: trùng thì bỏ qua — bản bao-CR-496 chỉ đánh dấu rồi vẫn ghi, prod dồn 806 dòng thừa.

Ghi bằng lệnh chèn hàng loạt: một tệp ~18.000 dòng, `db.add` từng dòng vừa chậm vừa kích
hoạt nhật ký trước/sau của `change_tracker`.
"""
from sqlalchemy import func, insert
from sqlalchemy.orm import Session

from app.modules.import_tool.model import (IMPORT_ROW_STATUS_LABELS, ImportBatch, ImportLog,
                                           ImportRowStatus, LogLevel)

from .constants import INSERT_CHUNK
from .dedupe import ExistingIndex
from .reader import ParseResult

SHEET = "GTT02"
CATEGORY = "customs_row"

#  (dòng trong tệp, ImportRowStatus, câu, tên hàng)
RowStatus = tuple[int, int, str, str]


def classify_rows(res: ParseResult, identities: list[str],
                  existing: ExistingIndex) -> tuple[list[RowStatus], list[dict], int]:
    """→ (kết cục từng dòng xếp theo dòng, các dòng CẦN CHÈN, số dòng nghi sửa giá).

    `res.rows` phải đã qua `dedupe.stamp_rows` (có `row_hash`); `identities` cùng thứ tự.
    Dòng lỗi lấy từ `res.logs` (mức ERROR, có số dòng).
    """
    out: list[RowStatus] = []
    for row_no, level, message in res.logs:
        if row_no > 0 and level == LogLevel.ERROR:
            out.append((row_no, int(ImportRowStatus.ERROR), message, ""))
    to_insert: list[dict] = []
    first_seen: dict[str, int] = {}
    suspect = 0
    for r, identity in zip(res.rows, identities):
        h = r["row_hash"]
        if h in existing.by_hash:
            out.append((r["source_row"], int(ImportRowStatus.EXISTING),
                        f"Đã có trong bảng giá (lô #{existing.by_hash[h]}) — bỏ qua", r["product_name"]))
        elif h in first_seen:
            out.append((r["source_row"], int(ImportRowStatus.DUPLICATE),
                        f"Giống hệt dòng {first_seen[h]} trong cùng tệp — bỏ qua", r["product_name"]))
        else:
            first_seen[h] = r["source_row"]
            to_insert.append(r)
            if identity in existing.by_identity:
                suspect += 1
                message = (f"Thêm mới — nghi sửa giá/số lượng so với dòng đã có ở lô "
                           f"#{existing.by_identity[identity]}, cần rà")
            else:
                message = "Thêm mới"
            out.append((r["source_row"], int(ImportRowStatus.NEW), message, r["product_name"]))
    out.sort(key=lambda t: t[0])
    return out, to_insert, suspect


def write_row_logs(db: Session, batch: ImportBatch, statuses: list[RowStatus]) -> dict[str, int]:
    """Chèn hàng loạt nhật ký từng dòng cho lô (kết quả `classify_rows`); → số dòng theo kết cục.

    KHÔNG tăng các bộ đếm cảnh báo/lỗi của lô — dòng lỗi đã được `add_log` đếm ở mức ERROR
    rồi; ở đây chỉ thêm góc nhìn «mỗi dòng một kết cục».
    """
    payload = [{"batch_id": batch.id, "sheet": SHEET, "row_no": row_no, "level": int(LogLevel.INFO),
                "category": CATEGORY, "message": message, "ref_key": name[:120],
                "row_status": status, "created_by": batch.created_by, "updated_by": batch.created_by}
               for row_no, status, message, name in statuses]
    for i in range(0, len(payload), INSERT_CHUNK):
        db.execute(insert(ImportLog), payload[i:i + INSERT_CHUNK])
    counts = {"new": 0, "error": 0, "duplicate": 0, "existing": 0}
    for _, status, _, _ in statuses:
        counts[_COUNT_KEY[status]] += 1
    return counts


_COUNT_KEY = {int(ImportRowStatus.NEW): "new", int(ImportRowStatus.ERROR): "error",
              int(ImportRowStatus.DUPLICATE): "duplicate", int(ImportRowStatus.EXISTING): "existing"}


def _row_query(db: Session, batch_id: int):
    return db.query(ImportLog).filter(ImportLog.batch_id == batch_id, ImportLog.row_status != 0)


def count_rows(db: Session, batch_id: int) -> dict:
    """Tổng theo từng kết cục cho đầu hộp «Nhật ký lô» — một truy vấn GROUP BY."""
    rows = (_row_query(db, batch_id).with_entities(ImportLog.row_status, func.count(ImportLog.id))
            .group_by(ImportLog.row_status).all())
    by = {int(s): int(n) for s, n in rows}
    return {"total": sum(by.values()),
            "new": by.get(int(ImportRowStatus.NEW), 0),
            "error": by.get(int(ImportRowStatus.ERROR), 0),
            "duplicate": by.get(int(ImportRowStatus.DUPLICATE), 0),
            "existing": by.get(int(ImportRowStatus.EXISTING), 0)}


def list_rows(db: Session, batch_id: int, row_status: int | None, pg: dict):
    """Danh sách từng dòng của lô, lọc theo kết cục, xếp theo số dòng trong tệp."""
    q = _row_query(db, batch_id)
    if row_status:
        q = q.filter(ImportLog.row_status == int(row_status))
    total = q.count()
    items = q.order_by(ImportLog.row_no.asc(), ImportLog.id.asc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, [serialize_row(x) for x in items]


def serialize_row(x: ImportLog) -> dict:
    status = int(x.row_status or 0)
    label = IMPORT_ROW_STATUS_LABELS.get(ImportRowStatus(status), "") if status in _COUNT_KEY else ""
    return {"id": x.id, "row_no": x.row_no, "row_status": status, "row_status_label": label,
            "product_name": x.ref_key, "message": x.message}
