# Phase 1 — Gửi Web Push / Email qua Worker (tin cậy) + Retry Email (B4)

> **Thứ tự làm:** Phase 1 thực hiện SAU Phase 0 (hạ tầng Redis + worker + beat đã sẵn sàng).  
> Bản tóm tắt toàn cục: [../chung/Plan_Celery_Worker.md](../chung/Plan_Celery_Worker.md) · Khung phase: [README.md](README.md).

---

## 1. Mục tiêu

### Vấn đề hiện tại

| Điểm gọi | Cơ chế hiện tại | Rủi ro |
|-----------|----------------|--------|
| `trigger_notification` (PYC, YCTT, Phiếu KS…) | `background_tasks.add_task(push_service.send_to_users, …)` | Worker FastAPI chết giữa chừng → mất push, không retry |
| `_notify` trong `survey_request/controller.py` | Như trên — `background_tasks.add_task` | Như trên |
| `send_account_creation_email` | `background_tasks.add_task(send_smtp_email, …)` | Không retry, mất email nếu SMTP tạm thời lỗi |
| `send_password_reset_email` | Như trên (force=True) | Người dùng không nhận được link reset |

FastAPI `BackgroundTasks` chạy **trong cùng tiến trình web**. Nếu request worker (uvicorn) thoát, timeout, hoặc server restart giữa chừng thì tác vụ nền bị mất hoàn toàn — không có cơ chế retry.

### Mục tiêu của Phase 1

1. **Độ tin cậy gửi push**: bọc `push_service.send_to_users` thành Celery task có `autoretry_for` + exponential backoff — worker riêng đảm bảo thực thi dù web server restart.
2. **Độ tin cậy gửi email**: bọc `send_smtp_email` thành Celery task tương tự.
3. **Retry email thất bại (B4)**: Celery Beat quét `tab_email_log` tìm record `pending`/`failed` (không vượt ngưỡng) và thử gửi lại — đặc biệt quan trọng cho `account_creation` và `password_reset`.
4. **Giữ fallback**: khi không có Redis (môi trường dev gọn nhẹ), giữ nguyên đường `background_tasks.add_task` / gọi đồng bộ — KHÔNG bắt buộc dựng full stack để dev.

---

## 2. Phạm vi & việc cụ thể

### Tạo mới

- [ ] `backend/app/tasks/notifications.py` — Celery tasks: `task_send_push`, `task_send_email`, `task_retry_failed_emails`
- [ ] `backend/app/worker/__init__.py` — nếu chưa có (expose `celery_app`)

### Sửa

- [ ] `backend/app/modules/notification/service.py`
  - `trigger_notification`: thay `background_tasks.add_task(push_service.send_to_users, …)` → `task_send_push.delay(…)` khi có Celery
  - `send_account_creation_email`: thay `background_tasks.add_task(send_smtp_email, …)` → `task_send_email.delay(…)`
  - `send_password_reset_email`: như trên (giữ `force=True` truyền vào task)

- [ ] `backend/app/modules/survey_request/controller.py`
  - Hàm `_notify`: thay `background_tasks.add_task(push_service.send_to_users, …)` → `task_send_push.delay(…)` khi có Celery

- [ ] `backend/app/tasks/notifications.py` — task B4 `task_retry_failed_emails` (xem §3.3)

### Cấu hình / hạ tầng

- [ ] Đăng ký task vào Celery Beat schedule (xem §4)
- [ ] Đảm bảo `VAPID_PRIVATE_KEY`, `SMTP_*`, `REDIS_URL` có trong ENV của container `celery-worker` + `celery-beat`

---

## 3. Thiết kế kỹ thuật

### 3.1 Celery task: gửi Web Push

**File:** `backend/app/tasks/notifications.py`

```python
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="notifications.send_push",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=30,   # giây; Celery nhân đôi mỗi lần: 30s → 60s → 120s
    retry_backoff=True,
    retry_jitter=True,
)
def task_send_push(self, user_ids: list[int], title: str, body: str, url: str = "") -> None:
    """Đẩy Web Push tới danh sách user. Celery retry tối đa 3 lần với backoff."""
    from app.core.database import SessionLocal
    from app.modules.push import service as push_service
    try:
        push_service.send_to_users(SessionLocal, user_ids, title, body, url)
    except Exception as exc:
        logger.warning("task_send_push thất bại, lần %d: %s", self.request.retries, exc)
        raise   # autoretry_for sẽ bắt và retry
```

**Lưu ý pywebpush:** `send_to_users` đã bọc từng endpoint trong try/except và xóa endpoint 404/410 tự động — task này chỉ retry khi toàn bộ hàm raise exception (ví dụ DB không kết nối được). Không gửi trùng push nếu retry vì hàm gốc là stateless (không đánh dấu DB).

---

### 3.2 Celery task: gửi Email

```python
@shared_task(
    bind=True,
    name="notifications.send_email",
    autoretry_for=(Exception,),
    max_retries=4,
    default_retry_delay=60,   # 60s → 120s → 240s → 480s
    retry_backoff=True,
    retry_jitter=True,
)
def task_send_email(self, log_id: int, to_email: str, subject: str,
                    html_body: str, force: bool = False) -> None:
    """Gửi email qua SMTP và cập nhật tab_email_log. Retry tối đa 4 lần."""
    from app.core.database import SessionLocal
    from app.modules.notification.service import send_smtp_email
    try:
        send_smtp_email(SessionLocal, log_id, to_email, subject, html_body, force)
    except Exception as exc:
        logger.warning("task_send_email log_id=%d thất bại, lần %d: %s",
                       log_id, self.request.retries, exc)
        raise
```

**Idempotent:** `send_smtp_email` kiểm tra `EmailLog.status` mỗi lần trước khi gửi — nếu record đã `sent` (do retry trước thành công nhưng Celery chưa nhận ACK) thì hàm vẫn đọc record và cập nhật trạng thái, nhưng cần thêm guard (xem §5).

---

### 3.3 Task B4: quét & retry email thất bại

```python
@shared_task(name="notifications.retry_failed_emails")
def task_retry_failed_emails() -> dict:
    """Beat job: quét tab_email_log tìm pending/failed chưa vượt giới hạn, thử gửi lại.
    Chỉ chạy khi email_enabled=True. Giới hạn 50 bản ghi mỗi lần chạy."""
    from app.core.database import SessionLocal
    from app.core import app_settings
    from app.modules.notification.model import EmailLog
    from app.modules.notification.service import send_smtp_email

    MAX_RETRIES_B4 = 5      # tổng số lần thử kể cả lần đầu
    BATCH_LIMIT   = 50      # mỗi lần beat chạy, xử lý tối đa N bản ghi

    if not app_settings.get("email_enabled"):
        return {"skipped": True, "reason": "email_enabled=false"}

    db = SessionLocal()
    sent = failed = 0
    try:
        # Chỉ retry event KHÔNG phải force (account_creation, thông thường).
        # password_reset: force=True — cũng retry (xem §5, tránh gửi link hết hạn).
        logs = (
            db.query(EmailLog)
            .filter(
                EmailLog.status.in_(["pending", "failed"]),
                EmailLog.retry_count < MAX_RETRIES_B4,
            )
            .order_by(EmailLog.id)
            .limit(BATCH_LIMIT)
            .all()
        )
        for log in logs:
            force = (log.event in ("password_reset",))
            try:
                # Tăng retry_count TRƯỚC để nếu gửi exception không bị lặp vô hạn
                log.retry_count = (log.retry_count or 0) + 1
                db.commit()

                # Không có html_body lưu sẵn → gọi thẳng send_smtp_email với body rỗng sẽ lỗi.
                # Giải pháp: thêm cột html_body vào EmailLog (xem §3.4), hoặc bỏ qua event cũ.
                if not getattr(log, "html_body", None):
                    log.status = "failed"
                    log.error = "B4: thiếu html_body — bỏ qua"
                    db.commit()
                    failed += 1
                    continue

                send_smtp_email(SessionLocal, log.id, log.to_email,
                                log.subject, log.html_body, force)
                sent += 1
            except Exception as exc:
                logger.warning("B4 retry log_id=%d lỗi: %s", log.id, exc)
                failed += 1
    finally:
        db.close()

    return {"sent": sent, "failed": failed}
```

---

### 3.4 Thay đổi schema `EmailLog` — thêm cột `html_body` và `retry_count`

Để B4 có thể gửi lại, cần lưu nội dung email. Hiện tại `EmailLog` (`tab_email_log`) **không** có cột này. Cần thêm migration:

```python
# backend/app/modules/notification/model.py  — thêm 2 cột

class EmailLog(Base, AuditMixin):
    __tablename__ = "tab_email_log"

    event:       Mapped[str]      = mapped_column(String(100))
    to_email:    Mapped[str]      = mapped_column(String(255))
    subject:     Mapped[str]      = mapped_column(String(255))
    html_body:   Mapped[str]      = mapped_column(Text, nullable=True)   # MỚI — nội dung để retry
    status:      Mapped[str]      = mapped_column(String(20), default="pending")
    error:       Mapped[str]      = mapped_column(Text, nullable=True)
    sent_at:     Mapped[datetime] = mapped_column(DateTime, nullable=True)
    retry_count: Mapped[int]      = mapped_column(Integer, default=0)    # MỚI — đếm lần B4 retry
```

**Migration:**
```bash
docker compose exec api alembic revision --autogenerate -m "email_log_add_html_body_retry_count"
docker compose exec api alembic upgrade head
```

---

### 3.5 Đổi điểm gọi — `trigger_notification`

```python
# backend/app/modules/notification/service.py
# Trong trigger_notification — thay đoạn push hiện tại:

def _celery_available() -> bool:
    """Kiểm tra nhanh xem Celery app có kết nối Redis không (không block)."""
    try:
        from app.worker import celery_app
        celery_app.backend   # chỉ truy cập thuộc tính, không gửi task
        return True
    except Exception:
        return False

# --- trong trigger_notification, thay khối push ---
try:
    from app.modules.push import service as push_service
    from app.core.database import SessionLocal
    uids = [r.id for r in recipients if r]
    if uids:
        if _celery_available():
            from app.worker.tasks.notifications import task_send_push
            task_send_push.delay(uids, subject, body, link)
        elif background_tasks is not None:
            background_tasks.add_task(push_service.send_to_users, SessionLocal, uids, subject, body, link)
        else:
            push_service.send_to_users(SessionLocal, uids, subject, body, link)
except Exception:
    pass
```

---

### 3.6 Đổi điểm gọi — `send_account_creation_email` và `send_password_reset_email`

```python
# send_account_creation_email — thay background_tasks.add_task:
email_log.html_body = html_content   # lưu để B4 có thể retry
db.add(email_log)
db.flush()
db.commit()

if _celery_available():
    from app.worker.tasks.notifications import task_send_email
    task_send_email.delay(email_log.id, email, subject, html_content, False)
else:
    background_tasks.add_task(send_smtp_email, SessionLocal, email_log.id, email, subject, html_content)

# send_password_reset_email — tương tự, force=True:
if _celery_available():
    task_send_email.delay(email_log.id, email, subject, html_content, True)   # force=True
else:
    background_tasks.add_task(send_smtp_email, SessionLocal, email_log.id, email, subject, html_content, True)
```

---

### 3.7 Đổi điểm gọi — `_notify` trong `survey_request/controller.py`

```python
def _notify(db, users, title, body, link, creator_id, background_tasks=None):
    from app.modules.notification.model import Notification
    seen = set()
    for u in users:
        if u and u.id not in seen:
            seen.add(u.id)
            db.add(Notification(user_id=u.id, title=title, body=body, link=link, created_by=creator_id))
    db.commit()

    try:
        from app.modules.push import service as push_service
        from app.core.database import SessionLocal
        from app.modules.notification.service import _celery_available
        uids = list(seen)
        if uids:
            if _celery_available():
                from app.worker.tasks.notifications import task_send_push
                task_send_push.delay(uids, title, body, link)
            elif background_tasks is not None:
                background_tasks.add_task(push_service.send_to_users, SessionLocal, uids, title, body, link)
            else:
                push_service.send_to_users(SessionLocal, uids, title, body, link)
    except Exception:
        pass
```

---

## 4. Cấu hình

### ENV cho worker (giống container `api`)

```env
REDIS_URL=redis://redis:6379/0
VAPID_PRIVATE_KEY=<key từ VPS .env>
VAPID_PUBLIC_KEY=<key>
VAPID_SUBJECT=mailto:admin@degoholding.vn
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=<brevo user>
SMTP_PASSWORD=<brevo key>
```

> Worker và Beat đọc chung `.env` với `api` (mount cùng file trong `docker-compose.yml`) — không cần file ENV riêng.

### Celery Beat — lịch task B4

```python
# backend/app/worker/celery_app.py (hoặc tương đương)
from celery.schedules import crontab

app.conf.beat_schedule = {
    # ... (các schedule của Phase 2, 3 nếu có)
    "b4-retry-failed-emails": {
        "task": "notifications.retry_failed_emails",
        "schedule": crontab(minute="*/15"),   # mỗi 15 phút
        "options": {"queue": "default"},
    },
}
app.conf.timezone = "Asia/Ho_Chi_Minh"
```

### Docker Compose

```yaml
# Thêm vào docker-compose.yml (sau khi Phase 0 đã có celery-worker, celery-beat)
# Worker cần queue mặc định (không cần queue riêng cho Phase 1)
celery-worker:
  command: celery -A app.worker.celery_app worker --loglevel=info -Q default
  environment:
    - REDIS_URL=redis://redis:6379/0
  # ... (mount .env, volumes như api)

celery-beat:
  command: celery -A app.worker.celery_app beat --loglevel=info
  # ...
```

---

## 5. Chống trùng / Idempotent

### Push (task_send_push)

- `send_to_users` gọi `webpush(…)` cho từng subscription — mỗi lần là 1 lần push riêng biệt.  
- **Tránh gửi trùng khi cả BackgroundTasks lẫn Celery task cùng chạy**: logic `_celery_available()` dùng `if/elif/else` — chỉ một nhánh được chọn. Nếu Celery có sẵn → dùng Celery, không gọi `background_tasks.add_task`.
- **Retry task_send_push** có thể gửi push nhiều lần tới cùng thiết bị nếu lần trước thực sự gửi thành công nhưng exception xảy ra sau (mạng không ổn định). Chấp nhận được — push là thông báo ngắn, không có hậu quả nghiêm trọng khi nhận trùng.

### Email (task_send_email và B4)

- `send_smtp_email` đọc `EmailLog` theo `log_id`. Cần thêm guard ngắn:

```python
# Đầu hàm send_smtp_email, sau khi load log:
if log.status == "sent":
    return   # đã gửi thành công (có thể do retry Celery gửi xong nhưng ACK chậm)
```

- **B4 và Celery task chạy cùng lúc**: B4 tăng `retry_count` và gọi `send_smtp_email`. Nếu Celery task vẫn đang pending trong queue (delay chưa đến) cũng có thể gửi cùng record. Guard `status == "sent"` trên ngăn gửi trùng dòng đã thành công.
- **`retry_count` giới hạn**: B4 không retry nếu `retry_count >= MAX_RETRIES_B4` (= 5). Bao gồm cả lần gốc (`send_account_creation_email` gọi task lần đầu thất bại → B4 chạy từ lần 2 trở đi).
- **`password_reset` và thời hạn link**: link reset thường hết hạn sau 1–24 giờ. B4 chạy mỗi 15 phút → tổng 5 lần trong ~75 phút. Nếu link đã hết hạn thì email vẫn đến nhưng người dùng phải yêu cầu link mới — chấp nhận được. Cân nhắc thêm cột `expires_at` vào `EmailLog` nếu cần lọc bỏ link hết hạn.

---

## 6. Kiểm thử & tiêu chí hoàn thành

### 6.1 Unit test (pytest, SQLite in-memory)

| Test | Kỳ vọng |
|------|---------|
| `test_send_push_task_dispatched_when_celery_available` | `task_send_push.delay` được gọi; `background_tasks.add_task` không được gọi |
| `test_send_push_fallback_background_tasks` | Khi `_celery_available()` = False → `background_tasks.add_task` được gọi |
| `test_send_email_task_dispatched` | `task_send_email.delay` gọi với đúng `log_id`, `force` |
| `test_send_smtp_email_idempotent_sent` | Record đã `status=sent` → hàm return sớm, không gửi SMTP |
| `test_b4_skips_when_email_disabled` | `email_enabled=false` → task return `{"skipped": True}` |
| `test_b4_increments_retry_count` | Record `status=failed, retry_count=0` → sau B4 `retry_count=1` |
| `test_b4_stops_at_max_retries` | `retry_count=5` → B4 bỏ qua record |

### 6.2 Kiểm thử tích hợp thủ công

1. **Bật Celery worker**, tắt SMTP (sai mật khẩu) → gửi yêu cầu tạo tài khoản → `tab_email_log` có record `status=failed`.
2. **Sửa lại SMTP** → đợi Beat chạy sau tối đa 15 phút → record đổi thành `status=sent`.
3. **Tắt Celery** → gọi `submit` một YCKS → push vẫn gửi qua `background_tasks` (fallback).
4. **Bật Celery** → gọi `submit` → Celery task xuất hiện trong Flower/log worker.

### 6.3 Tiêu chí hoàn thành

- [ ] Tất cả unit test xanh
- [ ] `tab_email_log` có cột `html_body` và `retry_count` (migration đã chạy)
- [ ] Push và email đi qua Celery khi worker chạy; fallback hoạt động khi không có Redis
- [ ] B4 tự retry email `failed`/`pending` mỗi 15 phút; dừng ở `retry_count=5`
- [ ] Không gửi trùng email đã `sent`
- [ ] Log Celery không có unhandled exception cho task push/email

---

## 7. Rủi ro & lưu ý

### 7.1 ENV thiếu trong worker

Worker cần **cùng ENV** với `api`. Nếu thiếu `VAPID_PRIVATE_KEY` → `send_to_users` return sớm (đã có guard trong `push/service.py`), không raise exception — push bị mất thầm lặng.

**Kiểm tra ngay khi deploy:**
```bash
docker compose exec celery-worker python -c "import os; print(os.getenv('VAPID_PRIVATE_KEY', 'THIẾU'))"
```

### 7.2 Tránh gửi trùng khi cả hai đường cùng chạy

- Logic `if _celery_available(): … elif background_tasks: … else: …` đảm bảo **chỉ một đường** được dùng trong một request.  
- Không để cả hai `background_tasks.add_task` và `task.delay` cùng tồn tại trong một nhánh.

### 7.3 `_celery_available()` gọi mỗi request

Hàm kiểm tra kết nối Celery/Redis mỗi lần có thể tạo overhead nhỏ. Cân nhắc cache kết quả 30 giây (dùng `functools.lru_cache` với TTL, hoặc biến module-level cập nhật theo ngoại lệ). Giai đoạn đầu không cần tối ưu.

### 7.4 `html_body` lưu trong DB có thể lớn

Email HTML từ template (`ACCOUNT_CREATION_TEMPLATE`, `PASSWORD_RESET_TEMPLATE`) thường vài KB — không đáng kể. Nếu sau này có email nội dung lớn (digest, báo cáo), cân nhắc lưu ra file/object storage.

### 7.5 B4 không retry email `disabled`

Record `status=disabled` (bị tắt qua `email_enabled=false`) KHÔNG bị B4 retry — đúng thiết kế. Chỉ `pending` (chưa gửi lần nào, hoặc worker chưa chạy) và `failed` (đã thử nhưng lỗi SMTP) mới được retry.

### 7.6 `password_reset` — link hết hạn khi retry

Email reset mật khẩu có `force=True` — B4 vẫn retry để đảm bảo email đến. Tuy nhiên nếu token đã hết hạn và người dùng nhấn link, họ sẽ thấy lỗi "link không hợp lệ". Đây là trade-off chấp nhận được; giải pháp lâu dài là thêm cột `token_expires_at` vào `EmailLog` để B4 bỏ qua email hết hạn.

### 7.7 Phụ thuộc Phase 0

Phase 1 **không thể hoạt động** nếu chưa có `celery_app`, `celery-worker`, `celery-beat` từ Phase 0. Fallback `BackgroundTasks` vẫn hoạt động nhưng không có retry.
