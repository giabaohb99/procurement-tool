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
    "company":                ("company", _IMG, 5),   # logo công ty / pháp nhân
    "supplier":               ("supplier", _DOC, 20),  # đính kèm nhà cung cấp (ĐKKD, hồ sơ năng lực...)
    "ticket":                 ("ticket", _DOC, 20),   # đính kèm phiếu hỗ trợ
    "ticket_message":         ("ticket", _DOC, 20),   # đính kèm 1 tin nhắn trả lời
    # (Ảnh đại diện KHÔNG nằm trong bảng này: nó không đi qua FileLink mà lưu thẳng
    #  tab_user.avatar_file_id → tab_file, quản lý qua user/service.set_user_avatar.)
    # Đính kèm bình luận (CR-033). Bình luận treo được vào NHIỀU loại chứng từ khác nhau nên
    # không có một entity cha cố định để điền vào đây — quyền thật do API bình luận quyết
    # (`comment/service.resolve_doc`: quyền đọc + phạm vi dữ liệu của chính chứng từ đó).
    # `__self__` ở đây chỉ mở bước TẢI FILE TẠM (chưa gắn vào đâu);
    # còn gắn/đọc/xóa link đều đi qua nhánh riêng trong `attachment/controller.py`.
    "comment":                ("__self__", _DOC, 20),
    # Đính kèm của văn bản treo vào PHIÊN BẢN (`entity_id` = id phiên bản), không
    # vào văn bản: bản đã duyệt phải tra ra đúng bộ tệp lúc duyệt, kể cả sau khi
    # bản mới đã gỡ bớt. Quyền kiểm trên entity cha `document`.
    "document_version":       ("document", _DOC, 30),
}

#  ENTITY RIÊNG TƯ — API **không trả `url` công khai** cho những entity này, chỉ
#  trả đường tải có kiểm quyền `GET /api/attachments/{link_id}/download`.
#
#  Vì sao cần: `upload_fileobj()` sinh URL đọc thẳng từ bucket (hoặc
#  `/api/uploads/...` khi chạy local — mà chỗ đó là `StaticFiles`, KHÔNG kiểm
#  đăng nhập). Đưa URL đó ra ngoài nghĩa là ai cầm được chuỗi đó đều mở được tệp,
#  kể cả người đã bị thu hồi quyền, kể cả người chưa đăng nhập.
#
#  ⚠️ Đây mới là **nửa việc**. Bản thân object trên storage vẫn đọc được nếu ai
#  đó đã có URL từ trước hoặc đoán đúng key — bịt hẳn thì phải chuyển bucket sang
#  private + đổi mọi phân hệ sang link tạm (P0-N02/N03), là việc hạ tầng đụng cả
#  `frontend/` đang đóng băng. Cho tới lúc đó: **không đưa văn bản Tuyệt mật thật
#  vào hệ thống**.
PRIVATE_ENTITIES: set[str] = {"document_version"}


def is_private(entity: str) -> bool:
    return entity in PRIVATE_ENTITIES


def is_image(filename: str, content_type: str = "") -> bool:
    """Ảnh thì hiện luôn ra, file khác chỉ hiện tên — dùng cho đính kèm bình luận."""
    return (content_type or "").startswith("image/") or ext_of(filename) in _IMG


def policy(entity: str):
    return FILE_POLICY.get(entity)


def ext_of(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else ""
