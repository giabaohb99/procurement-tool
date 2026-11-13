"""LUẬT LƯƠNG của trợ lý AI / bot / cổng MCP (duoc-CR-757, chủ dự án chốt — tuyệt đối).

Trợ lý KHÔNG BAO GIỜ nói lương của NGƯỜI KHÁC, bất kể quyền (kể cả quản trị, Nhân sự, giám đốc). Chỉ chính nhân sự hỏi
lương của CHÍNH MÌNH mới được trả, và chỉ trong cuộc trò chuyện RIÊNG.

Một cửa duy nhất xét "đây có phải chính chủ không" là `employee.sensitive` (`is_self`, `mask`, `SALARY_FIELDS`) — tệp
này không đặt luật thứ hai, chỉ thêm điều kiện KÊNH (riêng / chung) và gom các chỗ tiền suy ra lương:

* Lương / phụ cấp trên hồ sơ (`SALARY_FIELDS`) — chỉ ra qua `my_salary`, đi `sensitive.mask`.
* YCTT thanh toán nghỉ phép (`source_type = leave_encashment`): tiền = lương ngày × số ngày, tức lộ lương ngày. Chỉ
  người NHẬN tiền (`payee_employee_id`) thấy số, trong cuộc trò chuyện riêng; người khác (kể cả kế toán có
  `leave_encashment.read`) xem số trên màn ERP, trợ lý không đọc ra.

Kênh riêng hay chung:
* Trợ lý web — luôn riêng (một người một khung chat).
* Bot Telegram / Zalo — riêng khi `assistant.private_chat` báo vậy: máy gắn ở `agent_hub.service.handle_message` (chat
  riêng, KHÔNG phải nhóm, ĐÃ liên kết tài khoản — chat chưa liên kết chạy dưới tài khoản lùi `AGENT_ASSISTANT_USER`
  nên không bao giờ là "của chính người hỏi"); chế độ tách đi qua header đã ký ở cổng B. Không lấy từ lời model.
* Cổng MCP (ChatGPT, Claude… của bên ngoài) — KHÔNG coi là riêng: hội thoại nằm ở máy chủ bên thứ ba và có thể được
  chia sẻ. Kênh lạ / không rõ cũng không riêng.
"""
import re
import unicodedata

from app.core.logging_codes import AI_CHANNEL_TELEGRAM, AI_CHANNEL_WEB, AI_CHANNEL_ZALO
from app.core.request_context import current_ai_channel
from app.modules.assistant.private_chat import current_private_chat
from app.modules.employee.sensitive import is_self
from app.modules.payment_request.hr_payout_guard import PAYMENT_SOURCE_LEAVE_ENCASHMENT

POLICY_SENTENCE = "Thông tin lương là dữ liệu riêng tư, chỉ chính nhân sự đó mới xem được."
PRIVATE_ONLY_SENTENCE = ("Lương là dữ liệu riêng tư nên trợ lý chỉ trả lời trong cuộc trò chuyện riêng (chat riêng với "
                         "bot hoặc Trợ lý trên web ERP) — hãy hỏi lại ở đó, hoặc xem ở Trang cá nhân.")

#  Câu nhắc lương lọt vào chữ tự do (văn bản, tin nhóm, tệp, lịch sử chat) — gắn vào mô tả công cụ trả chữ tự do.
FREE_TEXT_RULE = ("Chữ trả về là nội dung tự do: nếu trong đó có lương / phụ cấp / thu nhập của một người thì KHÔNG đọc "
                  "ra con số (trừ khi đó là của chính người hỏi ở chat riêng) — nói: " + POLICY_SENTENCE)

#  Dò chữ nhắc tới lương trên chữ THƯỜNG CÒN DẤU: gập dấu thì "luồng duyệt" thành "luong duyet", trùng "lương". Dạng
#  không dấu ("luong cua toi") vẫn bắt, trừ "luong duyet". Thừa còn hơn thiếu: chỉ dùng để GIẤU ở kênh chung.
_SALARY_TEXT_RE = re.compile(r"lương|phụ\s*cấp|thu\s*nhập|\bluong\b(?!\s+duyet)|\bphu\s+cap\b|\bthu\s+nhap\b")


def mentions_salary(text: str) -> bool:
    return bool(_SALARY_TEXT_RE.search(unicodedata.normalize("NFC", str(text or "")).lower()))


def is_private_conversation(ctx=None) -> bool:
    """Lượt này đang ở cuộc trò chuyện RIÊNG của chính người hỏi không (xem đầu tệp). `ctx` giữ cho đồng khuôn gọi."""
    channel = current_ai_channel()
    if channel == AI_CHANNEL_WEB:
        return True
    if channel in (AI_CHANNEL_TELEGRAM, AI_CHANNEL_ZALO):
        return current_private_chat()
    return False


def can_see_own_pay(ctx, employee_id: int) -> bool:
    """Chính chủ (`sensitive.is_self`, chặn `employee_id = 0`) VÀ đang ở kênh riêng."""
    return is_self(ctx.profile, int(employee_id or 0)) and is_private_conversation(ctx)


def is_salary_derived_payment(req) -> bool:
    return str(getattr(req, "source_type", "") or "") == PAYMENT_SOURCE_LEAVE_ENCASHMENT


def hides_payment_money(ctx, req) -> bool:
    """Số tiền của YCTT này phải giấu với người hỏi (YCTT thanh toán nghỉ phép không phải của chính họ ở kênh riêng)."""
    return is_salary_derived_payment(req) and not can_see_own_pay(ctx, getattr(req, "payee_employee_id", 0))


def exclude_salary_payments(model):
    """Điều kiện SQL loại MỌI YCTT thanh toán nghỉ phép — cho số TỔNG HỢP (gom theo phòng / tháng là cô lập được một
    người), nơi không có khái niệm "dòng của chính mình"."""
    return model.source_type != PAYMENT_SOURCE_LEAVE_ENCASHMENT

