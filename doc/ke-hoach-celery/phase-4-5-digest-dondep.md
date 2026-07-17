# Phase 4–5 — Digest / Dọn dẹp / Sao lưu DB / Export Excel async

> **Thứ tự ưu tiên**: Phase 0 (hạ tầng) phải hoàn thành trước khi chạy bất kỳ task nào ở đây.
> Timezone mọi cron: `Asia/Ho_Chi_Minh`. Session: task tự mở `SessionLocal()` và đóng.

---

## Phase 4 — Digest / Nhắc việc chờ duyệt

### 1. Mục tiêu

Nhắc người duyệt qua **chuông in-app** (và tùy chọn email digest) khi còn phiếu đang chờ duyệt
vào cuối giờ làm việc mỗi ngày. Tránh tình trạng phiếu bị bỏ quên trong hàng đợi.

Ba loại phiếu cần nhắc:
- **PYC** (`tab_purchase_request`, `status = "submitted"`) — người duyệt là **Trưởng bộ phận** của từng phòng tạo phiếu.
- **YCKS** (`tab_survey_request`, `status = "submitted"`) — người duyệt tìm qua `get_approvers_for_entity(db, "survey_request")`.
- **YCTT** (`tab_payment_request`, `status = "submitted"`) — người duyệt tìm qua `get_approvers_for_entity(db, "payment_request")`.

### 2. Phạm vi & việc cụ thể

- [ ] Tạo file `backend/app/tasks/digest.py` chứa task `send_pending_digest`.
- [ ] Đăng ký beat schedule trong `backend/app/celery_app.py` (hoặc `celeryconfig.py`).
- [ ] Hàm digest PYC: gom phiếu `submitted` + `is_deleted = False` theo `department`, tìm trưởng phòng qua `get_department_head_users`.
- [ ] Hàm digest YCKS / YCTT: đếm tổng phiếu, tìm người duyệt qua `get_approvers_for_entity`.
- [ ] Tạo `Notification` (in-app bell) cho từng người duyệt — KHÔNG tạo nếu không có phiếu chờ.
- [ ] (Tùy chọn) Gửi email digest qua `send_smtp_email` khi `app_settings.get("email_enabled")` là `True`.
- [ ] Đánh dấu idempotent: không tạo chuông trùng nếu đã nhắc trong ngày (xem mục 5).

### 3. Thiết kế kỹ thuật

**File tạo mới:** `backend/app/tasks/digest.py`

```python
"""Phase 4 — Digest: nhắc người duyệt khi còn phiếu chờ duyệt."""
from __future__ import annotations

from datetime import date
from collections import defaultdict

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.modules.notification.model import Notification, EmailLog
from app.modules.notification.service import (
    get_approvers_for_entity,
    get_department_head_users,
    render_template,
    send_smtp_email,
)
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey_request.model import SurveyRequest
from app.modules.payment_request.model import PaymentRequest
from app.modules.user.model import User
from app.core import app_settings


DIGEST_TITLE = "[Nhắc việc] Còn {n} phiếu chờ duyệt — {today}"


@celery_app.task(name="digest.send_pending_digest", bind=True, max_retries=2)
def send_pending_digest(self):
    """Nhắc người duyệt qua chuông (+ email nếu bật) về phiếu chờ duyệt."""
    db = SessionLocal()
    today = date.today().strftime("%d/%m/%Y")
    try:
        _digest_pyc(db, today)
        _digest_generic(db, today, "survey_request", SurveyRequest, "YCKS")
        _digest_generic(db, today, "payment_request", PaymentRequest, "YCTT")
        db.commit()
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()


# ---- PYC: gom theo phòng ban, nhắc Trưởng bộ phận tương ứng ----

def _digest_pyc(db, today: str):
    pending = (
        db.query(PurchaseRequest)
        .filter(PurchaseRequest.status == "submitted", PurchaseRequest.is_deleted == False)
        .all()
    )
    if not pending:
        return

    # Gom số lượng phiếu theo phòng ban
    dept_count: dict[str, int] = defaultdict(int)
    for pr in pending:
        if pr.department:
            dept_count[pr.department] += 1

    seen_user_ids: set[int] = set()
    for dept, count in dept_count.items():
        heads = get_department_head_users(db, dept)
        for user in heads:
            if user.id in seen_user_ids:
                continue
            # Idempotent: bỏ qua nếu đã nhắc hôm nay (xem mục 5)
            if _already_notified_today(db, user.id, "digest_pyc"):
                continue
            seen_user_ids.add(user.id)
            title = DIGEST_TITLE.format(n=count, today=today)
            body = (
                f"Phòng {dept} có {count} Yêu cầu mua hàng (PYC) đang chờ bạn phê duyệt. "
                f"Vui lòng xử lý để không ảnh hưởng tiến độ mua hàng."
            )
            db.add(Notification(
                user_id=user.id,
                title=title,
                body=body,
                link="/purchase-requests?status=submitted",
                created_by=0,
            ))
            _maybe_send_email(db, user, title, body)


# ---- YCKS / YCTT: người duyệt theo entity permission ----

def _digest_generic(db, today: str, entity: str, Model, label: str):
    count = db.query(Model).filter(Model.status == "submitted").count()
    if count == 0:
        return

    approvers = get_approvers_for_entity(db, entity)
    link_map = {
        "survey_request": "/survey-requests?status=submitted",
        "payment_request": "/payment-requests?status=submitted",
    }
    for user in approvers:
        if _already_notified_today(db, user.id, f"digest_{entity}"):
            continue
        title = DIGEST_TITLE.format(n=count, today=today)
        body = (
            f"Có {count} phiếu {label} đang chờ bạn phê duyệt. "
            f"Vui lòng kiểm tra và xử lý sớm."
        )
        db.add(Notification(
            user_id=user.id,
            title=title,
            body=body,
            link=link_map.get(entity, "/"),
            created_by=0,
        ))
        _maybe_send_email(db, user, title, body)


# ---- Kiểm tra chuông đã tạo hôm nay chưa (idempotent) ----

def _already_notified_today(db, user_id: int, tag: str) -> bool:
    """Trả True nếu đã tạo chuông digest cho user trong ngày (so sánh ngày theo UTC)."""
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.link.contains("status=submitted"),
            Notification.body.contains("đang chờ"),
            Notification.created_at >= today_start,
        )
        .count()
    ) > 0


# ---- Email digest (tùy chọn) ----

def _maybe_send_email(db, user: User, subject: str, body_text: str):
    if not app_settings.get("email_enabled"):
        return
    if not user.email:
        return
    html = f"<p>{body_text}</p>"
    log = EmailLog(
        event="digest",
        to_email=user.email,
        subject=subject,
        status="pending",
        created_by=0,
    )
    db.add(log)
    db.flush()
    # Gửi nền (không block task)
    send_smtp_email.__wrapped__(SessionLocal, log.id, user.email, subject, html)
```

**Đăng ký beat (thêm vào `celery_app.py` hoặc `celeryconfig.py`):**

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # ... các schedule khác từ Phase 2/3 ...
    "digest-pending-approvals": {
        "task": "digest.send_pending_digest",
        "schedule": crontab(hour=16, minute=30, day_of_week="mon-fri"),
        # Thứ Hai–Sáu lúc 16:30 ICT
    },
}
celery_app.conf.timezone = "Asia/Ho_Chi_Minh"
```

**Hàm tái dùng từ code hiện có:**
- `notification/service.py`: `get_approvers_for_entity`, `get_department_head_users`, `send_smtp_email`, `render_template`
- `notification/model.py`: `Notification`, `EmailLog`

### 4. Cấu hình

| Biến / Tham số | Mặc định | Ghi chú |
|---|---|---|
| Cron | `16:30 Mon–Fri` | Tuỳ chỉnh trong `beat_schedule` |
| `email_enabled` | `false` | Cấu hình trang Cấu hình hệ thống hoặc `.env` |
| `EMAIL_TEST_OVERRIDE` | (rỗng) | Chuyển hướng email sang địa chỉ test khi dev |

**Docker:** celery-beat chạy cùng image api, command `celery -A app.celery_app beat --loglevel=info`.

### 5. Chống trùng / Idempotent

- Hàm `_already_notified_today` truy vấn `tab_notification` tìm chuông digest (theo `link` + `body` + `created_at >= today_start`) để **không tạo chuông thứ hai** nếu task bị chạy lại trong ngày.
- Nếu không có phiếu chờ duyệt, task kết thúc sớm — **không tạo chuông rỗng**.
- Email log chỉ tạo sau khi `Notification` đã được add vào session (tránh EmailLog mồ côi khi rollback).

### 6. Kiểm thử & tiêu chí hoàn thành

- [ ] Unit test (pytest, SQLite in-memory): seed 3 PYC `submitted` + 1 trưởng phòng → gọi `send_pending_digest` → kiểm tra 1 `Notification` được tạo, `body` chứa "3 Yêu cầu mua hàng".
- [ ] Gọi lại task lần 2 trong cùng ngày → số `Notification` không tăng (idempotent).
- [ ] Seed 0 phiếu chờ → không tạo `Notification` nào.
- [ ] Bật `email_enabled=True` + SMTP sandbox → kiểm tra `EmailLog.status = "sent"`.
- [ ] Chạy thủ công trên dev: `celery -A app.celery_app call digest.send_pending_digest` → kiểm tra chuông trên UI.

**Tiêu chí hoàn thành:** Chuông xuất hiện đúng người duyệt, đúng số lượng phiếu, không trùng trong ngày.

### 7. Rủi ro & lưu ý

- **Phòng ban chưa có trưởng phòng**: `get_department_head_users` trả `[]` — phiếu PYC của phòng đó KHÔNG được nhắc. Cần nhắc admin gán `Department.manager_id` khi onboard phòng mới.
- **Người duyệt có nhiều vai trò**: hàm `get_approvers_for_entity` có thể trả trùng — hàm `_digest_generic` dùng `seen_user_ids` để khử trùng (cần thêm nếu muốn xử lý cross-entity).
- **Gửi email async trong task**: tránh gọi `background_tasks.add_task` (không có FastAPI context) — gọi `send_smtp_email` trực tiếp hoặc tạo Celery sub-task riêng.
- **Cuối tuần / nghỉ lễ**: cron `Mon–Fri` bỏ qua T7, CN; cần xử lý thêm ngày lễ nếu cần.
- **Timezone**: beat chạy theo `Asia/Ho_Chi_Minh` — kiểm tra biến `CELERY_TIMEZONE` trong `.env` khớp với `celery_app.conf.timezone`.

---

## Phase 5 — Dọn dẹp dữ liệu cũ

### 1. Mục tiêu

Giữ DB gọn nhẹ bằng cách tự động xóa dữ liệu log/thông báo cũ không còn cần thiết:
- `tab_notification` — thông báo in-app đã đọc hoặc quá cũ.
- `tab_email_log` — log email đã gửi/lỗi quá cũ.
- `tab_audit_log` — nhật ký thao tác quá cũ.
- `tab_push_subscription` — đăng ký push subscription đã hết hạn (endpoint trả 410/404).

### 2. Phạm vi & việc cụ thể

- [ ] Tạo file `backend/app/tasks/cleanup.py` chứa các task prune.
- [ ] Task `prune_notifications`: xóa `tab_notification` cũ hơn `NOTIFICATION_KEEP_DAYS` ngày.
- [ ] Task `prune_email_logs`: xóa `tab_email_log` cũ hơn `EMAIL_LOG_KEEP_DAYS` ngày (chỉ xóa status `sent`/`failed`/`disabled`; giữ `pending`).
- [ ] Task `prune_audit_logs`: xóa `tab_audit_log` cũ hơn `AUDIT_LOG_KEEP_DAYS` ngày.
- [ ] Task `prune_dead_push_subscriptions`: quét `tab_push_subscription`, thử gửi ping, xóa khi nhận 410 Gone hoặc lỗi liên tục.
- [ ] Đăng ký beat schedule cho từng task.

### 3. Thiết kế kỹ thuật

**File tạo mới:** `backend/app/tasks/cleanup.py`

```python
"""Phase 5 — Dọn dẹp: prune Notification / EmailLog / AuditLog / PushSubscription."""
from __future__ import annotations

from datetime import datetime, timedelta

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.modules.notification.model import Notification, EmailLog
from app.modules.audit.model import AuditLog
from app.modules.push.model import PushSubscription

# ---- Tham số giữ lại (ngày) — đọc từ ENV hoặc dùng mặc định ----
import os

NOTIFICATION_KEEP_DAYS = int(os.getenv("NOTIFICATION_KEEP_DAYS", "90"))
EMAIL_LOG_KEEP_DAYS    = int(os.getenv("EMAIL_LOG_KEEP_DAYS",    "90"))
AUDIT_LOG_KEEP_DAYS    = int(os.getenv("AUDIT_LOG_KEEP_DAYS",   "365"))


@celery_app.task(name="cleanup.prune_notifications", bind=True, max_retries=2)
def prune_notifications(self):
    """Xóa thông báo in-app cũ hơn NOTIFICATION_KEEP_DAYS ngày."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=NOTIFICATION_KEEP_DAYS)
        deleted = (
            db.query(Notification)
            .filter(Notification.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return {"deleted_notifications": deleted}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=600)
    finally:
        db.close()


@celery_app.task(name="cleanup.prune_email_logs", bind=True, max_retries=2)
def prune_email_logs(self):
    """Xóa EmailLog đã hoàn thành (sent/failed/disabled) cũ hơn EMAIL_LOG_KEEP_DAYS ngày.
    Giữ nguyên log status='pending' để tránh mất task đang chờ gửi."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=EMAIL_LOG_KEEP_DAYS)
        deleted = (
            db.query(EmailLog)
            .filter(
                EmailLog.created_at < cutoff,
                EmailLog.status.in_(["sent", "failed", "disabled"]),
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return {"deleted_email_logs": deleted}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=600)
    finally:
        db.close()


@celery_app.task(name="cleanup.prune_audit_logs", bind=True, max_retries=2)
def prune_audit_logs(self):
    """Xóa AuditLog cũ hơn AUDIT_LOG_KEEP_DAYS ngày (mặc định 1 năm)."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=AUDIT_LOG_KEEP_DAYS)
        deleted = (
            db.query(AuditLog)
            .filter(AuditLog.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return {"deleted_audit_logs": deleted}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=600)
    finally:
        db.close()


@celery_app.task(name="cleanup.prune_dead_push_subscriptions", bind=True, max_retries=1)
def prune_dead_push_subscriptions(self):
    """Quét tab_push_subscription, xóa endpoint đã chết (410 Gone hoặc lỗi liên tục).

    Dùng pywebpush để gửi ping; nếu server push trả 410 Gone → endpoint hết hạn → xóa.
    Chạy chậm (delay giữa các sub) để không bị rate-limit bởi push service.
    """
    import time
    from pywebpush import webpush, WebPushException
    from app.core import app_settings

    vapid_private = app_settings.get("vapid_private_key")
    vapid_claims  = {"sub": "mailto:system@internal"}

    db = SessionLocal()
    deleted = 0
    try:
        subs = db.query(PushSubscription).all()
        dead_ids = []
        for sub in subs:
            if not sub.endpoint or not sub.p256dh or not sub.auth:
                dead_ids.append(sub.id)
                continue
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                    },
                    data="ping",
                    vapid_private_key=vapid_private,
                    vapid_claims=vapid_claims,
                )
            except WebPushException as ex:
                response = ex.response
                if response is not None and response.status_code in (410, 404):
                    dead_ids.append(sub.id)
            except Exception:
                pass  # lỗi mạng tạm thời — không xóa
            time.sleep(0.1)   # tránh rate-limit

        if dead_ids:
            db.query(PushSubscription).filter(PushSubscription.id.in_(dead_ids)).delete(
                synchronize_session=False
            )
            db.commit()
            deleted = len(dead_ids)
        return {"deleted_push_subscriptions": deleted}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=3600)
    finally:
        db.close()
```

**Đăng ký beat:**

```python
# Thêm vào celery_app.conf.beat_schedule
"prune-notifications-weekly": {
    "task": "cleanup.prune_notifications",
    "schedule": crontab(hour=2, minute=0, day_of_week="sun"),  # Chủ nhật 02:00
},
"prune-email-logs-weekly": {
    "task": "cleanup.prune_email_logs",
    "schedule": crontab(hour=2, minute=15, day_of_week="sun"),
},
"prune-audit-logs-monthly": {
    "task": "cleanup.prune_audit_logs",
    "schedule": crontab(hour=2, minute=30, day_of_month="1"),  # Ngày 1 mỗi tháng
},
"prune-dead-push-subs-weekly": {
    "task": "cleanup.prune_dead_push_subscriptions",
    "schedule": crontab(hour=3, minute=0, day_of_week="sun"),
},
```

### 4. Cấu hình

| Biến ENV | Mặc định | Ghi chú |
|---|---|---|
| `NOTIFICATION_KEEP_DAYS` | `90` | Số ngày giữ `tab_notification` |
| `EMAIL_LOG_KEEP_DAYS` | `90` | Số ngày giữ `tab_email_log` |
| `AUDIT_LOG_KEEP_DAYS` | `365` | Số ngày giữ `tab_audit_log` |
| `VAPID_PRIVATE_KEY` | — | Đã có trong VPS `.env` (từ Phase web-push) |

> Đặt biến trong file `.env` chung; worker đọc qua `os.getenv` khi khởi động.

### 5. Chống trùng / Idempotent

- Các lệnh `DELETE ... WHERE created_at < cutoff` hoàn toàn idempotent — chạy lại chỉ xóa những gì còn lại.
- `prune_dead_push_subscriptions` ping từng endpoint — nếu task bị interrupt giữa chừng, lần chạy sau sẽ tiếp tục với toàn bộ danh sách (tự nhiên idempotent).
- **Không dùng `db.bulk_delete`** — dùng `.delete(synchronize_session=False)` để hiệu quả hơn với số lượng lớn, không cần load object về Python.

### 6. Kiểm thử & tiêu chí hoàn thành

- [ ] Unit test `prune_notifications`: seed 5 thông báo (3 cũ hơn 90 ngày, 2 mới) → sau task chỉ còn 2.
- [ ] Unit test `prune_email_logs`: giữ log `pending` dù cũ.
- [ ] Unit test `prune_audit_logs`: seed log cũ hơn 365 ngày → bị xóa.
- [ ] Test `prune_dead_push_subscriptions` với mock: endpoint trả 410 → xóa; endpoint lỗi mạng → giữ.
- [ ] Chạy lại task sau khi đã prune → `deleted = 0` (không crash, không prune thêm).

**Tiêu chí hoàn thành:** Sau 1 tháng vận hành, kích thước `tab_notification` + `tab_email_log` không tăng vô hạn.

### 7. Rủi ro & lưu ý

- **Xóa dữ liệu không phục hồi**: đảm bảo backup đêm hôm trước (B5) chạy trước khi prune buổi sáng. Nếu cần, backup ngay trước khi xóa theo lịch.
- **Chạy trên bảng lớn**: câu DELETE lớn có thể lock bảng lâu trên MariaDB. Nếu `tab_audit_log` > 1 triệu dòng, cân nhắc xóa theo batch (LIMIT 1000 × lặp) thay vì 1 DELETE.
- **`prune_dead_push_subscriptions` chậm**: mỗi sub cần 1 HTTP request; nếu có 10.000 sub → mất hàng chục phút. Đặt lịch lúc ít tải (02:00–04:00 sáng). Có thể thêm timeout per-request.
- **VAPID_PRIVATE_KEY**: nếu key chưa set, task sẽ lỗi khi ping. Bắt exception và log warning thay vì crash toàn task.
- **Email log `pending` lâu ngày**: nếu worker không chạy được, log bị kẹt `pending` mãi. Cần alert riêng (Phase 2/alerting) nếu có log `pending` > 24h.

---

## B5 — Sao lưu DB hằng đêm

### 1. Mục tiêu

Tự động sao lưu DB `procurement` mỗi đêm bằng `mariadb-dump`, lưu trữ cục bộ trên VPS (giữ N bản xoay vòng), tùy chọn đẩy offsite lên Cloudflare R2. Bảo vệ dữ liệu khỏi sự cố phần cứng, xóa nhầm, lỗi deploy.

> **DB dùng chung**: container `dego-erp-db-1`, database `procurement`. Dùng `mariadb-dump` (KHÔNG `mysqldump`).

### 2. Phạm vi & việc cụ thể

- [ ] Tạo file `backend/app/tasks/backup.py` chứa task `backup_database`.
- [ ] Chạy `mariadb-dump` bên trong container `dego-erp-db-1` qua `docker exec` (hoặc kết nối TCP từ worker).
- [ ] Lưu file dump `.sql.gz` vào thư mục `/backups/procurement/` trên host (bind-mount vào container worker).
- [ ] Xoay vòng: giữ tối đa `DB_BACKUP_KEEP` bản (mặc định 7), xóa bản cũ nhất khi vượt.
- [ ] (Tùy chọn) Upload bản mới nhất lên Cloudflare R2 prefix `db-backups/`.
- [ ] Ghi log thành công/lỗi ra stdout (Celery log) và tạo `Notification` hệ thống cho admin khi lỗi.
- [ ] Đăng ký beat schedule: hằng đêm 01:00 ICT.

### 3. Thiết kế kỹ thuật

**File tạo mới:** `backend/app/tasks/backup.py`

```python
"""B5 — Sao lưu DB: mariadb-dump hằng đêm + xoay vòng + offsite R2."""
from __future__ import annotations

import gzip
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from app.celery_app import celery_app
from app.core import app_settings

# Thư mục lưu backup trên host (bind-mount vào container worker)
BACKUP_DIR   = Path(os.getenv("DB_BACKUP_DIR", "/backups/procurement"))
BACKUP_KEEP  = int(os.getenv("DB_BACKUP_KEEP", "7"))
DB_NAME      = os.getenv("DB_NAME", "procurement")
DB_USER      = os.getenv("DB_USER", "root")
DB_PASSWORD  = os.getenv("DB_PASSWORD", "")
DB_HOST      = os.getenv("DB_HOST", "dego-erp-db-1")   # hostname trong Docker network
DB_PORT      = int(os.getenv("DB_PORT", "3306"))


@celery_app.task(name="backup.backup_database", bind=True, max_retries=1)
def backup_database(self):
    """Dump DB procurement → gzip → lưu local → xoay vòng → tùy chọn upload R2."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_path   = BACKUP_DIR / f"procurement_{timestamp}.sql.gz"

    try:
        # ---- Chạy mariadb-dump (KHÔNG mysqldump) ----
        # Kết nối TCP tới dego-erp-db-1 từ bên trong Docker network
        cmd = [
            "mariadb-dump",
            f"--host={DB_HOST}",
            f"--port={DB_PORT}",
            f"--user={DB_USER}",
            f"--password={DB_PASSWORD}",
            "--single-transaction",         # InnoDB: consistent snapshot, không lock
            "--routines",                   # bao gồm stored procedures/functions nếu có
            "--events",
            "--set-gtid-purged=OFF",        # tránh lỗi GTID khi restore trên server khác
            DB_NAME,
        ]
        with gzip.open(dump_path, "wb") as gz_file:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            gz_file.write(result.stdout)

        size_mb = dump_path.stat().st_size / 1_048_576
        print(f"[backup] Dump OK: {dump_path.name} ({size_mb:.1f} MB)")

        # ---- Xoay vòng: xóa bản cũ khi vượt BACKUP_KEEP ----
        _rotate_backups()

        # ---- Upload offsite lên R2 (tùy chọn) ----
        _maybe_upload_r2(dump_path, timestamp)

        # Cảnh báo dung lượng tổng thư mục
        _warn_if_large()

        return {"status": "ok", "file": dump_path.name, "size_mb": round(size_mb, 2)}

    except subprocess.CalledProcessError as exc:
        err = exc.stderr.decode("utf-8", errors="replace")
        print(f"[backup] mariadb-dump FAILED: {err}")
        _notify_admin_error(f"mariadb-dump thất bại:\n{err[:500]}")
        raise self.retry(exc=exc, countdown=1800)  # thử lại sau 30 phút
    except Exception as exc:
        print(f"[backup] Backup FAILED: {exc}")
        _notify_admin_error(str(exc)[:500])
        raise


def _rotate_backups():
    """Giữ tối đa BACKUP_KEEP file .sql.gz mới nhất, xóa cái cũ hơn."""
    files = sorted(BACKUP_DIR.glob("procurement_*.sql.gz"), key=lambda p: p.stat().st_mtime)
    while len(files) > BACKUP_KEEP:
        old = files.pop(0)
        old.unlink()
        print(f"[backup] Đã xóa bản cũ: {old.name}")


def _maybe_upload_r2(dump_path: Path, timestamp: str):
    """Upload lên R2 nếu đã cấu hình (r2_endpoint + r2_access_key_id)."""
    r2_endpoint = app_settings.get("r2_endpoint")
    r2_key      = app_settings.get("r2_access_key_id")
    if not r2_endpoint or not r2_key:
        return
    try:
        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url=r2_endpoint,
            aws_access_key_id=r2_key,
            aws_secret_access_key=app_settings.get("r2_secret_access_key"),
            region_name="auto",
        )
        key = f"db-backups/procurement_{timestamp}.sql.gz"
        s3.upload_file(
            str(dump_path),
            app_settings.get("r2_bucket"),
            key,
        )
        print(f"[backup] Upload R2 OK: {key}")
    except Exception as ex:
        # Lỗi offsite KHÔNG abort task — backup local đã xong
        print(f"[backup] Upload R2 FAILED (non-fatal): {ex}")


def _warn_if_large():
    """Cảnh báo nếu tổng dung lượng backup > 2 GB."""
    total = sum(p.stat().st_size for p in BACKUP_DIR.glob("*.sql.gz"))
    gb = total / 1_073_741_824
    if gb > 2:
        print(f"[backup] CẢNH BÁO: tổng backup = {gb:.2f} GB > 2 GB — kiểm tra lại BACKUP_KEEP.")


def _notify_admin_error(message: str):
    """Tạo chuông in-app cho admin (role pur_admin) khi backup lỗi."""
    try:
        from app.core.database import SessionLocal
        from app.modules.notification.model import Notification
        from app.modules.notification.service import get_users_by_role_codes
        db = SessionLocal()
        admins = get_users_by_role_codes(db, ["pur_admin"])
        for admin in admins:
            db.add(Notification(
                user_id=admin.id,
                title="[LỖI] Sao lưu DB thất bại",
                body=message,
                link="",
                created_by=0,
            ))
        db.commit()
        db.close()
    except Exception:
        pass  # không để lỗi notification che lỗi backup
```

**Đăng ký beat:**

```python
"db-backup-nightly": {
    "task": "backup.backup_database",
    "schedule": crontab(hour=1, minute=0),  # 01:00 ICT hằng đêm
},
```

**Docker Compose — thêm bind-mount cho worker:**

```yaml
# docker-compose.yml (thêm vào service celery-worker)
celery-worker:
  image: procurement-api          # cùng image api
  command: celery -A app.celery_app worker --loglevel=info -Q default
  volumes:
    - ./backend:/app
    - backup_data:/backups/procurement  # lưu backup ra named volume
  env_file: .env

volumes:
  backup_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/lib/procurement-backups  # thư mục thật trên VPS host
```

**Cài `mariadb-dump` trong image:**

```dockerfile
# Thêm vào docker/Dockerfile.api (hoặc Dockerfile.worker nếu tách)
RUN apt-get update && apt-get install -y mariadb-client && rm -rf /var/lib/apt/lists/*
```

### 4. Cấu hình

| Biến ENV | Mặc định | Ghi chú |
|---|---|---|
| `DB_BACKUP_DIR` | `/backups/procurement` | Bind-mount ra host VPS |
| `DB_BACKUP_KEEP` | `7` | Số bản backup local giữ lại |
| `DB_HOST` | `dego-erp-db-1` | Hostname container DB trong Docker network |
| `DB_NAME` | `procurement` | Tên database |
| `DB_USER` | `root` | User MariaDB (đọc từ `.env`) |
| `DB_PASSWORD` | — | Password MariaDB (đọc từ `.env`) |
| `r2_endpoint` | — | Nếu có → upload offsite R2 (đọc từ app_settings) |
| `r2_bucket` | — | Bucket R2 |
| `r2_access_key_id` | — | Key R2 |
| `r2_secret_access_key` | — | Secret R2 |

**Quyền trên VPS host:**
```bash
mkdir -p /var/lib/procurement-backups
chown -R 1000:1000 /var/lib/procurement-backups   # UID của user trong container
chmod 700 /var/lib/procurement-backups
```

### 5. Chống trùng / Idempotent

- Mỗi file dump có timestamp giây (`procurement_20260717_010000.sql.gz`) — không bao giờ ghi đè.
- `_rotate_backups` an toàn khi gọi nhiều lần — chỉ xóa khi thực sự vượt `BACKUP_KEEP`.
- Nếu dump lỗi giữa chừng → file `.sql.gz` rỗng/lỗi không được đưa vào rotation (exception xảy ra trước `_rotate_backups`).

### 6. Kiểm thử & tiêu chí hoàn thành

- [ ] Trên dev (nếu có mariadb-client cài sẵn): chạy task thủ công, kiểm tra file `.sql.gz` tồn tại và giải nén được (`zcat file.sql.gz | head`).
- [ ] Tạo 8 dump thủ công → kiểm tra `_rotate_backups` xóa bản cũ nhất, còn lại 7.
- [ ] Mock `subprocess.run` raise `CalledProcessError` → kiểm tra `_notify_admin_error` tạo `Notification` cho admin và task retry.
- [ ] Kiểm tra file dump restore được: `mariadb -u root procurement < dump.sql` trên môi trường test.
- [ ] Bật R2 config → kiểm tra file xuất hiện trong bucket với prefix `db-backups/`.

**Tiêu chí hoàn thành:** File dump được tạo mỗi đêm, giải nén không lỗi, dung lượng không vượt ngưỡng cảnh báo, log ghi rõ kết quả.

### 7. Rủi ro & lưu ý

- **KHÔNG dùng `mysqldump`** — container MariaDB (`dego-erp-db-1`) không có `mysqldump`; dùng `mariadb-dump` (từ gói `mariadb-client`).
- **Kết nối TCP (không socket)**: worker chạy container riêng, kết nối qua hostname `dego-erp-db-1` trong Docker network — không cần SSH tunnel, đúng với quy ước ops VPS hiện tại.
- **Password lộ ra CLI**: `mariadb-dump --password=xxx` lộ password trong `ps aux`. Thay thế an toàn hơn: dùng file `.my.cnf` hoặc biến `MYSQL_PWD` (MariaDB đọc được). Với môi trường nội bộ ít người truy cập server, mức này chấp nhận được.
- **Dung lượng DB lớn**: với ~20–100 user + vài năm dữ liệu, dump có thể đạt 100–500 MB/bản. 7 bản × 500 MB = 3.5 GB — cân nhắc tăng VPS disk hoặc giảm `BACKUP_KEEP` xuống 5 khi không có R2 offsite.
- **`--single-transaction` chỉ hoạt động với InnoDB**: nếu có bảng MyISAM thì thêm `--lock-tables` hoặc chấp nhận lock ngắn.
- **Thời gian backup**: 01:00 sáng — trước `prune_notifications` (02:00) để đảm bảo dữ liệu đầy đủ trước khi dọn.
- **Restore**: lệnh restore: `zcat procurement_YYYYMMDD_HHMMSS.sql.gz | mariadb -h dego-erp-db-1 -u root -p procurement`

---

## B6 — Export Excel báo cáo bất đồng bộ (async)

> **Issue liên kết**: #62

### 1. Mục tiêu

Khi người dùng xuất báo cáo lớn (toàn bộ năm / nhiều tháng), thay vì chờ request timeout (30–60s), hệ thống nhận yêu cầu ngay, worker sinh file Excel ở nền, lưu vào R2 (hoặc local fallback), rồi thông báo người dùng khi xong để tải về.

Giải quyết: request timeout, UI đứng chờ, server hết bộ nhớ khi nhiều người export đồng thời.

### 2. Phạm vi & việc cụ thể

- [ ] Tạo model `ExportJob` (`tab_export_job`) để theo dõi trạng thái từng job export.
- [ ] Thêm vào `backend/app/core/all_models.py` để Alembic nhận.
- [ ] Tạo `backend/app/tasks/export_excel.py` chứa task `run_export_job`.
- [ ] API endpoint mới `POST /api/reports/export` — nhận params (year, company_id, loại báo cáo) → tạo `ExportJob` → enqueue Celery task → trả `{job_id}` ngay.
- [ ] API endpoint `GET /api/reports/export/{job_id}` — trả trạng thái + URL tải về khi xong.
- [ ] Task worker: gọi hàm `compute` từ `report/service.py` → render Excel bằng `openpyxl` → upload file qua `storage.upload_fileobj` → cập nhật `ExportJob.status = "done"` + `file_url` → tạo `Notification` cho user.
- [ ] Thêm `openpyxl` vào `requirements.txt`.
- [ ] Thêm route vào `app/main.py`.

### 3. Thiết kế kỹ thuật

**Model mới:** `backend/app/modules/report/export_model.py`

```python
"""Model theo dõi job export Excel bất đồng bộ."""
from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.base_model import Base, AuditMixin


class ExportJob(Base, AuditMixin):
    """Theo dõi 1 job export Excel. created_by = user_id yêu cầu."""
    __tablename__ = "tab_export_job"

    kind: Mapped[str] = mapped_column(String(50), default="")
    # "report_matrix" | "report_request_pyc" | "report_request_ycks" | ...
    params: Mapped[str] = mapped_column(Text, default="")    # JSON: year, company_id, ...
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | running | done | failed
    file_url: Mapped[str] = mapped_column(String(1000), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)  # người yêu cầu
```

**Thêm vào `all_models.py`:**
```python
from app.modules.report.export_model import ExportJob  # noqa: F401
```

**Task worker:** `backend/app/tasks/export_excel.py`

```python
"""B6 — Export Excel async: sinh file nền → lưu R2/local → thông báo user."""
from __future__ import annotations

import io
import json

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.core import storage
from app.modules.report.export_model import ExportJob
from app.modules.notification.model import Notification


@celery_app.task(name="export.run_export_job", bind=True, max_retries=2,
                 time_limit=300, soft_time_limit=240)  # timeout 5 phút
def run_export_job(self, job_id: int):
    """Chạy job export Excel: tính báo cáo → render Excel → upload → thông báo."""
    db = SessionLocal()
    try:
        job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
        if not job or job.status not in ("pending",):
            return  # đã chạy hoặc không tìm thấy

        job.status = "running"
        db.commit()

        params = json.loads(job.params or "{}")
        year       = params.get("year", "all")
        company_id = params.get("company_id")
        kind       = job.kind

        # ---- Tính dữ liệu (tái dùng hàm hiện có) ----
        data = _compute_data(db, kind, params)

        # ---- Render Excel ----
        xlsx_bytes = _render_excel(kind, data)

        # ---- Upload (R2 hoặc local fallback) ----
        key = f"exports/export_{kind}_{job_id}.xlsx"
        file_url = storage.upload_fileobj(
            io.BytesIO(xlsx_bytes),
            key,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # ---- Cập nhật job ----
        job.status   = "done"
        job.file_url = file_url
        db.commit()

        # ---- Thông báo người dùng ----
        db.add(Notification(
            user_id=job.user_id,
            title="[Báo cáo] File Excel đã sẵn sàng",
            body=f"Báo cáo '{_label(kind)}' năm {year} đã xuất xong. Nhấn để tải về.",
            link=f"/api/reports/export/{job_id}/download",
            created_by=0,
        ))
        db.commit()

    except Exception as exc:
        db.rollback()
        try:
            job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error  = str(exc)[:500]
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


def _compute_data(db, kind: str, params: dict):
    """Gọi hàm tính đúng theo loại báo cáo."""
    from app.modules.report import service as svc
    year       = params.get("year", "all")
    company_id = params.get("company_id")

    if kind == "report_matrix":
        return svc.compute(db, year, company_id)

    if kind in ("report_request_pyc", "report_request_ycks"):
        req_kind = "ycks" if kind == "report_request_ycks" else "pyc"
        return svc.compute_request_matrix(db, req_kind, year, company_id, user=None)

    raise ValueError(f"Loại báo cáo không hỗ trợ: {kind}")


def _render_excel(kind: str, data: dict) -> bytes:
    """Render dict data → bytes Excel (.xlsx) dùng openpyxl."""
    import openpyxl
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = _label(kind)

    # Tiêu đề đơn giản — mỗi loại báo cáo cần sheet riêng chi tiết hơn
    if kind == "report_matrix":
        months = [m["label"] for m in data.get("months", [])]
        # Sheet Bộ phận
        ws.append(["Bộ phận"] + months + ["Tổng", "Gấp", "% Gấp"])
        for row in data.get("department", []):
            ws.append(
                [row["key"]]
                + [row["m"].get(m["key"], {}).get("orders", 0) for m in data.get("months", [])]
                + [row["orders"], row["urgent"], row["rate"]]
            )
        # Thêm các sheet NCC, NSPT, VTBB nếu cần (tương tự)

    elif kind in ("report_request_pyc", "report_request_ycks"):
        months = [m["label"] for m in data.get("months", [])]
        ws.append(["Bộ phận"] + months + ["Tổng"])
        for row in data.get("rows", []):
            ws.append(
                [row["key"]]
                + [row["m"].get(m["key"], {}).get("total", 0) for m in data.get("months", [])]
                + [row["total"]]
            )

    # Auto-width cơ bản
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _label(kind: str) -> str:
    return {
        "report_matrix":       "Báo cáo ma trận",
        "report_request_pyc":  "Báo cáo PYC theo phòng ban",
        "report_request_ycks": "Báo cáo YCKS theo phòng ban",
    }.get(kind, kind)
```

**API endpoint (thêm vào `report/controller.py`):**

```python
from app.modules.report.export_model import ExportJob
import json

@router.post("/export")
def request_export(
    kind: str,
    year: str = "all",
    company_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tạo job export Excel bất đồng bộ. Trả job_id ngay."""
    job = ExportJob(
        kind=kind,
        params=json.dumps({"year": year, "company_id": company_id}),
        status="pending",
        user_id=current_user.id,
        created_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue Celery task (nếu Celery không có → chạy đồng bộ fallback)
    try:
        from app.tasks.export_excel import run_export_job
        run_export_job.delay(job.id)
    except Exception:
        # Fallback: chạy đồng bộ (dev không có Redis)
        from app.tasks.export_excel import run_export_job
        run_export_job(job.id)  # gọi trực tiếp — block request

    return success({"job_id": job.id}, "Đang xuất báo cáo, bạn sẽ nhận thông báo khi xong.")


@router.get("/export/{job_id}")
def get_export_status(job_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """Kiểm tra trạng thái job export."""
    job = db.query(ExportJob).filter(ExportJob.id == job_id, ExportJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(404, "Không tìm thấy job")
    return success({"status": job.status, "file_url": job.file_url, "error": job.error})
```

**Thêm `openpyxl` vào `requirements.txt`:**
```
openpyxl>=3.1
```

**Migration Alembic:**
```bash
docker compose exec api alembic revision --autogenerate -m "add_export_job"
docker compose exec api alembic upgrade head
```

### 4. Cấu hình

| Biến / Tham số | Mặc định | Ghi chú |
|---|---|---|
| `time_limit` Celery task | `300` s | Timeout cứng; báo cáo lớn ≤ 5 phút |
| `soft_time_limit` | `240` s | Gửi signal trước → task dọn dẹp rồi stop |
| Lưu file | R2 prefix `exports/` | Fallback: `uploads/exports/` trong container |
| `r2_public_url` | — | URL công khai để tải file (đã có trong app_settings) |
| `DB_EXPORT_TTL_DAYS` | `3` | (tuỳ chọn) xóa job + file cũ hơn 3 ngày (thêm vào prune Phase 5) |

### 5. Chống trùng / Idempotent

- Kiểm tra `job.status not in ("pending",)` đầu task: nếu job đã `running`/`done`/`failed` → bỏ qua, không tính lại.
- File export đặt tên theo `job_id` — mỗi job sinh đúng 1 file, không ghi đè job khác.
- `Notification` tạo 1 lần khi job `done` — nếu task retry sau khi file đã upload thành công, lần sau vào `job.status = "done"` → exit sớm → không tạo thêm chuông.
- (Tùy chọn) Thêm cleanup vào Phase 5: xóa `ExportJob` + file R2 cũ hơn `DB_EXPORT_TTL_DAYS`.

### 6. Kiểm thử & tiêu chí hoàn thành

- [ ] Unit test: seed dữ liệu PO → gọi `run_export_job` trực tiếp → kiểm tra `ExportJob.status = "done"` và `file_url` không rỗng.
- [ ] Kiểm tra file `.xlsx` mở được bằng openpyxl và có đúng số hàng.
- [ ] Integration test: `POST /api/reports/export?kind=report_matrix&year=2026` → nhận `job_id` → poll `GET /api/reports/export/{job_id}` cho đến `status=done`.
- [ ] Kiểm tra `Notification` được tạo cho user khi job done.
- [ ] Test timeout: seed job với dữ liệu giả lâu > `soft_time_limit` → task bị cancel, job.status = "failed".
- [ ] Test retry: mock lỗi lần 1 → task retry lần 2 → thành công.
- [ ] Fallback (không Redis): gọi function trực tiếp trong request → trả `file_url` đồng bộ.

**Tiêu chí hoàn thành:** Người dùng nhấn "Xuất Excel" → trang trả ngay (không chờ) → chuông báo sau vài giây → tải file thành công.

### 7. Rủi ro & lưu ý

- **Timeout request vs timeout task**: request FastAPI trả ngay sau enqueue (không block). Nếu Redis/Celery chưa dựng (dev), fallback đồng bộ — cần thêm `try/except` kiểm tra kết nối Redis trước khi `.delay()`.
- **Dữ liệu lớn + bộ nhớ**: `compute(db, "all", None)` load toàn bộ PO/item vào RAM. Nếu > 100.000 dòng, cân nhắc stream theo tháng hoặc dùng generator. Hiện tại ~20–100 user nên ổn.
- **File R2 tạm**: nếu R2 không cấu hình, file lưu vào `uploads/exports/` trong container — bị mất khi rebuild container. Cần bind-mount hoặc cấu hình R2 khi chạy production.
- **Phân quyền tải file**: endpoint `GET /api/reports/export/{job_id}` kiểm tra `user_id == current_user.id` — chỉ người tạo job mới tải được. URL R2 public cần đặt đúng bucket policy (private + presigned URL) nếu muốn bảo mật file.
- **openpyxl memory**: tạo file xlsx lớn có thể ngốn nhiều RAM; cân nhắc `WriteOnlyWorksheet` của openpyxl cho sheet hàng trăm nghìn dòng.
- **Celery `soft_time_limit`**: cần cài `billiard` / `celery[redis]` đầy đủ; soft_time_limit ném `SoftTimeLimitExceeded` — bắt trong task để cập nhật `job.status = "failed"` trước khi bị kill.
- **Migration**: `ExportJob` là bảng mới — chạy `alembic revision --autogenerate` sau khi thêm vào `all_models.py`. Kiểm tra file migration trước khi upgrade.

---

## Tóm tắt lịch cron

| Task | Lịch (ICT) | Mô tả |
|---|---|---|
| `digest.send_pending_digest` | 16:30 T2–T6 | Nhắc duyệt PYC/YCKS/YCTT |
| `cleanup.prune_notifications` | CN 02:00 | Xóa chuông cũ > 90 ngày |
| `cleanup.prune_email_logs` | CN 02:15 | Xóa email log cũ > 90 ngày |
| `cleanup.prune_audit_logs` | Ngày 1 hàng tháng 02:30 | Xóa audit log cũ > 365 ngày |
| `cleanup.prune_dead_push_subscriptions` | CN 03:00 | Xóa push sub chết (410 Gone) |
| `backup.backup_database` | 01:00 hằng đêm | Dump MariaDB + xoay vòng 7 bản + R2 |

> Export Excel (`export.run_export_job`) không theo lịch — enqueue theo yêu cầu người dùng.

## Phụ lục: file cần tạo / sửa

| Hành động | File |
|---|---|
| Tạo mới | `backend/app/tasks/digest.py` |
| Tạo mới | `backend/app/tasks/cleanup.py` |
| Tạo mới | `backend/app/tasks/backup.py` |
| Tạo mới | `backend/app/tasks/export_excel.py` |
| Tạo mới | `backend/app/modules/report/export_model.py` |
| Sửa | `backend/app/celery_app.py` (beat_schedule) |
| Sửa | `backend/app/core/all_models.py` (import ExportJob) |
| Sửa | `backend/app/modules/report/controller.py` (2 endpoint export) |
| Sửa | `backend/requirements.txt` (thêm `openpyxl`) |
| Sửa | `docker/Dockerfile.api` (thêm `mariadb-client`) |
| Sửa | `docker-compose.yml` (volume backup cho celery-worker) |
| Migration | `alembic revision --autogenerate -m "add_export_job"` |
