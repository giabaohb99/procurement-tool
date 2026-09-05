# Kịch bản KIỂM TRA phân quyền — phân hệ Đặt xe

Kiểm bằng tay trên bản DEV (cổng 8083): dùng nút **"Đổi tài khoản nhanh"** (biểu tượng
👥 góc phải thanh trên, chấm vàng) để chuyển giữa các tài khoản, nhóm **"TK Đặt xe"**.

## 0. Chuẩn bị (một lần)
```bash
# Đặt mật khẩu dego123 + email @dego.com cho 7 tài khoản test (vai trò/phòng ban đã set sẵn)
docker compose exec -T api python -m scripts.seed_datxe_test_accounts
```
Mật khẩu tất cả: **`dego123`**. Nếu login lỗi → chạy lại lệnh trên.

## 1. Bảy tài khoản

| Ký hiệu | Tên | Mã NV | Email | Vai trò | Phạm vi xem |
|---|---|---|---|---|---|
| **NS1** | Dương Hải Yến | NSU203 | duonghaiyen.idagroup@dego.com | Nhân sự | Của mình |
| **TP1** | Nguyễn Đỗ Quyên | NSU202 | ndquyen.idagroup@dego.com | Trưởng bộ phận | Phòng ban |
| **NS2** | Hồ Ngọc Quế Anh | NSU171 | hnqanh.idagroup@dego.com | Nhân sự | Của mình |
| **TP2** | Nguyễn Minh Toàn | NSU170 | nmtoan.idagroup@dego.com | Trưởng bộ phận | Phòng ban |
| **ĐPV** | Bùi Huỳnh Trường Thành | NSU055 | bhtthanh.idaglobal@dego.com | Điều phối viên | Tất cả |
| **TX1** | Lê Tấn Nhựt | NSU060 | ltnhut.idagroup@dego.com | Tài xế | Chuyến được giao |
| **TX2** | Trần Quốc Thái | NSU058 | tqthai.idagroup@dego.com | Tài xế | Chuyến được giao |

> NS1↔TP1 một phòng, NS2↔TP2 phòng khác. Mọi chuyến ở dưới đây tạo ở `/vehicle-booking/new`.

## 2. Dựng dữ liệu mẫu (làm 1 lần, theo thứ tự)

| # | Tài khoản | Việc | Kết quả |
|---|---|---|---|
| D1 | NS1 | Tạo & **gửi duyệt** 1 yêu cầu (mục đích: "NS1 đi họp") | Có phiếu **A** (Chờ duyệt) |
| D2 | NS2 | Tạo & **gửi duyệt** 1 yêu cầu ("NS2 giao hàng") | Có phiếu **B** (Chờ duyệt) |
| D3 | TP1 | Mở phiếu **A** → **Duyệt** | A → Đã duyệt |
| D4 | TP2 | Mở phiếu **B** → **Duyệt** | B → Đã duyệt |
| D5 | ĐPV | Điều phối **A** cho **TX1** (xe bất kỳ); điều phối **B** cho **TX2** | A,B → Điều phối |

## 3. Các ca kiểm (đánh dấu ✅/❌)

| # | Đăng nhập | Thao tác | Kỳ vọng |
|---|---|---|---|
| T1 | **NS1** | Mở danh sách `/vehicle-booking` | Thấy phiếu **A**, **KHÔNG** thấy phiếu **B** (của NS2) |
| T2 | **NS1** | — | **KHÔNG** thấy phiếu do **TP1** tạo (nếu có) — chỉ thấy của mình |
| T3 | **TP1** | Mở danh sách | Thấy phiếu phòng mình (A), **KHÔNG** thấy phiếu **B** (NS2 khác phòng) |
| T4 | **TP1** | — | **KHÔNG** thấy phiếu do **TP2** tạo (khác phòng) |
| T5 | **ĐPV** | Mở danh sách | Thấy **TẤT CẢ** phiếu (A, B, và mọi phiếu khác) |
| T6 | **TX1** | Mở danh sách / "Chuyến của tôi" | Chỉ thấy phiếu **A** (được điều phối cho mình) |
| T7 | **TX1** | — | **KHÔNG** thấy phiếu **B** (điều phối cho TX2) |
| T8 | **TX2** | "Chuyến của tôi" | Chỉ thấy **B**, không thấy **A** |

## 4. Kiểm HIỂN THỊ (mỗi vai trò thấy đúng nút/menu)

| Vai trò | Kỳ vọng |
|---|---|
| **NS1 / NS2** | Có nút **Tạo yêu cầu**; **không** có nút Duyệt/Điều phối trên phiếu của người khác |
| **TP1 / TP2** | Trên phiếu **Chờ duyệt** của phòng mình: có **Duyệt · Yêu cầu chỉnh sửa · Từ chối** |
| **ĐPV** | Trên phiếu **Đã duyệt**: có nút **Điều phối**; thấy menu/khối của mọi phiếu |
| **TX1 / TX2** | Trên phiếu **Điều phối** của mình: có **Chấp nhận · Bắt đầu · Hoàn tất**; menu **"Chuyến của tôi"** |

## 5. Ghi chú
- Chốt chặn thật ở **backend** (`require` + `apply_scope`/`get_scoped`) — không phải ẩn nút. Gõ thẳng
  id lên URL (`/vehicle-booking/<id>` của phiếu ngoài phạm vi) vẫn **404**, không xem lén được.
- Đổi tài khoản xong **đứng nguyên trang**, bộ nhớ đệm truy vấn bị xóa nên dữ liệu tự hỏi lại theo quyền mới.
- Tự lái: người yêu cầu là tài xế → chính họ (NS) thấy chuyến ở "Chuyến của tôi" và Chấp nhận/Hoàn tất
  (cần vai trò có `vehicle_booking.write` phạm vi own/assigned).
