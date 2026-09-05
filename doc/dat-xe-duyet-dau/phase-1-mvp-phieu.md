# PHA 1 — MVP phiếu (tạo & theo dõi) ✅

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **ĐÃ XONG** (hồi cứu).

## Mục tiêu
Người dùng tạo được **yêu cầu đặt xe** 2 loại (công tác chở người / giao hàng chở hàng), có **lộ trình +
điểm dừng trung gian**, **lưu nháp / gửi duyệt**, xem **danh sách + chi tiết**, và sửa khi phiếu còn
sửa được. Đây là xương sống nghiệp vụ trước khi có điều phối.

## Phạm vi & việc đã làm
- [x] Tạo phiếu 2 loại; lưu nháp (không kiểm) / gửi duyệt (kiểm trường bắt buộc).
- [x] Điểm dừng trung gian: mỗi điểm có **địa điểm + tên người liên hệ + SĐT**, thêm/xóa/đổi thứ tự.
- [x] Danh sách + chi tiết + sửa (**chỉ khi** phiếu Nháp / bị Yêu cầu chỉnh sửa).
- [x] Badge trạng thái phiếu + nhãn tiếng Việt (API trả **số kèm label**).

## Thiết kế kỹ thuật
| Việc | Vị trí |
|---|---|
| Nghiệp vụ tạo/sửa/serialize | `backend/app/modules/vehicle_booking/service.py` (`create_booking`, `update_booking`, `serialize_booking(viewer)`, `serialize_bookings` gom nhãn theo lô) |
| Điểm dừng | `schema.StopItem` (`{location, contact_name, contact_phone}`), lưu JSON ở cột `stops`; tương thích ngược phần tử chuỗi cũ → bọc `{location}` |
| Route API | `controller.py` (list / get / create / update; `_scoped_or_404` để lấy 1 phiếu qua `get_scoped`) |
| Sinh mã | `generate_code(db, VehicleBooking, "DX")` → `DX###` |
| Trang danh sách/chi tiết/form | `frontend-v2/src/modules/vehicle-booking/pages/*` + `hooks/use-vehicle-bookings.ts` + `api/vehicle-booking-api.ts` |
| Badge | `components/status-pill.tsx` (`BookingStatusBadge`, `DriverStatusBadge`) |

**Trường bắt buộc khi gửi duyệt** (không chặn lúc lưu nháp): mục đích, điểm đi, điểm đến, giờ đi, giờ
về (`end_time > start_time`); loại công tác thêm **số hành khách ≥ 1**; loại giao hàng thêm **tên hàng
hóa · người gửi + SĐT · người nhận + SĐT**.

## Cấu hình / migration
- Không thêm ENV; cột phiếu đã có từ PHA 0.

## Chống trùng / Idempotent
- Mã `DX###` unique — dựa `generate_code`; xung đột hiếm khi tạo song song thì thử lại.

## Đã kiểm (tiêu chí hoàn thành)
- Tạo 2 loại phiếu, lưu nháp rồi gửi duyệt; kiểm chặn đúng khi thiếu trường bắt buộc.
- Sửa phiếu Nháp / bị trả được; phiếu đã vào luồng thì **khóa** (`EDITABLE_STATUSES`).
- Điểm dừng đổi thứ tự, lưu lại đúng thứ tự.

## Rủi ro & lưu ý
- **VAT/giá không có ở đây** — đây là phiếu điều vận, không phải chứng từ tiền.
- `stops` là JSON trong cột Text: đọc phải parse an toàn (đã có nhánh tương thích bản cũ).
