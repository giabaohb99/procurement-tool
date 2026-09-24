"""BỘ MÃ SỐ CỦA HỒ SƠ — theo R2/QĐ-11 (phân hệ Hồ sơ, 16/09/2026).

Cột `tab_dossier.status` lưu `SMALLINT`, tiếng Việt chỉ sống ở `*_LABELS` và ở
tầng hiển thị. Cùng khuôn với `employee/constants.py` và `leave/constants.py`.

Bản TypeScript gõ tay ở `frontend-v2/src/modules/dossier/types/dossier.ts` —
`scripts/gen_status_ts.py` chỉ sinh cho bộ mã CHUỖI. Đổi ở đây thì phải nhớ sửa
tay bên kia; có test chốt số mục.
"""

# --------------------------------------------------------------------------
# Tình trạng hồ sơ — VÒNG ĐỜI DO NGƯỜI ĐẶT, ba mức
# --------------------------------------------------------------------------
#  ⚠️ **Cố ý KHÔNG có mã «Hết hạn» / «Sắp hết hạn».** Hai thứ đó suy ra được từ
#  `expiry_date` và ngày hôm nay, nên lưu chúng thành cột là tự dựng một sự thật
#  thứ hai: tới nửa đêm nó sai, và phải có một tác vụ chạy nền đi lật từng dòng
#  để nó đúng lại. Bỏ quên tác vụ ấy một tuần thì màn hình báo «Còn hiệu lực»
#  cho giấy phép đã hết hạn — đúng loại sai nguy hiểm nhất của cả phân hệ này.
#  Tình trạng hiệu lực tính ở `service.expiry_state()`, mỗi lần đọc một lần
#  tính, không bao giờ cũ.
DOSSIER_DRAFT = 1       # mới lập, chưa nộp vào kho hồ sơ
DOSSIER_ACTIVE = 2      # đã nộp, đang theo dõi
DOSSIER_ARCHIVED = 3    # hết vòng đời, chuyển kho lưu trữ

DOSSIER_STATUS_VALUES = (DOSSIER_DRAFT, DOSSIER_ACTIVE, DOSSIER_ARCHIVED)

DOSSIER_STATUS_LABELS = {
    DOSSIER_DRAFT: "Nháp",
    DOSSIER_ACTIVE: "Đang lưu",
    DOSSIER_ARCHIVED: "Đã lưu trữ",
}

# --------------------------------------------------------------------------
# Tình trạng HIỆU LỰC — SUY RA, không lưu cột nào
# --------------------------------------------------------------------------
#  Tính từ `expiry_date` mỗi lần đọc (xem `service.expiry_state`). Có mặt trong
#  phong bì trả về để giao diện khỏi chép lại luật ngày tháng — và để bản in với
#  tệp Excel nói cùng một câu với màn hình.
EXPIRY_NONE = 0       # vô thời hạn — `expiry_date` bỏ trống, một câu trả lời thật
EXPIRY_VALID = 1      # còn hạn
EXPIRY_NEAR = 2       # còn hạn nhưng trong ngưỡng cảnh báo
EXPIRY_OVER = 3       # đã quá hạn

EXPIRY_STATE_LABELS = {
    EXPIRY_NONE: "Vô thời hạn",
    EXPIRY_VALID: "Còn hạn",
    EXPIRY_NEAR: "Sắp hết hạn",
    EXPIRY_OVER: "Hết hạn",
}

#  Bao nhiêu ngày trước hạn thì kêu «sắp hết hạn».
#
#  30 ngày vì đó là khoảng xin gia hạn giấy phép con thực tế cần — cảnh báo muộn
#  hơn thì không kịp làm gì, mà sớm hơn nhiều thì cả danh sách vàng khè quanh
#  năm và không ai nhìn nữa.
EXPIRY_WARN_DAYS = 30

# --------------------------------------------------------------------------
# TIẾN ĐỘ hồ sơ THEO TỪNG CHỨNG TỪ — `tab_dossier_progress`
# --------------------------------------------------------------------------
#  ⚠️ **Đừng lẫn với `DOSSIER_*` ở trên.** Hai cột nói hai chuyện khác hẳn:
#    · `tab_dossier.status`  = tờ giấy ĐÃ CÓ trong kho công ty chưa (nháp/đang
#      lưu/lưu trữ) — một giá trị cho cả công ty.
#    · `tab_dossier_progress.status` = việc làm tờ giấy đó CHO MỘT PHIẾU cụ thể
#      tới đâu rồi — mỗi phiếu một giá trị.
#  Tờ «Giấy đăng ký kinh doanh của NCC» đang lưu trong kho (`DOSSIER_ACTIVE`)
#  vẫn có thể «Chưa bắt đầu» ở một phiếu mới lập, vì chưa ai đi lấy bản sao kèm
#  vào phiếu đó. Gộp hai thang là mất đúng thông tin người dùng cần.
#
#  Bốn mức chép của `survey_request/report_constants.py` để thẻ «Hồ sơ cần hoàn
#  thành» nói cùng một ngôn ngữ với khối «Báo cáo thực hiện». Cố ý KHÔNG import
#  từ đó: phân hệ Hồ sơ không được phụ thuộc vào phân hệ Thu mua — thẻ này chạy
#  ở cả bốn loại chứng từ, trong đó có hai loại không thuộc Thu mua.
DP_IDLE = 0     # Chưa bắt đầu
DP_DOING = 1    # Đang làm
DP_REVIEW = 2   # Chờ duyệt
DP_DONE = 3     # Hoàn thành

DP_STATUS_VALUES = (DP_IDLE, DP_DOING, DP_REVIEW, DP_DONE)

DP_STATUS_LABELS = {
    DP_IDLE: "Chưa bắt đầu",
    DP_DOING: "Đang làm",
    DP_REVIEW: "Chờ duyệt",
    DP_DONE: "Hoàn thành",
}

#  Trần số hồ sơ tiên quyết của MỘT tờ hồ sơ. Cùng con số với khối «Báo cáo thực
#  hiện» (`report_constants.MAX_DEPENDS`) — không phải vì hai bên dùng chung mã,
#  mà vì cùng một cỡ dữ liệu: một tờ giấy chờ quá ba bốn tờ khác đã là dấu hiệu
#  khai sai, 30 chỉ để chặn ca dán nhầm cả danh sách.
MAX_DOSSIER_DEPENDS = 30
