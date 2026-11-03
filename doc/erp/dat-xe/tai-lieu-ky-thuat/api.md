# TÀI LIỆU API — ĐẶT XE

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `driver`, `sync-datxe`, `vehicle`, `vehicle-booking`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `vehicle_booking`, `legacy_datxe`; danh mục dựng bằng `make_crud_router`: `/api/vehicles`, `/api/drivers`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/dispatch/drivers` | Tài xế để đổ vào ô chọn khi điều phối (xem `service.drivers_for_dispatch`). | `vehicle_booking.write` |  | |
| GET | `/api/dispatch/my-driver` | Hồ sơ tài xế của chính người đăng nhập — để form TỰ LÁI tự điền GPLX. `null` nếu chưa là tài xế. | `vehicle_booking.read` |  | |
| GET | `/api/drivers/export/xlsx` | export drivers xlsx | `driver.export` |  | |
| GET | `/api/vehicle-bookings` | Danh sách phiếu trong phạm vi người xem ("Yêu cầu của tôi" khi phạm vi = own). | `vehicle_booking.read` |  | |
| POST | `/api/vehicle-bookings` | create booking | `vehicle_booking.create` |  | |
| GET | `/api/vehicle-bookings/export/xlsx` | Xuất Excel danh sách phiếu theo ĐÚNG bộ lọc đang hiển thị (danh sách + Chuyến của tôi). | `vehicle_booking.export` |  | |
| GET | `/api/vehicle-bookings/overview` | Tổng quan Đặt xe theo vai trò — gác từng khối bằng quyền, lọc theo phạm vi. | — |  | |
| GET | `/api/vehicle-bookings/pick-options` | Hai ô "Công ty" + "Người duyệt" trên phiếu (duoc-CR-681). Người duyệt = người có quyền Duyệt | — |  | |
| GET | `/api/vehicle-bookings/summary` | booking summary | `báo cáo 9`, `vehicle_booking.read` |  | |
| GET | `/api/vehicle-bookings/summary/export` | booking summary export | `báo cáo 9`, `vehicle_booking.export` |  | |
| GET | `/api/vehicle-bookings/timeline` | Các chuyến xe theo DÒNG THỜI GIAN cho trang Timeline (lịch tháng). | `vehicle_booking.read` |  | |
| DELETE | `/api/vehicle-bookings/{bid}` | Xóa mềm — giữ lại để không phá timeline/thống kê. | `vehicle_booking.delete` | `get_scoped` | |
| GET | `/api/vehicle-bookings/{bid}` | get booking | — | `get_scoped` | |
| PATCH | `/api/vehicle-bookings/{bid}` | update booking | `vehicle_booking.write` | `get_scoped` | |
| POST | `/api/vehicle-bookings/{bid}/approve` | Người duyệt CHẤP NHẬN phiếu (Chờ duyệt → Đã duyệt). | `vehicle_booking.approve` |  | |
| POST | `/api/vehicle-bookings/{bid}/dispatch` | Điều phối: gán xe + tài xế cho phiếu (điều phối viên = quyền write). | `vehicle_booking.write` | `get_scoped` | |
| POST | `/api/vehicle-bookings/{bid}/dispatch/reject` | Điều phối viên TỪ CHỐI phiếu ĐANG Đã điều phối → khóa phiếu (gỡ điều phối). | `vehicle_booking.write` |  | |
| POST | `/api/vehicle-bookings/{bid}/dispatch/return` | Điều phối viên YÊU CẦU CHỈNH SỬA phiếu ĐANG Đã điều phối → trả về người tạo (gỡ điều phối). | `vehicle_booking.write` |  | |
| POST | `/api/vehicle-bookings/{bid}/driver/accept` | Tài xế CHẤP NHẬN chuyến (Chờ tài xế → Đã nhận). | `vehicle_booking.write` |  | |
| POST | `/api/vehicle-bookings/{bid}/driver/complete` | Tài xế HOÀN TẤT chuyến (Đang đi → Hoàn thành). | `vehicle_booking.write` |  | |
| POST | `/api/vehicle-bookings/{bid}/driver/reject` | Tài xế TỪ CHỐI chuyến → quay về điều phối phân lại. | `vehicle_booking.write` |  | |
| POST | `/api/vehicle-bookings/{bid}/driver/start` | Tài xế BẮT ĐẦU chuyến (Đã nhận → Đang đi). | `vehicle_booking.write` |  | |
| POST | `/api/vehicle-bookings/{bid}/reject` | Người duyệt TỪ CHỐI (Chờ duyệt → Từ chối). | `vehicle_booking.approve` |  | |
| POST | `/api/vehicle-bookings/{bid}/return` | Người duyệt YÊU CẦU CHỈNH SỬA (Chờ duyệt → Yêu cầu chỉnh sửa). | `vehicle_booking.approve` |  | |
| GET | `/api/vehicles/export/xlsx` | export vehicles xlsx | `vehicle.export` |  | |
| POST | `/api/sync/datxe/events` | Nhận MỘT sự kiện từ app cũ. | — |  | |
| GET | `/api/vehicles` | list items | `vehicle.read` | `apply_scope` | |
| POST | `/api/vehicles` | create item | `vehicle.create` |  | |
| GET | `/api/vehicles/export/csv` | export csv | `vehicle.export` | `apply_scope` | |
| POST | `/api/vehicles/import/csv` | import csv | `vehicle.import` | `scope_condition` | |
| DELETE | `/api/vehicles/{oid}` | delete item | `vehicle.delete` | `get_scoped` | |
| GET | `/api/vehicles/{oid}` | get item | `vehicle.read` | `get_scoped` | |
| PATCH | `/api/vehicles/{oid}` | update item | `vehicle.write` | `get_scoped` | |
| GET | `/api/drivers` | list items | `driver.read` | `apply_scope` | |
| POST | `/api/drivers` | create item | `driver.create` |  | |
| GET | `/api/drivers/export/csv` | export csv | `driver.export` | `apply_scope` | |
| POST | `/api/drivers/import/csv` | import csv | `driver.import` | `scope_condition` | |
| DELETE | `/api/drivers/{oid}` | delete item | `driver.delete` | `get_scoped` | |
| GET | `/api/drivers/{oid}` | get item | `driver.read` | `get_scoped` | |
| PATCH | `/api/drivers/{oid}` | update item | `driver.write` | `get_scoped` | |

## 2. Dữ liệu vào / ra chính

Chưa có — người phụ trách điền các trường mang luật nghiệp vụ.

## 3. Lỗi riêng của phân hệ

Chưa có.

## 4. Bộ lọc danh sách

Chưa có.

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
| 03/11/2026 | bao-CR-712 | Dựng bản đầu từ mã |
