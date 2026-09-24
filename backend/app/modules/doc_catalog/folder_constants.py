"""Hằng số của CÂY THƯ MỤC VĂN BẢN (R2/QĐ-11 — SMALLINT + IntEnum).

Thiết kế đầy đủ: `frontend-v2/plans/260923-1000-van-ban-thu-muc-nguoi-duyet/phase-03-backend-cay-thu-muc.md`.
"""
from enum import IntEnum

#  Sâu tối đa của cây, TÍNH CẢ gốc (gốc = 1). 7 chứ không phải 6 từ
#  24/09/2026: thư mục pháp nhân dời vào trong thư mục nhóm «Công ty», tầng nhóm
#  đó không được lấy mất một cấp của người dùng.
MAX_DEPTH = 7

#  Tên thư mục nhóm chứa mọi thư mục pháp nhân (`FolderKind.COMPANY_GROUP`).
COMPANY_GROUP_NAME = "Công ty"


class FolderKind(IntEnum):
    """Loại thư mục. Pháp nhân là GỐC tự sinh; thư mục thường do người dùng tạo."""

    COMPANY = 1   # thư mục pháp nhân — mỗi Company một dòng, tên lấy từ Company
    NORMAL = 2    # thư mục thường, nằm dưới một nhánh pháp nhân
    #  Thư mục NHÓM «Công ty» ở gốc cây (24/09/2026) — chứa mọi thư mục pháp
    #  nhân. Đúng MỘT dòng, `company_id = 0`, AI thấy cây cũng thấy nó (chỉ là
    #  lối vào), không xóa/chuyển được.
    COMPANY_GROUP = 3


class FolderStatus(IntEnum):
    ACTIVE = 1
    ARCHIVED = 2


FOLDER_KIND_LABELS = {
    FolderKind.COMPANY: "Thư mục pháp nhân",
    FolderKind.NORMAL: "Thư mục",
    FolderKind.COMPANY_GROUP: "Nhóm thư mục công ty",
}

FOLDER_STATUS_LABELS = {
    FolderStatus.ACTIVE: "Đang dùng",
    FolderStatus.ARCHIVED: "Ngừng dùng",
}


class FolderAccessLevel(IntEnum):
    """Mức quyền hiệu lực trên một thư mục — dùng ở phase 04 (ACL thư mục).

    Khai SỚM ở đây (phase 03) vì cột `DocFolder.default_access` đã ghi xuống DB
    từ phase này; phase 04 xây `folder_access_service.effective_levels()` đọc
    đúng bốn mức này, không định nghĩa lại.

    `PRIVATE = 0` là mức ĐẶT TƯỜNG MINH để KHÓA một nhánh con với người chỉ có
    quyền theo pháp nhân (khác với `default_access = NULL` nghĩa là "chưa khai,
    kế thừa từ tổ tiên gần nhất").
    """

    PRIVATE = 0
    VIEW = 1
    CONTRIBUTE = 2
    MANAGE = 3


FOLDER_ACCESS_LEVEL_LABELS = {
    FolderAccessLevel.PRIVATE: "Riêng tư",
    FolderAccessLevel.VIEW: "Xem",
    FolderAccessLevel.CONTRIBUTE: "Đóng góp",
    FolderAccessLevel.MANAGE: "Quản lý",
}

#  Mức nền của THƯ MỤC PHÁP NHÂN lúc tự sinh (`folder_service.ensure_company_roots`).
#  Phase 04 §"Mức nền": "gốc pháp nhân mặc định 2 Đóng góp".
COMPANY_ROOT_DEFAULT_ACCESS = FolderAccessLevel.CONTRIBUTE

#  Chế độ gắn văn bản hàng loạt — `folder_link_service.move_documents`.
LINK_MODE_ADD = "add"
LINK_MODE_REPLACE = "replace"
LINK_MODES = (LINK_MODE_ADD, LINK_MODE_REPLACE)
