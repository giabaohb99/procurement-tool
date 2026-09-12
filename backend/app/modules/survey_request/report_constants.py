"""Bộ mã của KHỐI BÁO CÁO THỰC HIỆN trên phiếu YCBG — số nguyên, theo R2/QĐ-11.

Trạng thái một HỒ SƠ trong báo cáo (giấy phép, hợp đồng, chứng từ vận chuyển…)
lưu `SMALLINT`; tiếng Việt chỉ sống ở `REPORT_DOC_STATUS_LABELS` và tầng hiển thị.
Đừng lẫn với `SurveyRequest.status` (mã CHUỖI draft/submitted… — ngoại lệ QĐ-9
của thu mua): hai cột nói về hai thứ khác nhau, khối báo cáo là bảng MỚI nên
theo luật mới.
"""

RD_IDLE = 0    # Chưa bắt đầu
RD_DOING = 1   # Đang làm
RD_REVIEW = 2  # Chờ duyệt
RD_DONE = 3    # Hoàn thành

REPORT_DOC_STATUS_LABELS = {
    RD_IDLE: "Chưa bắt đầu",
    RD_DOING: "Đang làm",
    RD_REVIEW: "Chờ duyệt",
    RD_DONE: "Hoàn thành",
}

#  5 giai đoạn mặc định khi bấm "Khởi tạo báo cáo" — theo mẫu báo cáo nhập khẩu
#  của Phòng Thu mua (09/2026). Chỉ là ĐIỂM XUẤT PHÁT: người dùng sửa/xóa/thêm
#  tự do, phiếu mua trong nước cứ đổi tên cho hợp.
DEFAULT_PHASES = (
    ("Pháp lý & Giấy phép", "Trước khi đặt hàng"),
    ("Đặt hàng & Hợp đồng", "Làm việc với NCC"),
    ("Sản xuất & Vận chuyển", "NCC sản xuất, giao hàng"),
    ("Kiểm tra & Thông quan", "Kiểm tra chất lượng, thủ tục"),
    ("Nhận hàng & Về kho", "Nhận hàng, đối chiếu, nhập kho"),
)

#  Trần số hồ sơ tiên quyết của MỘT hồ sơ — đủ rộng cho mọi quy trình thật,
#  đồng thời chặn payload rác (cột JSON không tự chặn gì cả, xem duoc-CR-316).
MAX_DEPENDS = 30
