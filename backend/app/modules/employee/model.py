from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, AuditMixin
from app.core.status_codes import EMPLOYEE_STATUS


class Employee(Base, AuditMixin):
    """Nhân viên — thuộc công ty & phòng ban; gắn với tài khoản qua tab_user.employee_id."""

    __tablename__ = "tab_employee"

    code: Mapped[str] = mapped_column(String(25), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(25), default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    position: Mapped[str] = mapped_column(String(100), default="")   # Vị trí / Chức vụ — CHỈ là chữ
    # CR-022: KHÔNG dùng nữa. Trước đây ô "Vai trò" ở màn Nhân sự tự cấp quyền cho tài khoản; nay
    # quyền chỉ gán ở "Phân quyền tài khoản" (tab_user_role). Cột giữ lại để không mất dữ liệu cũ.
    role_name: Mapped[str] = mapped_column(String(100), default="")
    # B-03: lưu MÃ tiếng Anh (`app/core/status_codes.EMPLOYEE_STATUS`), không lưu chữ tiếng Việt.
    # Nhãn hiển thị đi kèm ở `status_label` bên dưới.
    status: Mapped[str] = mapped_column(String(50), default="official")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    department = relationship(
        "Department",
        primaryjoin="foreign(Employee.department_id) == Department.id",
        uselist=False,
        viewonly=True
    )

    # Tài khoản đăng nhập gắn với nhân sự (nếu đã được cấp). Ảnh đại diện chỉ lưu MỘT chỗ
    # là tab_user.avatar — nhân sự đọc ké qua đây để khỏi có 2 nguồn dữ liệu lệch nhau.
    user = relationship(
        "User",
        primaryjoin="foreign(User.employee_id) == Employee.id",
        uselist=False,
        viewonly=True
    )

    @property
    def department_name(self) -> str | None:
        return self.department.name if self.department else None

    @property
    def manager_name(self) -> str | None:
        return self.department.manager_name if self.department else None

    @property
    def user_id(self) -> int:
        return self.user.id if self.user else 0

    @property
    def avatar(self) -> str:
        return (self.user.avatar or "") if self.user else ""

    @property
    def status_label(self) -> str:
        """Nhãn tiếng Việt của `status` (B-03).

        Mã lạ -> trả rỗng chứ KHÔNG trả lại chính mã: giao diện đã có sẵn nhánh lùi
        `status_label || status`, còn ở đây trả rỗng thì nhìn dữ liệu là biết ngay dòng nào
        chưa chạy migration. Cột này cũng là cột XUẤT CSV (xem controller) nên đừng bỏ.
        """
        return EMPLOYEE_STATUS.label_of(self.status)
