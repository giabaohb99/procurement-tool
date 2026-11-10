"""Sắp xếp các bảng của "Lịch sử nạp" (duoc-CR-744): danh sách lô, nhật ký lô, kết quả từng dòng.

Lô nạp dùng chung bảng `tab_import_batch` / `tab_import_log` của `import_tool` — module đó không được sửa ở đây
nên câu truy vấn có sắp xếp nằm trong tệp này và được gọi từ `customs/controller.py`, `saved_filter_controller.py`.

Xếp theo ĐÚNG giá trị ô hiển thị (khóa = `key` cột bên giao diện):

  · `status` hiển thị nhãn ghép từ trạng thái + chế độ ("Chạy thử xong" / "Đã ghi" / "Đang chạy" / "Lỗi" /
    "Đã hoàn tác") -> xếp theo chính nhãn đó, không theo mã số.
  · `range` (Khoảng ngày), `date_fixed` (Vá ngày), `skipped_rows` (Bỏ qua = đã có + trùng) lấy từ JSON `sheet_info`
    của lô -> trích bằng `json_extract`. `sheet_info` rỗng / hỏng không phải JSON thì ra trống (CASE chặn trước khi
    MySQL phân tích — nếu không, MỘT lô hỏng làm cả danh sách trả 500).
  · `created_by_name` xếp theo họ tên nhân sự của tài khoản nạp (không có thì email); id 0 = "Hệ thống".
  · `finished_at` hiển thị `finished_at || created_at` -> `coalesce` y như vậy.
"""
from sqlalchemy import Integer, String, and_, case, cast, func, select
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee
from app.modules.import_tool.model import (IMPORT_ROW_STATUS_LABELS, ImportBatch, ImportLog, ImportMode,
                                           ImportStatus)
from app.modules.user.model import User

from .list_sort import SortExpression, build_order, text_col

B = ImportBatch

#  Khóa xếp được; bài kiểm canh khớp các cột bên giao diện.
BATCH_SORT_KEYS = frozenset({"id", "filename", "mode", "status", "created_count", "updated_count",
                             "deleted_count", "range", "date_fixed", "skipped_rows", "created_by_name",
                             "finished_at"})
LOG_SORT_KEYS = frozenset({"row_no", "level", "message"})
ROW_SORT_KEYS = frozenset({"row_no", "row_status", "product_name", "message"})


def _json_value(db: Session, path: str):
    """Trường `path` trong JSON `sheet_info`; trống nếu cột rỗng / không phải JSON."""
    is_object = B.sheet_info.like("{%")
    value = func.json_extract(B.sheet_info, f"$.{path}")
    if db.get_bind().dialect.name == "mysql":
        value = func.json_unquote(value)   # MySQL trả JSON có nháy; SQLite trả sẵn giá trị thường
    return case((is_object, value), else_=None)


def _json_number(db: Session, path: str):
    return func.coalesce(cast(_json_value(db, path), Integer), 0)


def _created_by_name():
    full_name = (select(Employee.full_name).join(User, User.employee_id == Employee.id)
                 .where(User.id == B.created_by).scalar_subquery())
    email = select(User.email).where(User.id == B.created_by).scalar_subquery()
    return case((func.coalesce(B.created_by, 0) == 0, "Hệ thống"),
                else_=func.coalesce(func.nullif(full_name, ""), email))


def build_batch_sort_map(db: Session) -> dict[str, SortExpression]:
    status_label = case((B.status == int(ImportStatus.REVERTED), "Đã hoàn tác"),
                        (B.status == int(ImportStatus.FAILED), "Lỗi"),
                        (and_(B.status == int(ImportStatus.DONE), B.mode == int(ImportMode.DRY_RUN)),
                         "Chạy thử xong"),
                        (B.status == int(ImportStatus.DONE), "Đã ghi"), else_="Đang chạy")
    return {
        "id": B.id,
        "filename": text_col(B.filename),
        "mode": text_col(case({int(ImportMode.DRY_RUN): "Chạy thử", int(ImportMode.APPLY): "Ghi thật"},
                              value=B.mode, else_=None)),
        "status": text_col(status_label),
        "created_count": B.created_count,
        "updated_count": B.updated_count,
        "deleted_count": B.deleted_count,
        "range": [text_col(cast(_json_value(db, "date_from"), String(10))),
                  text_col(cast(_json_value(db, "date_to"), String(10)))],
        "date_fixed": _json_number(db, "date_fixed"),
        "skipped_rows": _json_number(db, "existing_rows") + _json_number(db, "duplicate_rows"),
        "created_by_name": text_col(_created_by_name()),
        "finished_at": func.coalesce(B.finished_at, B.created_at),
    }


def batch_order(db: Session, sort_by: str | None, sort_dir: str | None):
    """ORDER BY danh sách lô; `None` khi khóa rỗng / lạ (nơi gọi dùng mặc định: lô mới nhất lên đầu)."""
    key = (sort_by or "").strip()
    if key not in BATCH_SORT_KEYS:
        return None
    return build_order(key, sort_dir, build_batch_sort_map(db), B.id)


def list_logs(db: Session, batch_id: int, level: int | None, pg: dict, sort_by: str | None, sort_dir: str | None):
    """Nhật ký lô (hộp "Nhật ký lô" > "Ghi chú lỗi / cảnh báo"): cùng bộ lọc với `import_service.get_logs`."""
    q = db.query(ImportLog).filter(ImportLog.batch_id == batch_id, ImportLog.row_status == 0)
    if level is not None:
        q = q.filter(ImportLog.level == level)
    total = q.count()
    key = (sort_by or "").strip()
    sort_map = {"row_no": func.nullif(ImportLog.row_no, 0), "level": ImportLog.level,
                "message": text_col(ImportLog.message)}
    order = (build_order(key, sort_dir, sort_map, ImportLog.id) if key in LOG_SORT_KEYS else None) \
        or [ImportLog.level.desc(), ImportLog.id.asc()]
    return total, q.order_by(*order).offset(pg["offset"]).limit(pg["limit"]).all()


def row_log_order(sort_by: str | None, sort_dir: str | None):
    """ORDER BY "Kết quả từng dòng"; `None` -> mặc định theo số dòng trong tệp."""
    key = (sort_by or "").strip()
    if key not in ROW_SORT_KEYS:
        return None
    status_label = text_col(case({int(code): label for code, label in IMPORT_ROW_STATUS_LABELS.items() if label},
                                 value=ImportLog.row_status, else_=None))
    sort_map = {"row_no": func.nullif(ImportLog.row_no, 0), "row_status": status_label,
                "product_name": text_col(ImportLog.ref_key), "message": text_col(ImportLog.message)}
    return build_order(key, sort_dir, sort_map, ImportLog.id)

