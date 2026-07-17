"""Task kiểm tra hạ tầng Celery (smoke test). Không dùng trong logic nghiệp vụ."""
from app.core.celery_app import celery_app


@celery_app.task(name="debug.ping")
def ping(message: str = "pong") -> dict:
    """Trả lại message để xác nhận worker hoạt động."""
    return {"status": "ok", "echo": message}
