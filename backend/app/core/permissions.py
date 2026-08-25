"""Danh sách quyền dùng chung (nguồn chân lý duy nhất).

Quyền = ENTITY (đối tượng) x ACTION (hành động). Seed & kiểm tra đều dựa vào đây.
"""

ENTITIES = [
    "company", "department", "employee", "user", "role",
    "warehouse", "unit", "item_group", "brand",
    "supplier", "product", "contract",
    "purchase_request", "survey", "purchase_order", "goods_receipt",
    "inventory", "payable", "payment", "payment_request",
    "report", "setting", "category_assignee", "survey_request", "import", "backup",
    "help_article", "ticket",
    # Phân hệ Văn thư
    #  ⚠️ MỘT KHÓA = MỘT MÀN HÌNH. Trước 25/08/2026 bốn màn danh mục (Loại văn
    #  bản · Thư viện mẫu · Quy tắc đánh số · Quy tắc quan hệ) dùng CHUNG khóa
    #  `doc_type`, nên cho ai sửa quy tắc đánh số là cho họ sửa luôn loại văn
    #  bản — ba việc do ba người khác nhau làm mà không tách được (CR-157).
    "doc_type", "doc_template", "doc_numbering_rule", "doc_link_rule",
    "external_party", "document_book", "document", "security_level",
    # Phân hệ Duyệt dấu
    "seal_request", "seal_type",
    # Phân hệ Đặt xe
    "vehicle_booking", "vehicle", "driver",
    # Bộ máy phê duyệt dùng chung — KHÔNG thuộc phân hệ nào, mọi loại chứng từ
    # đều chạy qua nó.
    "approval_flow",
    # Trợ lý AI — cổng bật/tắt theo vai trò (chỉ ban lãnh đạo). Không có bảng
    # dữ liệu để lọc theo dòng nên khai PUBLIC ở scoping.
    "assistant",
]

ACTIONS = ["read", "create", "write", "delete", "approve", "cancel", "print", "export"]

# Nhãn tiếng Việt để hiển thị ở màn cấu hình phân quyền
ENTITY_LABELS = {
    "company": "Công ty (pháp nhân)",
    "department": "Phòng ban",
    "employee": "Nhân viên",
    "user": "Tài khoản",
    "role": "Vai trò & phân quyền",
    "warehouse": "Kho",
    "unit": "Đơn vị tính",
    "item_group": "Phân loại VTBB/NL",
    "brand": "Thương hiệu / Bộ phận",
    "supplier": "Nhà cung cấp",
    "product": "Sản phẩm / Hàng hóa",
    "contract": "Hợp đồng",
    "purchase_request": "Yêu cầu mua hàng",
    "survey": "Khảo sát",
    "purchase_order": "Đơn mua hàng",
    "goods_receipt": "Nhận hàng (GR)",
    "inventory": "Kho / Tồn",
    "payable": "Công nợ",
    "payment": "Thanh toán",
    "payment_request": "Yêu cầu thanh toán",
    "report": "Báo cáo",
    "setting": "Cấu hình hệ thống",
    "category_assignee": "Phân công phụ trách (theo phân loại)",
    "survey_request": "Yêu cầu báo giá",
    "import": "Nhập dữ liệu (Import)",
    "backup": "Sao lưu CSDL",
    "help_article": "Hướng dẫn sử dụng (Help Center)",
    "ticket": "Phiếu hỗ trợ",
    #  Nhãn đi theo ĐƯỜNG MENU chứ không theo tên bảng: người khai quyền tìm
    #  theo thứ họ bấm trên màn hình, không theo thứ lập trình viên đặt tên.
    "doc_type": "Văn thư › Thiết lập › Loại văn bản",
    "doc_template": "Văn thư › Thiết lập › Thư viện văn bản mẫu",
    "doc_numbering_rule": "Văn thư › Quy tắc đánh số",
    "doc_link_rule": "Văn thư › Quy tắc quan hệ",
    "external_party": "Văn thư › Thiết lập › Đơn vị gửi nhận",
    "security_level": "Văn thư › Thiết lập › Mức mật / Độ khẩn",
    "document_book": "Văn thư › Sổ văn bản",
    "document": "Văn thư › Văn bản",
    "seal_request": "Yêu cầu duyệt dấu",
    "seal_type": "Loại con dấu",
    "vehicle_booking": "Yêu cầu đặt xe",
    "vehicle": "Phương tiện (Xe)",
    "driver": "Tài xế",
    "approval_flow": "Luồng phê duyệt (dùng chung)",
    "assistant": "Trợ lý AI",
}

ACTION_LABELS = {
    "read": "Xem", "create": "Tạo", "write": "Sửa", "delete": "Xóa",
    "approve": "Duyệt", "cancel": "Hủy", "print": "In", "export": "Xuất",
}

# Phạm vi theo cấp bậc (tương đối với công ty/phòng ban của chính user)
# "assigned" (Được giao) = của mình HOẶC được phân bổ cho mình — dùng cho nhân viên thu mua trên PYC.
SCOPES = ["own", "assigned", "proc", "dept", "company", "all"]
SCOPE_LABELS = {
    "own": "Của mình", "assigned": "Được giao", "proc": "Thu mua (được giao + đã duyệt)",
    "dept": "Phòng ban", "company": "Công ty", "all": "Tất cả",
}
SCOPE_RANK = {"own": 0, "assigned": 1, "proc": 1, "dept": 2, "company": 3, "all": 4}
