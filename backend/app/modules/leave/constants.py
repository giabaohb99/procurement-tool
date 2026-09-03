"""BỘ MÃ CỦA PHÂN HỆ NGHỈ PHÉP — số nguyên, theo R2/QĐ-11.

Cột nào mang nghĩa *trạng thái · loại · buổi · đơn vị* thì lưu `SMALLINT` và so
với hằng số ở đây; tiếng Việt chỉ sống trong các `*_LABELS` bên dưới và ở tầng
hiển thị. Cùng khuôn với `vehicle_booking/model.py` và `document/`.

⚠️ **Đừng nhầm với `app/core/leave_codes.py`.** Tệp kia khai mã **CHUỖI**
(`annual`, `sick`, `morning`…) và đó là ngoại lệ CÓ LÝ DO: chúng nằm trong ô JSON
`tab_document.metadata` của Giấy nghỉ phép (GNP), nơi không có kiểu và không có
ràng buộc, nên đọc `{"leave_type": "sick"}` mới hiểu được mà không phải tra bảng.

Ở đây thì ngược lại — mọi thứ là CỘT, nên là số. Hai thế giới nối với nhau qua
`tab_leave_type.code`: mã chuỗi đó chính là giá trị ghi sang metadata của giấy
GNP sinh ra sau khi đơn được duyệt (QĐ-NP5).

Vì sao **loại nghỉ** không nằm ở đây mà thành BẢNG: V1-6 đòi người quản trị đổi
được luật (thêm loại, sửa hạn mức, sửa bậc thâm niên) mà không cần sửa mã và
deploy. Bảng thì sửa được; hằng số thì không.
"""

# --------------------------------------------------------------------------
# Trạng thái ĐƠN nghỉ phép
# --------------------------------------------------------------------------
#  Bám sát bộ trạng thái của Đặt xe (`vehicle_booking`) vì cả hai đều là "phiếu
#  nội bộ chạy qua bộ máy duyệt dùng chung" — người dùng gặp cùng một chuỗi ở
#  hai màn hình thì không phải học lại lần thứ hai.
LR_DRAFT = 1      # Nháp — người tạo còn sửa, chưa vào luồng duyệt
LR_PENDING = 2    # Chờ duyệt — đang trong luồng
LR_APPROVED = 3   # Đã duyệt — quỹ phép đã trừ, giấy GNP đã sinh
LR_REJECTED = 4   # Từ chối — khóa, muốn nghỉ thì nộp đơn khác
LR_RETURNED = 5   # Trả về chỉnh sửa — sửa xong gửi duyệt lại
LR_CANCELLED = 6  # Đã hủy (người nộp tự hủy, kể cả sau khi duyệt)

LEAVE_REQUEST_STATUS_LABELS = {
    LR_DRAFT: "Nháp",
    LR_PENDING: "Chờ duyệt",
    LR_APPROVED: "Đã duyệt",
    LR_REJECTED: "Từ chối",
    LR_RETURNED: "Trả về chỉnh sửa",
    LR_CANCELLED: "Đã hủy",
}

#  Sửa được khi chưa vào luồng hoặc vừa bị trả về. Giống `EDITABLE_STATUSES` của
#  Đặt xe — và giống nó ở chỗ đây là nguồn DUY NHẤT, đừng rải `status in (1, 5)`.
EDITABLE_STATUSES = (LR_DRAFT, LR_RETURNED)

#  Trạng thái GIỮ CHỖ quỹ phép: đơn đã ăn vào số ngày còn lại của người ta.
#  `LR_PENDING` giữ chỗ (`pending_days`), `LR_APPROVED` trừ thật (`used_days`).
#  Thiếu nhánh giữ chỗ thì nộp mười đơn liền tay đều lọt, vì đơn nào cũng thấy
#  quỹ còn nguyên — lỗi cổ điển của mọi hệ nghỉ phép.
HOLDING_STATUSES = (LR_PENDING, LR_APPROVED)

# --------------------------------------------------------------------------
# Buổi nghỉ
# --------------------------------------------------------------------------
SESSION_FULL = 1       # Cả ngày
SESSION_MORNING = 2    # Buổi sáng
SESSION_AFTERNOON = 3  # Buổi chiều

LEAVE_SESSION_LABELS = {
    SESSION_FULL: "Cả ngày",
    SESSION_MORNING: "Buổi sáng",
    SESSION_AFTERNOON: "Buổi chiều",
}

#  Số công của mỗi buổi — dùng khi GỢI Ý tổng số ngày.
SESSION_CREDIT = {SESSION_FULL: 1.0, SESSION_MORNING: 0.5, SESSION_AFTERNOON: 0.5}

#  Cầu nối sang mã chuỗi của giấy GNP (`core/leave_codes.LEAVE_SESSION_SET`).
#  Bảng dịch nằm ở ĐÂY, một chỗ — chứ không nội suy bằng `if` rải trong bridge.
SESSION_TO_DOC_CODE = {
    SESSION_FULL: "full",
    SESSION_MORNING: "morning",
    SESSION_AFTERNOON: "afternoon",
}

# --------------------------------------------------------------------------
# Đơn vị nghỉ — QĐ-NP4
# --------------------------------------------------------------------------
#  Bản này CHỈ dùng `UNIT_DAY`. Hai giá trị còn lại khai sẵn để khi có phân hệ
#  **Lịch làm việc** thì chỉ phải viết thêm cách quy đổi, KHÔNG phải đổi cấu
#  trúc bảng và chạy migration trên dữ liệu đã có.
UNIT_DAY = 1       # Theo ngày (đang dùng)
UNIT_HALF_DAY = 2  # Theo nửa ngày — chờ Lịch làm việc
UNIT_HOUR = 3      # Theo giờ — chờ Lịch làm việc

LEAVE_UNIT_LABELS = {
    UNIT_DAY: "Ngày",
    UNIT_HALF_DAY: "Nửa ngày",
    UNIT_HOUR: "Giờ",
}

# --------------------------------------------------------------------------
# Giới tính — dùng cho `tab_employee.gender` và bộ lọc loại nghỉ
# --------------------------------------------------------------------------
#  `0` là **chưa khai**, không phải "khác". Hồ sơ cũ nhập trước đợt này đều rơi
#  vào đó, và loại nghỉ giới hạn giới tính (thai sản) phải cho họ qua chứ không
#  chặn — chặn thì cả công ty không nộp được đơn cho tới khi Nhân sự nhập bù.
GENDER_UNKNOWN = 0
GENDER_MALE = 1
GENDER_FEMALE = 2

GENDER_LABELS = {
    GENDER_UNKNOWN: "Chưa khai",
    GENDER_MALE: "Nam",
    GENDER_FEMALE: "Nữ",
}


def label(labels: dict, value: int | None, default: str = "") -> str:
    """Nhãn của một mã. Mã lạ (dữ liệu cũ, nhập tay) trả `default` chứ không nổ."""
    return labels.get(int(value), default) if value is not None else default
