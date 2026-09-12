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

#  MẪU CHUNG — bộ hồ sơ đi kèm 5 giai đoạn trên (bao-CR-388). «Khởi tạo báo cáo
#  mẫu» dựng cả hồ sơ chứ không chỉ khung (khung 5 giai đoạn rỗng thì "bấm xong
#  hổng có gì hết trơn"), và nút «Tạo mẫu» trên từng nút dòng hàng / giai đoạn
#  đổ đúng phần mẫu đó vào. Cố ý để TRONG MÃ NGUỒN, chưa có bảng: quản lý mẫu
#  (lưu/sửa nhiều mẫu) là việc sau, khi có thì thay nguồn đọc ở
#  `report_service.apply_template`, chỗ gọi không đổi.
#  Mỗi dòng: (số thứ tự giai đoạn trong DEFAULT_PHASES 1..5, tiêu đề, mô tả,
#  bắt buộc, tiên quyết theo SỐ THỨ TỰ 1-based trong chính danh sách này).
DEFAULT_TEMPLATE_DOCS = (
    # 1. Pháp lý & Giấy phép
    (1, "Giấy đăng ký kinh doanh của NCC",
     "Bản sao còn hiệu lực, đối chiếu ngành nghề với mặt hàng cung cấp.", True, []),
    (1, "Hồ sơ năng lực của NCC",
     "Khách hàng tham chiếu, công suất, chứng nhận chất lượng (ISO...).", False, []),
    (1, "Giấy phép / chứng nhận của sản phẩm",
     "Giấy phép lưu hành, kiểm định, COA... nếu mặt hàng thuộc diện quản lý.", False, []),
    # 2. Đặt hàng & Hợp đồng
    (2, "Báo giá chính thức có ký, đóng dấu",
     "Ghi rõ đơn giá, VAT, điều kiện giao hàng và thời hạn hiệu lực.", True, [1]),
    (2, "Hợp đồng mua bán / hợp đồng nguyên tắc",
     "Điều khoản thanh toán, phạt chậm giao, bảo hành.", True, [4]),
    (2, "Đơn mua hàng (PO) phát hành",
     "Phát hành sau khi hợp đồng ký xong.", True, [5]),
    (2, "Xác nhận đơn hàng của NCC",
     "NCC xác nhận số lượng, đơn giá, ngày giao bằng văn bản.", False, [6]),
    # 3. Sản xuất & Vận chuyển
    (3, "Lịch sản xuất & ngày giao dự kiến",
     "NCC gửi lịch chia lô nếu giao nhiều đợt.", True, [6]),
    (3, "Chứng từ vận chuyển",
     "Vận đơn / phiếu xuất kho kiêm vận chuyển, biển số xe, tên tài xế.", True, [8]),
    # 4. Kiểm tra & Thông quan
    (4, "Biên bản kiểm tra chất lượng",
     "Kiểm quy cách, số lượng theo lô; ghi rõ số lượng không đạt nếu có.", True, [9]),
    (4, "Chứng từ thông quan",
     "Tờ khai hải quan, C/O, kiểm dịch... chỉ áp dụng hàng nhập khẩu.", False, [9]),
    # 5. Nhận hàng & Về kho
    (5, "Biên bản giao nhận có ký hai bên",
     "Ký sau khi kiểm tra xong, ghi số lượng thực nhận.", True, [10]),
    (5, "Phiếu nhập kho",
     "Nhập đúng mã hàng, đối chiếu với đơn mua hàng.", True, [12]),
    (5, "Hóa đơn GTGT",
     "Kiểm tên, mã số thuế, đơn giá trước khi chuyển kế toán.", True, [12]),
    (5, "Biên bản đối chiếu công nợ",
     "Đối chiếu trước khi đề nghị thanh toán phần còn lại.", False, [14]),
)

#  Trần số hồ sơ tiên quyết của MỘT hồ sơ — đủ rộng cho mọi quy trình thật,
#  đồng thời chặn payload rác (cột JSON không tự chặn gì cả, xem duoc-CR-316).
MAX_DEPENDS = 30
