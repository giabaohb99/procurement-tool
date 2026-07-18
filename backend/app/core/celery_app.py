"""Celery app dùng chung cho toàn bộ procurement-tool.

Import ở mọi nơi:  from app.core.celery_app import celery_app
Chạy worker:       celery -A app.core.celery_app worker -l info
Chạy beat:         celery -A app.core.celery_app beat -l info
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "procurement",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    # Múi giờ VN — mọi crontab + timestamp theo giờ Hà Nội (khỏi cộng trừ 7h)
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=False,

    # Liệt kê task tường minh (không autodiscover mù). Thêm module khi làm phase sau:
    imports=[
        "app.tasks.debug",              # Phase 0 — smoke test ping
        "app.modules.import_tool.tasks",  # Import Khảo sát / Đơn mua hàng (chạy nền)
        # "app.tasks.alerts",           # Phase 2 — cảnh báo theo lịch
        # "app.tasks.report_tasks",     # Phase 3 — refresh báo cáo
    ],

    # Serialization JSON (an toàn hơn pickle)
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Kết quả task sống 24h (đủ debug, không phình Redis)
    result_expires=86400,

    # Worker crash giữa chừng → task quay lại queue, không mất
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Lịch beat — các phase sau điền vào
    beat_schedule={},
)
