"""Tác vụ Celery dựng chỉ mục tìm kiếm toàn văn — chạy trên celery-worker.

Cùng khuôn `app/modules/assistant/rag/tasks.py`: SESSION RIÊNG (task mở
`SessionLocal()` của chính nó, request đã đóng khi task chạy), RETRY có giãn
cách cho lỗi tạm thời (mạng chập lúc đọc R2, khóa dòng MySQL). Không cần cờ
"tính năng tắt" như RAG — tìm kiếm văn bản luôn bật cùng phân hệ Văn thư.
"""
import logging

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper trước khi mở session
from app.core.celery_app import celery_app
from app.core.database import SessionLocal

from . import search_index_service

log = logging.getLogger("app.document.search")

_RETRY = dict(
    autoretry_for=(Exception,),
    max_retries=5,
    retry_backoff=4,
    retry_backoff_max=300,
    retry_jitter=True,
)


@celery_app.task(name="document.search.reindex", **_RETRY)
def reindex_document_task(document_id: int) -> dict:
    """Dựng lại chỉ mục của MỘT văn bản. Văn bản đã bị xóa → xóa dòng chỉ mục,
    không lỗi (`search_index_service.reindex` tự xử lý cả hai trường hợp)."""
    db = SessionLocal()
    try:
        row = search_index_service.reindex(db, document_id)
        return {"status": "success", "document_id": document_id,
               "indexed": row is not None}
    finally:
        db.close()
