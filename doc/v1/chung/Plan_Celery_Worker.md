# Plan — Celery + Redis (worker / beat)

Nền tảng **chạy ngầm + theo lịch** cho procurement-tool: nhắc chủ động, gửi push/email tin cậy, tự refresh báo cáo. Làm theo phase, tick từng mục.

> Nguyên tắc chung: mỗi task tự mở DB session riêng (`SessionLocal`), **idempotent** (chạy lại không tạo trùng), lịch chạy theo **giờ VN**.

---

## Phase 0 — Hạ tầng (bắt buộc làm trước)
- [ ] Thêm dependency: `celery`, `redis` vào `backend/requirements.txt`
- [ ] `app/core/celery_app.py`: cấu hình Celery (broker + backend = Redis), autodiscover tasks, timezone Asia/Ho_Chi_Minh
- [ ] Biến môi trường: `REDIS_URL` / `CELERY_BROKER_URL` (dev + prod `.env`)
- [ ] Thêm service Docker: `redis`, `celery-worker`, `celery-beat`
  - [ ] `docker-compose.yml` (dev)
  - [ ] `docker-compose.production.yml` (prod — dùng chung image api, khác `command`)
- [ ] Script chạy worker/beat + log; kiểm tra kết nối Redis
- [ ] Smoke test: 1 task `ping` chạy được qua worker

## Phase 1 — Chuyển việc GỬI sang worker (độ tin cậy)
- [ ] Task gửi **Web Push** (thay `BackgroundTasks`) — có **retry**, tự xóa endpoint hết hạn (404/410)
- [ ] Task gửi **email** (cấp tài khoản / reset mật khẩu) — có retry
- [ ] Giữ **fallback đồng bộ** khi Celery/Redis không chạy (dev không cần dựng full)
- [ ] Điểm gọi: `trigger_notification` + `_notify` (survey_request) đẩy task thay vì chạy nền in-process

## Phase 2 — Beat: CẢNH BÁO theo lịch ⭐ (giá trị lớn nhất)
- [ ] Job quét cảnh báo **mỗi sáng** (vd 8h, cron): tái dùng logic `GET /api/alerts`
  - [ ] Công nợ **đến hạn / quá hạn**
  - [ ] Đơn mua hàng **giao trễ / sắp tới hạn giao**
  - [ ] Hợp đồng **sắp hết hạn**
- [ ] Sinh **Notification + Web Push** tới đúng người (người phụ trách / người tạo / QL)
- [ ] **Chống spam**: chỉ báo 1 lần / mục / ngày (đánh dấu đã báo — bảng cờ hoặc key Redis)

## Phase 3 — Báo cáo TỰ REFRESH
- [ ] Job **hằng đêm**: refresh `tab_report_snapshot`
- [ ] Nút "Cập nhật" thủ công: giữ lại (chạy tay khi cần) hoặc ẩn

## Phase 4 — Digest / nhắc việc (tùy chọn)
- [ ] Nhắc **người duyệt** còn phiếu **chờ duyệt** (PYC / YCKS / YCTT) — theo lịch
- [ ] **Email digest** hằng ngày (chỉ khi bật `email_enabled`)

## Phase 5 — Dọn dẹp định kỳ
- [ ] Prune **notification / audit log / email log** cũ (giữ N ngày)
- [ ] (tùy) refresh cache / cảnh báo dung lượng

---

## Bổ sung — rà thêm (đặc thù mua hàng, dễ quên)

### B1. Nhắc / leo thang theo SLA (workflow bị TREO) ⭐
- [ ] Phiếu **chờ duyệt** (PYC / YCKS / YCTT) quá **X ngày** chưa xử lý → nhắc người duyệt; (tùy) **leo thang** lên cấp trên
- [ ] YCKS đã duyệt nhưng NSTM **chưa khảo sát** quá lâu (đang xử lý, chưa có phương án) → nhắc NSTM
- [ ] ĐMH/PYC còn dòng **"Chưa đặt hàng"** tồn quá lâu sau khi duyệt → nhắc người phụ trách

### B2. Nhắc theo NGÀY CẦN HÀNG / giao hàng ⭐ (đặc thù, quan trọng)
- [ ] PYC/ĐMH **sắp tới `need_date` / `required_date`** mà **chưa nhận đủ** (`qty_received < qty`) → nhắc
- [ ] **Quá** ngày cần hàng vẫn chưa nhận đủ → cảnh báo **trễ** (không chỉ trễ theo `expected_date` lần giao)

### B3. Nhắc THANH TOÁN
- [ ] YCTT `approved` nhưng **chưa `paid`** quá lâu → nhắc QLTM ghi nhận chi
- [ ] Công nợ (payable) **sắp tới hạn / quá hạn** trả NCC → nhắc chủ động theo lịch

### B4. Email log — RETRY
- [ ] Quét `tab_email_log` status `pending` / `failed` → **gửi lại** (khi `email_enabled`), giới hạn số lần retry

### B5. Sao lưu DB tự động (ops)
- [ ] Beat job **`mariadb-dump`** hằng đêm + **xoay vòng** giữ N bản; (tùy) đẩy offsite (R2)

### B6. Xuất Excel báo cáo BẤT ĐỒNG BỘ (gắn issue #62)
- [ ] Báo cáo lớn → worker **sinh file nền** → xong thì thông báo/cho tải (tránh timeout request)

### B7. Precompute Dashboard / dọn dẹp (tùy chọn)
- [ ] Precompute **Dashboard overview** + KPI theo lịch (giống report snapshot) → mở trang nhanh
- [ ] Quét **push subscription chết** định kỳ (ngoài việc xóa khi gửi lỗi 404/410)

> Nhiều mục B1–B3 là **mở rộng của Phase 2** (cùng cơ chế beat quét → sinh thông báo + push), chỉ khác tiêu chí quét. Nên gộp chung 1 khung "job cảnh báo theo lịch" rồi thêm dần từng loại tiêu chí.

---

## Lưu ý kỹ thuật cần nhớ
- **Timezone**: cron theo `Asia/Ho_Chi_Minh` (không để UTC lệch 7h).
- **Idempotent**: job cảnh báo phải chống tạo thông báo trùng khi chạy lại (đánh dấu "đã báo hôm nay").
- **DB session**: task dùng `SessionLocal()` tự đóng, KHÔNG dùng session của request.
- **Prod**: `celery-worker` và `celery-beat` chạy **cùng image api**, khác `command`; cùng mạng để tới DB + Redis.
- **Monitoring** (tùy chọn): thêm **Flower** để xem hàng đợi/task; hoặc chỉ đọc log.
- **VAPID / SMTP**: worker cần cùng ENV như api (VAPID_PRIVATE_KEY, SMTP…).

## Thứ tự đề xuất làm
1. **Phase 0** (hạ tầng) → 2. **Phase 2** (cảnh báo theo lịch — đáng giá nhất) → 3. **Phase 3** (refresh báo cáo) → 4. **Phase 1** (chuyển gửi push/email cho tin cậy) → 5. **Phase 4–5** (digest, dọn dẹp).

> Ghi chú: hiện push/email đã chạy tạm bằng `BackgroundTasks` (ổn ở quy mô nhỏ), nên **Phase 1 không gấp**; ưu tiên **Phase 2** vì đó là thứ hệ thống đang thiếu (nhắc chủ động theo lịch).
