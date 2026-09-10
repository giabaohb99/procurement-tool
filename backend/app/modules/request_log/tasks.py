"""Dọn dòng ĐỌC quá hạn khỏi `tab_request_log` (bao-CR-346).

Việc này là **điều kiện đi kèm** của quyết định ghi hết GET, không phải một tối
ưu thêm vào sau. Đo trên prod: 7.440 lượt GET/ngày, bỏ hai đầu gọi máy dội thì
còn ~3.000. Giữ đủ 16 tháng như dòng ghi thì riêng phần đọc là ~1,4 triệu dòng,
nằm chen giữa vài chục nghìn dòng thao tác thật — và bảng sẽ chậm đúng ở màn
dựng ra để tra nó.

Hai luật, và luật thứ hai mới là luật quan trọng:

1. Chỉ xóa dòng `method = 'GET'` cũ hơn `GET_RETENTION_DAYS`. Dòng ghi (POST /
   PATCH / PUT / DELETE) **không bao giờ** bị đụng tới ở đây.
2. **Chỉ xóa thứ đã có bản sao ngoài máy.** Việc đóng gói tháng
   (`audit.archive`) chép nguyên vẹn cả bảng lên R2 kèm mã băm; chưa cấu hình
   R2 thì việc này tự tắt. Xóa bản duy nhất của một dòng nhật ký là **hủy chứng
   cứ**, và một việc chạy nền lúc 3 giờ sáng không phải chỗ để quyết định đó
   xảy ra vì lỡ thiếu một biến môi trường.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging_policy import (CLEANUP_BATCH_SIZE, CLEANUP_MAX_BATCHES,
                                     GET_RETENTION_DAYS)
from app.core.storage import is_remote_storage_ready

from .model import RequestLog

log = logging.getLogger("app.request_log.cleanup")


@celery_app.task(name="request_log.cleanup")
def cleanup_get_logs_task(days: int = 0, dry_run: bool = False) -> dict:
    """Xóa theo LÔ các dòng GET quá hạn. Trả về số dòng đã xóa.

    `days` để chạy tay với hạn khác; `dry_run=True` chỉ đếm, không xóa.
    """
    if not is_remote_storage_ready() and not dry_run:
        #  Không ném lỗi: máy dev không nối R2 là chuyện bình thường, và làm đỏ
        #  bảng việc nền mỗi đêm thì ba hôm sau không ai đọc bảng đó nữa.
        log.info("Bỏ qua dọn nhật ký GET: chưa cấu hình R2 nên chưa có bản sao ngoài máy.")
        return {"status": "skipped", "reason": "no_remote_archive", "deleted": 0}

    cutoff = datetime.now() - timedelta(days=days or GET_RETENTION_DAYS)
    db = SessionLocal()
    try:
        condition = (RequestLog.method == "GET") & (RequestLog.created_at < cutoff)
        if dry_run:
            total = db.execute(select(func.count()).select_from(RequestLog)
                               .where(condition)).scalar() or 0
            return {"status": "dry_run", "cutoff": cutoff.isoformat(), "matched": total}

        deleted = 0
        for _ in range(CLEANUP_MAX_BATCHES):
            #  ⚠️ XÓA THEO LÔ, KHÔNG XÓA MỘT PHÁT. Một câu `DELETE` quét vài trăm
            #  nghìn dòng giữ khóa đủ lâu để **mọi lượt gọi API đứng chờ ghi nhật
            #  ký** — dọn rác mà thành sự cố toàn hệ. Chọn id trước rồi xóa theo
            #  `IN` vì MySQL không cho `DELETE ... LIMIT` đi kèm subquery cùng bảng.
            ids = [row[0] for row in db.execute(
                select(RequestLog.id).where(condition)
                .order_by(RequestLog.id.asc()).limit(CLEANUP_BATCH_SIZE))]
            if not ids:
                break
            db.execute(delete(RequestLog).where(RequestLog.id.in_(ids)))
            db.commit()
            deleted += len(ids)
        else:
            #  Chạm trần số lô: còn dòng chưa xóa, để lần chạy sau. Nói ra thay
            #  vì lặng lẽ dừng — trần này tồn tại để một lần chạy không kéo dài
            #  vô hạn, chứ không phải để giấu chuyện dọn chưa hết.
            log.warning("Dọn nhật ký GET chạm trần %s lô, còn dòng quá hạn chưa xóa.",
                        CLEANUP_MAX_BATCHES)

        log.info("Đã dọn %s dòng GET cũ hơn %s", deleted, cutoff.date())
        return {"status": "success", "cutoff": cutoff.isoformat(), "deleted": deleted}
    finally:
        db.close()
