"""Đóng gói nhật ký hằng tháng ra R2 — bản sao thứ hai của chứng cứ.

Chính sách: **KHÔNG xóa dòng nào khỏi CSDL ở đây.** Việc này chỉ chép ra ngoài.
Dọn dẹp là việc riêng của `request_log.cleanup`, và nó cố ý nằm ở tệp khác để
không ai lỡ tay gộp hai thứ vào một luồng.

Key R2: `{env}/log-archive/{YYYY-MM}/{bảng}.jsonl.gz` + tệp `.sha256` đi kèm.

⚠️ **VÌ SAO KÉO VIỆC NÀY LÊN SỚM** (bao-CR-346, vốn thuộc P6).
QĐ-C đã loại bốn bảng nhật ký khỏi bản sao lưu hằng đêm — hợp lý, vì chúng phình
nhanh và không cần khôi phục cùng dữ liệu nghiệp vụ. Nhưng gói R2 lại xếp ở P6,
giai đoạn CUỐI. Khoảng giữa hai mốc đó, nhật ký tồn tại **đúng một bản, nằm trên
chính cái máy** mà kẻ tấn công đang đứng. Nhật ký chỉ có giá trị khi người bị nó
ghi lại không xóa được nó; một bản duy nhất cùng chỗ thì không thỏa điều đó.

Ba thứ đã sửa so với bản cũ của tệp này:

1. **Chép ĐỦ CỘT.** Bản cũ liệt kê tay 7 trường, trong khi `tab_audit_log` nay có
   20 cột — nghĩa là bản lưu trữ rụng sạch `request_id`, `ip`, `session_id`,
   `actor_kind`, `doc_code`… đúng phần ngữ cảnh mà cả CR-312 dựng ra. Nay đọc
   cột từ mapper, nên thêm cột ở model là bản lưu trữ tự có.
2. **Có tệp `.sha256`.** Không có nó thì "bản lưu trữ" chỉ là một tệp gz, không
   ai chứng minh được nó chưa bị thay. Đặt `mtime=0` cho gzip để cùng dữ liệu
   luôn cho ra cùng byte — không thì mỗi lần chạy lại ra một mã băm khác và mã
   băm hết nói lên điều gì.
3. **Hỏng thì NÉM LỖI.** Bản cũ nuốt mọi ngoại lệ rồi trả `{"status": "failed"}`,
   mà không ai đọc giá trị trả về của một việc chạy nền — R2 hết hạn khóa thì
   suốt nhiều tháng không có bản lưu trữ nào, trong im lặng hoàn toàn.
"""
import gzip
import hashlib
import io
import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import inspect as sa_inspect

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.storage import env_prefix, is_remote_storage_ready, upload_fileobj
from app.modules.request_log.model import RequestLog

from .model import AuditLog

log = logging.getLogger("app.audit.archive")

#  Đọc theo lô thay vì `.all()`. Một tháng của prod hôm nay là vài nghìn dòng
#  audit — nhưng nay ghi cả GET, nên `tab_request_log` một tháng là ~90.000 dòng
#  và con số đó còn tăng. `.all()` nạp trọn vào RAM của container Celery.
ARCHIVE_CHUNK = 2000

ARCHIVE_TABLES = (("audit", AuditLog), ("request", RequestLog))


def _month_bounds(ref: datetime) -> tuple[datetime, datetime, str]:
    """Mốc đầu/cuối của THÁNG TRƯỚC so với ref, và nhãn 'YYYY-MM'."""
    first_this = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # lùi 1 ngày để rơi vào tháng trước, rồi lấy ngày 1 của tháng đó
    last_prev = first_this - timedelta(days=1)
    start = last_prev.replace(day=1)
    return start, first_this, f"{start:%Y-%m}"


def _jsonable(value):
    """Giá trị cột -> thứ `json.dumps` nuốt được.

    `bytes` ra chuỗi hex chứ không base64: `request_id` và `device_hash` đều là
    nhị phân, mà hex thì dán thẳng vào `WHERE request_id = UNHEX('...')` được —
    bản lưu trữ phải tra được bằng tay, đó là toàn bộ lý do nó tồn tại.
    """
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _row_to_dict(row, columns) -> dict:
    return {name: _jsonable(getattr(row, name, None)) for name in columns}


def _column_names(model) -> list[str]:
    return [c.key for c in sa_inspect(model).mapper.column_attrs]


def _archive_table(db, model, name: str, start: datetime, end: datetime, label: str) -> dict:
    """Gói một bảng của một tháng thành `.jsonl.gz` + `.sha256` trên R2."""
    columns = _column_names(model)
    raw = io.BytesIO()
    rows = 0
    #  `mtime=0`: gzip mặc định nhét thời điểm nén vào header, nên cùng dữ liệu
    #  chạy hai lần ra hai tệp khác byte — và mã băm mất hết ý nghĩa đối chiếu.
    with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=6, mtime=0) as gz:
        query = (db.query(model)
                 .filter(model.created_at >= start, model.created_at < end)
                 .order_by(model.id.asc()))
        for row in query.yield_per(ARCHIVE_CHUNK):
            line = json.dumps(_row_to_dict(row, columns), ensure_ascii=False)
            gz.write((line + "\n").encode("utf-8"))
            rows += 1
    if rows == 0:
        return {"table": name, "rows": 0, "status": "empty"}

    blob = raw.getvalue()
    digest = hashlib.sha256(blob).hexdigest()
    key = f"{env_prefix()}/log-archive/{label}/{name}.jsonl.gz"
    upload_fileobj(io.BytesIO(blob), key, "application/gzip")
    upload_fileobj(io.BytesIO(f"{digest}  {name}.jsonl.gz\n".encode("utf-8")),
                   f"{key}.sha256", "text/plain")
    return {"table": name, "rows": rows, "status": "success",
            "key": key, "size": len(blob), "sha256": digest}


@celery_app.task(name="audit.archive")
def archive_audit_task(month: str | None = None) -> dict:
    """Xuất nhật ký của tháng trước ra R2. KHÔNG xóa dữ liệu.

    `month='YYYY-MM'` (tùy chọn) để chạy tay một tháng cụ thể.
    """
    #  ⚠️ CHẶN Ở ĐÂY, KHÔNG ĐỂ `upload_fileobj` TỰ XOAY. Khi R2 chưa cấu hình,
    #  nó lặng lẽ ghi xuống `uploads/<key>` — mà `uploads/` được `main.py` gắn
    #  ra `/api/uploads` bằng `StaticFiles` KHÔNG có lớp gác nào. Nghĩa là bản
    #  lưu trữ chứa nguyên nhật ký toàn hệ sẽ nằm ở một URL công khai đoán được.
    #  Máy nào chưa nối R2 thì thà không có bản lưu trữ, còn hơn có một bản ai
    #  cũng tải được.
    if not is_remote_storage_ready():
        raise RuntimeError(
            "Chưa cấu hình R2 nên không đóng gói nhật ký. Không ghi tạm xuống "
            "'uploads/' vì thư mục đó phục vụ công khai qua /api/uploads.")

    db = SessionLocal()
    try:
        if month:
            y, m = (int(x) for x in month.split("-"))
            start = datetime(y, m, 1)
            end = datetime(y + (m // 12), (m % 12) + 1, 1)
            label = f"{start:%Y-%m}"
        else:
            start, end, label = _month_bounds(datetime.now())

        results = [_archive_table(db, model, name, start, end, label)
                   for name, model in ARCHIVE_TABLES]
        total = sum(r["rows"] for r in results)
        log.info("Đã đóng gói nhật ký tháng %s: %s dòng", label, total)
        return {"status": "success" if total else "empty", "month": label,
                "rows": total, "tables": results}
    finally:
        db.close()
