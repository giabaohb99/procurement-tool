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

#  ─── MẪU KHỞI TẠO (duoc-CR-614) ───────────────────────────────────────────────
#  Người dùng CHỌN mẫu lúc bấm «Khởi tạo báo cáo mẫu»; mẫu đã chọn LƯU ở
#  `ExecReport.template` (SMALLINT, R2) để nút «Tạo mẫu» trên từng dòng hàng /
#  giai đoạn về sau đổ đúng mẫu của khối đó, không mặc định quay về mẫu chung.
#  Số đã cấp KHÔNG đổi, KHÔNG tái dùng — khối cũ lưu số này trong DB.
RT_COMMON = 1       # Mẫu chung hồ sơ nhập khẩu — 5 giai đoạn (bao-CR-388/391/393)
RT_IMPORT_PLAN = 2  # Tiến độ kế hoạch công việc nhập khẩu — 1 giai đoạn, 21 việc

#  Mẫu «Tiến độ kế hoạch công việc nhập khẩu» — chép file Excel cùng tên của Phòng
#  Thu mua (đại ca gửi 09/10/2026): danh sách PHẲNG 21 việc (STT 0–20), không chia
#  giai đoạn → gom vào MỘT giai đoạn (đại ca chốt). Excel tính «Ngày dự kiến hoàn
#  thành = ngày bắt đầu + Time xử lý (Ngày)»; đại ca chốt KHÔNG đặt ngày lúc khởi
#  tạo, chỉ ghi số ngày xử lý vào mô tả — người dùng tự điền ngày trên dạng Bảng.
#  Cột «Người/Đơn vị phụ trách» (Nguyên · Tiên · Ngân) không chép: người thực hiện
#  là nhân sự thật, chọn trên dạng Bảng. Trạng thái «Hủy» của Excel không có — việc
#  bị hủy thì xóa dòng (đại ca chốt). Mỗi dòng: (tên việc, số ngày xử lý, bắt buộc).
IMPORT_PLAN_PHASES = (
    ("Kế hoạch công việc nhập khẩu", "Theo mẫu báo cáo tiến độ của Phòng Thu mua"),
)
IMPORT_PLAN_TASKS = (
    ("Tìm NCC nước ngoài", 1, True),
    ("Lấy mẫu", 0, True),
    ("Deal giá + hình thức thanh toán công nợ", 5, True),
    ("Duyệt giá", 1, True),
    ("Chốt PO Ký hợp đồng", 1, True),
    ("Dự trù tài chính", 1, True),
    ("NCC sắp xếp hàng hóa trước mỗi sáng Thứ 6", 7, True),
    ("Chuẩn bị hàng", 7, True),
    ("Vận chuyển hàng từ Nhà máy -> cảng", 5, True),
    ("Đóng hàng lên tàu, Tàu chạy", 3, True),
    ("Hàng về cập cảng + Tờ khai hàng nhập", 3, True),
    #  Việc DỰ PHÒNG — chỉ làm khi trễ lịch, nên không bắt buộc.
    ("Phương án không kịp thời gian", 1, False),
    ("Đóng thuế", 2, True),
    ("Kéo hàng về kho", 2, True),
    ("Lấy mẫu kiểm dịch", 1, True),
    ("Chờ kết quả kiểm dịch", 7, True),
    ("Có kết quả", 1, True),
    ("Thông Quan", 1, True),
    ("Đưa hàng vào sản xuất", 1, True),
    ("Lấy mẫu check đối chiếu", 7, True),
    ("Theo dõi thanh toán công nợ", 90, True),
)
#  Cùng hình dạng với `DEFAULT_TEMPLATE_DOCS` để `apply_template` đọc chung một đường.
IMPORT_PLAN_DOCS = tuple(
    (1, title, f"Thời gian xử lý: {days} ngày", required, [])
    for title, days, required in IMPORT_PLAN_TASKS
)

#  Sổ mẫu: mã → (tên hiển thị, mô tả ngắn, giai đoạn, hồ sơ). Thứ tự khai = thứ tự
#  trong ô chọn của hộp khởi tạo; mẫu đầu là mặc định.
REPORT_TEMPLATES = {
    RT_COMMON: (
        "Mẫu chung hồ sơ nhập khẩu",
        "5 giai đoạn (Pháp lý → Nhận hàng & về kho), bộ hồ sơ chứng từ nhập khẩu có tiên quyết.",
        DEFAULT_PHASES,
        DEFAULT_TEMPLATE_DOCS,
    ),
    RT_IMPORT_PLAN: (
        "Tiến độ kế hoạch công việc nhập khẩu",
        "21 việc từ Tìm NCC nước ngoài tới Theo dõi thanh toán công nợ, gom một giai đoạn; "
        "mô tả ghi số ngày xử lý, ngày tự điền.",
        IMPORT_PLAN_PHASES,
        IMPORT_PLAN_DOCS,
    ),
}

#  Trần số hồ sơ tiên quyết của MỘT hồ sơ — đủ rộng cho mọi quy trình thật,
#  đồng thời chặn payload rác (cột JSON không tự chặn gì cả, xem duoc-CR-316).
MAX_DEPENDS = 30

#  Trần số hồ sơ của MỘT lượt «xóa nhiều» — bằng trần số hồ sơ của cả khối
#  (`_ROW_CAPS` ở report_service), nên xóa sạch một khối đầy vẫn lọt một lượt.
MAX_BULK_DELETE_DOCS = 500
