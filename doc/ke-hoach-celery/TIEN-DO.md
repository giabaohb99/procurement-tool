# TIẾN ĐỘ — Celery + Redis (nhánh `celery-worker`)

Ghi lại đã làm gì / đang ở đâu / làm gì tiếp. Cập nhật mỗi lần xong 1 mốc.

## Đã xong
### ✅ Phase 0 — Hạ tầng (commit `165ce80`)
- `backend/app/core/celery_app.py` — Celery app (broker+backend=Redis, timezone `Asia/Ho_Chi_Minh`, `imports` tường minh, `task_acks_late`, `result_expires=86400`).
- `backend/app/core/config.py` — `REDIS_URL` + property `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`.
- `backend/app/tasks/debug.py` — task `ping` (smoke test). `app/tasks/__init__.py`.
- `backend/requirements.txt` — `celery==5.4.0`, `redis==5.1.1`.
- Docker **dev** (`docker-compose.yml`): `redis` + `redisinsight` (http://localhost:5540) + `celery-worker` + `celery-beat`.
- Docker **prod** (`docker-compose.production.yml`): `redis` + `worker` + `beat` (network `dego-erp_default` + `procurement-internal`, beat state → volume `beat_data`); **không** RedisInsight ở prod.
- `.gitignore` — bỏ qua `celerybeat-schedule*`.
- **Smoke test local PASS**: `ping.delay('hello-celery')` → `{'status':'ok','echo':'hello-celery'}` (worker chạy, kết quả về qua Redis backend).

## Quy ước đã chốt (theo yêu cầu)
- **Tên task/hàm trong CODE = tiếng Anh** (vd `send_push`, `scan_alerts`). Tên tiếng Việt trong doc plan sẽ cập nhật sau.
- **Email**: khi làm Phase 1 → **viết code nhưng comment lại** (chưa bật). **Push**: làm thật.
- Trước khi làm push/cảnh báo → xem [notification-cases.md](notification-cases.md) (liệt kê rõ: sự kiện, nơi kích, ai nhận, kênh).

## Chưa làm (thứ tự đề xuất)
- [ ] **Phase 2 — Cảnh báo theo lịch** ⭐ (giá trị cao nhất): khung `scan_alerts` + các case (công nợ, giao trễ, HĐ, SLA, ngày cần hàng, thanh toán). Xem [phase-2](phase-2-canh-bao-theo-lich.md).
- [ ] **Phase 3 — Refresh báo cáo** theo lịch.
- [ ] **Phase 1 — Gửi push/email qua worker** (push làm, email comment) + retry. Xem [phase-1](phase-1-gui-tin-cay.md).
- [ ] **Phase 4–5** — digest, dọn dẹp, backup DB, export async.

## Lưu ý vận hành
- Phase 0 **CHƯA deploy lên VPS** (mới là hạ tầng rỗng, chỉ có task `ping`). Deploy khi bắt đầu có task nghiệp vụ.
- Nhánh này (`celery-worker`) tách từ `bao` — các fix nghiệp vụ mới trên `bao` (vd fix tạo YCMH cho người yêu cầu) sẽ **merge `bao` → `celery-worker`** trước khi deploy nhánh này.
