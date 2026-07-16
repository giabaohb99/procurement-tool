# NHẬT KÝ THAY ĐỔI & YÊU CẦU THAY ĐỔI (Change Log / CR)

## Mini Tool Quản lý Thu Mua — DEGO Holding

Ghi lại **AI đổi gì, khi nào, ảnh hưởng ra sao** (theo [quy-trinh-tai-lieu.md](quy-trinh-tai-lieu.md) §⑥). Mọi thay đổi cấu trúc/luồng phải có 1 dòng CR ở đây.

**Trạng thái:** `Đề xuất` → `Đã duyệt` → `Đang làm` → `Hoàn tất` (hoặc `Từ chối` / `Hoãn`).

---

| CR | Ngày | Người đề xuất | Nội dung | Ảnh hưởng scope | Trạng thái | Tài liệu liên quan |
|---|---|---|---|---|---|---|
| **CR-001** | 2026-07-13 | Khách (phòng TM) | **Redesign phân hệ Kho**: thêm `company_id` (kho nội bộ) + `supplier_code` (kho đối tác) + `warehouse_type`; phân loại & redesign UI. **Giữ nguyên mã kho cũ** (không đụng tồn kho/PO/PYC). | Trung bình — thêm 3 cột `tab_warehouse` + migration phân loại; đổi UI danh mục Kho. Không ảnh hưởng tham chiếu string hiện có. | `Đề xuất` (chờ duyệt) | [tdd-redesign-kho.md](tdd-redesign-kho.md) |
| **CR-002** | 2026-07-15 | Team kỹ thuật | **PWA & Web Push**: cài Progressive Web App (installable, precache, workbox `registerType: prompt`); đẩy thông báo thực tế tới thiết bị qua VAPID + pywebpush (module `app/modules/push`, bảng `tab_push_subscription`). Toggle banner mời cài qua build arg `VITE_PWA_INSTALL_PROMPT=on`; Service Worker chỉ chạy bản build prod (dev tắt). | Trung bình — thêm module `push` (model/service/controller), bảng `tab_push_subscription`, Dockerfile.web.prod thêm build-arg; VPS phải đặt `VAPID_PRIVATE_KEY` trong `.env` (nếu rỗng → bỏ qua push, chuông vẫn chạy). | `Hoàn tất` | [technical-design.md §7, §10, §11](technical-design.md) |
| **CR-003** | 2026-07-15 | Team kỹ thuật | **Phân quyền thu mua tái cơ cấu** (`pur_manager` / `pur_admin`): `pur_manager` ("Quản lý thu mua") = 8 hành động đầy đủ trên mọi entity trừ `user/role/setting`, scope `all`; `pur_admin` ("Admin thu mua") = CRUD 9 entity danh mục + chỉ đọc `proc` các entity nghiệp vụ. Seed dùng hàm `resync_role_perms()` (xóa cũ → tạo lại, khác `seed_standard_roles` chỉ INSERT-only). Gộp + xóa vai trò legacy "Nhân viên" (code `STAFF`) vào "Nhân sự (cơ bản)" (code `employee`) qua `cleanup_legacy_staff_role()` — chạy sau `seed_demo_accounts` vì MariaDB so sánh code không phân biệt hoa/thường. | Cao — thay đổi toàn bộ quyền hai vai trò `pur_manager`/`pur_admin` trên DB đã triển khai. Mọi user đang gán `STAFF` được chuyển sang `employee` tự động. | `Hoàn tất` | [technical-design.md §7](technical-design.md) |
| **CR-004** | 2026-07-15 | Team kỹ thuật | **Tạo tài khoản từ nhân sự** (`POST /api/employees/{eid}/set-password`): nếu nhân sự chưa có `User` thì tự gọi `provision_user(email + vai trò lấy từ emp.role_name)` rồi đặt mật khẩu; mật khẩu tối thiểu 4 ký tự; nhân sự phải có email. Nếu đã có `User` thì chỉ đặt lại mật khẩu. Yêu cầu quyền `employee.write`. | Nhỏ — thêm endpoint, không thêm bảng. | `Hoàn tất` | — |
| **CR-005** | 2026-07-15 | Team kỹ thuật | **Thông báo (`trigger_notification`) tái cơ cấu**: chia người nhận theo cấp nhân sự; bổ sung sự kiện YCKS (`sr_submitted/approved/rejected/returned`) và YCTT (`pay_submitted/approved/rejected/paid`); PO trả lại/hủy báo người tạo qua fallback `DOC_LABEL + STATUS_VERB`; **mỗi sự kiện = 1 thông báo riêng** (bỏ gộp/coalescing). Sau khi ghi chuông vào DB → đẩy Web Push nền qua `background_tasks.add_task(push_service.send_to_users, ...)`. Module `survey_request` thêm helper `_notify` (đã tích hợp web push). | Trung bình — refactor logic người nhận; thêm gọi push_service; cũ không có sự kiện YCKS/YCTT. | `Hoàn tất` | — |
| **CR-006** | 2026-07-15 | Team kỹ thuật | **Email & Đăng nhập Google**: `send_smtp_email(force=False)` — tham số `force=True` bỏ qua công tắc `email_enabled` (dùng cho reset mật khẩu). Cấu hình SMTP/secret lưu DB (`tab_setting`, secret mã hóa Fernet theo `JWT_SECRET`), `.env` là fallback (`app_settings.py`). Wire `VITE_GOOGLE_CLIENT_ID` làm build arg trong `docker-compose.production.yml` + `docker/Dockerfile.web.prod`; backend verify qua `settings.GOOGLE_CLIENT_ID`. | Nhỏ–Trung bình — thêm tham số `force`; wire Google OAuth build arg. | `Hoàn tất` | — |

---

## Quyết định đã chốt (Decision log)

| # | Ngày | Quyết định | Lý do |
|---|---|---|---|
| D-001 | 2026-07-13 | Kho: **giữ nguyên mã cũ**, không chuẩn hóa mã hàng loạt đợt này | Mã kho là khóa ngoại dạng chuỗi ở tồn kho/GR/PO/PYC → đổi mã dễ làm mồ côi dữ liệu. Chuẩn hóa mã cũ (nếu cần) tách thành CR riêng kèm migration ánh xạ toàn bảng. |
| D-002 | 2026-07-13 | Chủ sở hữu kho: **nội bộ → `company_id`**, **đối tác → `supplier_code`** | Kho đối tác (An Nông, Agama…) thuộc NCC bên ngoài, không phải công ty tập đoàn → link NCC mới đúng bản chất, tránh trùng danh mục NCC. |
| D-003 | 2026-07-15 | Mỗi sự kiện thông báo = **1 thông báo riêng** (không gộp) | Người dùng cần thấy từng sự kiện rõ ràng; gộp dễ bỏ sót khi nhiều phiếu cùng lúc đổi trạng thái. |
| D-004 | 2026-07-15 | `VAPID_PRIVATE_KEY` **bắt buộc từ ENV** (không commit vào source); nếu rỗng → bỏ qua Web Push, chuông vẫn hoạt động | Private key VAPID không được lưu trong source; chuông in-app vẫn chạy độc lập khi chưa cấu hình push. |
| D-005 | 2026-07-15 | `cleanup_legacy_staff_role()` **chạy sau `seed_demo_accounts()`** trong `run()` | MariaDB so sánh `Role.code` không phân biệt hoa/thường → "STAFF" (legacy) và "staff" (demo) va chạm; phải dọn cả hai sau khi đã tạo xong demo. |
