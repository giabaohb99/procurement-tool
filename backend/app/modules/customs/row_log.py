"""Nhật ký TỪNG DÒNG của một lô nạp GTT02 — bao-CR-496 (F01, ghi chú 25/09 của chị Mi),
đổi luật trùng ở bao-CR-541.

Mỗi dòng dữ liệu trong tệp có đúng MỘT dòng nhật ký mang `row_status` (`ImportRowStatus`):

  · NEW       — đọc được và chưa có, ghi vào bảng giá. Trùng các cột nhận diện với một dòng
                đã có mà khác giá / lượng thì câu ghi «nghi sửa giá» để người nạp rà — vẫn
                THÊM, không ghi đè (xem `dedupe.py`: đo trên dữ liệu thật, đa số là lô thật);
  · ERROR     — bộ đọc bỏ dòng (hiện chỉ có một lý do: không đọc được Ngày đăng ký);
  · DUPLICATE — giống hệt một dòng ĐỨNG TRƯỚC trong cùng tệp → BỎ QUA;
  · EXISTING  — giống hệt một dòng đã lưu (lô khác) → BỎ QUA;
  · UPDATED   — bao-CR-608: ô «ID» trỏ đúng một dòng đã có → GHI ĐÈ dòng đó («Ghi đè ID n»);
  · DELETED   — bao-CR-608: ô «Thao tác» = xóa và ID có thật → XÓA dòng đó («Xóa ID n»);
  · IGNORED   — bao-CR-608: xóa mà ID trống / không có, hoặc ID đã xử lý ở dòng trên → BỎ QUA.

«Giống hệt» = cùng mã băm `row_hash` (đủ các cột dữ liệu sau chuẩn hóa). Đại ca chốt
01/10/2026: trùng thì bỏ qua — bản bao-CR-496 chỉ đánh dấu rồi vẫn ghi, prod dồn 806 dòng thừa.

Ghi bằng lệnh chèn hàng loạt: một tệp ~18.000 dòng, `db.add` từng dòng vừa chậm vừa kích
hoạt nhật ký trước/sau của `change_tracker`.
"""
from dataclasses import dataclass, field

from sqlalchemy import func, insert
from sqlalchemy.orm import Session

from app.modules.import_tool.model import (IMPORT_ROW_STATUS_LABELS, ImportBatch, ImportLog,
                                           ImportRowStatus, LogLevel)

from .constants import INSERT_CHUNK, REF_ID_KEY
from .dedupe import ExistingIndex
from .reader import ParseResult

SHEET = "GTT02"
CATEGORY = "customs_row"

#  (dòng trong tệp, ImportRowStatus, câu, tên hàng)
RowStatus = tuple[int, int, str, str]


@dataclass
class Classification:
    """Kết quả phân loại một tệp — bao-CR-608 gom vào một chỗ (trước chỉ có thêm mới)."""
    statuses: list[RowStatus] = field(default_factory=list)   # kết cục từng dòng, xếp theo dòng
    to_insert: list[dict] = field(default_factory=list)       # dòng THÊM MỚI
    to_update: list[tuple[dict, int]] = field(default_factory=list)   # (dòng trong tệp, id bị ghi đè)
    to_delete: list[int] = field(default_factory=list)        # id bị xóa
    suspect: int = 0                                          # thêm mới nhưng nghi sửa giá
    id_not_found: int = 0                                     # ô ID có số mà không có dòng đó
    ignored: int = 0                                          # dòng bỏ qua (xóa hỏng / ID lặp)
    warnings: list[tuple[int, str]] = field(default_factory=list)   # (dòng, câu) → nhật ký cảnh báo


def classify_rows(res: ParseResult, identities: list[str], existing: ExistingIndex,
                  target_ids: frozenset[int] | set[int] = frozenset(),
                  unchanged_rows: frozenset[int] | set[int] = frozenset()) -> Classification:
    """Phân loại từng dòng của tệp theo THỨ TỰ DÒNG.

    `res.rows` phải đã qua `dedupe.stamp_rows` (có `row_hash`); `identities` cùng thứ tự.
    Dòng lỗi lấy từ `res.logs` (mức ERROR, có số dòng).

    bao-CR-608: `target_ids` = các id mà ô «ID» của tệp trỏ tới VÀ có thật trong bảng;
    `unchanged_rows` = số dòng (trong tệp) có ID mà dữ liệu y hệt dòng đã lưu. Luật:
      · «Thao tác = xóa»: ID có thật → XÓA; ID trống / không có → BỎ QUA kèm cảnh báo;
      · ô ID có thật → GHI ĐÈ, không qua bộ lọc trùng (dòng ghi đè không bao giờ là «trùng
        trong tệp»); y hệt dòng đã lưu → «Đã có», không ghi gì;
      · ô ID có số mà không có → THÊM MỚI như dòng thường (vẫn qua chống trùng), kèm cảnh báo;
      · một ID xuất hiện ở nhiều dòng → dòng ĐẦU TIÊN thắng, các dòng sau BỎ QUA kèm cảnh báo.
    """
    out = Classification()
    for row_no, level, message in res.logs:
        if row_no > 0 and level == LogLevel.ERROR:
            out.statuses.append((row_no, int(ImportRowStatus.ERROR), message, ""))
    items = [(r["source_row"], False, r, identity) for r, identity in zip(res.rows, identities)]
    items += [(d["source_row"], True, d, "") for d in res.deletes]
    items.sort(key=lambda t: t[0])
    first_seen: dict[str, int] = {}
    claimed: dict[int, int] = {}          # id → dòng đã xử lý nó

    def skip(row_no: int, name: str, message: str) -> None:
        out.ignored += 1
        out.statuses.append((row_no, int(ImportRowStatus.IGNORED), message, name))
        out.warnings.append((row_no, message))

    for row_no, is_delete, r, identity in items:
        ref = r.get(REF_ID_KEY)
        name = r.get("product_name") or ""
        if is_delete:
            if ref is None:
                skip(row_no, name, "Xóa: ô ID trống — bỏ qua")
            elif ref not in target_ids:
                skip(row_no, name, f"Xóa: ID {ref} không có — bỏ qua")
            elif ref in claimed:
                skip(row_no, name, f"Xóa: ID {ref} đã xử lý ở dòng {claimed[ref]} — bỏ qua")
            else:
                claimed[ref] = row_no
                out.to_delete.append(ref)
                out.statuses.append((row_no, int(ImportRowStatus.DELETED), f"Xóa ID {ref}", name))
            continue
        h = r["row_hash"]
        if ref is not None and ref in target_ids:
            if ref in claimed:
                skip(row_no, name, f"ID {ref} đã xử lý ở dòng {claimed[ref]} — bỏ qua")
                continue
            claimed[ref] = row_no
            first_seen.setdefault(h, row_no)
            if row_no in unchanged_rows:
                out.statuses.append((row_no, int(ImportRowStatus.EXISTING),
                                     f"ID {ref} — dữ liệu không đổi, bỏ qua", name))
                continue
            out.to_update.append((r, ref))
            out.statuses.append((row_no, int(ImportRowStatus.UPDATED), f"Ghi đè ID {ref}", name))
            continue
        prefix = ""
        if ref is not None:
            out.id_not_found += 1
            prefix = f"ID {ref} không có — "
            out.warnings.append((row_no, f"ID {ref} không có — thêm mới"))
        if h in existing.by_hash:
            out.statuses.append((row_no, int(ImportRowStatus.EXISTING),
                                 f"{prefix}Đã có trong bảng giá (lô #{existing.by_hash[h]}) — bỏ qua", name))
        elif h in first_seen:
            out.statuses.append((row_no, int(ImportRowStatus.DUPLICATE),
                                 f"{prefix}Giống hệt dòng {first_seen[h]} trong cùng tệp — bỏ qua", name))
        else:
            first_seen[h] = row_no
            out.to_insert.append(r)
            if identity in existing.by_identity:
                out.suspect += 1
                message = (f"{prefix}Thêm mới — nghi sửa giá/số lượng so với dòng đã có ở lô "
                           f"#{existing.by_identity[identity]}, cần rà")
            else:
                message = f"{prefix}thêm mới" if prefix else "Thêm mới"
            out.statuses.append((row_no, int(ImportRowStatus.NEW), message, name))
    out.statuses.sort(key=lambda t: t[0])
    return out


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
    counts = {key: 0 for key in _COUNT_KEY.values()}
    for _, status, _, _ in statuses:
        counts[_COUNT_KEY[status]] += 1
    return counts


_COUNT_KEY = {int(ImportRowStatus.NEW): "new", int(ImportRowStatus.ERROR): "error",
              int(ImportRowStatus.DUPLICATE): "duplicate", int(ImportRowStatus.EXISTING): "existing",
              #  bao-CR-608 — ghi đè / xóa theo cột «ID» + «Thao tác», và dòng bỏ qua vì xóa hỏng.
              int(ImportRowStatus.UPDATED): "updated", int(ImportRowStatus.DELETED): "deleted",
              int(ImportRowStatus.IGNORED): "ignored"}


def _row_query(db: Session, batch_id: int):
    return db.query(ImportLog).filter(ImportLog.batch_id == batch_id, ImportLog.row_status != 0)


def count_rows(db: Session, batch_id: int) -> dict:
    """Tổng theo từng kết cục cho đầu hộp «Nhật ký lô» — một truy vấn GROUP BY."""
    rows = (_row_query(db, batch_id).with_entities(ImportLog.row_status, func.count(ImportLog.id))
            .group_by(ImportLog.row_status).all())
    by = {int(s): int(n) for s, n in rows}
    out = {"total": sum(by.values())}
    out.update({key: by.get(status, 0) for status, key in _COUNT_KEY.items()})
    return out


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
