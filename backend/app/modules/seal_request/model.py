from sqlalchemy import BigInteger, Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class SealType(Base, AuditMixin):
    """Loại con dấu (Master data)."""
    __tablename__ = "tab_seal_type"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SealRequest(Base, AuditMixin):
    """Yêu cầu đóng dấu (Duyệt dấu)."""
    __tablename__ = "tab_seal_request"

    __table_args__ = (Index("ix_seal_created_by", "created_by"),)

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    purpose: Mapped[str] = mapped_column(Text, default="")
    
    seal_type_id: Mapped[int] = mapped_column(BigInteger, index=True)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    
    # Nguoi tao (Luu log)
    requester: Mapped[str] = mapped_column(String(255), default="")
    requester_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    
    # Submitter choice
    first_approver_id: Mapped[int] = mapped_column(BigInteger, default=0)
    
    status: Mapped[str] = mapped_column(String(30), default="draft")
    note: Mapped[str] = mapped_column(Text, default="")
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
