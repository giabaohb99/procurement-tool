# PHA 3 — Thông báo & Email theo bước

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **CHƯA LÀM**.
> Khuôn 1-1: `backend/app/modules/vehicle_booking/notify.py` + `notification/email_template_*`.

## Mục tiêu
Bắn **chuông + email** cho đúng người ở từng mốc, đặc biệt **Duyệt xong → NSYC + Văn thư (theo công ty)
+ Giám đốc công ty**. Tái dùng khung thông báo/email đã có (mẫu email HTML sửa được, loại trừ email).

## Phạm vi & việc cụ thể
- [ ] `seal_request/notify.py`: `notify(db, event, req, background_tasks, actor, reason="")` — tính người nhận theo nghiệp vụ, luôn ghi `Notification` (chuông) rồi gửi email qua `email_template_service.send_event_email`.
- [ ] Sự kiện + người nhận:
  - `dd_submitted` (NS gửi duyệt) → **TBP** (`first_approver_id`).
  - `dd_approved` (TBP duyệt) → **NSYC + Văn thư (role `seal_clerk`, lọc theo `company_id`) + Giám đốc công ty**.
  - `dd_returned` (TBP/Văn thư yêu cầu chỉnh sửa) → **NSYC**.
  - `dd_rejected` (TBP/Văn thư từ chối) → **NSYC**.
  - `dd_completed` (Văn thư đóng dấu xong) → **NSYC** (+ TBP nếu khách muốn).
- [ ] Mẫu email mặc định `DEFAULTS` cho từng sự kiện (tách người nhận nếu cần 2 mẫu — như Đặt xe tách "Điều phối viên / Người tạo").
- [ ] Đăng ký nhóm sự kiện **Duyệt dấu** vào trang cài đặt `/system/settings` (bật/tắt, sửa HTML, xem trước, gửi thử).
- [ ] Cho phép **loại trừ email** theo cá nhân/phòng/công ty cho các sự kiện Duyệt dấu (reuse `email_exclusion_*`).

## Thiết kế kỹ thuật
- Gọi `notify(...)` **trong** các hàm chuyển trạng thái ở PHA 2 (`approve_seal` → `dd_approved`, …), truyền `background_tasks`. Mọi lỗi thông báo **nuốt** để không vỡ chuyển trạng thái.
- Recipient helpers (`notification/service.py`, đã có): `get_users_by_role_codes(["seal_clerk"], company_id=…)`, người tạo (`req.created_by`), Giám đốc (`get_users_by_role_codes(["director"|role giám đốc], company_id)`), `_abs_link("/approval-seal/{id}")`.
- Ngữ cảnh render (`ctx`): mã phiếu, mục đích, loại con dấu, công ty (+MST), người tạo, số bản, lý do, link. Biến `{{...}}` + `{% if %}` như `render_template`.
- Email đi qua `send_smtp_email` (tôn trọng `email_enabled`/SMTP; chưa cấu hình thì bỏ, không lỗi).

## Cấu hình / migration
- Không thêm bảng — dùng `tab_email_template` + `tab_email_exclusion` sẵn có; chỉ thêm **event key** + `DEFAULTS`.
- Cần xác định **"vai trò Giám đốc"**: nếu chưa có mã vai trò chuẩn, dùng cờ trên hồ sơ công ty hoặc vai trò `company_director` — chốt ở quyết định còn mở A.

## Chống trùng / Idempotent
- Mỗi lần chuyển trạng thái bắn **một** sự kiện; không lặp khi bấm lại (đã chặn trạng thái nguồn ở PHA 2).
- Loại trừ email lọc trước khi gửi (`filter_recipients(db, recipients, event)`), không đụng chuông.

## Kiểm thử & tiêu chí
- Test tầng service: `approve_seal` tạo `Notification` cho NSYC + Văn thư công ty đúng + Giám đốc; Văn thư công ty **khác** không nhận.
- `test_email_loai_tru` mở rộng: loại trừ 1 cá nhân khỏi `dd_approved` thì người đó không có trong danh sách email nhưng vẫn có chuông.
- Bật/tắt mẫu ở `/system/settings` → email không gửi khi tắt.

## Rủi ro & lưu ý
- **Văn thư lọc theo `company_id`** — nếu quên, mọi văn thư mọi công ty đều nhận (rò thông tin). Test riêng ca đa công ty.
- Giám đốc: xác định nguồn "ai là giám đốc công ty X" cho chắc (vai trò + `company_id`), tránh gửi nhầm.
- Đừng để lỗi SMTP làm hỏng bước Duyệt — bọc try/except, chỉ log.
