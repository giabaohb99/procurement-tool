"""Celery app dùng chung cho toàn bộ procurement-tool.

Import ở mọi nơi:  from app.core.celery_app import celery_app
Chạy worker:       celery -A app.core.celery_app worker -l info
Chạy beat:         celery -A app.core.celery_app beat -l info
"""
from celery import Celery
from celery.schedules import crontab

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
        "app.modules.backup.tasks",       # Sao lưu CSDL định kỳ (2 lần/ngày)
        "app.modules.notification.tasks", # Dọn thông báo cũ (mỗi ngày)
        "app.modules.audit.tasks",        # Lưu trữ audit ra R2 (hằng tháng, không xóa DB)
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

    # Lịch beat — giờ Hà Nội (enable_utc=False). Sao lưu CSDL 2 lần/ngày.
    beat_schedule={
        "backup-db-sang": {
            "task": "backup.run",
            "schedule": crontab(hour=1, minute=0),   # 01:00 VN
            "kwargs": {"source": "auto", "actor_id": 0},
        },
        "backup-db-chieu": {
            "task": "backup.run",
            "schedule": crontab(hour=13, minute=0),  # 13:00 VN
            "kwargs": {"source": "auto", "actor_id": 0},
        },
        "cleanup-notifications": {
            "task": "notification.cleanup",
            "schedule": crontab(hour=2, minute=30),  # 02:30 VN, mỗi ngày
        },
        "archive-audit-monthly": {
            "task": "audit.archive",
            "schedule": crontab(day_of_month=1, hour=3, minute=0),  # 03:00 ngày 1 hằng tháng
        },
    },
)
