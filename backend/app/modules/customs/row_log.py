"""Nhật ký TỪNG DÒNG của một lô nạp GTT02 — bao-CR-496 (F01, ghi chú 25/09 của chị Mi).

Trước CR này nhật ký lô chỉ có dòng cảnh báo / lỗi (`add_log`), người nạp không trả lời được
«dòng 1.234 trong tệp đi đâu». Nay mỗi dòng dữ liệu trong tệp có đúng MỘT dòng nhật ký mang
`row_status` (`ImportRowStatus`):

  · NEW       — đọc được, ghi vào bảng giá;
  · ERROR     — bộ đọc bỏ dòng (hiện chỉ có một lý do: không đọc được Ngày đăng ký);
  · DUPLICATE — giống hệt 32 cột với một dòng ĐỨNG TRƯỚC trong cùng tệp. Chỉ ĐÁNH DẤU, dòng
                vẫn ghi: nguồn không có số tờ khai, hai dòng giống hệt có thể là hai lô hàng
                thật (01 N-04: tệp mẫu có 806 cặp như vậy). Luật đếm của `reader` giữ nguyên.

Cố ý KHÔNG có «Cập nhật» — không có khóa để biết dòng nào là dòng cũ (02 §3.1).

Ghi bằng lệnh chèn hàng loạt: một tệp ~18.000 dòng, `db.add` từng dòng vừa chậm vừa kích
hoạt nhật ký trước/sau của `change_tracker`.
"""
from sqlalchemy import func, insert
from sqlalchemy.orm import Session

from app.modules.import_tool.model import (IMPORT_ROW_STATUS_LABELS, ImportBatch, ImportLog,
                                           ImportRowStatus, LogLevel)

from .constants import INSERT_CHUNK
from .reader import ParseResult

SHEET = "GTT02"
CATEGORY = "customs_row"

#  Hai khóa KHÔNG thuộc 32 cột dữ liệu: vị trí trong tệp và cờ «đã vá ngày».
_NON_DATA_KEYS = frozenset({"source_row", "date_fixed"})


def data_key(row: dict) -> tuple:
    """Khóa so trùng = đủ 32 cột dữ liệu (sau chuẩn hóa của bộ đọc), bỏ vị trí dòng."""
    return tuple(sorted((k, v) for k, v in row.items() if k not in _NON_DATA_KEYS))


def build_row_statuses(res: ParseResult) -> list[tuple[int, int, str, str]]:
    """→ [(dòng trong tệp, ImportRowStatus, câu, tên hàng)], xếp theo dòng.

    Dòng lỗi lấy từ `res.logs` (mức ERROR, có số dòng); dòng đọc được lấy từ `res.rows`,
    dòng nào lặp lại khóa của dòng trước thì DUPLICATE kèm số dòng gốc.
    """
    out: list[tuple[int, int, str, str]] = []
    for row_no, level, message in res.logs:
        if row_no > 0 and level == LogLevel.ERROR:
            out.append((row_no, int(ImportRowStatus.ERROR), message, ""))
    first_seen: dict[tuple, int] = {}
    for r in res.rows:
        key = data_key(r)
        origin = first_seen.get(key)
        if origin is None:
            first_seen[key] = r["source_row"]
            out.append((r["source_row"], int(ImportRowStatus.NEW), "Thêm mới", r["product_name"]))
        else:
            out.append((r["source_row"], int(ImportRowStatus.DUPLICATE),
                        f"Giống hệt dòng {origin} trong cùng tệp — vẫn ghi vào bảng giá, cần rà tay",
                        r["product_name"]))
    out.sort(key=lambda t: t[0])
    return out


def write_row_logs(db: Session, batch: ImportBatch, res: ParseResult) -> dict[str, int]:
    """Chèn hàng loạt nhật ký từng dòng cho lô; → số dòng theo từng kết cục.

    KHÔNG tăng các bộ đếm cảnh báo/lỗi của lô — dòng lỗi đã được `add_log` đếm ở mức ERROR
    rồi; ở đây chỉ thêm góc nhìn «mỗi dòng một kết cục».
    """
    statuses = build_row_statuses(res)
    payload = [{"batch_id": batch.id, "sheet": SHEET, "row_no": row_no, "level": int(LogLevel.INFO),
                "category": CATEGORY, "message": message, "ref_key": name[:120],
                "row_status": status, "created_by": batch.created_by, "updated_by": batch.created_by}
               for row_no, status, message, name in statuses]
    for i in range(0, len(payload), INSERT_CHUNK):
        db.execute(insert(ImportLog), payload[i:i + INSERT_CHUNK])
    counts = {"new": 0, "error": 0, "duplicate": 0}
    for _, status, _, _ in statuses:
        counts[_COUNT_KEY[status]] += 1
    return counts


_COUNT_KEY = {int(ImportRowStatus.NEW): "new", int(ImportRowStatus.ERROR): "error",
              int(ImportRowStatus.DUPLICATE): "duplicate"}


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
            "duplicate": by.get(int(ImportRowStatus.DUPLICATE), 0)}


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
