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
    "doc_type", "external_party", "document_book",
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
    "doc_type": "Loại văn bản (Văn thư)",
    "external_party": "Đơn vị gửi nhận (Văn thư)",
    "document_book": "Sổ văn bản (Văn thư)",
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
