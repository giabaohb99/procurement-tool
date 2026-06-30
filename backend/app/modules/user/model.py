from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class User(Base, AuditMixin):
    __tablename__ = "tab_user"

    email: Mapped[str] = mapped_column(String(255), default="", index=True)
    google_sub: Mapped[str] = mapped_column(String(100), default="")
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserRole(Base, AuditMixin):
    __tablename__ = "tab_user_role"

    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, index=True)
