"""Đăng ký chính sách file đính kèm (P1).

Mỗi entity đính kèm → (entity CHA để kiểm quyền, tập đuôi cho phép, dung lượng tối đa MB).
Entity không có ở đây sẽ bị TỪ CHỐI upload (chống entity rác).
"""

_DOC = {"pdf", "jpg", "jpeg", "png", "xlsx", "xls", "docx", "doc"}
_IMG = {"jpg", "jpeg", "png", "webp"}

FILE_POLICY: dict[str, tuple[str, set[str], int]] = {
    "purchase_request":       ("purchase_request", _DOC, 20),
    "purchase_request_quote": ("purchase_request", _DOC, 20),
    "survey":                 ("survey", {"pdf", "jpg", "jpeg", "png", "xlsx", "xls"}, 20),
    "survey_line":            ("survey", {"pdf", "jpg", "jpeg", "png", "xlsx", "xls"}, 20),
    "survey_request":         ("survey_request", _DOC, 20),
    "survey_request_line":    ("survey_request", {"pdf", "jpg", "jpeg", "png", "webp"}, 20),
    "purchase_order":         ("purchase_order", _DOC, 20),
    "delivery":               ("purchase_order", _DOC, 20),
    "contract":               ("contract", {"pdf", "jpg", "jpeg", "png", "docx", "doc"}, 30),
    "payment_request":        ("payment_request", {"pdf", "jpg", "jpeg", "png"}, 20),
    "avatar":                 ("__self__", _IMG, 5),   # __self__ = chỉ cần đăng nhập (ảnh của chính mình)
}


def policy(entity: str):
    return FILE_POLICY.get(entity)


def ext_of(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else ""
