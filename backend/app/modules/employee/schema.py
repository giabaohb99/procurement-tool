from datetime import datetime
from pydantic import BaseModel, field_validator

from app.core.status_codes import EMPLOYEE_STATUS


class EmployeeBase(BaseModel):
    code: str = ""
    full_name: str
    email: str = ""
    phone: str = ""
    company_id: int = 0
    department_id: int = 0
    position: str = ""
    role_name: str = ""
    status: str = "official"      # B-03: MÃ, xem `EMPLOYEE_STATUS`
    is_active: bool = True


class EmployeeCreate(EmployeeBase):
    # Chặn ở CẢ Create lẫn Update. Chỉ chặn một bên thì màn còn lại vẫn ghi chữ tự do vào
    # lại cột, và cột lại đẻ giá trị lạ đúng như trước B-03.
    #
    # Cố ý KHÔNG nhận "Chính thức" rồi âm thầm đổi thành `official`: dịch hộ thì bản giao
    # diện chưa vá vẫn chạy được và sẽ không ai vá nữa. Thà 422 ngay lúc deploy.
    # (Đường CSV nhập từ tệp người dùng là ngoại lệ có chủ đích — nó dịch, xem controller.)
    #
    # `allow_blank=False`: khác `legal_type` của NCC (rỗng = chưa chọn, và là tình trạng của
    # gần hết dữ liệu thật), nhân sự thì LUÔN có tình trạng làm việc — rỗng không mang nghĩa gì.
    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        return EMPLOYEE_STATUS.validate(v, allow_blank=False)


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company_id: int | None = None
    department_id: int | None = None
    position: str | None = None
    role_name: str | None = None
    status: str | None = None
    is_active: bool | None = None

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str | None) -> str | None:
        # `None` = không gửi trường này (PATCH), cho qua. Nhưng `""` là CÓ gửi và gửi rỗng:
        # hồ sơ mang giá trị cũ ngoài bộ mã thì ô chọn không khớp mục nào, để rỗng lọt qua là
        # bấm lưu xong xóa trắng trạng thái thật của một con người mà không ai biết.
        if v is None:
            return None
        return EMPLOYEE_STATUS.validate(v, allow_blank=False)


class EmployeeOut(EmployeeBase):
    id: int
    code: str
    # B-03: nhãn tiếng Việt gửi kèm để giao diện khỏi khai lại bảng mã bằng tay.
    # Đọc từ `Employee.status_label` (property trên model).
    status_label: str = ""
    department_name: str | None = None
    #  Pháp nhân của nhân sự. Đọc từ property `Employee.company_name`; danh sách
    #  phải `selectinload(Employee.company)` — xem `service.list_employees` — nếu
    #  không mỗi dòng tự lazy-load thành N+1.
    company_name: str | None = None
    manager_name: str | None = None
    created_at: datetime | None = None
    # Ảnh đại diện lấy từ tài khoản đăng nhập (tab_user.avatar). Danh sách phải
    # selectinload(Employee.user) — xem service.list_employees — để không thành N+1.
    avatar: str = ""
    # Ảnh chữ ký cá nhân, cũng đọc từ tài khoản đăng nhập (tab_user.signature).
    signature: str = ""
    model_config = {"from_attributes": True}


class EmployeeDetailOut(EmployeeOut):
    """Bản dùng cho MÀN CHI TIẾT — kèm id tài khoản đăng nhập để biết đã cấp tài khoản chưa."""

    user_id: int = 0
