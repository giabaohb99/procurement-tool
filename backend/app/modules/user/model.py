from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class User(Base, AuditMixin):
    __tablename__ = "tab_user"

    email: Mapped[str] = mapped_column(String(255), default="", index=True)
    google_sub: Mapped[str] = mapped_column(String(100), default="")
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    avatar: Mapped[str] = mapped_column(String(500), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserRole(Base, AuditMixin):
    __tablename__ = "tab_user_role"

    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, index=True)


class UserScope(Base, AuditMixin):
    """Phạm vi dữ liệu theo NGƯỜI DÙNG (Lớp B). Mỗi dòng = 1 giá trị được cấp/loại trừ.

    entity = ''  → áp CHUNG cho mọi chức năng (phạm vi tổng);
    entity = 'purchase_request'... → override riêng cho chức năng đó.
    dim = company (value = company_id) | department (value = tên phòng ban).
    is_exclude = True → loại trừ giá trị này.
    """

    __tablename__ = "tab_user_scope"

    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)  # phạm vi theo từng vai trò của user
    entity: Mapped[str] = mapped_column(String(50), default="", index=True)  # dự phòng override theo chức năng
    dim: Mapped[str] = mapped_column(String(20), default="company")          # company | department | employee
    value: Mapped[str] = mapped_column(String(100), default="")
    is_exclude: Mapped[bool] = mapped_column(Boolean, default=False)
