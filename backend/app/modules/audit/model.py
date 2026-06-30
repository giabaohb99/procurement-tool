from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class AuditLog(Base, AuditMixin):
    """Nhật ký thao tác: ai (created_by) làm gì (action) trên đối tượng nào, lúc nào (created_at)."""

    __tablename__ = "tab_audit_log"

    entity: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, index=True)
    action: Mapped[str] = mapped_column(String(20))  # create | update | delete
    message: Mapped[str] = mapped_column(Text, default="")
