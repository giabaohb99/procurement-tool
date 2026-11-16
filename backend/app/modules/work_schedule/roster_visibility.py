"""AI THẤY AI TRÊN LỊCH LÀM VIỆC (duoc-CR-761, chủ dự án chốt 16/11/2026) — MỘT chỗ duy nhất cho mọi đường đọc ca / lịch.

Dùng ở: lưới "Ai làm / ai nghỉ" (`roster_service`), danh sách ca `/api/work-shifts` (`shift_controller`) và công cụ trợ lý
`employee_work_shifts`. Ba bậc, theo quyền của người XEM (không theo bậc `employee.read` của họ):

* **Nhân sự** — có `work_schedule.write` (hoặc quản trị hệ thống): mọi người trong phạm vi đọc hồ sơ `employee` (như trước).
* **Trưởng phòng** — không có khóa trên nhưng có `work_schedule_personal.read`: người nằm trong phạm vi khóa đó (đo trên hồ
  sơ nhân sự đích, gồm phòng kiêm nhiệm và luật ô "Phòng ban được xem" cùng công ty) CỘNG chính mình.
* **Còn lại** — chỉ chính mình (`employee_id` của tài khoản; chưa gắn hồ sơ = không thấy ai).

Bộ lọc phòng / pháp nhân / mã người ở từng đường đọc vẫn AND thêm BÊN TRONG tập này, nên chọn người ngoài tập thì ra rỗng,
không lộ người đó có thật không.
"""
from sqlalchemy import false, or_

from app.core.auth import user_has_permission
from app.core.privilege_escalation import is_system_admin
from app.core.scoping import exclude_deleted, scope_condition
from app.modules.employee.model import Employee

from .assignment_access import PERSONAL_ENTITY, holds_hr_key


def visible_employee_condition(db, user, profile: dict):
    """Điều kiện SQL trên `Employee` của những người `user` được xem lịch / ca; `None` = không giới hạn."""
    if holds_hr_key(db, user, "write") or is_system_admin(db, user.id):
        return scope_condition(Employee, "employee", user, profile)
    own = int(profile.get("employee_id") or 0)   # 0 = chưa gắn hồ sơ → không bao giờ khớp ai (đừng so `== 0`)
    self_cond = (Employee.id == own) if own else false()
    if user_has_permission(db, user, PERSONAL_ENTITY, "read"):
        cond = scope_condition(Employee, PERSONAL_ENTITY, user, profile, "read")
        return None if cond is None else or_(cond, self_cond)
    return self_cond


def apply_visible_employees(query, db, user, profile: dict):
    """Gắn tập người xem được vào truy vấn trên `Employee` (đồng thời loại hồ sơ đã xóa mềm)."""
    cond = visible_employee_condition(db, user, profile)
    query = exclude_deleted(query, Employee)
    return query if cond is None else query.filter(cond)
