"""Celery app dùng chung cho toàn bộ procurement-tool.

Import ở mọi nơi:  from app.core.celery_app import celery_app
Chạy worker:       celery -A app.core.celery_app worker -l info
Chạy beat:         celery -A app.core.celery_app beat -l info
"""
import os
import sys

# Đảm bảo /app (WORKDIR của container) trong sys.path, để các module nằm ngoài
# backend/ (ví dụ scripts/legacy_sync/) import được khi chạy trong Celery worker.
# Celery fork worker không kế thừa sys.path của tiến trình cha đầy đủ.
_app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _app_root not in sys.path:
    sys.path.insert(0, _app_root)

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "procurement",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Lịch sao lưu CSDL. Prod: 2 lần/ngày (01:00 + 13:00). Dev đặt BACKUP_ONCE_DAILY=true
# để chỉ giữ lịch sáng — một dãy dict dựng động, không viết cứng hai lịch ở dưới.
_backup_schedule = {
    "backup-db-sang": {
        "task": "backup.run",
        "schedule": crontab(hour=1, minute=0),   # 01:00 VN
        "kwargs": {"source": "auto", "actor_id": 0},
    },
}
if not settings.BACKUP_ONCE_DAILY:
    _backup_schedule["backup-db-chieu"] = {
        "task": "backup.run",
        "schedule": crontab(hour=13, minute=0),  # 13:00 VN
        "kwargs": {"source": "auto", "actor_id": 0},
    }

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
        "app.modules.audit.tasks",        # Đóng gói nhật ký ra R2 (hằng tháng, không xóa DB)
        "app.modules.request_log.tasks",  # Dọn dòng GET quá 90 ngày (mỗi ngày, sau khi đã có gói R2)
        "app.modules.attachment.tasks",   # Dọn tệp đính kèm mồ côi quá 7 ngày (mỗi ngày)
        "app.modules.assistant.rag.tasks",  # Nạp chỉ mục vector loại B (HDSD + FAQ) khi có hook / bấm nút
        "app.modules.coffee_point.tasks",   # Điểm cà phê × POS365 — kéo đơn / reset kỳ / đối chiếu
        "app.modules.legacy_datxe.tasks",   # App đặt xe / duyệt dấu cũ — lưới an toàn + chạy lại
        "app.modules.agent_hub.tasks",      # Agent Hub — kéo tin Telegram, gom việc, nạp kho tài liệu
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

    #  Việc sửa mã của Agent Hub (bậc 2, ai-CR-011) đi hàng đợi RIÊNG: chỉ service
    #  `agent-runner` (có git + node + Claude Code CLI, có volume worktree) nghe `agent_code`;
    #  `celery-worker` thường nghe hàng đợi mặc định nên không bao giờ nhận nhầm việc này,
    #  và runner cũng không nhận việc thường.
    task_routes={
        "agent.code_task": {"queue": "agent_code"},
        "agent.publish_task": {"queue": "agent_code"},   # ai-CR-012: đẩy nhánh + mở PR
        "agent.ask_task": {"queue": "agent_code"},       # ai-CR-013: hỏi thêm về bản vá
        "agent.scan_task": {"queue": "agent_code"},      # ai-CR-017: rà soát mã trước kế hoạch
        "agent.deploy_task": {"queue": "agent_code"},    # ai-CR-014: gộp erp-v2 + deploy dev
        "agent.revert_task": {"queue": "agent_code"},    # ai-CR-014: thu hồi bản gộp
        "agent.cleanup_task": {"queue": "agent_code"},   # ai-CR-033: dọn nhánh bot khi việc đóng
    },

    # Lịch beat — giờ Hà Nội (enable_utc=False). Sao lưu CSDL: xem _backup_schedule.
    beat_schedule={
        **_backup_schedule,
        "cleanup-notifications": {
            "task": "notification.cleanup",
            "schedule": crontab(hour=2, minute=30),  # 02:30 VN, mỗi ngày
        },
        "archive-audit-monthly": {
            "task": "audit.archive",
            "schedule": crontab(day_of_month=1, hour=3, minute=0),  # 03:00 ngày 1 hằng tháng
        },
        #  ⚠️ 03:40 chứ không phải 03:00 — phải chạy SAU việc đóng gói tháng.
        #  Ngày 1 hằng tháng hai việc này cùng thức dậy; đảo thứ tự thì có đêm
        #  dọn trước, đóng gói sau, và phần bị dọn không nằm trong gói nào.
        #  (Bản thân việc dọn còn tự kiểm tra R2 trước khi xóa, nhưng đặt lịch
        #  đúng thì không phải trông vào chốt cuối.)
        "cleanup-get-logs": {
            "task": "request_log.cleanup",
            "schedule": crontab(hour=3, minute=40),  # 03:40 VN, mỗi ngày
        },
        #  Tệp tải lên mà không bao giờ được gắn vào phiếu nào (người dùng bỏ dở form)
        #  — trước bao-CR-408 chúng nằm lại vĩnh viễn trên storage. Xem attachment/tasks.py.
        "purge-orphan-attachments": {
            "task": "attachment.purge_orphans",
            "schedule": crontab(hour=4, minute=10),  # 04:10 VN, mỗi ngày
        },
        # --- Điểm cà phê × POS365 (doc/erp/diem-ca-phe/03 §4). Cầu dao
        # POS365_HARD_OFF: khi tắt thì không đưa các task này vào lịch beat.
        # coffee.mirror_balance (D-07) CHƯA có lịch — bật sau khi POC P5 xác nhận
        # PartnerSave ghi được Point.
        # --- App đặt xe / duyệt dấu cũ (doc/dong-bo-dat-xe-duyet-dau/ §11).
        # Đường chính là cái móc bên app cũ gọi thẳng vào ERP; hai vòng này là
        # lưới an toàn. Chưa bật SYNC_DATXE_ENABLED hoặc chưa khai khóa đọc
        # Firebase thì chúng kết thúc ngay bằng một dòng sổ SKIPPED.
        "datxe-pull-updated": {
            "task": "datxe.pull_updated",
            "schedule": crontab(minute=f"*/{settings.SYNC_DATXE_PULL_MINUTES}"),
        },
        #  Lệch nhịp với vòng kéo (phút lẻ 3, 13, 23…): hai vòng cùng thức dậy
        #  thì chúng tranh nhau chính những dòng sổ vừa hỏng.
        "datxe-retry-pending": {
            "task": "datxe.retry_pending",
            "schedule": crontab(minute="3,13,23,33,43,53"),
        },
    },
)

#  Agent Hub — chỉ đưa vào lịch khi đã bật, vì hai vòng này thức dậy rất dày và
#  không có lý do gì để chúng chạy trên máy chưa cấu hình bot.
if settings.AGENT_HUB_ENABLED:
    celery_app.conf.beat_schedule.update({
        "agent-triage-inbox": {
            "task": "agent.triage_inbox",
            "schedule": crontab(minute="*"),
            "options": {"expires": 50},
        },
        #  Hẹn giờ gộp + deploy dev (ai-CR-014): vòng này nhặt dòng sổ STAGE_DEPLOY đã tới giờ
        #  rồi ném `agent.deploy_task` sang runner. Cố ý KHÔNG dùng `eta` của Celery: việc có eta
        #  nằm trong bộ nhớ worker, restart runner là mất hẹn mà không ai biết; dòng sổ thì còn.
        "agent-deploy-due": {
            "task": "agent.deploy_due",
            "schedule": crontab(minute="*"),
            "options": {"expires": 50},
        },
        #  ai-CR-021: việc chạy lâu mà im quá 90 giây thì nhắn «em vẫn đang làm», rồi cập nhật phút.
        "agent-heartbeat": {
            "task": "agent.heartbeat",
            "schedule": crontab(minute="*"),
            "options": {"expires": 50},
        },
        #  ai-CR-037: phiếu hỗ trợ ERP giao cho bot / mang nhãn bộ phận đã khai -> việc của bot.
        "agent-pull-tickets": {
            "task": "agent.pull_tickets",
            "schedule": crontab(minute="*"),
            "options": {"expires": 50},
        },
    })
    #  Vòng kéo tin CHỈ vào lịch khi không có tiến trình `agent-poller` riêng (ai-CR-008):
    #  poller giữ kết nối chờ tin, còn vòng này hỏi-rồi-về mỗi 10 giây. Hai bên cùng đọc
    #  một con trỏ là xử trùng một tin, nên cờ `AGENT_LONG_POLL` chọn đúng MỘT bên.
    if not settings.AGENT_LONG_POLL:
        celery_app.conf.beat_schedule["agent-poll-telegram"] = {
            #  10 giây một lượt: Telegram không giữ kết nối chờ (xem `telegram.POLL_TIMEOUT`)
            #  nên độ trễ đại ca cảm thấy đúng bằng nhịp này.
            #  `expires` NGẮN HƠN nhịp là chủ ý: worker bận một phút rồi rảnh ra thì sáu
            #  lượt kéo cũ dồn cục sẽ chạy liền nhau và cùng đọc một con trỏ — thà bỏ đi.
            "task": "agent.poll_telegram",
            "schedule": 10.0,
            "options": {"expires": 8},
        }

if not settings.POS365_HARD_OFF:
    celery_app.conf.beat_schedule.update({
        "coffee-pull-orders": {
            "task": "coffee.pull_orders",
            "schedule": crontab(minute=f"*/{settings.POS365_PULL_MINUTES}"),
        },
        "coffee-check-voids": {
            "task": "coffee.check_voids",
            "schedule": crontab(minute=15),
        },
        "coffee-monthly-reset": {
            "task": "coffee.monthly_reset",
            "schedule": crontab(day_of_month=1, hour=0, minute=5),
        },
        "coffee-reconcile": {
            "task": "coffee.reconcile",
            "schedule": crontab(hour=6, minute=0),
        },
    })

