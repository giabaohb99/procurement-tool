"""BỘ MÃ CỦA PHÂN HỆ ĐẶT PHÒNG HỌP — số nguyên, theo R2/QĐ-11.

Cột nào mang nghĩa *trạng thái* thì lưu `SMALLINT` và so với hằng số ở đây;
tiếng Việt chỉ sống trong các `*_LABELS` bên dưới và ở tầng hiển thị. Cùng khuôn
với `leave/constants.py` và `vehicle_booking/model.py`.

Bộ trạng thái **bám sát Nghỉ phép** (vốn đã bám Đặt xe): cả ba đều là "phiếu nội
bộ chạy qua bộ máy duyệt dùng chung", người dùng gặp cùng một chuỗi ở ba màn thì
không phải học lại lần thứ ba.
"""

# --------------------------------------------------------------------------
# Trạng thái PHIẾU ĐẶT PHÒNG
# --------------------------------------------------------------------------
RB_DRAFT = 1      # Nháp — người đặt còn sửa, CHƯA giữ phòng
RB_PENDING = 2    # Chờ duyệt — đã giữ phòng, đang trong luồng
RB_APPROVED = 3   # Đã duyệt — phòng thuộc về phiếu này
RB_REJECTED = 4   # Từ chối — khóa, muốn họp thì đặt phiếu khác
RB_RETURNED = 5   # Trả về chỉnh sửa — sửa xong gửi duyệt lại
RB_CANCELLED = 6  # Đã hủy (người đặt tự hủy, kể cả sau khi duyệt)

ROOM_BOOKING_STATUS_LABELS = {
    RB_DRAFT: "Nháp",
    RB_PENDING: "Chờ duyệt",
    RB_APPROVED: "Đã duyệt",
    RB_REJECTED: "Từ chối",
    RB_RETURNED: "Trả về chỉnh sửa",
    RB_CANCELLED: "Đã hủy",
}

#  Sửa được khi chưa vào luồng hoặc vừa bị trả về. Nguồn DUY NHẤT — đừng rải
#  `status in (1, 5)` khắp nơi.
#
#  ⚠️ Không nới thêm `RB_APPROVED` vào đây. Phiếu đã duyệt mà sửa được giờ là
#  sửa xong đè lên phòng người khác đang giữ, trong khi người duyệt đã ký cho
#  một khung giờ khác. Đổi giờ = hủy phiếu cũ, đặt phiếu mới.
EDITABLE_STATUSES = (RB_DRAFT, RB_RETURNED)

#  ⚠️ TRẠNG THÁI GIỮ PHÒNG — trái tim của cả phân hệ.
#
#  Một phòng chỉ thuộc về một phiếu trong một khung giờ, và "thuộc về" bắt đầu
#  từ lúc GỬI DUYỆT chứ không phải lúc duyệt xong. Bỏ `RB_PENDING` ra khỏi đây
#  thì hai người cùng gửi duyệt một khung giờ đều lọt, và người phát hiện ra lại
#  là người duyệt — lúc đó cả hai đã báo lịch họp cho khách rồi.
#
#  Cùng lẽ với `HOLDING_STATUSES` của quỹ phép: giữ chỗ ngay khi trình, nhả ra ở
#  cả ba kết cục không-duyệt.
BLOCKING_STATUSES = (RB_PENDING, RB_APPROVED)

#  Ba trạng thái KHÓA hẳn phiếu: không sửa, không gửi lại, không hủy thêm lần nữa.
FINAL_STATUSES = (RB_APPROVED, RB_REJECTED, RB_CANCELLED)
