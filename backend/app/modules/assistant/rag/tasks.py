"""Task nền nạp chỉ mục vector loại B (HDSD + FAQ) — chạy trên celery-worker.

Vì sao đẩy ra worker: nhúng đoạn văn gọi Gemini API qua mạng, lúc nghẽn có thể mất vài giây.
Không giữ request lưu bài / bấm nút chờ mạng — hook chỉ XẾP HÀNG (.delay) rồi trả ngay.

Ba nguyên tắc:
  1. SESSION RIÊNG: task mở `SessionLocal()` của chính nó, KHÔNG dùng session của request
     (request đã đóng khi task chạy). Luôn đóng ở finally.
  2. RETRY: lỗi phụ trợ (Gemini hết quota, Qdrant sập, mạng chập) là tạm thời -> tự thử lại
     có giãn cách (backoff). Bản ghi bị xóa mất thì reindex_source trả 0 lặng lẽ, không lỗi.
  3. GÁC CỜ: RAG tắt -> task về ngay, phòng khi worker chạy mà .env chưa bật.
"""
import logging

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper trước khi mở session
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal

from . import indexer

log = logging.getLogger("app.assistant.rag")

# Thử lại tối đa 5 lần, giãn 4s -> 8s -> ... trần 5 phút, có nhiễu để khỏi dồn cục.
_RETRY = dict(
    autoretry_for=(Exception,),
    max_retries=5,
    retry_backoff=4,
    retry_backoff_max=300,
    retry_jitter=True,
)


@celery_app.task(name="assistant.rag.reindex_source", **_RETRY)
def reindex_source_task(source: str, source_id: int) -> dict:
    """Nạp lại chỉ mục MỘT bài HDSD / câu FAQ. Trả số đoạn đã nạp."""
    if not settings.AI_RAG_ENABLED:
        return {"status": "skipped", "reason": "AI_RAG_ENABLED=false"}
    db = SessionLocal()
    try:
        n = indexer.reindex_source(db, source, source_id)
        return {"status": "success", "source": source, "source_id": source_id, "chunks": n}
    finally:
        db.close()


@celery_app.task(name="assistant.rag.remove_source", **_RETRY)
def remove_source_task(source: str, source_id: int) -> dict:
    """Xóa mọi đoạn của một bản ghi đã bị xóa. Không đụng DB."""
    if not settings.AI_RAG_ENABLED:
        return {"status": "skipped", "reason": "AI_RAG_ENABLED=false"}
    indexer.remove_source(source, source_id)
    return {"status": "success", "source": source, "source_id": source_id}


@celery_app.task(name="assistant.rag.rebuild_all", **_RETRY)
def rebuild_all_task() -> dict:
    """Dựng lại TOÀN BỘ chỉ mục (đường A) — do nút 'Nạp lại chỉ mục' ở Cấu hình hệ thống gọi.

    RẢI RA, không nạp cả mẻ trong một task: chỉ liệt kê mọi nguồn rồi xếp mỗi nguồn MỘT task
    `reindex_source` riêng. Vì sao: nhúng có trần request/phút (key free 100/phút) — gộp một khối
    mà 429 giữa chừng thì retry chạy lại từ đầu, khó xong; rải ra thì worker (`-c 2`) tự tiết lưu
    lượng dưới trần, và nguồn nào 429 chỉ mình nó retry, không kéo cả mẻ. Point id tất định nên
    nạp đè đúng chỗ, chạy lại vô hại.
    """
    if not settings.AI_RAG_ENABLED:
        return {"status": "skipped", "reason": "AI_RAG_ENABLED=false"}
    db = SessionLocal()
    try:
        refs = indexer.all_source_refs(db)
    finally:
        db.close()
    for source, source_id in refs:
        reindex_source_task.delay(source, source_id)
    log.info("Đã rải %s task nạp lại chỉ mục", len(refs))
    return {"status": "queued", "sources": len(refs)}
