from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, AuditMixin


class Company(Base, AuditMixin):
    """Pháp nhân nhận hóa đơn (có phân cấp qua `parent`)."""

    __tablename__ = "tab_company"

    code: Mapped[str] = mapped_column(String(25), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    tax_code: Mapped[str] = mapped_column(String(25), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    invoice_email: Mapped[str] = mapped_column(String(255), default="")
    parent: Mapped[int] = mapped_column(BigInteger, default=0)  # 0 = gốc
    legal_representative_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    legal_rep_title: Mapped[str] = mapped_column(String(100), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationship to Employee for legal representative
    legal_rep = relationship(
        "Employee",
        primaryjoin="foreign(Company.legal_representative_id) == Employee.id",
        uselist=False,
        viewonly=True
    )

    @property
    def legal_rep_name(self) -> str | None:
        return self.legal_rep.full_name if self.legal_rep else None

    @property
    def export_tax_code(self) -> str:
        return f"'{self.tax_code}" if self.tax_code else ""
