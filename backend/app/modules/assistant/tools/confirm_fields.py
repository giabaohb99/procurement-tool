"""Hỏi lại cho ĐỦ trước khi soạn nháp (đại ca 09/10/2026: «có những trường cần thiết nhưng nó không hỏi lại, xác nhận lại
để đủ thông tin hơn»).

Ca thật: «tạo đơn nghỉ việc vào thứ 2 tuần sau» → bot soạn luôn loại «Phép năm» (tool tự lấy mặc định) và lý do «Việc
cá nhân» (model tự bịa). Ba lớp chặn:

  1. Ô QUAN TRỌNG còn trống → tool không tự lấy mặc định nữa mà trả `need_info` (kèm lựa chọn nếu có) để Trợ lý hỏi MỘT
     tin gồm mọi ý còn thiếu.
  2. Ô do model điền nhưng NGƯỜI DÙNG CHƯA NÓI → coi như trống. Trợ lý chèn câu chữ gần nhất của người dùng vào tham số
     ẩn `_user_text` (`assistant.service`), tool so: giá trị phải xuất hiện (cụm hai chữ, bỏ dấu) trong lời người dùng.
  3. Ô có mặc định hợp lý (nghỉ cả ngày, chưa đặt hạn) → vẫn soạn, nhưng ghi vào `assumptions` để thẻ nháp hiện «Em
     hiểu là: …» cho người dùng xác nhận khi nhắn «tạo».

Người dùng đã được hỏi mà bảo bỏ qua → Trợ lý gọi lại với `asked_fields` chứa ô đó, tool không hỏi lần hai.
"""
from __future__ import annotations

import re

USER_TEXT_ARG = "_user_text"
ASKED_ARG = "asked_fields"
#  Các tool soạn nháp nhận câu chữ của người dùng (Trợ lý chèn vào trước khi chạy tool).
TOOLS_WITH_USER_TEXT = frozenset({"draft_leave_request", "draft_purchase_request", "draft_survey_request",
                                  "draft_work_task"})
USER_TEXT_MAX = 3000

ASKED_PARAM = {
    "type": "array", "items": {"type": "string"},
    "description": ("Tên các ô ĐÃ hỏi người dùng ở lượt trước mà họ bảo bỏ qua / chưa có — tool không hỏi lại các ô "
                    "này. Lần gọi đầu để trống."),
}


def _fold(text: str) -> str:
    from app.modules.assistant.glossary import fold

    return fold(text or "")


#  Gọi tool KHÔNG qua hội thoại (không có lời người dùng — bài kiểm, gọi thẳng) thì không có ai để hỏi lại: coi như mọi ô
#  đã hỏi, tool giữ hành vi cũ (mặc định + nhắc trong `reminder`).
ALL_ASKED = frozenset({"reason", "leave_type", "purpose", "qty", "need_date", "warehouse", "assignees", "due_date"})


def take_context(args: dict) -> tuple[str, set[str]]:
    """Bóc tham số ẩn khỏi `args` (để không lọt vào bản nháp). Trả (lời người dùng đã bỏ dấu, các ô đã hỏi)."""
    user_text = _fold(str(args.pop(USER_TEXT_ARG, "") or ""))
    asked = {str(x).strip() for x in (args.get(ASKED_ARG) or []) if str(x).strip()}
    if not user_text:
        asked |= ALL_ASKED
    return user_text, asked


def stated(user_text: str, value: str) -> bool:
    """Giá trị `value` có thật sự từ lời người dùng không. Không có lời người dùng (gọi tool trực tiếp) → tin model.
    Một chữ: chữ đó (≥ 3 ký tự) phải có trong lời. Nhiều chữ: ít nhất một cụm hai chữ liền nhau phải có."""
    if not user_text:
        return True
    words = [w for w in _fold(value).split() if w]
    if not words:
        return False
    hay = f" {user_text} "
    if len(words) == 1:
        return len(words[0]) >= 3 and f" {words[0]} " in hay
    return any(f" {a} {b} " in hay for a, b in zip(words, words[1:]))


def mentions(user_text: str, *hints: str) -> bool:
    """Lời người dùng có nhắc một trong các gợi ý (đã bỏ dấu) không."""
    if not user_text:
        return True
    return any(re.search(rf"(?<!\w){re.escape(_fold(h))}(?!\w)", user_text) for h in hints)


def need(items: list[dict]) -> dict:
    """Kết quả «chưa đủ thông tin»: Trợ lý hỏi MỘT tin gồm mọi ý, đánh số, đưa lựa chọn nếu có."""
    return {
        "need_info": items,
        "note": ("CHƯA soạn nháp. Hỏi người dùng MỘT tin gồm các ý dưới đây (đánh số, kèm lựa chọn nếu có). KHÔNG tự "
                 "điền thay họ. Họ trả lời xong thì gọi lại tool với đủ thông tin; ý nào họ bảo bỏ qua thì đưa tên ô vào "
                 f"`{ASKED_ARG}`."),
    }


def recent_user_text(message: str, history: list | None) -> str:
    """Câu hiện tại + vài câu gần nhất của người dùng (người dùng hay trả lời từng ý ở các tin sau)."""
    parts = [str(h.get("content") or "") for h in (history or [])[-6:]
             if isinstance(h, dict) and h.get("role") == "user" and isinstance(h.get("content"), str)]
    parts.append(str(message or ""))
    return "\n".join(parts)[-USER_TEXT_MAX:]
