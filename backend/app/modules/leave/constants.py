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
from datetime import time

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
#  Nghỉ THEO GIỜ (07/09/2026): chọn giờ bắt đầu / kết thúc thay vì cả buổi —
#  đi khám nửa buổi, ra ngân hàng hai tiếng. Chỉ dùng cho đơn nghỉ TRONG MỘT
#  NGÀY: nghỉ nhiều ngày mà lẻ giờ ở hai đầu là chuyện của bảng công, không
#  phải của tờ đơn (xem `check_date_range`).
SESSION_HOURLY = 4

LEAVE_SESSION_LABELS = {
    SESSION_FULL: "Cả ngày",
    SESSION_MORNING: "Buổi sáng",
    SESSION_AFTERNOON: "Buổi chiều",
    SESSION_HOURLY: "Theo giờ",
}

#  Số công của NGÀY ĐẦU và NGÀY CUỐI khoảng nghỉ, theo ô buổi.
#
#  ⚠️ **Hai bảng KHÁC NHAU, và đó chính là chỗ bản cũ tính sai** (vá 07/09/2026).
#  Trước đó cả hai đầu dùng chung một bảng `{Cả ngày: 1, Sáng: .5, Chiều: .5}`,
#  tức coi ô buổi là *"buổi nào của ngày đó được nghỉ"*. Nhưng nhãn trên màn hình
#  là **«Buổi bắt đầu»** / **«Buổi kết thúc»** — nó nói MỐC, không nói buổi:
#
#      bắt đầu buổi Sáng ngày 05  →  nghỉ TRỌN ngày 05 (1.0), không phải nửa
#      kết thúc buổi Chiều ngày 07 →  nghỉ TRỌN ngày 07 (1.0), không phải nửa
#
#  Chính luật *"chiều → sáng cùng ngày là khoảng trống"* (`check_date_range`)
#  cũng chỉ đúng khi đọc theo mốc: kết thúc trước lúc bắt đầu. Bản cũ chặn theo
#  mốc nhưng lại tính theo buổi, nên hai vế mâu thuẫn nhau — hậu quả: đơn *«từ
#  Sáng 05 đến hết 07»* bị trừ 2.5 thay vì 3 ngày, im lặng, không ai thấy.
#
#  `SESSION_HOURLY` cố ý KHÔNG có mặt: số công của nó tính từ khoảng giờ
#  (`count_hourly_days`), không phải một hằng số.
START_DAY_CREDIT = {SESSION_FULL: 1.0, SESSION_MORNING: 1.0, SESSION_AFTERNOON: 0.5}
END_DAY_CREDIT = {SESSION_FULL: 1.0, SESSION_MORNING: 0.5, SESSION_AFTERNOON: 1.0}


def same_day_credit(from_session: int, to_session: int) -> float:
    """Số công khi nghỉ GỌN trong một ngày — hai ô buổi cùng nói về ngày đó.

    Tính bằng hai mốc nửa ngày: bắt đầu ở nửa `0` (sáng) hay `1` (chiều), kết
    thúc ở nửa `0` hay `1`. Số nửa ngày phủ được là `end − start + 1`.

    Không lấy riêng một trong hai ô như bản cũ: lấy `from_session` thì
    *«Cả ngày → Sáng»* ra **1.0** trong khi người dùng khai kết thúc lúc hết
    buổi sáng, tức nửa ngày — và người lao động mất oan 0.5 ngày phép.

    *«Chiều → Sáng»* ra `0.0` (kết thúc trước lúc bắt đầu); `check_date_range`
    đã chặn trước, đây chỉ là để hàm không trả số âm.
    """
    start = 1 if from_session == SESSION_AFTERNOON else 0
    end = 0 if to_session == SESSION_MORNING else 1
    return max(0.0, (end - start + 1) * 0.5)

#  ── Khung giờ làm việc, dùng để quy đổi «nghỉ mấy giờ» ra «mấy ngày phép» ────
#
#  ⚠️ Hằng số vì hệ CHƯA có phân hệ Lịch làm việc (xem ghi chú ở `UNIT_HOUR`
#  bên dưới). Công ty đổi giờ làm thì sửa ĐÚNG bốn dòng này; đừng rải `/ 8` hay
#  `time(8, 0)` khắp nơi trong mã.
#
#  Bốn con số phải KHỚP NHAU: (kết thúc − bắt đầu) − nghỉ trưa = giờ công một
#  ngày. Lệch thì nghỉ từ đầu giờ tới cuối giờ ra một con số khác 1.0 ngày, và
#  không ai hiểu vì sao.
WORK_DAY_START = time(8, 0)
WORK_DAY_END = time(17, 0)
LUNCH_START = time(12, 0)
LUNCH_END = time(13, 0)
WORK_HOURS_PER_DAY = 8.0

#  Cầu nối sang mã chuỗi của giấy GNP (`core/leave_codes.LEAVE_SESSION_SET`).
#  Bảng dịch nằm ở ĐÂY, một chỗ — chứ không nội suy bằng `if` rải trong bridge.
SESSION_TO_DOC_CODE = {
    SESSION_FULL: "full",
    SESSION_MORNING: "morning",
    SESSION_AFTERNOON: "afternoon",
    SESSION_HOURLY: "hourly",
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
