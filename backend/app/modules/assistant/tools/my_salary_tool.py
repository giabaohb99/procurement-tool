"""Tool LƯƠNG CỦA TÔI — `my_salary` (duoc-CR-757).

Luật chủ dự án chốt (tuyệt đối): trợ lý không bao giờ nói lương của người khác; chỉ chính nhân sự hỏi lương của CHÍNH
MÌNH mới được trả, và chỉ trong cuộc trò chuyện RIÊNG (`salary_privacy.is_private_conversation`). Tool này là đường DUY
NHẤT trợ lý đọc ô lương / phụ cấp trên hồ sơ:

* Không có tham số chọn người — luôn là hồ sơ gắn với tài khoản đang hỏi (`user.employee_id`, khác 0).
* Số đi qua đúng một cửa che lương của phân hệ Nhân sự: `employee.sensitive.mask` (về 0 nếu không phải chính chủ).
* Kênh chung (nhóm Telegram / Zalo, cổng MCP của ứng dụng AI bên ngoài, kênh không rõ) → từ chối, dặn hỏi ở chat riêng.
* Không đăng ký ở cổng MCP (`mcp.HIDDEN`): MCP không bao giờ là kênh riêng nên tool vô dụng ở đó.
"""
from app.modules.employee.model import Employee
from app.modules.employee.sensitive import SALARY_FIELDS, is_self, mask

from .base import ToolContext, ToolSpec
from .salary_privacy import POLICY_SENTENCE, PRIVATE_ONLY_SENTENCE, is_private_conversation

_DESC = (
    "LƯƠNG và PHỤ CẤP hằng tháng trên hồ sơ của CHÍNH người hỏi (đồng / tháng). Chỉ gọi khi người dùng hỏi lương của "
    "CHÍNH HỌ ('lương của tôi bao nhiêu', 'phụ cấp của em'). Không có tham số chọn người: hỏi lương NGƯỜI KHÁC (kể cả "
    "người hỏi là quản trị, Nhân sự, giám đốc) thì KHÔNG gọi công cụ nào, trả lời đúng câu: '" + POLICY_SENTENCE + "' — "
    "không ước tính từ tiền thanh toán nghỉ phép, YCTT hay bất kỳ số nào khác. Ở nhóm chat / kênh chung công cụ trả từ "
    "chối: nói lại đúng lời nhắc của nó (hỏi trong chat riêng)."
)


def _run(ctx: ToolContext, args: dict) -> dict:
    emp_id = int(getattr(ctx.user, "employee_id", 0) or 0)
    if not emp_id:
        return {"error": "Tài khoản của bạn chưa gắn hồ sơ nhân sự nên không có ô lương để xem."}
    if not is_private_conversation(ctx):
        return {"denied": True, "reason": PRIVATE_ONLY_SENTENCE}
    emp = ctx.db.get(Employee, emp_id)   # hồ sơ của CHÍNH người hỏi — không đọc hồ sơ ai khác
    if emp is None:
        return {"error": "Không tìm thấy hồ sơ nhân sự gắn với tài khoản của bạn."}
    data = {"id": emp.id, **{f: getattr(emp, f, 0) for f in SALARY_FIELDS}}
    mask(data, allowed=True, profile=ctx.profile)   # một cửa che lương: về 0 nếu không phải chính chủ
    if not is_self(ctx.profile, emp.id):
        return {"denied": True, "reason": POLICY_SENTENCE}
    return {
        "full_name": emp.full_name, "salary_set": bool(getattr(emp, "salary_set", False)),
        "salary_monthly": int(data.get("salary_monthly") or 0),
        "allowance_monthly": int(data.get("allowance_monthly") or 0),
        "currency": "VND", "url": "/me",
        "note": ("Số trên hồ sơ của bạn (đồng / tháng). Chỉ nói cho chính bạn trong chat riêng; salary_set=false là "
                 "Nhân sự chưa nhập."),
    }


MY_SALARY_SPEC = ToolSpec(
    name="my_salary",
    description=_DESC,
    parameters={"type": "object", "properties": {}},
    handler=_run,
)
