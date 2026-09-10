"""BỘ MÃ SỐ CỦA BA LỚP NHẬT KÝ — số nguyên, theo R2/QĐ-11 (bao-CR-312, P1).

Mọi cột mang nghĩa *nguồn · loại người làm · nhóm hành động* đều lưu `SMALLINT`
và so với hằng số ở đây; tiếng Việt chỉ sống trong các `*_LABELS` bên dưới.

⚠️ Đừng nhầm với `action` của `tab_audit_log`: cột đó vẫn là **mã chuỗi**
(`create`, `approve`, `login_failed`…) vì 213 lời gọi `record(...)` đang truyền
chuỗi, đổi sang số là sửa hết 213 chỗ mà chẳng được gì. Tập chuỗi đó nay ràng
bằng `ACTION_CATALOG` ở **`core/action_catalog.py`** (NT-4, bao-CR-358) — cùng
với nhãn và nhóm của từng mã. Cái ở đây là `action_group` — **nhóm** của hành
động, thứ dùng để lọc và để cảnh báo, và nó là số.

⚠️ **Tệp này cố ý KHÔNG import `action_catalog`** (chiều import là
`action_catalog` → `logging_codes`, một chiều). Cần `group_of_action` thì lấy ở
`action_catalog`, đừng thêm re-export ở đây kẻo vòng import.

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

#  ⚠️ BẢNG `ACTION_GROUP_BY_ACTION` TỪNG NẰM Ở ĐÂY — đã dời sang
#  `core/action_catalog.py` (bao-CR-358 / NT-4). Lý do dời: nhóm và nhãn của
#  cùng một mã hành động khai ở hai tệp không biết nhau, nên thêm mã mới thì
#  quên một trong hai là chuyện thường — đã quên thật, `closed` mất nhóm ở 36
#  dòng prod và 9 mã mất nhãn ở 971 dòng. Nay một dòng khai đủ ba thứ.
#
#  Dùng `from app.core.action_catalog import group_of_action` — KHÔNG import
#  ngược vào tệp này (xem chú thích đầu tệp).
