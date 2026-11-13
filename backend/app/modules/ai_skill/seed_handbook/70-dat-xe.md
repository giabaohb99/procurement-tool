# Đặt xe (phiếu đặt xe công tác và xe giao hàng)

Cẩm nang này chỉ dạy **khi nào gọi công cụ nào** cho câu hỏi về đặt xe. Quy trình chi tiết nằm
ở bài hướng dẫn sử dụng của phân hệ Đặt xe.

## Điều CẤM nói

- **Đừng khẳng định còn xe trống hay tài xế rảnh.** Không công cụ nào trả lịch xe trống; việc
  phân xe là của người điều phối. Chỉ đường tới màn *Lịch Timeline* (`/vehicle-booking/timeline`).
- **Đừng báo là đã tạo phiếu** khi mới có bản nháp. Phiếu chỉ có sau khi người dùng đồng ý và
  bản nháp được xác nhận.
- **Không đọc ra số điện thoại, bằng lái, ảnh của tài xế** — công cụ không trả các trường đó,
  đừng đoán.

## Công cụ nào cho câu nào

| Người dùng hỏi | Gọi |
|---|---|
| "phiếu đặt xe của tôi tới đâu rồi", "tuần này có những chuyến nào" | `office_read` với `resource` = `vehicle_booking` |
| "xem phiếu đặt xe số 123" | `office_read` với `resource` = `vehicle_booking`, `id` = 123 |
| "đặt xe đi Cần Thơ sáng thứ 6", "xe giao hàng cho khách X" | `draft_vehicle_booking` |

- `office_read` đọc **đúng như màn danh sách trên web**, đúng phạm vi quyền của người hỏi. Lọc
  được theo `search`, `status`, `request_type`, `company_id`, `department_id`. Phiếu ngoài phạm vi
  thì công cụ không trả — nói là **không truy cập được**, đừng nói phiếu không tồn tại.
- Mỗi dòng có `url` mở màn chi tiết; đưa đường dẫn đó cho người dùng thay vì chép lại cả phiếu.

## Soạn phiếu bằng `draft_vehicle_booking`

- Cần đủ: **mục đích**, **điểm đón**, **điểm đến**, **giờ đi**, **giờ về / xong**, **người phê
  duyệt**. Thiếu gì công cụ trả câu hỏi — hỏi người dùng **một câu**, đừng tự điền.
- Giờ truyền dạng `YYYY-MM-DD HH:MM`, giờ Việt Nam. Đổi "sáng thứ 6" ra ngày giờ cụ thể rồi đọc
  lại cho người dùng xác nhận. Giờ về phải sau giờ đi.
- `request_type`: `cong_tac` (chở người, mặc định) hoặc `giao_hang` (chở hàng — điền thêm hàng
  cần chở và người nhận).
- **Người phê duyệt** là người có quyền duyệt đặt xe, **không chọn chính mình**. Tên mơ hồ thì
  công cụ trả danh sách để chọn.
- Công ty bỏ trống thì lấy công ty của người hỏi.
- Có bản nháp rồi: đưa người dùng xem, họ đồng ý rõ thì xác nhận nháp với kind
  `vehicle_booking` (trên cổng MCP là `confirm_draft`). Họ muốn gửi duyệt luôn thì xác nhận kèm
  `submit=true`; không thì phiếu nằm ở *Nháp*.
- Người không có quyền lập phiếu đặt xe thì công cụ trả *không có quyền* — báo lại đúng như vậy.

## Ai duyệt được, ai nhận chuông (từ đầu tháng 11/2026)

Chọn ***Người phê duyệt*** là chọn người được **báo** trước, không khóa phiếu vào riêng một người:

- **Chuông và thư** (*YCĐX … chờ bạn duyệt*) chỉ tới **người được chọn** (họ đang ủy quyền thì người nhận ủy quyền cũng nhận thư).
- **Người khác cùng quyền Duyệt đặt xe** cũng duyệt được, miễn **phạm vi của họ phủ phiếu**: phạm vi *Phòng ban* = phiếu của phòng
  họ; *Công ty* = phiếu của công ty họ, tính cả công ty người tạo lẫn công ty chọn trên phiếu; *Tất cả* = mọi phiếu. Họ **không
  nhận chuông**, thấy phiếu ở **Đặt xe ▸ Yêu cầu đặt xe** (lọc *Chờ duyệt*) hoặc khối ***Chờ tôi duyệt*** ở **Đặt xe ▸ Tổng quan**
  (khối ẩn sẵn, bật ở nút ***Hiển thị***).
- Ai bấm trước thì phiếu đi theo người đó. Người được chọn chưa duyệt mà phiếu đã qua bước = một người cùng quyền đã duyệt trước;
  xem ở khối *Tiến trình xử lý* của phiếu.
- Hỏi "tôi có quyền duyệt đặt xe mà phiếu không có nút Duyệt" → phạm vi không phủ phiếu, hoặc luồng nhiều chặng chưa tới chặng
  của họ. Hỏi "sao tôi không nhận chuông" → họ không phải người được chọn; đó là đúng thiết kế, không phải lỗi.
- Người được chọn vẫn duyệt được dù phạm vi của họ không phủ phiếu (ví dụ phiếu thuộc công ty khác).

## Trạng thái phiếu — đọc nhãn, đừng đoán

`Nháp → Chờ duyệt → Đã duyệt → Đã điều phối → Hoàn thành`, cộng ba ngã rẽ *Từ chối*, *Đã hủy*,
*Yêu cầu chỉnh sửa*.

- *Đã duyệt* nghĩa là **chờ điều phối**, chưa có xe. *Đã điều phối* mới là đã phân xe và tài xế.
- Chỉ sửa được ở *Nháp* và *Yêu cầu chỉnh sửa*. Sửa, hủy, duyệt làm trên web, trợ lý không làm.

## Màn trên web

| Màn | Đường dẫn |
|---|---|
| Tổng quan | `/vehicle-booking` |
| Danh sách phiếu | `/vehicle-booking/requests` |
| Lập phiếu mới | `/vehicle-booking/new` |
| Chuyến của tài xế | `/vehicle-booking/my-trips` |
| Lịch Timeline | `/vehicle-booking/timeline` |

## Trên cổng MCP

Hai nhóm công cụ do quản trị bật ở cấu hình cổng MCP, **tắt mặc định**: nhóm đọc (`office_read`)
và nhóm lập phiếu (`draft_vehicle_booking`). Công cụ không có trong danh sách thì nói là quản trị
chưa bật, đừng đoán số liệu.
