"""QUY ĐỊNH HỎI VÀ LÀM của bot — nguồn DUY NHẤT (ai-CR-073). Bản dễ đọc: `doc/agent-hub/09-quy-dinh-hoi-va-lam.md`.

Đại ca chốt 05/10/2026: *"quy trình có hết rồi cần chi hỏi quá nhiều… làm cái file quy định để mọi thứ ổn định"*.
Mọi chỗ trong bot quyết «làm luôn hay hỏi» phải đọc từ đây, không tự đặt luật riêng. Tệp nằm trong danh sách cấm
của bot code (V-05): bot không tự nới luật của mình.

Ba mức:
  ACT     — làm luôn, xong báo.
  CONFIRM — hỏi ĐÚNG MỘT lần («đúng» / «thôi») bằng thẻ tiếng Việt nói rõ sẽ đổi gì; không hỏi thêm câu nào.
  REFUSE  — không làm, nói lý do một câu.
"""
from __future__ import annotations

ACT = "act"
CONFIRM = "confirm"
REFUSE = "refuse"

#  Thao tác trên máy chủ (V-03). Khóa = (đọc/sửa, môi trường).
OPS_RULES = {
    ("read", "dev"): ACT,          # xem dev: tự do
    ("read", "preview"): ACT,
    ("read", "prod"): CONFIRM,     # xem prod: một chữ «đúng»
    ("write", "dev"): CONFIRM,     # sửa dev: «đúng» + sao lưu trước + nhật ký + hoàn tác
    ("write", "preview"): CONFIRM,
    ("write", "prod"): CONFIRM,    # sửa prod: «đúng» (+ OTP khi làm V-04)
}

#  Sửa dữ liệu bằng lời (ai-CR-073): bước TRA để soạn lệnh là đọc — làm luôn, kể cả trên prod, vì chính câu nhờ
#  sửa của đại ca đã là lời cho phép đọc phần cần sửa. Bước GHI luôn CONFIRM.
DATA_PLAN_READ = ACT
#  Trần số dòng một lệnh sửa dữ liệu được đụng. Quá trần = REFUSE, đại ca chia nhỏ hoặc giao thành việc sửa mã.
DATA_MAX_ROWS = 500
#  Bảng bot KHÔNG sửa bằng lệnh dữ liệu, dù đại ca nhờ: tài khoản / phân quyền / nhật ký / sổ của chính bot.
#  Mấy thứ này đã có màn hình hoặc đường riêng có kiểm quyền; sửa thẳng là lách cổng.
DATA_DENY_TABLE_PREFIXES = (
    "tab_user", "tab_role", "tab_permission", "tab_perm", "tab_report_access", "tab_login", "tab_session",
    "tab_setting", "tab_audit", "tab_change_log", "tab_request_log", "tab_system_log", "tab_agent_",
    "alembic_version", "tab_doc_folder_access",
)

#  Luật chung cho câu chữ của bot trên Telegram (chèn vào lời nhắc của Trợ lý AI).
ASSISTANT_RULES = (
    "Quy định hỏi và làm (đại ca chốt 05/10/2026): yêu cầu đủ rõ để làm thì LÀM LUÔN, không hỏi lại. "
    "Chỉ hỏi khi thiếu một thông tin KHÔNG suy ra được từ dữ liệu, tài liệu hay mạch hội thoại — và hỏi tối đa MỘT câu, "
    "gom mọi điều cần hỏi vào câu đó. Mơ hồ nhẹ thì chọn cách hợp lý nhất, làm, và nói rõ giả định trong câu trả lời. "
    "KHÔNG bao giờ bảo người dùng tự gõ câu lệnh SQL, lệnh máy chủ hay mã nguồn. "
    "Chỉ báo «đã làm» khi công cụ trả thành công; không có công cụ đúng việc thì nói thẳng là chưa làm được, KHÔNG dùng "
    "một công cụ khác làm thay (vd «dời lịch» không được tạo thêm lịch mới)."
)


def ops_rule(kind: str, env_kind: str) -> str:
    return OPS_RULES.get((kind, env_kind), CONFIRM)


def data_table_denied(table: str) -> bool:
    t = (table or "").lower()
    return any(t.startswith(p) for p in DATA_DENY_TABLE_PREFIXES)
