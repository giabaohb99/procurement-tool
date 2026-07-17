# Phase 3 — Tự refresh báo cáo + precompute dashboard

> **Yêu cầu tiên quyết**: Phase 0 (hạ tầng Redis + worker + beat) phải hoàn thành trước.
>
> Tài liệu gốc tóm tắt: [../chung/Plan_Celery_Worker.md](../chung/Plan_Celery_Worker.md).

---

## 1. Mục tiêu

| Vấn đề hiện tại | Sau Phase 3 |
|---|---|
| Snapshot báo cáo (`tab_report_snapshot`) chỉ được làm mới khi user bấm nút "Cập nhật" hoặc khi TTL hết (120 s, tự tính lại qua `BackgroundTasks` trong request). Nếu không ai mở báo cáo qua đêm, sáng hôm sau mở sẽ phải chờ tính lại ~5–15 s. | Job Celery beat tự động refresh snapshot **mỗi đêm** (ngoài giờ cao điểm), sáng mở báo cáo trả dữ liệu ngay (đọc snapshot). |
| Endpoint `GET /api/dashboard/overview` tính toàn bộ PO + item + giao hàng + công nợ + tồn kho mỗi lần user mở trang chủ — chậm khi dữ liệu lớn. | *(Tùy chọn)* Precompute/cache phần dữ liệu nặng của dashboard, giảm thời gian load trang chủ. |
| Nút "Cập nhật" thủ công trên UI vẫn có giá trị (force refresh khi vừa nhập dữ liệu quan trọng). | **Giữ nguyên** cơ chế `refresh=1` hiện có — không thay đổi controller. |

---

## 2. Phạm vi & việc cụ thể

### 2A. Báo cáo ma trận (bắt buộc)

- [ ] Tạo `backend/app/tasks/report_tasks.py` — task `refresh_report_snapshot`
- [ ] Task lấy danh sách các `(year, company_id)` đang có trong `tab_report_snapshot` **cộng** thêm năm hiện tại cho từng công ty (tránh bỏ sót năm mới chưa ai xem)
- [ ] Gọi lại đúng hàm `compute(db, year, company_id)` từ `app.modules.report.service` → `_persist_snapshot(db, key, data)` — KHÔNG viết logic mới
- [ ] Đăng ký task vào lịch beat (cron hằng đêm, giờ VN)
- [ ] Cập nhật `backend/app/core/celery_app.py` (ở Phase 0): thêm `app/tasks/report_tasks` vào `autodiscover_tasks`

### 2B. Dashboard overview (tùy chọn — làm sau 2A)

- [ ] Đánh giá khả năng cache: dashboard áp `apply_scope` theo user → mỗi user có kết quả khác nhau → **không** precompute toàn bộ theo lịch được
- [ ] Hướng thực tế: cache Redis ngắn hạn (5–10 phút) cho **dữ liệu nặng không phụ thuộc scope** (VD: tổng tồn kho công ty, chi phí 12 tháng) — phần còn lại vẫn tính theo scope
- [ ] Tạo helper `get_cached(redis_client, key, ttl, fn)` trong `app/core/cache.py`
- [ ] Áp dụng vào `dashboard/controller.py` ở các block `can("purchase_order")` + `can("inventory")` nặng nhất

### 2C. Không làm trong phase này

- Xuất báo cáo Excel bất đồng bộ (B6 — phase riêng)
- Backup DB (B5 — phase 4–5)

---

## 3. Thiết kế kỹ thuật

### 3.1 Task `refresh_report_snapshot`

**File mới**: `backend/app/tasks/report_tasks.py`

```python
"""Task Celery — tự refresh tab_report_snapshot hằng đêm.

Gọi lại đúng hàm compute() + _persist_snapshot() đã có trong report/service.py.
Mở SessionLocal riêng (không dùng session request). Idempotent: ghi đè key.
"""
import logging
from datetime import datetime

from app.core.celery_app import celery_app          # sẽ có sau Phase 0
from app.core.database import SessionLocal
from app.modules.report.service import compute, _persist_snapshot, _key
from app.modules.report.model import ReportSnapshot
from app.modules.purchase_order.model import PurchaseOrder

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.report.refresh_report_snapshot", bind=True, max_retries=2)
def refresh_report_snapshot(self):
    """Refresh toàn bộ snapshot báo cáo ma trận.

    Chiến lược:
    - Lấy danh sách (year, company_id) từ các key đang có trong tab_report_snapshot.
    - Bổ sung key năm hiện tại × từng company_id khác biệt trong PurchaseOrder.
    - Luôn refresh key 'all|all' (toàn hệ thống, không lọc công ty).
    - Ghi đè snapshot (idempotent).
    """
    db = SessionLocal()
    try:
        current_year = str(datetime.now().year)

        # --- Tập hợp (year, company_id) cần refresh ---
        pairs: set[tuple] = set()

        # 1) Tất cả key đang có trong bảng snapshot (tránh bỏ sót năm cũ còn xem)
        existing = db.query(ReportSnapshot.key).all()
        for (k,) in existing:
            parts = k.split("|")
            if len(parts) == 2:
                yr, cid = parts
                pairs.add((yr if yr != "all" else None,
                           int(cid) if cid != "all" else None))

        # 2) Năm hiện tại × mỗi company_id đang có trong PurchaseOrder
        company_ids = [row[0] for row in
                       db.query(PurchaseOrder.company_id).distinct().all()
                       if row[0] is not None]
        for cid in company_ids:
            pairs.add((current_year, cid))
        pairs.add((current_year, None))   # toàn công ty, năm này
        pairs.add((None, None))           # key 'all|all'

        logger.info("refresh_report_snapshot: %d pair(s) cần refresh", len(pairs))
        ok, failed = 0, 0
        for (year, company_id) in pairs:
            try:
                data = compute(db, year, company_id)
                _persist_snapshot(db, _key(year, company_id), data)
                ok += 1
            except Exception as exc:
                failed += 1
                logger.error("Lỗi refresh key %s: %s", _key(year, company_id), exc)

        logger.info("refresh_report_snapshot xong: ok=%d failed=%d", ok, failed)
        return {"ok": ok, "failed": failed}

    except Exception as exc:
        logger.error("refresh_report_snapshot ngoại lệ: %s", exc)
        raise self.retry(exc=exc, countdown=300)   # thử lại sau 5 phút
    finally:
        db.close()
```

### 3.2 Đăng ký lịch beat

Trong `backend/app/core/celery_app.py` (tạo ở Phase 0), thêm vào `beat_schedule`:

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # ... các job phase 2 ...

    # Phase 3 — Refresh báo cáo mỗi đêm 2:00 AM giờ VN
    "refresh-report-snapshot-nightly": {
        "task": "tasks.report.refresh_report_snapshot",
        "schedule": crontab(hour=2, minute=0),
        # timezone được set ở celery_app.conf.timezone = "Asia/Ho_Chi_Minh"
    },
}
```

### 3.3 Đăng ký autodiscover

```python
# backend/app/core/celery_app.py
celery_app.autodiscover_tasks([
    "app.tasks.report_tasks",
    # app.tasks.alert_tasks   (Phase 2)
    # app.tasks.notify_tasks  (Phase 1)
])
```

### 3.4 Quan hệ với cơ chế SWR hiện có

Cơ chế **stale-while-revalidate** trong `service.get_snapshot()` (`_SNAP_TTL = 120 s`) vẫn giữ nguyên:

```
User mở báo cáo
    │
    ├─ Snapshot tươi (< 120 s)?  → Trả ngay ✓
    ├─ Snapshot cũ (> 120 s)?    → Trả ngay + tính lại ngầm qua BackgroundTasks
    └─ Chưa có snapshot?         → Tính đồng bộ rồi trả (lần đầu tiên)

Job beat 2:00 AM  → compute() + _persist_snapshot()  (ghi đè key)
    → Sáng hôm sau snapshot luôn tươi, user không phải chờ
```

Nút "Cập nhật" trên UI (`GET /api/reports/matrix?refresh=1`) gọi `get_snapshot(..., refresh=True)` → tính đồng bộ ngay. **Không thay đổi controller hay service.**

### 3.5 (Tùy chọn) Cache dashboard overview

Dashboard `GET /api/dashboard/overview` có hai loại tính toán:

| Phần | Phụ thuộc scope user? | Chiến lược |
|---|---|---|
| Cost 12 tháng, phân loại VTBB/NL, tồn kho toàn công ty | Có (apply_scope) | **Không cache chung** — tính theo scope |
| Tổng tồn kho công ty (Inventory aggregation) | Một phần (theo company_id) | Cache Redis 10 phút theo `company_id` |
| Alerts (`build_alerts`) | Không | Cache Redis 5 phút (key cố định) |

Phác thảo helper nếu triển khai:

```python
# backend/app/core/cache.py
import json
from typing import Callable, Any
import redis as redis_lib

_redis: redis_lib.Redis | None = None

def get_redis() -> redis_lib.Redis | None:
    """Trả None nếu REDIS_URL chưa cấu hình (dev nhẹ)."""
    global _redis
    if _redis is None:
        import os
        url = os.getenv("REDIS_URL")
        if url:
            _redis = redis_lib.from_url(url, decode_responses=True)
    return _redis


def get_cached(key: str, ttl: int, fn: Callable[[], Any]) -> Any:
    """Đọc từ Redis; nếu miss thì gọi fn(), lưu TTL giây, trả kết quả.
    Nếu Redis không có → gọi fn() thẳng (fallback)."""
    r = get_redis()
    if r is not None:
        raw = r.get(key)
        if raw:
            return json.loads(raw)
    result = fn()
    if r is not None:
        r.set(key, json.dumps(result, ensure_ascii=False), ex=ttl)
    return result
```

---

## 4. Cấu hình

### 4.1 Biến môi trường

```dotenv
# .env (dev + prod — dùng chung file)
REDIS_URL=redis://redis:6379/0          # (đã thêm ở Phase 0)
# Không cần biến mới cho Phase 3
```

### 4.2 Docker (prod)

Không cần service mới; `celery-beat` đã được thêm ở Phase 0 và tự pick up beat_schedule mới sau khi rebuild image.

```yaml
# docker-compose.production.yml (khai báo ở Phase 0, KHÔNG sửa thêm ở phase này)
celery-beat:
  image: procurement-api
  command: celery -A app.core.celery_app beat --loglevel=info
  # ...
```

### 4.3 Lịch cron

| Job | Cron (giờ VN) | Lý do chọn giờ |
|---|---|---|
| `refresh_report_snapshot` | `0 2 * * *` — 2:00 AM | Sau nửa đêm, trước giờ mở văn phòng (~7–8 h); tránh giờ cao điểm 8–17 h |

> **Lưu ý timezone**: `celery_app.conf.timezone = "Asia/Ho_Chi_Minh"` bắt buộc phải set ở Phase 0. Không để mặc định UTC (lệch +7 h → chạy vào 9 h sáng).

---

## 5. Chống trùng / Idempotent

Snapshot lưu theo `key = '{year}|{company_id}'` với ràng buộc `unique=True` trên cột `key` (model `ReportSnapshot`). Hàm `_persist_snapshot` đã xử lý upsert:

```python
snap = db.query(ReportSnapshot).filter(ReportSnapshot.key == key).first()
if not snap:
    snap = ReportSnapshot(key=key)
    db.add(snap)
snap.data = json.dumps(data, ensure_ascii=False)
snap.computed_at = data["computed_at"]
db.commit()
```

→ Chạy lại nhiều lần chỉ **ghi đè** bản đã có, không tạo bản mới. Không cần cờ "đã xử lý" như Phase 2 (cảnh báo).

Nếu job bị lỗi giữa chừng (một số key thất bại), lần chạy tiếp theo tự refresh lại toàn bộ danh sách — an toàn.

---

## 6. Kiểm thử & tiêu chí hoàn thành

### 6.1 Unit test task

File `test/backend/test_report_snapshot_task.py`:

```python
"""Kiểm tra refresh_report_snapshot không crash và cập nhật snapshot."""
import json
from unittest.mock import patch, MagicMock
from app.tasks.report_tasks import refresh_report_snapshot


def test_refresh_creates_snapshot(db_session):
    """Sau khi chạy task, tab_report_snapshot có ít nhất 1 bản ghi."""
    # Giả lập compute trả dữ liệu tối giản
    fake_data = {"computed_at": "2026-01-01 02:00:00", "months": [], "department": []}
    with patch("app.tasks.report_tasks.compute", return_value=fake_data):
        result = refresh_report_snapshot.apply()   # chạy đồng bộ (không cần broker)
    assert result.get("failed", 0) == 0


def test_snapshot_matches_direct_compute(db_session):
    """Số liệu snapshot == tính trực tiếp compute() với cùng tham số."""
    from app.modules.report.service import compute, get_snapshot, _key
    from app.modules.report.model import ReportSnapshot

    year = "2026"
    company_id = None

    # Tính trực tiếp
    direct = compute(db_session, year, company_id)

    # Gọi task refresh (đồng bộ)
    with patch("app.tasks.report_tasks.SessionLocal", return_value=db_session):
        refresh_report_snapshot.apply()

    snap = db_session.query(ReportSnapshot).filter(
        ReportSnapshot.key == _key(year, company_id)
    ).first()
    assert snap is not None
    saved = json.loads(snap.data)
    # So sánh chiều tháng (không phụ thuộc thứ tự dòng detail)
    assert saved["year"] == direct["year"]
    assert len(saved["months"]) == len(direct["months"])
```

### 6.2 Kiểm thử thủ công (trên môi trường dev có Redis)

```bash
# Kích hoạt task ngay (không chờ lịch beat)
docker compose exec celery-worker celery -A app.core.celery_app call tasks.report.refresh_report_snapshot

# Xem kết quả trong log
docker compose logs celery-worker --tail=30

# Kiểm tra snapshot trong DB
docker compose exec api python -c "
from app.core.database import SessionLocal
from app.modules.report.model import ReportSnapshot
db = SessionLocal()
snaps = db.query(ReportSnapshot).all()
for s in snaps:
    print(s.key, s.computed_at)
db.close()
"

# Mở báo cáo UI → không thấy nút spinner tính lại (snapshot đã tươi)
```

### 6.3 Tiêu chí hoàn thành

- [ ] Task chạy không lỗi với DB trống (không có PO nào) — trả `ok=0, failed=0`
- [ ] Task chạy với dữ liệu thật → cập nhật `computed_at` trong `tab_report_snapshot`
- [ ] Số liệu snapshot khớp với kết quả gọi `compute()` trực tiếp cùng tham số (test 6.2)
- [ ] Mở trang Báo cáo sau khi task chạy → trang load < 1 s (không tính lại đồng bộ)
- [ ] Nút "Cập nhật" thủ công vẫn hoạt động bình thường (`?refresh=1`)
- [ ] Log beat ghi rõ thời điểm chạy và số key refresh

---

## 7. Rủi ro & lưu ý

### 7.1 Thời điểm chạy

- **Chọn 2:00 AM giờ VN** (19:00 UTC hôm trước) — sau khi dữ liệu cuối ngày đã nhập xong, trước khi văn phòng mở cửa (~7–8 h).
- Tránh khung **7:00–18:00** (giờ cao điểm): nhiều request đang chạy, DB tải cao, compute báo cáo có thể kéo dài 3–10 s/key.
- Nếu dữ liệu lớn (> 10.000 PO/năm), xem xét chạy tuần tự từng key (đã làm trong code phác thảo) thay vì song song, để tránh quá tải DB.

### 7.2 Snapshot theo kỳ nào

- **key `{year}|{company_id}`**: snapshot cho **toàn bộ năm** `year`. Không cache theo tháng — không cần thiết vì `compute()` đã nhanh khi dữ liệu ≤ 1 năm.
- **key `all|all`** và **`all|{cid}`**: snapshot không lọc năm (tất cả thời gian). Tập dữ liệu lớn hơn → tính lâu hơn. Nếu ít dùng, có thể bỏ khỏi danh sách refresh tự động.
- Năm cũ (ví dụ `2024|all`): vẫn refresh nếu còn trong `tab_report_snapshot` — dữ liệu năm cũ đã đóng sổ, thực tế không đổi, nhưng chi phí nhỏ nên vẫn làm cho nhất quán.

### 7.3 Lần đầu (chưa có snapshot)

- Khi triển khai Phase 3 lần đầu, `tab_report_snapshot` có thể rỗng (chưa ai mở báo cáo).
- Pair `(current_year, company_id)` được thêm tự động từ danh sách PurchaseOrder → task vẫn tự sinh đủ key để warmup lần đầu.
- Hoặc kích hoạt thủ công bằng lệnh `celery call` (xem mục 6.2).

### 7.4 Thất bại 1 key không chặn key khác

- Task bắt `Exception` per-key, đếm `failed` riêng, tiếp tục vòng lặp — một năm/công ty lỗi không làm hỏng toàn bộ job.
- Nếu toàn bộ job crash (ngoại lệ cấp ngoài vòng lặp), Celery retry sau 5 phút (tối đa 2 lần, xem `max_retries=2`).

### 7.5 Dashboard overview (tùy chọn)

- Dashboard áp `apply_scope` per-user → **không thể** precompute kết quả cuối theo lịch (mỗi user thấy dữ liệu khác).
- Cache Redis ngắn hạn (5–10 phút) chỉ có ý nghĩa với dữ liệu không phụ thuộc scope (alerts, tồn kho tổng công ty). Nếu số user ít (< 20), độ trễ hiện tại thường chấp nhận được — **không bắt buộc làm Phase 3B**.
- Nếu làm 3B: phải đo thực tế thời gian `/api/dashboard/overview` trước và sau để xác nhận cải thiện.

### 7.6 Phụ thuộc Phase 0

Phase này hoàn toàn phụ thuộc Phase 0 (celery_app, Redis, worker, beat). **Không thể chạy độc lập.** Nếu Phase 0 chưa xong, giữ nguyên cơ chế SWR + BackgroundTasks hiện có — đã đủ dùng ở quy mô hiện tại.
