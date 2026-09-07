from datetime import date, datetime
from pydantic import BaseModel, field_validator

from app.core.status_codes import EMPLOYEE_STATUS

#  Bí danh của `datetime.date` — cùng lý do với `schema.DateOnly` của Nghỉ phép:
#  lớp nào có trường tên là `date` thì tên đó che mất kiểu. Ở đây chưa có trường
#  nào tên vậy, nhưng giữ một tên rõ ràng cho các cột ngày thì đọc dễ hơn.
DateOnly = date


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

    #  ⚠️ QĐ-NP3 — hai cột này có trong bảng từ 03/09/2026 nhưng **không nằm
    #  trong schema nào cho tới 07/09/2026**, nên API không nhận cũng không trả:
    #  cả hai luật nghỉ phép dựa vào chúng đều im lặng không chạy.
    #
    #  · `hire_date` là mốc tính THÂM NIÊN. Rỗng thì `balance_service` coi là
    #    0 năm, tức mọi người mất phần ngày phép cộng thêm mà không ai báo.
    #  · `gender` để chặn loại nghỉ theo giới (thai sản). `0` = chưa khai, và
    #    chưa khai thì KHÔNG bị chặn — nên khi không ô nào khai được, chốt giới
    #    tính coi như không tồn tại.
    #
    #  Cả hai đều để trống được: hồ sơ cũ chưa ai nhập, và chặn thì cả công ty
    #  không sửa nổi hồ sơ cho tới khi Nhân sự nhập bù hàng trăm dòng (D-018).
    hire_date: DateOnly | None = None
    gender: int = 0

    @field_validator("gender", mode="before")
    @classmethod
    def _gender_none_is_unknown(cls, v):
        """`NULL` trong cột → `0` (chưa khai), đừng để nó nổ ở tầng đọc.

        Cột khai `default=0` nhưng đó là mặc định lúc INSERT: bản ghi dựng trong
        bộ nhớ mà chưa flush vẫn mang `None`, và dòng cũ có trước cột này cũng
        có thể `NULL`. Ném ở đây thì **cả màn danh sách nhân sự** trả 500 vì một
        ô chưa ai nhập — đắt hơn nhiều so với việc đọc nó thành «chưa khai».
        """
        return 0 if v is None else v


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

    @field_validator("gender")
    @classmethod
    def _check_gender(cls, v: int) -> int:
        if v not in (0, 1, 2):
            raise ValueError("Giới tính chỉ nhận 0 (chưa khai), 1 (nam) hoặc 2 (nữ)")
        return v


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
    #  `None` = không gửi (giữ nguyên). Muốn XÓA ngày vào làm thì gửi `null`
    #  tường minh — Pydantic phân biệt được hai thứ đó qua `exclude_unset`.
    hire_date: DateOnly | None = None
    gender: int | None = None

    @field_validator("gender")
    @classmethod
    def _check_gender(cls, v: int | None) -> int | None:
        """Chỉ nhận `0` chưa khai · `1` nam · `2` nữ — khớp `leave/constants.py`.

        Chặn ở đây chứ không để cột `SMALLINT` nhận bừa: giá trị lạ thì
        `check_gender` của nghỉ phép so `want != got` ra True và chặn nhầm loại
        nghỉ, mà không chỗ nào giải thích được vì sao.
        """
        if v is not None and v not in (0, 1, 2):
            raise ValueError("Giới tính chỉ nhận 0 (chưa khai), 1 (nam) hoặc 2 (nữ)")
        return v

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
    updated_at: datetime | None = None   # bao-CR-294 — cột "Ngày cập nhật" ở màn danh sách
    # Ảnh đại diện lấy từ tài khoản đăng nhập (tab_user.avatar). Danh sách phải
    # selectinload(Employee.user) — xem service.list_employees — để không thành N+1.
    avatar: str = ""
    # Ảnh chữ ký cá nhân, cũng đọc từ tài khoản đăng nhập (tab_user.signature).
    signature: str = ""
    model_config = {"from_attributes": True}


class EmployeeDetailOut(EmployeeOut):
    """Bản dùng cho MÀN CHI TIẾT — kèm id tài khoản đăng nhập để biết đã cấp tài khoản chưa."""

    user_id: int = 0
