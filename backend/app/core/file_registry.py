"""Đăng ký chính sách file đính kèm (P1).

Mỗi entity đính kèm → (entity CHA để kiểm quyền, tập đuôi cho phép, dung lượng tối đa MB).
Entity không có ở đây sẽ bị TỪ CHỐI upload (chống entity rác).
"""

_DOC = {"pdf", "jpg", "jpeg", "png", "webp", "xlsx", "xls", "docx", "doc", "txt", "csv", "xml", "msg", "eml",
        "cdr"}  # cdr = file thiết kế CorelDRAW (mẫu bao bì/nhãn NCC gửi kèm)
_IMG = {"jpg", "jpeg", "png", "webp"}

# CR-148: file thiết kế in ấn (PDF xuất từ Corel/AI, .cdr) thường 30-50MB nên trần
# chứng từ nâng 20/30 → 50MB. Nới thêm phải xem lại client_max_body_size của nginx
# (docker/nginx.prod.conf) và trần 100MB/request của Cloudflare tunnel bản free.
FILE_POLICY: dict[str, tuple[str, set[str], int]] = {
    "purchase_request":       ("purchase_request", _DOC, 50),
    "purchase_request_quote": ("purchase_request", _DOC, 50),
    "purchase_request_line_image": ("purchase_request", _IMG, 5),  # ảnh đối chiếu theo dòng PYC, entity_id = PurchaseRequestItem.id
    "survey":                 ("survey", _DOC, 50),
    "survey_line":            ("survey", _DOC, 50),
    "survey_request":         ("survey_request", _DOC, 50),
    "survey_request_line":    ("survey_request", _DOC, 50),
    "purchase_order":         ("purchase_order", _DOC, 50),
    "delivery":               ("purchase_order", _DOC, 50),
    "contract":               ("contract", _DOC, 50),
    "payment_request":        ("payment_request", _DOC, 50),
    "product":                ("product", _IMG, 5),   # ảnh sản phẩm, ≤5MB, cần write/create trên product
    "company":                ("company", _IMG, 5),   # logo công ty / pháp nhân
    "supplier":               ("supplier", _DOC, 50),  # đính kèm nhà cung cấp (ĐKKD, hồ sơ năng lực...)
    "ticket":                 ("ticket", _DOC, 50),   # đính kèm phiếu hỗ trợ
    "ticket_message":         ("ticket", _DOC, 50),   # đính kèm 1 tin nhắn trả lời
    # (Ảnh đại diện KHÔNG nằm trong bảng này: nó không đi qua FileLink mà lưu thẳng
    #  tab_user.avatar_file_id → tab_file, quản lý qua user/service.set_user_avatar.)
    # Đính kèm bình luận (CR-033). Bình luận treo được vào NHIỀU loại chứng từ khác nhau nên
    # không có một entity cha cố định để điền vào đây — quyền thật do API bình luận quyết
    # (`comment/service.resolve_doc`: quyền đọc + phạm vi dữ liệu của chính chứng từ đó).
    # `__self__` ở đây chỉ mở bước TẢI FILE TẠM (chưa gắn vào đâu);
    # còn gắn/đọc/xóa link đều đi qua nhánh riêng trong `attachment/controller.py`.
    "comment":                ("__self__", _DOC, 50),
    # Bài viết diễn đàn: ảnh + video (D-Q3 chốt 27/08/2026 — video quay điện thoại
    # đăng thẳng, mp4/webm là hai định dạng <video> mọi trình duyệt phát được).
    # Trần 50MB/tệp vì video: ảnh cũng ăn chung trần này — chấp nhận, vì policy
    # mỗi entity chỉ có một con số; trần 10 TỆP/bài kiểm ở tầng service khi gắn.
    # `__self__` vì người dùng thường không có grant RBAC trên `forum_post`
    # (đăng/đọc đi theo luật audience) — F1 thêm nhánh kiểm audience riêng trong
    # `attachment/controller.py`, đúng khuôn `_check_comment`.
    "forum_post":             ("__self__", _IMG | {"mp4", "webm"}, 50),
    # Đính kèm của văn bản treo vào PHIÊN BẢN (`entity_id` = id phiên bản), không
    # vào văn bản: bản đã duyệt phải tra ra đúng bộ tệp lúc duyệt, kể cả sau khi
    # bản mới đã gỡ bớt. Quyền kiểm trên entity cha `document`.
    "document_version":       ("document", _DOC, 50),
    # Duyệt dấu: chứng từ có CHỮ KÝ SỐNG (doc_type="signed_doc", NSYC upload để Văn
    # thư đối chiếu trước khi đóng dấu) + ảnh minh họa cho ghi chú (doc_type="note").
    # Chứng từ có thể là PDF hợp đồng ~17MB nên dùng trần _DOC 50MB. Quyền kiểm trên
    # entity cha `seal_request` (read/write + phạm vi dữ liệu của phiếu).
    "seal_request":           ("seal_request", _DOC, 50),
    # Đính kèm của một CÔNG VIỆC trong phân hệ Dự án (E-03). Entity cha là
    # `work_task` thật (lớp RBAC hỏi được), nhưng lớp PHẠM VI thì `apply_scope`
    # vô dụng — `work_task` khai `PUBLIC` ở `SCOPE_FIELDS` vì phạm vi thật là tư
    # cách THÀNH VIÊN của danh sách chứa việc. Vì vậy `attachment_scope.ensure_in_scope`
    # rẽ riêng sang `_ensure_task_member`, đúng khuôn nhánh `document` ngay trên;
    # bỏ nhánh ấy đi là ai đăng nhập cũng tải được tệp của dự án mình không tham gia.
    # 50MB chứ không ít hơn: mọi ô nhận PDF đều tối thiểu 50 (CR-148 — PDF in ấn
    # và .cdr thường 30-50MB), có bài quét cả bảng ghim con số đó.
    "work_task":              ("work_task", _DOC | _IMG, 50),
}

#  CỬA NHẬN TỆP KHÔNG ĐI QUA `FileLink` — ảnh đại diện, ảnh chữ ký, ảnh chèn bài HDSD.
#  `FILE_POLICY` ở trên chỉ nói về đính kèm có dây; mấy cửa này lưu thẳng vào
#  `tab_user.avatar_file_id` / `tab_user.signature` / nội dung bài viết nên trước
#  bao-CR-408 chúng nằm NGOÀI mọi bảng chính sách: không kiểm đuôi, không kiểm dung
#  lượng, chỉ hỏi `content_type.startswith("image/")` — mà chuỗi đó là lời khai của
#  máy khách, `image/svg+xml` đi qua tuốt (BM-026 · BM-027).
#
#  Bảng này là nơi DUY NHẤT khai luật cho chúng. Cửa thứ năm mọc ra thì thêm một
#  dòng ở đây rồi gọi `upload_guard.guard_upload`, đừng chép luật vào controller.
_IMG_WEB = _IMG | {"gif"}   # ảnh chèn bài HDSD: thêm GIF ảnh động minh họa thao tác

DIRECT_FILE_POLICY: dict[str, tuple[set[str], int]] = {
    "avatar":     (_IMG, 5),
    "signature":  (_IMG, 5),
    "help_image": (_IMG_WEB, 10),
    "id_image":   (_IMG, 10),   # ảnh CCCD hai mặt — điện thoại chụp nên trần rộng hơn avatar
}


def direct_policy(kind: str) -> tuple[set[str], int]:
    """(tập đuôi cho phép, trần MB) của một cửa tải tệp trực tiếp. Khóa lạ → lỗi lập trình."""
    pol = DIRECT_FILE_POLICY.get(kind)
    if not pol:
        raise ValueError(f"Chưa khai chính sách tệp cho cửa '{kind}' trong DIRECT_FILE_POLICY")
    return pol


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
