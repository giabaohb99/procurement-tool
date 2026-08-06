"""Đăng ký chính sách file đính kèm (P1).

Mỗi entity đính kèm → (entity CHA để kiểm quyền, tập đuôi cho phép, dung lượng tối đa MB).
Entity không có ở đây sẽ bị TỪ CHỐI upload (chống entity rác).
"""

_DOC = {"pdf", "jpg", "jpeg", "png", "webp", "xlsx", "xls", "docx", "doc", "txt", "csv", "xml", "msg", "eml",
        "cdr"}  # cdr = file thiết kế CorelDRAW (mẫu bao bì/nhãn NCC gửi kèm)
_IMG = {"jpg", "jpeg", "png", "webp"}

FILE_POLICY: dict[str, tuple[str, set[str], int]] = {
    "purchase_request":       ("purchase_request", _DOC, 20),
    "purchase_request_quote": ("purchase_request", _DOC, 20),
    "purchase_request_line_image": ("purchase_request", _IMG, 5),  # ảnh đối chiếu theo dòng PYC, entity_id = PurchaseRequestItem.id
    "survey":                 ("survey", _DOC, 20),
    "survey_line":            ("survey", _DOC, 20),
    "survey_request":         ("survey_request", _DOC, 20),
    "survey_request_line":    ("survey_request", _DOC, 20),
    "purchase_order":         ("purchase_order", _DOC, 20),
    "delivery":               ("purchase_order", _DOC, 20),
    "contract":               ("contract", _DOC, 30),
    "payment_request":        ("payment_request", _DOC, 20),
    "product":                ("product", _IMG, 5),   # ảnh sản phẩm, ≤5MB, cần write/create trên product
    "ticket":                 ("ticket", _DOC, 20),   # đính kèm phiếu hỗ trợ
    "ticket_message":         ("ticket", _DOC, 20),   # đính kèm 1 tin nhắn trả lời
    "avatar":                 ("__self__", _IMG, 5),   # __self__ = chỉ cần đăng nhập (ảnh của chính mình)
}


def policy(entity: str):
    return FILE_POLICY.get(entity)


def ext_of(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else ""
