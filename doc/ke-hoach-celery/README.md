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
