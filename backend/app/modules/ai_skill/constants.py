"""Mã cố định của Kho skill AI — lưu SMALLINT, nhãn tiếng Việt chỉ ở tầng hiển thị (luật R2)."""
from enum import IntEnum

ENTITY = "ai_skill"


class SkillSetStatus(IntEnum):
    DRAFT = 1       # đang soạn — chưa lộ ra MCP
    ACTIVE = 2      # đang dùng
    ARCHIVED = 3    # lưu trữ — thôi phát, giữ lịch sử


SKILL_SET_STATUS_LABELS = {
    SkillSetStatus.DRAFT: "Nháp",
    SkillSetStatus.ACTIVE: "Đang dùng",
    SkillSetStatus.ARCHIVED: "Lưu trữ",
}


class SkillStatus(IntEnum):
    DRAFT = 1       # chưa xuất bản lần nào
    ACTIVE = 2      # có phiên bản hiện hành, đang phát
    ARCHIVED = 3


SKILL_STATUS_LABELS = {
    SkillStatus.DRAFT: "Nháp",
    SkillStatus.ACTIVE: "Đang dùng",
    SkillStatus.ARCHIVED: "Lưu trữ",
}


class SecurityLevel(IntEnum):
    """Mức bảo mật của BỘ skill — quyết định cổng MCP trả gì (doc 21 §4.5)."""
    OPEN = 1        # nội dung + tệp đi kèm
    PROTECTED = 2   # nội dung, KHÔNG trả tệp đi kèm
    LOCKED = 3      # chỉ tên + tóm tắt; nội dung chỉ bot / Trợ lý nội bộ đọc


SECURITY_LEVEL_LABELS = {
    SecurityLevel.OPEN: "Mở",
    SecurityLevel.PROTECTED: "Bảo vệ",
    SecurityLevel.LOCKED: "Khóa",
}


class AccessTarget(IntEnum):
    """Dòng quyền đọc gắn vào BỘ hay vào một SKILL lẻ (skill có dòng riêng thì thay quyền bộ — thu hẹp)."""
    SKILL_SET = 1
    SKILL = 2


ACCESS_TARGET_LABELS = {AccessTarget.SKILL_SET: "Bộ skill", AccessTarget.SKILL: "Skill"}

#  Chủ thể THÊM của kho skill, nối tiếp 1..4 của `core/subject_match.py` (người · phòng ban · pháp nhân · vai trò).
#  Khai riêng ở đây (không đụng `get_perm_profile` / `subject_match`) — đợt K1 giữ bán kính thay đổi nhỏ; khi văn bản /
#  thư mục cũng cần chủ thể chức vụ, cấp bậc thì dời lên `core/subject_match.py` một lần.
SUBJECT_POSITION = 5    # chức vụ (`tab_job_position.id`)
SUBJECT_JOB_LEVEL = 6   # cấp bậc (`tab_employee.job_level`, mã của JOB_LEVEL_LABELS)

#  Trần (khớp `String(n)` của model — SQLite không ép độ dài, chặn ở schema).
CODE_MAX = 50
NAME_MAX = 150
DESC_MAX = 500
SLUG_MAX = 100
TITLE_MAX = 200
SUMMARY_MAX = 500
NOTE_MAX = 500
FILE_PATH_MAX = 200
BODY_MAX_CHARS = 200_000            # nội dung SKILL.md
FILE_MAX_BYTES = 2 * 1024 * 1024    # mỗi tệp đính kèm
FILES_MAX_BYTES = 20 * 1024 * 1024  # tổng tệp đính kèm một skill
PACKAGE_MAX_BYTES = 8 * 1024 * 1024
PACKAGE_MAX_ENTRIES = 1000
FILE_PATH_MAX_DEPTH = 6
MAX_GRANT_SUBJECTS = 200
MAX_TREE_DEPTH = 6                  # cây phòng ban — chặn vòng lặp khi đi xuống phòng con

#  Tệp đính kèm CHỈ nhận văn bản — AI đọc chúng dạng chữ qua MCP.
TEXT_FILE_EXTS = (".md", ".markdown", ".txt", ".json", ".csv", ".tsv", ".yaml", ".yml", ".xml", ".html", ".htm")
