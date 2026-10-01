from pydantic import BaseModel
from app.modules.employee.field_limits import Str255


class UserProvision(BaseModel):
    """Cấp tài khoản cho 1 nhân viên đã có."""

    employee_id: int
    email: Str255 = ""
    password: str
    role_ids: list[int] = []


class PasswordReset(BaseModel):
    new_password: str


class RoleAssign(BaseModel):
    role_ids: list[int]
    #  bao-CR-523: quản trị TỰ bỏ vai trò Quản trị hệ thống của chính mình phải gửi
    #  kèm cờ này = true. Thiếu cờ thì backend trả 409 kèm câu hỏi để giao diện
    #  hiện hộp xác nhận rồi gửi lại. Mọi trường hợp khác cờ này không có tác dụng.
    confirm_self_admin_removal: bool = False


class ActiveUpdate(BaseModel):
    is_active: bool


class NotifyEmailUpdate(BaseModel):
    """Bật/tắt email thông báo luồng duyệt của một tài khoản (bao-CR-349)."""

    notify_email: bool


class ScopeUpdate(BaseModel):
    """Phạm vi tổng theo user (Lớp B). Trống = không giới hạn chiều đó."""

    companies: list[int] = []
    departments: list[str] = []
    employees: list[int] = []
    exclude_companies: list[int] = []
    exclude_departments: list[str] = []
    exclude_employees: list[int] = []


class UserOut(BaseModel):
    id: int
    email: str
    employee_id: int
    is_active: bool
    notify_email: bool = True
    role_ids: list[int] = []
    model_config = {"from_attributes": True}
