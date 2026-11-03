"""PHẠM VI của phân bổ chính sách (duoc-CR-717, review H2 + M1).

Chọn ứng viên theo phạm vi XEM hồ sơ (`employee.read`, cùng luật "Cấp quỹ") NHƯNG mỗi người còn phải nằm trong phạm vi
GHI quỹ phép (`leave_balance.write`) — thứ thực sự bị đổi. Nếu không, vai trò giữ `employee.read = all` ở chỗ khác
phân bổ được cho công ty không thuộc phần của mình rồi chính họ không thấy / sửa / xóa được lượt vừa tạo.

Điều kiện phạm vi ghi quỹ được dựng THẲNG trên cột hồ sơ (không tạo dòng nào): `SCOPE_FIELDS["leave_balance"]` chỉ khai
`company` → `company_id` và `self` → `employee_id`, nên "bảng giả" có hai cột đó là đủ — và đúng bằng điều kiện
`get_scoped(LeavePolicyAssignment, "leave_balance", …, "write")` sẽ áp lên phân bổ sau này (`company_id` của phân bổ
chép từ hồ sơ lúc tạo). Xem `test_phan_bo_pham_vi_ghi_khop_get_scoped`.
"""
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.scoping import apply_scope, scope_condition
from app.modules.employee.model import Employee

SCOPE_ENTITY = "leave_balance"


def writable_employee_query(db: Session, user):
    """Query `Employee` trong phạm vi xem hồ sơ VÀ phạm vi ghi quỹ phép của người bấm."""
    profile = get_perm_profile(db, user)
    query = apply_scope(db.query(Employee), Employee, "employee", user, profile)
    stand_in = SimpleNamespace(company_id=Employee.company_id, employee_id=Employee.id)
    cond = scope_condition(stand_in, SCOPE_ENTITY, user, profile, "write")
    return query if cond is None else query.filter(cond)


def is_own_employee(user, employee_id: int) -> bool:
    """`employee_id` là hồ sơ của chính người bấm? (`0` = tài khoản chưa gắn hồ sơ → không bao giờ trùng.)"""
    own = getattr(user, "employee_id", 0) or 0
    return bool(own) and own == employee_id
