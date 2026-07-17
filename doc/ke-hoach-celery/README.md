# Kế hoạch chi tiết — Celery + Redis (worker / beat)

Nền tảng **chạy ngầm + theo lịch** cho procurement-tool. Mỗi phase 1 file chi tiết (thiết kế, việc cụ thể, cấu hình, cách test). Bản tóm tắt gốc: [../chung/Plan_Celery_Worker.md](../chung/Plan_Celery_Worker.md).

## Mục lục (theo THỨ TỰ LÀM)
1. [Phase 0 — Hạ tầng](phase-0-ha-tang.md) — dựng Redis + worker + beat (bắt buộc trước)
2. [Phase 2 — Cảnh báo theo lịch ⭐](phase-2-canh-bao-theo-lich.md) — khung job + các loại tiêu chí (gồm B1 SLA, B2 ngày cần hàng, B3 thanh toán)
3. [Phase 3 — Tự refresh báo cáo + precompute dashboard](phase-3-refresh-bao-cao.md)
4. [Phase 1 — Gửi push/email qua worker (tin cậy) + retry email](phase-1-gui-tin-cay.md)
5. [Phase 4–5 — Digest, dọn dẹp, sao lưu DB, export async](phase-4-5-digest-dondep.md)

## Quy ước chung (mọi phase tuân theo)
- **Tiếng Việt**, bám đúng code hiện tại (tên file/hàm/cột thật), không bịa.
- **Timezone**: mọi lịch cron theo `Asia/Ho_Chi_Minh` (không để UTC lệch 7h).
- **Idempotent**: job chạy lại KHÔNG tạo thông báo/dữ liệu trùng (đánh dấu "đã xử lý").
- **DB session**: task tự mở `SessionLocal()` và đóng; KHÔNG dùng session của request.
- **Prod**: `celery-worker` + `celery-beat` chạy **cùng image api** (`docker/Dockerfile.api`), khác `command`; cùng mạng để tới MariaDB (`dego-erp-db-1`) + Redis.
- **ENV cho worker** giống api: `JWT_SECRET`, `VAPID_PRIVATE_KEY`, SMTP… (dùng chung `.env`).
- **Fallback**: giữ đường chạy đồng bộ khi Celery/Redis không có (để dev nhẹ, không bắt buộc dựng full).
- **Vị trí task chuẩn**: đặt ở `backend/app/tasks/*.py` (vd `tasks/notifications.py`, `tasks/alerts.py`, `tasks/report_tasks.py`, `tasks/digest.py`, `tasks/maintenance.py`); khai báo `imports` tường minh trong `celery_app.py`.

## Giải đáp nhanh (các câu hay hỏi)

**1. Có nêu rõ điểm cần SỬA/BỎ trong API để gọi task không?** — Có, tập trung ở [Phase 1](phase-1-gui-tin-cay.md). Các điểm hiện dùng `BackgroundTasks` (chạy trong tiến trình web) sẽ đổi sang gọi task:
- `notification/service.py` → `trigger_notification` (push) + `send_account_creation_email` / `send_password_reset_email` (email).
- `survey_request/controller.py` → helper `_notify` (push).
- Cách đổi: có hàm `_celery_available()` → nếu có Celery thì `task.delay(...)`, không thì giữ **fallback đồng bộ** (dev không cần dựng Redis). *(Các phase 2/3/4-5 chủ yếu THÊM task chạy theo lịch — không thay call cũ trong API.)*

**2. Task lỗi có retry không? Bao nhiêu lần?** — Có, cấu hình theo từng task:
| Task | max_retries | Backoff |
|---|---|---|
| Gửi Web Push (`task_send_push`) | 3 | 30s → 60s → 120s (jitter) |
| Gửi email (`task_send_email`) | 4 | có backoff |
| Retry email log (B4) | quét lại theo lịch, giới hạn tổng ~5 lần/record |
| Cảnh báo / báo cáo / backup | 3–5 (mặc định), retry sau vài phút |
Ngoài ra `task_acks_late=True` + `task_reject_on_worker_lost=True`: worker chết giữa chừng → task **quay lại queue** (không mất).

**3. Kết quả ghi vào Redis không?** — Có. `CELERY_RESULT_BACKEND = Redis`, kết quả sống `result_expires=86400` (24h, đủ để debug, không phình Redis). *Lưu ý:* task gửi thông báo là "fire-and-forget" — thường không cần đọc kết quả; result backend chủ yếu để **debug / xem trạng thái task** (thành công/lỗi) qua RedisInsight hoặc Flower.

**4. Quản lý Redis dễ hơn** — đã thêm **RedisInsight** (GUI) vào [Phase 0](phase-0-ha-tang.md) (dev, `http://localhost:5540`): xem queue Celery, task đang chờ, kết quả task, memory, monitor. (Chỉ dev — không đưa lên prod.)

**5. Task chạy hằng ngày ĐĂNG KÝ / LƯU ở đâu?** — Cần tách **2 lớp**:
- **Định nghĩa lịch** (task nào, mấy giờ) = **CODE** trong `beat_schedule` của `celery_app.py` (mỗi phase thêm entry, vd `crontab(hour=8)`). → Nằm trong **git**, deploy theo app. Đây là "nguồn sự thật"; đổi lịch = sửa code + deploy lại beat. **KHÔNG lưu ở DB/Redis** (với `PersistentScheduler`).
- **Trạng thái beat** (mốc "đã chạy lần cuối" để biết khi nào chạy tiếp) = **file `celerybeat-schedule`** do `PersistentScheduler` ghi trong container beat. → Prod cần **volume persist** (`beat_data`), nếu mất chỉ mất mốc chạy cuối (beat tính lại), không mất định nghĩa.
- Muốn **lưu lịch trong Redis** (đổi lịch không cần deploy, hoặc chạy nhiều beat) → dùng **`celery-redbeat`** (nêu ở [Phase 0 §7](phase-0-ha-tang.md)). Hiện plan chọn `PersistentScheduler` (đơn giản, đủ dùng vì lịch cố định).

## Mẫu lịch cron (crontab) thường dùng

Celery `crontab` có 5 trường: `minute`, `hour`, `day_of_week`, `day_of_month`, `month_of_year`.

| Lịch | Cấu hình |
|---|---|
| Mỗi ngày 8h sáng | `crontab(hour=8, minute=0)` |
| **Ngày 15 hằng tháng, 8h** | `crontab(day_of_month=15, hour=8, minute=0)` |
| Ngày 1 hằng tháng, 0h30 | `crontab(day_of_month=1, hour=0, minute=30)` |
| Mỗi quý (tháng 1/4/7/10, ngày 1) | `crontab(day_of_month=1, month_of_year="1,4,7,10", hour=0)` |
| Thứ 2 hằng tuần, 9h | `crontab(day_of_week=1, hour=9, minute=0)` |
| Mỗi 15 phút | `crontab(minute="*/15")` |
| **Cuối tháng** (không có sẵn) | chạy **hằng ngày** + trong task check `if (date.today()+timedelta(days=1)).day == 1: ...` |

### ⚠️ Lưu ý QUAN TRỌNG cho lịch tháng (vd tính công nợ ngày 15)
- **Beat KHÔNG chạy bù**: nếu đúng ngày 15 mà `celery-beat` đang tắt/deploy, crontab sẽ **bỏ lỡ** lần đó (chỉ chạy vào lần khớp tiếp theo — tháng sau). Với việc quan trọng theo tháng (công nợ, chốt sổ) → **KHÔNG dựa hoàn toàn vào crontab**.
- **Giải pháp an toàn (khuyến nghị)**: đặt task chạy **hằng ngày**, trong task **tự kiểm tra** "đã chạy tháng này chưa" (đánh dấu marker `tab_alert_sent`/bảng riêng theo `YYYY-MM`) và điều kiện ngày (vd `today.day >= 15`) → nếu đủ điều kiện và chưa chạy thì làm → **tự bù** khi beat từng tắt. Idempotent, không sợ lỡ.
- Kết hợp cả hai: crontab `day_of_month=15` để chạy đúng ngày, + guard marker để không chạy trùng nếu vì lý do gì task được kích lại.

## Khung mỗi file phase (mục chuẩn)
1. **Mục tiêu** — làm gì, vì sao.
2. **Phạm vi & việc cụ thể** — checklist.
3. **Thiết kế kỹ thuật** — file tạo/sửa, cấu trúc task, code phác thảo, tái dùng hàm nào.
4. **Cấu hình** — ENV, Docker, lịch (cron).
5. **Chống trùng / Idempotent** (nếu có).
6. **Kiểm thử & tiêu chí hoàn thành**.
7. **Rủi ro & lưu ý**.

## Trạng thái
- [ ] Phase 0 — Hạ tầng
- [ ] Phase 2 — Cảnh báo theo lịch
- [ ] Phase 3 — Refresh báo cáo
- [ ] Phase 1 — Gửi tin cậy
- [ ] Phase 4–5 — Digest / dọn dẹp / backup
