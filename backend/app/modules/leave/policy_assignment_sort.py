"""Biểu thức SẮP XẾP tại server cho bảng Phân bổ chính sách nghỉ phép (duoc-CR-748).

Trước đây danh sách cố định `từ ngày giảm dần, id giảm dần` và tiêu đề cột không bấm được. Mỗi khóa dưới
đây xếp theo ĐÚNG thứ ô đang hiện, trên CẢ TẬP (đúng qua phân trang):

- `employee_name` ("Nhân sự"): HỌ TÊN nhân sự, không theo `employee_id` (thứ tự số vô nghĩa). Nhân sự đã
  xóa hồ sơ -> ô trống, xuống CUỐI.
- `policy_name` ("Chính sách"): TÊN gói chính sách, không theo `policy_id`.
- `effective_from` ("Từ ngày") / `effective_to` ("Đến ngày"): cột ngày thật. "Đến ngày" để trống nghĩa là
  KHÔNG THỜI HẠN và ô đó hiện chữ "Không thời hạn" chứ không phải một ngày; theo luật chung của duoc-CR-744
  (mọi ô trống xuống CUỐI cả hai chiều) nên phân bổ không thời hạn luôn nằm dưới cùng, không bị coi là ngày
  vô cực nằm đầu khi xếp giảm dần. Chọn như vậy để cột này cư xử y hệt mọi cột ngày khác của hệ thống.
- `state` ("Trạng thái"): DẪN XUẤT theo ngày hôm nay (`vn_today()`, giờ Việt Nam) — đúng quy tắc của
  `policy_assignment_plan.assignment_state`, dựng thành `CASE` để xếp được trên cả tập: 1 Sắp tới → 2 Đang
  hiệu lực → 3 Đã kết thúc (thứ tự dòng đời; cũng là thứ tự của `LeavePolicyAssignmentState`).
- `note` ("Ghi chú"): cột chữ thật, ô trống xuống CUỐI.
- Cột "Hạn mức năm nay" tính từ bảng quỹ phép ở tầng khác nên KHÔNG cho xếp (khóa lạ -> thứ tự mặc định).
- Khóa phụ luôn là `id` giảm dần.
"""
from datetime import date

from sqlalchemy import case, select
from sqlalchemy.orm import aliased

from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.modules.employee.model import Employee

from .constants import LeavePolicyAssignmentState as State
from .policy_model import LeavePolicy, LeavePolicyAssignment as A

#  Bí danh để câu con không tự "tương quan" nhầm với bảng nhân sự khác trong truy vấn ngoài.
_EMPLOYEE = aliased(Employee)


def build_state_rank(today: date):
    """Hạng trạng thái phân bổ tại ngày `today` — cùng quy tắc `assignment_state` (so từ ngày trước, đến ngày sau)."""
    return case(
        (A.effective_from > today, int(State.UPCOMING)),
        ((A.effective_to.is_not(None)) & (A.effective_to < today), int(State.ENDED)),
        else_=int(State.ACTIVE),
    )


def _spec(today: date) -> dict:
    """{khóa cột: (biểu thức, là cột chữ?)} — cột chữ thì chuỗi rỗng cũng là ô trống."""
    return {
        "employee_name": (select(_EMPLOYEE.full_name).where(_EMPLOYEE.id == A.employee_id)
                          .correlate(A).limit(1).scalar_subquery(), True),
        "policy_name": (select(LeavePolicy.name).where(LeavePolicy.id == A.policy_id)
                        .correlate(A).limit(1).scalar_subquery(), True),
        "effective_from": (A.effective_from, False),
        "effective_to": (A.effective_to, False),
        "state": (build_state_rank(today), False),
        "note": (A.note, True),
    }


def build_order_by(sort_by: str, sort_dir: str, today: date) -> list:
    """Danh sách ORDER BY (đã gồm khóa phụ `id`); khóa lạ / không chọn -> thứ tự mặc định cũ (không lỗi)."""
    spec = _spec(today).get((sort_by or "").strip())
    if spec is None:
        return [A.effective_from.desc(), A.id.desc()]
    expr, is_text = spec
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), A.id)
