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

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `vehicle_booking`, `legacy_datxe`; danh mục dựng bằng `make_crud_router`: `/api/vehicles`, `/api/drivers`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/dispatch/drivers` | Tài xế để đổ vào ô chọn khi điều phối (xem `service.drivers_for_dispatch`). | `vehicle_booking.write` |  | tự dò: v2 `vehicle-booking` |
| GET | `/api/dispatch/my-driver` | Hồ sơ tài xế của chính người đăng nhập — để form TỰ LÁI tự điền GPLX. | `vehicle_booking.read` |  | tự dò: v2 `vehicle-booking` |
| GET | `/api/drivers` | Danh sách tài xế, có lọc và phân trang. | `driver.read` | `apply_scope` | tự dò: v2 `vehicle-booking` |
| POST | `/api/drivers` | Thêm một dòng tài xế; chặn trùng mã, ghi nhật ký. | `driver.create` |  | tự dò: v2 `vehicle-booking` |
| GET | `/api/drivers/export/csv` | Xuất tài xế ra tệp CSV theo bộ lọc đang chọn. | `driver.export` | `apply_scope` |  |
| GET | `/api/drivers/export/xlsx` | export drivers xlsx | `driver.export` |  |  |
| POST | `/api/drivers/import/csv` | Nhập tài xế hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `driver.import` | `scope_condition` |  |
| GET | `/api/drivers/{oid}` | Xem một dòng tài xế theo id. | `driver.read` | `get_scoped` |  |
| PATCH | `/api/drivers/{oid}` | Sửa một dòng tài xế; chỉ ghi các ô gửi lên, ghi nhật ký. | `driver.write` | `get_scoped` |  |
| DELETE | `/api/drivers/{oid}` | Xóa một dòng tài xế; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `driver.delete` | `get_scoped` |  |
| POST | `/api/sync/datxe/events` | Nhận MỘT sự kiện từ app cũ. | công khai |  |  |
| GET | `/api/vehicle-bookings` | Danh sách phiếu trong phạm vi người xem ("Yêu cầu của tôi" khi phạm vi = own). | `vehicle_booking.read` |  | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings` | create booking | `vehicle_booking.create` |  | tự dò: v2 `vehicle-booking` |
| GET | `/api/vehicle-bookings/export/xlsx` | Xuất Excel danh sách phiếu theo ĐÚNG bộ lọc đang hiển thị (danh sách + Chuyến của tôi). | `vehicle_booking.export` |  | tự dò: v2 `vehicle-booking` |
| GET | `/api/vehicle-bookings/overview` | Tổng quan Đặt xe theo vai trò — gác từng khối bằng quyền, lọc theo phạm vi. | đăng nhập |  | tự dò: v2 `vehicle-booking`, v2 dùng chung |
| GET | `/api/vehicle-bookings/pick-options` | Hai ô "Công ty" + "Người duyệt" trên phiếu (duoc-CR-681). | đăng nhập |  | tự dò: v2 `vehicle-booking` |
| GET | `/api/vehicle-bookings/summary` | booking summary | `báo cáo 9`, `vehicle_booking.read` |  | tự dò: v2 `report` |
| GET | `/api/vehicle-bookings/summary/export` | booking summary export | `báo cáo 9`, `vehicle_booking.export` |  | tự dò: v2 `report` |
| GET | `/api/vehicle-bookings/timeline` | Các chuyến xe theo DÒNG THỜI GIAN cho trang Timeline (lịch tháng). | `vehicle_booking.read` |  | tự dò: v2 `vehicle-booking` |
| GET | `/api/vehicle-bookings/{bid}` | get booking | đăng nhập | `get_scoped` | tự dò: v2 `vehicle-booking` |
| PATCH | `/api/vehicle-bookings/{bid}` | update booking | `vehicle_booking.write` | `get_scoped` | tự dò: v2 `vehicle-booking` |
| DELETE | `/api/vehicle-bookings/{bid}` | Xóa mềm — giữ lại để không phá timeline/thống kê. | `vehicle_booking.delete` | `get_scoped` | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings/{bid}/approve` | Người duyệt CHẤP NHẬN phiếu (Chờ duyệt → Đã duyệt). | `vehicle_booking.approve` |  | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings/{bid}/dispatch` | Điều phối: gán xe + tài xế cho phiếu (điều phối viên = quyền write). | `vehicle_booking.write` | `get_scoped` | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings/{bid}/dispatch/reject` | Điều phối viên TỪ CHỐI phiếu ĐANG Đã điều phối → khóa phiếu (gỡ điều phối). | `vehicle_booking.write` |  | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings/{bid}/dispatch/return` | Điều phối viên YÊU CẦU CHỈNH SỬA phiếu ĐANG Đã điều phối → trả về người tạo (gỡ điều phối). | `vehicle_booking.write` |  | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings/{bid}/driver/accept` | Tài xế CHẤP NHẬN chuyến (Chờ tài xế → Đã nhận). | `vehicle_booking.write` |  | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings/{bid}/driver/complete` | Tài xế HOÀN TẤT chuyến (Đang đi → Hoàn thành). | `vehicle_booking.write` |  | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings/{bid}/driver/reject` | Tài xế TỪ CHỐI chuyến → quay về điều phối phân lại. | `vehicle_booking.write` |  | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings/{bid}/driver/start` | Tài xế BẮT ĐẦU chuyến (Đã nhận → Đang đi). | `vehicle_booking.write` |  | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings/{bid}/reject` | Người duyệt TỪ CHỐI (Chờ duyệt → Từ chối). | `vehicle_booking.approve` |  | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicle-bookings/{bid}/return` | Người duyệt YÊU CẦU CHỈNH SỬA (Chờ duyệt → Yêu cầu chỉnh sửa). | `vehicle_booking.approve` |  | tự dò: v2 `vehicle-booking` |
| GET | `/api/vehicles` | Danh sách phương tiện (Xe), có lọc và phân trang. | `vehicle.read` | `apply_scope` | tự dò: v2 `vehicle-booking` |
| POST | `/api/vehicles` | Thêm một dòng phương tiện (Xe); chặn trùng mã, ghi nhật ký. | `vehicle.create` |  | tự dò: v2 `vehicle-booking` |
| GET | `/api/vehicles/export/csv` | Xuất phương tiện (Xe) ra tệp CSV theo bộ lọc đang chọn. | `vehicle.export` | `apply_scope` |  |
| GET | `/api/vehicles/export/xlsx` | export vehicles xlsx | `vehicle.export` |  |  |
| POST | `/api/vehicles/import/csv` | Nhập phương tiện (Xe) hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `vehicle.import` | `scope_condition` |  |
| GET | `/api/vehicles/{oid}` | Xem một dòng phương tiện (Xe) theo id. | `vehicle.read` | `get_scoped` |  |
| PATCH | `/api/vehicles/{oid}` | Sửa một dòng phương tiện (Xe); chỉ ghi các ô gửi lên, ghi nhật ký. | `vehicle.write` | `get_scoped` |  |
| DELETE | `/api/vehicles/{oid}` | Xóa một dòng phương tiện (Xe); danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `vehicle.delete` | `get_scoped` |  |

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
