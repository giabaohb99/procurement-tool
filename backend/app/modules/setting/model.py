from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Setting(Base, AuditMixin):
    """Cấu hình hệ thống dạng key-value (KHÔNG chứa secret). Secret nằm ở .env."""

    __tablename__ = "tab_setting"

    skey: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    svalue: Mapped[str] = mapped_column(Text, default="")
