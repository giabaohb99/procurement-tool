"""BỘ MÃ SỐ CỦA BA LỚP NHẬT KÝ — số nguyên, theo R2/QĐ-11 (bao-CR-312, P1).

Mọi cột mang nghĩa *nguồn · loại người làm · nhóm hành động* đều lưu `SMALLINT`
và so với hằng số ở đây; tiếng Việt chỉ sống trong các `*_LABELS` bên dưới.

⚠️ Đừng nhầm với `action` của `tab_audit_log`: cột đó vẫn là **mã chuỗi**
(`create`, `approve`, `login_failed`…) vì 213 lời gọi `record(...)` đang truyền
chuỗi, đổi sang số là sửa hết 213 chỗ mà chẳng được gì. P2 sẽ ràng tập chuỗi đó
bằng `ACTION_CATALOG` (NT-4). Cái ở đây là `action_group` — **nhóm** của hành
động, thứ dùng để lọc và để cảnh báo, và nó là số.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.
"""

# --------------------------------------------------------------------------
# Nguồn sinh ra một dòng `tab_request_log`
# --------------------------------------------------------------------------
#  Việc nền và script cũng là một dòng ở bảng đó (bản 2.2 của tài liệu), để màn
#  Nhật ký hệ thống có MỘT dòng chảy chứ không phải hai chỗ phải mở song song.
SOURCE_API = 1     # lời gọi HTTP đi qua middleware
SOURCE_CELERY = 2  # task nền
SOURCE_SCRIPT = 3  # script chạy tay (nhập liệu, backfill)

SOURCE_LABELS = {
    SOURCE_API: "Lời gọi API",
    SOURCE_CELERY: "Việc nền",
    SOURCE_SCRIPT: "Script",
}

# --------------------------------------------------------------------------
# Ai làm — `tab_audit_log.actor_kind`
# --------------------------------------------------------------------------
#  Hôm nay `created_by = 0` vừa nghĩa "hệ thống làm" vừa nghĩa "không biết ai
#  làm". Tách ra để câu hỏi *"cái này người bấm hay máy chạy?"* trả lời được
#  bằng một bộ lọc thay vì đọc `message`.
ACTOR_KIND_UNKNOWN = 0      # dòng cũ, trước khi bật P1 — không suy đoán
ACTOR_KIND_USER = 1         # người bấm nút (kể cả chưa đăng nhập: đăng nhập hỏng)
ACTOR_KIND_SYSTEM = 2       # Celery, seed, hook nội bộ
ACTOR_KIND_SCRIPT = 3       # script nhập liệu — bật cờ GỘP, xem bẫy 3 ở §6
ACTOR_KIND_INTEGRATION = 4  # tích hợp ngoài

ACTOR_KIND_LABELS = {
    ACTOR_KIND_UNKNOWN: "Không rõ",
    ACTOR_KIND_USER: "Người dùng",
    ACTOR_KIND_SYSTEM: "Hệ thống",
    ACTOR_KIND_SCRIPT: "Script nhập liệu",
    ACTOR_KIND_INTEGRATION: "Tích hợp ngoài",
}

# --------------------------------------------------------------------------
# Nhóm hành động — `tab_audit_log.action_group`
# --------------------------------------------------------------------------
ACTION_GROUP_UNKNOWN = 0
ACTION_GROUP_VIEW = 1        # xem (chỉ mấy lượt xem CÓ giá trị truy vết)
ACTION_GROUP_EDIT = 2        # thêm / sửa / đổi trạng thái nghiệp vụ
ACTION_GROUP_APPROVE = 3     # quyết định trong bộ máy duyệt
ACTION_GROUP_DELETE = 4      # xóa bản ghi
ACTION_GROUP_AUTH = 5        # đăng nhập / đăng xuất / gia hạn phiên
ACTION_GROUP_EXPORT = 6      # xuất dữ liệu, in
ACTION_GROUP_PERMISSION = 7  # phân quyền

ACTION_GROUP_LABELS = {
    ACTION_GROUP_UNKNOWN: "Không rõ",
    ACTION_GROUP_VIEW: "Xem",
    ACTION_GROUP_EDIT: "Sửa",
    ACTION_GROUP_APPROVE: "Duyệt",
    ACTION_GROUP_DELETE: "Xóa",
    ACTION_GROUP_AUTH: "Đăng nhập",
    ACTION_GROUP_EXPORT: "Xuất dữ liệu",
    ACTION_GROUP_PERMISSION: "Phân quyền",
}

#  Mã hành động -> nhóm. Danh sách mã lấy từ `ACTION_LABELS` của
#  `modules/audit/controller.py` — nơi duy nhất đang liệt kê đủ tập mã đang dùng.
#
#  ⚠️ P2 dựng `ACTION_CATALOG` (mã + nhãn + nhóm, NT-4) thì bảng này **nhập vào
#  đó**, đừng để hai chỗ cùng khai nhóm. Sở dĩ khai sớm ở P1: cột `action_group`
#  ra đời cùng migration đầu, mà mỗi dòng ghi ra với `0` là một dòng phải đi
#  backfill sau — rẻ hơn nhiều nếu điền đúng ngay từ dòng đầu tiên.
ACTION_GROUP_BY_ACTION = {
    # -- sửa dữ liệu ------------------------------------------------------
    "create": ACTION_GROUP_EDIT,
    "update": ACTION_GROUP_EDIT,
    "write": ACTION_GROUP_EDIT,
    "adjust": ACTION_GROUP_EDIT,
    "assign": ACTION_GROUP_EDIT,
    "dispatched": ACTION_GROUP_EDIT,
    "paid": ACTION_GROUP_EDIT,
    "processing": ACTION_GROUP_EDIT,
    "completed": ACTION_GROUP_EDIT,
    "auto_done": ACTION_GROUP_EDIT,
    "fill_line": ACTION_GROUP_EDIT,
    "item_progress": ACTION_GROUP_EDIT,
    "item_progress_auto": ACTION_GROUP_EDIT,
    "document_status": ACTION_GROUP_EDIT,
    "line_status": ACTION_GROUP_EDIT,
    "expected_date": ACTION_GROUP_EDIT,
    "pr_created": ACTION_GROUP_EDIT,
    "sync_options": ACTION_GROUP_EDIT,
    "add_option": ACTION_GROUP_EDIT,
    "del_option": ACTION_GROUP_EDIT,
    "option_add": ACTION_GROUP_EDIT,
    "option_remove": ACTION_GROUP_EDIT,
    "choose_option": ACTION_GROUP_EDIT,
    "unchoose_option": ACTION_GROUP_EDIT,
    "reply": ACTION_GROUP_EDIT,
    #  Đóng phiếu hỗ trợ. Từng RƠI RA NGOÀI bảng này — 36 dòng trên prod mang
    #  `action_group = 0`, tức lọc theo nhóm thì chúng biến mất khỏi mọi kết quả.
    "closed": ACTION_GROUP_EDIT,
    # -- phân quyền -------------------------------------------------------
    #  ⚠️ `ACTION_GROUP_PERMISSION` ra đời ở P1 nhưng **không mã nào trỏ vào nó**,
    #  vì `role/` và `user/` chưa từng gọi `record(...)`. Nghĩa là bộ lọc "Phân
    #  quyền" của màn nhật ký chắc chắn trả về rỗng — trông y như "chưa ai đổi
    #  quyền bao giờ". Sáu mã dưới đây (bao-CR-346) là thứ lấp chỗ đó.
    "set_permissions": ACTION_GROUP_PERMISSION,
    "assign_roles": ACTION_GROUP_PERMISSION,
    "set_scope": ACTION_GROUP_PERMISSION,
    "reset_password": ACTION_GROUP_PERMISSION,
    "activate": ACTION_GROUP_PERMISSION,
    "deactivate": ACTION_GROUP_PERMISSION,
    # -- bộ máy duyệt -----------------------------------------------------
    "submit": ACTION_GROUP_APPROVE,
    "submitted": ACTION_GROUP_APPROVE,
    "approve": ACTION_GROUP_APPROVE,
    "approved": ACTION_GROUP_APPROVE,
    "reject": ACTION_GROUP_APPROVE,
    "rejected": ACTION_GROUP_APPROVE,
    "return": ACTION_GROUP_APPROVE,
    "returned": ACTION_GROUP_APPROVE,
    "withdraw": ACTION_GROUP_APPROVE,
    "withdrawn": ACTION_GROUP_APPROVE,
    "cancel": ACTION_GROUP_APPROVE,
    "cancelled": ACTION_GROUP_APPROVE,
    "line_approve": ACTION_GROUP_APPROVE,
    # -- xóa --------------------------------------------------------------
    "delete": ACTION_GROUP_DELETE,
    # -- phiên ------------------------------------------------------------
    "login": ACTION_GROUP_AUTH,
    "login_failed": ACTION_GROUP_AUTH,
    "logout": ACTION_GROUP_AUTH,
    "refresh": ACTION_GROUP_AUTH,
    "refresh_failed": ACTION_GROUP_AUTH,
    "refresh_ip_changed": ACTION_GROUP_AUTH,
    # -- xuất / xem -------------------------------------------------------
    "export": ACTION_GROUP_EXPORT,
    "print": ACTION_GROUP_EXPORT,
    "view_file": ACTION_GROUP_VIEW,
}


def group_of_action(action: str) -> int:
    """Nhóm của một mã hành động; `0` nếu chưa khai (không đoán bừa)."""
    return ACTION_GROUP_BY_ACTION.get(action or "", ACTION_GROUP_UNKNOWN)
