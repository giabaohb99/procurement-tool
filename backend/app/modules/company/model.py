from sqlalchemy import BigInteger, Boolean, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, AuditMixin


class Company(Base, AuditMixin):
    """Pháp nhân nhận hóa đơn (có phân cấp qua `parent`)."""

    __tablename__ = "tab_company"

    code: Mapped[str] = mapped_column(String(25), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    #  MÃ ĐI VÀO SỐ HIỆU VĂN BẢN (`DEGO` trong `DEGO-QC-012`) — chỉ chữ và số.
    #  Cố ý KHÔNG dùng `code`: `code` là mã hiển thị, chứa được dấu tiếng Việt và
    #  khoảng trắng, ghép vào số hiệu thì ra `Cty Dego-QC-012` (`van-thu` chỗ dễ
    #  sai số 1). Đã cấp số rồi thì không đổi được nữa.
    issue_code: Mapped[str] = mapped_column(String(20), default="", index=True)
    #  Tên gọi tắt dùng trên thể thức văn bản, vd "DEGO Holding".
    short_name: Mapped[str] = mapped_column(String(100), default="")
    #  1 Tập đoàn · 2 công ty thành viên · 3 đơn vị trực thuộc.
    level: Mapped[int] = mapped_column(SmallInteger, default=2)
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
