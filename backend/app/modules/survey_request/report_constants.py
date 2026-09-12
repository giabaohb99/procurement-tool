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
#  «Nhập khẩu K₂SO₄ & KNO₃» của Phòng Thu mua (11/09/2026). Chỉ là ĐIỂM XUẤT PHÁT:
#  người dùng sửa/xóa/thêm tự do, phiếu mua trong nước cứ đổi tên cho hợp.
DEFAULT_PHASES = (
    ("Pháp lý & Giấy phép", "Việt Nam — trước khi đặt hàng"),
    ("Đặt hàng & Hợp đồng", "DEGO ↔ NCC nước ngoài"),
    ("Sản xuất & Vận chuyển", "Nước xuất khẩu → cảng Việt Nam"),
    ("Kiểm tra & Thông quan", "Cảng nhập (Cát Lái · TP.HCM)"),
    ("Nhận hàng & Về kho", "Kho DEGO · Cần Thơ"),
)

#  MẪU CHUNG — bộ hồ sơ đi kèm 5 giai đoạn trên (bao-CR-388; nội dung theo mẫu
#  «Nhập khẩu K₂SO₄ & KNO₃» của Phòng Thu mua, bao-CR-391, rồi GOM về bản chung ở
#  bao-CR-393). «Khởi tạo báo cáo mẫu» dựng cả hồ sơ chứ không chỉ khung (khung 5
#  giai đoạn rỗng thì "bấm xong hổng có gì hết trơn"), và nút «Tạo mẫu» trên từng
#  nút dòng hàng / giai đoạn đổ đúng phần mẫu đó vào. Cố ý để TRONG MÃ NGUỒN, chưa
#  có bảng: quản lý mẫu (lưu/sửa nhiều mẫu) là việc sau, khi có thì thay nguồn đọc
#  ở `report_service.apply_template`, chỗ gọi không đổi.
#  Luật gom (bao-CR-393): mẫu là BỘ CHUNG cho một lô nhập khẩu — mỗi việc đúng
#  MỘT dòng, KHÔNG tách theo mặt hàng (mẫu gốc từng có hai dòng «Hợp đồng NK» cho
#  K₂SO₄ và KNO₃, hai dòng Giấy CN lưu hành…). Hồ sơ chỉ một mặt hàng mới cần
#  (giấy phép tiền chất Bộ Công An, kiểm tra thực tế 100%, sổ theo dõi tiền chất)
#  người dùng THÊM TAY vào đúng nút dòng hàng đó; mẫu chỉ giữ lại một dòng «Giấy
#  phép NK chuyên ngành (nếu có)» không bắt buộc để khỏi quên hỏi.
#  Mỗi dòng: (số thứ tự giai đoạn trong DEFAULT_PHASES 1..5, tiêu đề, mô tả,
#  bắt buộc, tiên quyết theo SỐ THỨ TỰ 1-based trong chính danh sách này).
DEFAULT_TEMPLATE_DOCS = (
    # 1. Pháp lý & Giấy phép
    (1, "Giấy phép nhập khẩu chuyên ngành (nếu mặt hàng cần)",
     "Mặt hàng thuộc diện quản lý riêng (vd tiền chất → Cục KTNV Bộ Công An, "
     "NĐ 113/2017; xử lý 30–45 ngày) phải có giấy phép TRƯỚC khi ký HĐ — Hải quan "
     "từ chối thông quan nếu thiếu. Không thuộc diện thì xóa dòng này.", False, []),
    (1, "Giấy CN đăng ký lưu hành phân bón",
     "NĐ 84/2019. Lần đầu 3–6 tháng tại Cục BVTV; nếu SP đã có mã: chỉ bổ sung "
     "công ty vào danh sách nhà phân phối.", True, []),
    # 2. Đặt hàng & Hợp đồng
    (2, "RFQ & báo giá NCC",
     "Gửi Request for Quotation chính thức, thu thập báo giá FOB/CIF từ NCC.", True, []),
    (2, "Hợp đồng NK + đặt cọc",
     "Ký HĐ, đặt cọc L/C hoặc T/T; chốt giá, thanh toán, bảo hiểm. Mặt hàng cần "
     "giấy phép chuyên ngành thì CHỈ ký sau khi có giấy phép.", True, [3]),
    (2, "Yêu cầu NCC: C/O Form E + CoA + MSDS",
     "Form E (ACFTA) do CCPIT/CIQ cấp để hưởng thuế 0%; CoA (kết quả phân tích) & "
     "MSDS phục vụ kiểm tra chất lượng và hồ sơ chuyên ngành.", True, [3]),
    # 3. Sản xuất & Vận chuyển
    (3, "NCC xuất hàng FOB",
     "Lead time sản xuất ~15 ngày. NCC giao hàng lên tàu theo điều kiện FOB.", True, [4]),
    (3, "Booking container & cước biển (Logistics)",
     "Giữ chỗ container, đặt cước tàu biển tuyến cảng đi → cảng đến cho cả lô.",
     False, [4]),
    (3, "Commercial Invoice",
     "Ghi rõ HS Code, đơn giá FOB/CIF, trị giá lô hàng.", True, [6]),
    (3, "Packing List",
     "Số lượng, trọng lượng từng kiện/container.", True, [8]),
    (3, "Bill of Lading (B/L) / Sea Waybill",
     "Vận đơn gốc hoặc Sea Waybill do hãng tàu phát hành.", True, [6]),
    (3, "C/O Form E (ACFTA)",
     "Bắt buộc để hưởng thuế NK 0% — do CCPIT/CIQ Trung Quốc cấp.", True, [5, 8]),
    # 4. Kiểm tra & Thông quan
    (4, "Đăng ký kiểm tra chất lượng phân bón",
     "Cơ quan chỉ định lấy mẫu tại cửa khẩu (TT 09/2019/TT-BNNPTNT). Lấy mẫu + "
     "phân tích 3–5 ngày.", True, [10]),
    (4, "Phiếu kiểm dịch thực vật (nếu HQ yêu cầu)",
     "Xác nhận trước với Chi cục Kiểm dịch thực vật — một số trường hợp HQ yêu cầu.",
     False, [10]),
    (4, "Khai hải quan điện tử VNACCS/VCIS",
     "Khai tờ khai điện tử, nộp bộ hồ sơ hải quan lên hệ thống.", True,
     [8, 9, 10, 11, 12]),
    (4, "Kiểm tra thực tế lô hàng (nếu HQ phân luồng đỏ)",
     "Hải quan kiểm tra thực tế khi phân luồng đỏ; mặt hàng quản lý riêng (tiền "
     "chất) bị kiểm 100%.", False, [14]),
    (4, "Nộp thuế VAT 5%",
     "Luật 45/2024/QH15 — phân bón chịu VAT 5% từ 01/07/2025.", True, [14]),
    # 5. Nhận hàng & Về kho
    (5, "Thông quan",
     "Thông quan 1–3 ngày nếu hồ sơ đầy đủ; lô bị kiểm tra thực tế thì lâu hơn.",
     True, [14, 16]),
    (5, "Vận chuyển đường bộ về kho Cần Thơ",
     "Cảng Cát Lái (HCM) → kho DEGO Cần Thơ.", True, [17]),
    (5, "Nhập kho & đối chiếu số lượng",
     "Nhận hàng tại kho, đối chiếu số lượng/chất lượng với Packing List và hợp đồng.",
     True, [18]),
)

#  Trần số hồ sơ tiên quyết của MỘT hồ sơ — đủ rộng cho mọi quy trình thật,
#  đồng thời chặn payload rác (cột JSON không tự chặn gì cả, xem duoc-CR-316).
MAX_DEPENDS = 30
