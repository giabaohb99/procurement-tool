# Requirement — Phase 3 + Phase 4 + UX (sidebar gom nhóm · chi tiết NCC · search tức thì)

Tài liệu gộp: phân tích yêu cầu + cách làm + trạng thái. Triển khai theo thứ tự: **(1) Search tức thì → (7) Gom sidebar → Phase 4 Hợp đồng → (9) Chi tiết NCC → Phase 3 Cảnh báo/chạy ngầm.**

---
## Task 1 — Ô search text tự tìm khi ngừng gõ (debounce)
**Yêu cầu:** các ô lọc dạng text, người dùng gõ xong (ngừng ~400ms) là tự lọc, không phải bấm nút "Lọc".
**Cách làm:** trong `FilterBar`, ô `type=text` dùng **debounce 400ms** → gọi `onApply` tự động; ô `select`/`source` áp dụng ngay khi đổi. Vẫn giữ nút Lọc/Xóa lọc cho rõ ràng.
**Ảnh hưởng:** mọi màn list dùng `FilterBar` (danh mục, PO, công nợ, YCTT…).

---
## Task 7 — Gom sidebar theo cụm
**Yêu cầu:** thay vì liệt kê phẳng, gom menu thành cụm có tiêu đề, cụm danh mục có thể thu gọn.
**Cách làm:** `AppLayout` đổi `NAV` phẳng → mảng **nhóm** `{title, items[]}`; render tiêu đề nhóm nhỏ + item; nhóm "Danh mục" cho phép **thu gọn/mở** (nhớ trạng thái ở localStorage). Nhóm đề xuất:
- **Tổng quan**: Trang chủ · Báo cáo mua hàng
- **Mua hàng**: Yêu cầu mua · Khảo sát NCC · Khảo sát SP · Đơn mua hàng
- **Kho & Công nợ**: Tồn kho · Công nợ · Yêu cầu thanh toán
- **Danh mục** (thu gọn được): Nhà cung cấp · Sản phẩm · Kho · ĐVT · Phân loại · Phòng ban · Hợp đồng
- **Hệ thống**: Công ty · Nhân sự · Vai trò

---
## Phase 4 — Hợp đồng (TỔNG QUÁT) + cảnh báo hết hạn  ✅ (đã chỉnh theo phản hồi)
**Yêu cầu (chốt lại):** hợp đồng **tổng quát nhiều đối tượng** (NCC / Khách hàng / Khác), **KHÔNG cần giá trị**, chỉ cần biết đối tượng ký với **công ty nào** + **đính kèm file HĐ thật** và xem lại file.
**Model `tab_contract`:** `code` (auto HD#####), `party_type` (Nhà cung cấp/Khách hàng/Khác), `party_code`, `party_name`, `company_id` (pháp nhân mình ký), `title`, `contract_type`, `start_date`, `end_date`, `signed` (đã ký), `status` (Hiệu lực/Hết hạn/Thanh lý), `note`. **File** dùng hệ thống đính kèm R2 (`entity='contract'`) — không lưu trong bảng.
**Cảnh báo hết hạn:** ≤30 ngày → "Sắp hết hạn"; quá hạn → "Hết hạn" (tính khi đọc, tô badge).
**API:** CRUD `/api/contracts` (filter party_type/party_code/status) + `_fill_party` tự điền tên NCC theo mã.
**FE:** trang **ContractDetail** riêng (form + đính kèm/hiển thị file) + list; hiển thị trong **chi tiết NCC** (tab Hợp đồng — biết NCC ký với công ty nào).

---
## Task 9 — Sửa giao diện màn Nhà cung cấp (trang chi tiết dạng tab)
**Yêu cầu:** chi tiết 1 NCC gồm nhiều mảng: thông tin, **đánh giá NCC**, **hợp đồng**, **công nợ**…
**Cách làm:** trang riêng `/suppliers/:id` (`SupplierDetail`) thay CrudDetail, chia **tab**:
1. **Thông tin**: form NCC (mã, tên, MST, địa chỉ, loại, hình thức TT, TK ngân hàng…) — sửa/lưu.
2. **Đánh giá**: tổng hợp từ khảo sát NCC (mức tin cậy, NSPT đạt/không) + KPI giao hàng của NCC (số lần giao, tỷ lệ trễ — lấy từ báo cáo) — chỉ đọc.
3. **Hợp đồng**: danh sách hợp đồng của NCC (từ `/api/contracts?supplier_code=`) + trạng thái hết hạn + thêm nhanh.
4. **Công nợ**: các khoản `payable` của NCC (`/api/payables?supplier_code=`) — tổng nợ/đã trả/còn lại + link phiếu.
- Danh sách NCC (list) giữ nguyên; click dòng → mở trang chi tiết tab này.

---
## Phase 3 — Cảnh báo & chạy ngầm (worker)
**Yêu cầu:** hệ thống tự nhắc: giao hàng trễ/sắp tới hạn, công nợ đến hạn/quá hạn, hợp đồng sắp hết hạn; **tự refresh snapshot báo cáo**.

**Kiến trúc (2 bước):**
1. **Logic cảnh báo (làm trước, không cần worker):** service `alerts.build(db)` quét:
   - PO delivery: `expected/promised_date` ≤ hôm nay + 2 ngày mà chưa nhận → *sắp tới hạn giao*; đã quá hạn chưa nhận → *trễ giao*.
   - Payable: `due_date` ≤ hôm nay + 3 ngày & chưa trả → *công nợ sắp đến hạn*; quá hạn → *quá hạn*.
   - Contract: `end_date` ≤ hôm nay + 30 → *hợp đồng sắp hết hạn*.
   Trả danh sách + đếm. Endpoint `GET /api/alerts` để chuông/badge hiển thị.
2. **Chạy ngầm (worker):** thêm service **Redis + Celery beat** trong docker; job định kỳ:
   - Mỗi 15–30' hoặc đầu ngày: `alerts.build` → tạo `Notification` (in-app) + email cho người phụ trách; **refresh snapshot báo cáo** (`report_service.get_snapshot(..., refresh=True)`).
   - Trước mắt (chưa dựng Celery): endpoint `POST /api/alerts/run` để chạy tay hoặc gắn cron ngoài (crontab gọi curl).

**Docker (khi bật Celery):** thêm `redis`, `worker` (celery -A ... worker), `beat` (celery beat); dùng chung image api.

**Trạng thái triển khai:** logic + endpoint `/api/alerts` làm ngay; Celery/Redis + lịch để bước sau (đã mô tả cách gắn).
