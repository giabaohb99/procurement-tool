"""Móc nối nghiệp vụ -> chỉ mục vector. Service HDSD/FAQ gọi hai hàm này sau khi commit.

HAI nguyên tắc cứng ở đây:
  1. GÁC CỜ: RAG tắt (AI_RAG_ENABLED=false) thì không làm gì — môi trường không có Qdrant vẫn
     lưu bài bình thường.
  2. NUỐT LỖI: chỉ XẾP HÀNG cho worker (.delay) rồi trả ngay — không nhúng ngay tại đây. Việc
     nhúng/nạp thật chạy nền ở celery-worker (có retry). Lỡ broker (Redis) chập lúc xếp hàng thì
     ghi log rồi thôi, TUYỆT ĐỐI không để vỡ việc lưu bài; bấm 'Nạp lại chỉ mục' sau là xong.
"""
import logging

from sqlalchemy.orm import Session

from app.core.config import settings

from .tasks import reindex_source_task, remove_source_task

log = logging.getLogger("app.assistant.rag")


def on_source_saved(db: Session, source: str, source_id: int) -> None:
    """Gọi sau khi tạo/sửa một bài HDSD hoặc câu FAQ. `db` giữ cho khớp chữ ký cũ, không dùng
    tới nữa — worker tự mở session riêng."""
    if not settings.AI_RAG_ENABLED:
        return
    try:
        reindex_source_task.delay(source, source_id)
    except Exception:  # noqa: BLE001 - lỗi xếp hàng (broker) không được làm vỡ nghiệp vụ
        log.exception("Xếp hàng nạp lại chỉ mục thất bại: %s#%s", source, source_id)


def on_source_deleted(source: str, source_id: int) -> None:
    """Gọi sau khi xóa một bài HDSD hoặc câu FAQ."""
    if not settings.AI_RAG_ENABLED:
        return
    try:
        remove_source_task.delay(source, source_id)
    except Exception:  # noqa: BLE001
        log.exception("Xếp hàng xóa chỉ mục thất bại: %s#%s", source, source_id)
