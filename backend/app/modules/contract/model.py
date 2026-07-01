from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Contract(Base, AuditMixin):
    """Hợp đồng tổng quát — dùng cho nhiều đối tượng (Nhà cung cấp, Khách hàng…).

    Đơn giản: chỉ để biết đối tượng đã ký với công ty nào + đính kèm file HĐ thật.
    """

    __tablename__ = "tab_contract"

    code: Mapped[str] = mapped_column(String(50), default="")           # HD00001
    party_type: Mapped[str] = mapped_column(String(30), default="Nhà cung cấp")  # Nhà cung cấp | Khách hàng | Khác
    party_code: Mapped[str] = mapped_column(String(50), default="", index=True)  # mã đối tượng (vd mã NCC)
    party_name: Mapped[str] = mapped_column(String(255), default="")    # tên đối tượng
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)       # công ty (pháp nhân mình) ký HĐ
    title: Mapped[str] = mapped_column(String(255), default="")         # tên/trích yếu HĐ
    contract_type: Mapped[str] = mapped_column(String(50), default="")  # Mua bán/Nguyên tắc/Vận chuyển…
    start_date: Mapped[str] = mapped_column(String(10), default="")
    end_date: Mapped[str] = mapped_column(String(10), default="", index=True)
    signed: Mapped[bool] = mapped_column(Boolean, default=False)        # đã ký
    status: Mapped[str] = mapped_column(String(30), default="Hiệu lực")  # Hiệu lực/Hết hạn/Thanh lý
    note: Mapped[str] = mapped_column(Text, default="")
