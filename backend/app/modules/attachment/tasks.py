"""Dọn tệp đính kèm MỒ CÔI — chạy theo lịch (celery-beat), bao-CR-408 (BM-031).

Mồ côi = dòng `tab_file` của khâu đính kèm mà không có `tab_file_link` nào trỏ tới.
Chúng sinh ra ở `POST /api/attachments/upload-file`: tệp lên storage TRƯỚC khi bản ghi
cha có id, rồi `/register` mới gắn dây. Người dùng bỏ dở form là tệp nằm lại vĩnh viễn
— `_delete_file_if_orphan` chỉ thức dậy khi có ai xóa một dây, mà tệp chưa từng có dây
thì không có nhịp nào chạm tới nó.

⚠️ Giữ `ORPHAN_KEEP_DAYS` (7 ngày) chứ đừng dọn ngay trong ngày: có luồng người dùng
tải tệp lên hôm nay rồi mai mới quay lại bấm Lưu phiếu.
"""
import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.database import SessionLocal

from .service import ORPHAN_KEEP_DAYS, purge_orphan_files


@celery_app.task(name="attachment.purge_orphans")
def purge_orphan_files_task(keep_days: int | None = None) -> dict:
    """Xóa tệp đính kèm mồ côi quá hạn (cả dòng DB lẫn object trên storage)."""
    days = ORPHAN_KEEP_DAYS if keep_days is None else keep_days
    db = SessionLocal()
    try:
        deleted = purge_orphan_files(db, keep_days=days)
    finally:
        db.close()
    return {"status": "done", "keep_days": days, "deleted": deleted}
