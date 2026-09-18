"""Bốn việc chạy nền của Agent Hub. Lịch beat khai ở `core/celery_app.py`.

Cả bốn đều GÁC CỜ `AGENT_HUB_ENABLED` ở dòng đầu: worker có thể đang chạy trong khi
`.env` chưa bật, và một con bot tự nhắn tin cho người ta vì ai đó quên tắt cờ là loại
lỗi không xin lỗi được.

⚠️ KHÔNG `autoretry_for` ở vòng kéo tin. Kéo hỏng thì 10 giây nữa có lượt mới, còn thử
lại thì lượt cũ và lượt mới cùng đọc một con trỏ và xử trùng một tin.
"""
import logging

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper trước khi mở session
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal

from . import memory, service, telegram

log = logging.getLogger("app.agent_hub.tasks")


def _off() -> dict | None:
    if not telegram.is_enabled():
        return {"status": "skipped", "reason": "AGENT_HUB_ENABLED / token / chat_id chưa đủ"}
    return None


@celery_app.task(name="agent.poll_telegram")
def poll_telegram_task() -> dict:
    """Kéo tin Telegram. Chạy mỗi 10 giây.

    ponytail: không có khóa chống chạy chồng — `celery-worker` đang chạy `-c 1` nên chỉ
    một việc chạy tại một thời điểm. Nâng lên nhiều tiến trình thì phải thêm khóa Redis
    quanh chỗ đọc/ghi con trỏ, không thì hai lượt cùng đọc một offset và xử trùng.
    """
    if (off := _off()) is not None:
        return off
    db = SessionLocal()
    try:
        n = service.poll_once(db)
        db.commit()
        return {"status": "success", "updates": n}
    except Exception:
        db.rollback()
        log.exception("agent_hub: vòng kéo tin hỏng")
        return {"status": "error"}
    finally:
        db.close()


@celery_app.task(name="agent.triage_inbox")
def triage_inbox_task() -> dict:
    """Gom tin đã nằm yên đủ lâu thành task. Chạy mỗi phút."""
    if (off := _off()) is not None:
        return off
    db = SessionLocal()
    try:
        n = service.triage_inbox(db)
        db.commit()
        return {"status": "success", "tasks": n}
    except Exception:
        db.rollback()
        log.exception("agent_hub: vòng gom hỏng")
        return {"status": "error"}
    finally:
        db.close()


@celery_app.task(name="agent.reindex_docs")
def reindex_docs_task() -> dict:
    """Nạp lại kho tài liệu vào Qdrant. Chạy TAY, không có lịch.

    Cố ý không đặt lịch: tài liệu chỉ đổi khi có người sửa, mà một lượt nạp là vài
    nghìn lượt nhúng.

    ⚠️ Phải chạy TRONG `celery-worker` — `doc/` chỉ mount ở đó, container `api` không
    thấy thư mục ấy. Gọi bằng:
        docker compose exec celery-worker python -c \
          "from app.modules.agent_hub.tasks import reindex_docs_task; print(reindex_docs_task())"
    """
    if not settings.AGENT_GEMINI_API_KEY:
        return {"status": "skipped", "reason": "AGENT_GEMINI_API_KEY chưa khai"}
    return {"status": "success", **memory.reindex()}
