# Phase 0 — Hạ tầng Celery + Redis

> **Trạng thái:** Chưa bắt đầu  
> **Phụ thuộc:** Không có (phase đầu tiên, phải làm trước tất cả phase còn lại)  
> **Ảnh hưởng code hiện tại:** Không phá vỡ logic nào — chỉ thêm service + module mới

---

## 1. Mục tiêu

Dựng nền tảng **chạy tác vụ ngầm và theo lịch** cho procurement-tool, gồm:

- Một **Redis instance** làm message broker (nhận/giao task) và result backend (lưu kết quả).
- Một **`celery-worker`** container nhận task từ queue và thực thi.
- Một **`celery-beat`** container phát lịch cron (dùng ở Phase 2 trở đi).
- Module **`backend/app/core/celery_app.py`** — điểm khai báo Celery app dùng chung cho toàn bộ backend.

Sau phase này, các phase sau chỉ cần `from app.core.celery_app import celery_app` rồi viết `@celery_app.task` là đủ — không phải cấu hình thêm infra.

**Vì sao cần Celery + Redis?**  
Nhiều tác vụ tốn thời gian hoặc cần chạy nền (gửi email/push, cảnh báo SLA, xuất báo cáo, dọn dẹp DB) hiện chạy đồng bộ trong request hoặc chưa được làm. Celery cho phép tách các tác vụ đó ra khỏi request-response cycle, đảm bảo retry, schedule, và không block API.

---

## 2. Phạm vi & việc cụ thể

### Checklist triển khai

- [ ] **[PY-1]** Thêm `celery` và `redis` vào `backend/requirements.txt`
- [ ] **[PY-2]** Tạo `backend/app/core/celery_app.py` với đầy đủ cấu hình broker/backend/timezone/autodiscover
- [ ] **[PY-3]** Thêm biến `REDIS_URL` vào `backend/app/core/config.py` (class `Settings`)
- [ ] **[PY-4]** Thêm `REDIS_URL` vào file `.env` (dev) và ghi chú vào `.env` (prod trên VPS)
- [ ] **[DC-1]** Thêm service `redis` vào `docker-compose.yml` (dev)
- [ ] **[DC-2]** Thêm service `celery-worker` vào `docker-compose.yml` (dev)
- [ ] **[DC-3]** Thêm service `celery-beat` vào `docker-compose.yml` (dev)
- [ ] **[DC-4]** Thêm service `redis` vào `docker-compose.production.yml` (prod, cùng `procurement-internal`)
- [ ] **[DC-5]** Thêm service `celery-worker` vào `docker-compose.production.yml` (prod, cùng image Dockerfile.api)
- [ ] **[DC-6]** Thêm service `celery-beat` vào `docker-compose.production.yml` (prod)
- [ ] **[TEST-1]** Viết task `ping` trong `backend/app/tasks/debug.py` để smoke test
- [ ] **[TEST-2]** Smoke test: gọi `ping.delay()` từ `docker compose exec api python -c ...`, xác nhận worker nhận và trả kết quả

---

## 3. Thiết kế kỹ thuật

### 3.1 File tạo mới: `backend/app/core/celery_app.py`

```python
# backend/app/core/celery_app.py
"""
Khai báo Celery app dùng chung cho toàn bộ procurement-tool.
Import ở mọi nơi: from app.core.celery_app import celery_app
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "procurement",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    # Timezone Việt Nam — mọi lịch cron và timestamp dùng múi giờ này
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=False,

    # Autodiscover tasks trong các module; thêm module mới vào list này
    # khi triển khai Phase 1, 2, 3...
    # Quy ước: mỗi module có thể có file tasks.py hoặc thư mục tasks/
    imports=[
        "app.tasks.debug",          # smoke-test ping (Phase 0)
        # "app.modules.notification.tasks",   # Phase 1 — gửi push/email
        # "app.modules.alert.tasks",          # Phase 2 — cảnh báo SLA
        # "app.modules.report.tasks",         # Phase 3 — refresh báo cáo
    ],

    # Serialization — json an toàn hơn pickle
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Kết quả tác vụ sống 24h (đủ để debug, không phình Redis)
    result_expires=86400,

    # Retry mặc định: worker crash thì task không bị mất
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Beat schedule (trống, các phase sau điền vào)
    beat_schedule={},
)
```

**Lưu ý thiết kế:**
- `imports` (không phải `autodiscover_tasks`) — liệt kê tường minh để dễ kiểm soát; tránh Celery load toàn bộ `app/` khi khởi động, hạn chế hiệu ứng phụ.
- `task_acks_late=True` + `task_reject_on_worker_lost=True`: nếu worker bị kill giữa chừng, task quay lại queue thay vì bị mất.
- `enable_utc=False` + `timezone="Asia/Ho_Chi_Minh"`: các `crontab(hour=8, minute=0)` sẽ tính theo giờ Hà Nội, không cần cộng trừ 7h thủ công.

---

### 3.2 File sửa: `backend/app/core/config.py`

Thêm 2 biến vào class `Settings` (sau nhóm biến DB):

```python
# --- Celery / Redis ---
REDIS_URL: str = "redis://redis:6379/0"
# Broker và Backend đều dùng cùng Redis (đơn giản, đủ cho scale ~20-100 user).
# Nếu sau này tách, khai báo 2 URL riêng.
@property
def CELERY_BROKER_URL(self) -> str:
    return self.REDIS_URL

@property
def CELERY_RESULT_BACKEND(self) -> str:
    return self.REDIS_URL
```

> **Tại sao dùng property?** Cho phép sau này đổi broker (ví dụ sang RabbitMQ) hoặc tách result backend mà không cần đổi code `celery_app.py`.

---

### 3.3 File tạo mới: `backend/app/tasks/debug.py`

Task duy nhất trong Phase 0, dùng để smoke test:

```python
# backend/app/tasks/debug.py
"""
Tasks dùng để kiểm tra hạ tầng Celery. Không dùng trong production logic.
"""
from app.core.celery_app import celery_app


@celery_app.task(name="debug.ping")
def ping(message: str = "pong") -> dict:
    """Trả lại message để xác nhận worker hoạt động."""
    return {"status": "ok", "echo": message}
```

---

### 3.4 File sửa: `backend/requirements.txt`

Thêm 2 dòng vào cuối (giữ phiên bản cụ thể để build lại image được cacheably):

```
celery==5.4.0
redis==5.1.1
```

**Lý do chọn phiên bản:**
- `celery==5.4.0` — bản ổn định mới nhất (2024), tương thích Python 3.12.
- `redis==5.1.1` — client Python cho Redis; Celery dùng nội bộ, không cần `hiredis` cho workload này.

---

### 3.5 Task và DB session

Các task ở phase sau cần query DB phải tự quản lý session:

```python
# Mẫu đúng — task tự mở/đóng session
from app.core.database import SessionLocal

@celery_app.task
def my_task():
    db = SessionLocal()
    try:
        # ... query logic ...
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

**KHÔNG** dùng `get_db()` (generator của FastAPI) — `get_db()` dành riêng cho request context.

---

## 4. Cấu hình

### 4.1 Biến môi trường `.env`

Thêm vào file `.env` (dev và prod):

```dotenv
# --- Celery / Redis ---
REDIS_URL=redis://redis:6379/0
```

Trên VPS, `redis` là tên service trong `docker-compose.production.yml` — DNS tự resolve trong Docker network `procurement-internal`.

---

### 4.2 Docker — dev (`docker-compose.yml`)

Thêm 3 service sau vào `docker-compose.yml` (đặt sau service `api`):

```yaml
  redis:
    image: redis:7.2-alpine
    restart: unless-stopped
    # Không expose port ra host (chỉ dùng nội bộ)
    # Nếu muốn inspect từ host: thêm ports: ["6379:6379"] tạm thời

  celery-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    env_file: .env
    volumes:
      - ./backend:/app          # hot reload code tasks khi dev
    command: celery -A app.core.celery_app worker -l info -c 2
    depends_on:
      - redis
      - api                     # đảm bảo DB đã migrate trước (api start.sh chạy migrate)

  celery-beat:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    env_file: .env
    volumes:
      - ./backend:/app
    command: celery -A app.core.celery_app beat -l info --scheduler celery.beat:PersistentScheduler
    depends_on:
      - redis
      - celery-worker
```

**Lưu ý dev:**
- Worker concurrency `-c 2` — đủ cho dev, tránh tốn RAM.
- `celery-beat` dùng `PersistentScheduler` (lưu lịch vào file `celerybeat-schedule` trong `/app`) — đơn giản, không cần DB thêm.
- Volume mount `./backend:/app` giữ cho code tasks hot-reload khi sửa (worker cần restart thủ công: `docker compose restart celery-worker`).

---

### 4.3 Docker — prod (`docker-compose.production.yml`)

Thêm 3 service sau (đặt sau service `api`):

```yaml
  redis:
    image: redis:7.2-alpine
    container_name: procurement-redis
    restart: always
    networks:
      - procurement-internal    # chỉ nội bộ, không lộ ra ngoài
    volumes:
      - redis_data:/data        # persist data qua restart
    command: redis-server --save 60 1 --loglevel warning

  celery-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.api   # cùng image với api
    container_name: procurement-celery-worker
    env_file: .env
    restart: always
    command: celery -A app.core.celery_app worker -l info -c 4
    depends_on:
      - redis
    networks:
      - dego-erp_default        # để tới MariaDB (dego-erp-db-1:3306)
      - procurement-internal    # để tới Redis

  celery-beat:
    build:
      context: .
      dockerfile: docker/Dockerfile.api   # cùng image với api
    container_name: procurement-celery-beat
    env_file: .env
    restart: always
    command: celery -A app.core.celery_app beat -l info --scheduler celery.beat:PersistentScheduler
    depends_on:
      - redis
      - celery-worker
    networks:
      - procurement-internal    # beat chỉ cần nói chuyện với Redis

volumes:
  redis_data:
```

Thêm `redis_data` vào phần `volumes:` cấp cao nhất của file nếu chưa có.

**Lưu ý prod:**
- Worker join **cả hai** network: `dego-erp_default` (để query MariaDB) và `procurement-internal` (để nhận task từ Redis).
- Beat chỉ cần `procurement-internal` (chỉ đẩy task vào Redis, không truy cập DB trực tiếp).
- `restart: always` — nếu Redis khởi động lại (VPS reboot), worker/beat tự reconnect.
- `--save 60 1` — Redis lưu snapshot mỗi 60s nếu có ít nhất 1 key thay đổi (đủ cho result backend, không cần AOF).

---

## 5. Chống trùng / Idempotent

Phase 0 không có task thực tế, không cần cơ chế idempotent.

Quy tắc áp dụng cho **tất cả task từ Phase 1 trở đi** (ghi ở đây để thống nhất):

1. **Đánh dấu trước khi làm** — ví dụ task gửi thông báo: update cột `notified_at IS NOT NULL` trước khi gửi; nếu task chạy lại (retry) thì check trường này trước và bỏ qua nếu đã đánh dấu.
2. **Lock bằng Redis nếu cần** — dùng `cache.set("lock:task_name:id", 1, nx=True, ex=60)` để đảm bảo chỉ 1 worker xử lý cùng lúc.
3. **Tránh `apply_async` nhiều lần trong beat** — kiểm tra khoảng cách thời gian giữa 2 lần chạy trước khi enqueue.

---

## 6. Kiểm thử & tiêu chí hoàn thành

### 6.1 Smoke test — task `ping`

Sau khi chạy `docker compose up --build`, thực hiện:

```bash
# Từ máy local — gọi task qua api container
docker compose exec api python -c "
from app.tasks.debug import ping
result = ping.delay('hello-celery')
print('Task ID:', result.id)
print('Kết quả:', result.get(timeout=10))
"
```

**Kết quả mong đợi:**
```
Task ID: <uuid>
Kết quả: {'status': 'ok', 'echo': 'hello-celery'}
```

### 6.2 Kiểm tra worker log

```bash
docker compose logs celery-worker --tail=30
```

Phải thấy dòng:
```
[tasks]
  . debug.ping
...
celery@<hostname> ready.
...
Task debug.ping[<uuid>] succeeded in <N>s: {'status': 'ok', 'echo': 'hello-celery'}
```

### 6.3 Kiểm tra beat log

```bash
docker compose logs celery-beat --tail=20
```

Phải thấy:
```
beat: Starting...
Scheduler: Sending due task ...   ← (sẽ xuất hiện khi có schedule ở phase sau)
```

### 6.4 Tiêu chí hoàn thành (Definition of Done)

| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| 1 | `redis` container chạy và healthy | `docker compose ps` — status `Up` |
| 2 | `celery-worker` khởi động không lỗi import | `docker compose logs celery-worker` — không có `ImportError` |
| 3 | `celery-beat` khởi động không lỗi | `docker compose logs celery-beat` — `beat: Starting...` |
| 4 | Task `ping` gửi và nhận kết quả trong < 5s | Chạy smoke test ở 6.1 |
| 5 | Prod: worker kết nối được MariaDB và Redis | `docker compose -f docker-compose.production.yml logs celery-worker` |
| 6 | `REDIS_URL` không hardcode trong code | `grep -r "redis://" backend/app/` chỉ thấy trong `config.py` |

---

## 7. Rủi ro & lưu ý

### 7.1 Worker PHẢI có cùng ENV như api

Container `celery-worker` và `celery-beat` dùng `env_file: .env` — giống `api`. Tuy nhiên cần **kiểm tra rõ** các biến sau có trong `.env` VPS khi deploy:

| Biến | Dùng ở | Hậu quả nếu thiếu |
|------|--------|-------------------|
| `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Mọi task query DB | Task crash `OperationalError` |
| `JWT_SECRET` | Task gọi hàm verify token (nếu có) | Token decode fail |
| `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY` | Task gửi web push (Phase 1) | Push thất bại |
| `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` | Task gửi email (Phase 1) | Email fail |
| `REDIS_URL` | Celery broker/backend | Worker không start |

**Hành động:** Trước khi deploy prod, so sánh `.env` trên VPS với danh sách biến trong `config.py` — đảm bảo không thiếu biến nào.

### 7.2 `celery-beat` chỉ nên chạy 1 instance

Chạy nhiều `celery-beat` đồng thời sẽ phát lịch trùng → task duplicate. Trong Docker Compose đã dùng `container_name` cố định, không scale service này.

Nếu sau này dùng Kubernetes / nhiều replica: chuyển sang `redbeat` (Django Celery Beat hoặc `celery-redbeat`) để lưu lịch trong Redis thay vì file.

### 7.3 Redis không có authentication (dev)

Dev không cần auth Redis. Prod cũng ổn vì Redis chỉ trong network nội bộ Docker (`procurement-internal`), không expose port ra host/internet.

Nếu VPS có yêu cầu security cao hơn, thêm `--requirepass <password>` vào `command` của service redis và cập nhật `REDIS_URL=redis://:password@redis:6379/0`.

### 7.4 Fallback khi Celery không chạy (dev nhẹ)

Dev có thể bỏ qua dựng Celery. Các task ở phase sau cần có đường fallback đồng bộ:

```python
try:
    my_task.delay(...)
except Exception:
    # Celery không có — chạy thẳng (dev/test mode)
    my_task(...)
```

Hoặc wrap trong utility:

```python
def enqueue_or_run(task_fn, *args, **kwargs):
    """Gửi vào Celery queue; nếu lỗi (broker không có) thì chạy đồng bộ."""
    try:
        task_fn.delay(*args, **kwargs)
    except Exception:
        task_fn(*args, **kwargs)
```

### 7.5 Image size và cache Docker

`celery-worker` và `celery-beat` dùng cùng `docker/Dockerfile.api` — khi `requirements.txt` thêm `celery` và `redis`, image sẽ build lại lần đầu mất vài phút. Các lần sau sử dụng layer cache (`COPY requirements.txt` → `RUN pip install`), build nhanh.

Trên VPS: chạy `docker compose -f docker-compose.production.yml build --no-cache` lần đầu; sau đó `docker compose up -d --build` tận dụng cache.

### 7.6 `celery-beat` cần file lịch persistent

`PersistentScheduler` lưu trạng thái lịch vào file `celerybeat-schedule` trong WORKDIR (`/app`). Ở dev, file này nằm trong volume mount `./backend` — không bị mất khi restart. Ở prod, file nằm trong container layer — **bị mất khi container bị xóa và dựng lại**.

Ảnh hưởng: beat sẽ chạy lại toàn bộ task quá hạn ngay sau khi restart (có thể gây spike). Với Phase 2 (cảnh báo), task có cơ chế idempotent nên không tạo duplicate.

Nếu muốn an toàn hơn: thêm volume cho beat state trong prod:
```yaml
  celery-beat:
    volumes:
      - beat_data:/app/celerybeat-schedule   # persist beat state
```

---

*Xem thêm: [README.md](README.md) — quy ước chung; [Phase 2](phase-2-canh-bao-theo-lich.md) — dùng hạ tầng này để gửi cảnh báo SLA.*
