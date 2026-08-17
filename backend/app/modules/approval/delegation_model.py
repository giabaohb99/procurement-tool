"""ỦY QUYỀN CÓ THỜI HẠN (I12).

Hai ràng buộc, cả hai đều cố ý:

1. **`from_date` và `to_date` bắt buộc.** Ủy quyền vô thời hạn là thứ người ta
   khai một lần rồi quên, và ba năm sau vẫn còn người ký thay cho một người đã
   nghỉ việc. Bắt khai hạn thì nó tự hết.
2. **Cấm ủy quyền dây chuyền** — A ủy cho B thì B không ủy tiếp phần việc nhận
   từ A cho C. Chặn ở tầng dịch vụ (`delegation_service.resolve`), không phải ở
   đây: ràng buộc dữ liệu không nhìn thấy được chuỗi. Cho phép dây chuyền thì
   không ai truy được trách nhiệm cuối cùng thuộc về ai.
"""
from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class Delegation(Base, AuditMixin):
    __tablename__ = "tab_delegation"
    __table_args__ = (
        #  Tra "ai đang ủy quyền cho tôi" mỗi lần dựng màn Việc của tôi.
        Index("ix_delegation_to", "to_employee_id", "is_active"),
        Index("ix_delegation_from", "from_employee_id", "is_active"),
    )

    from_employee_id: Mapped[int] = mapped_column(BigInteger)
    to_employee_id: Mapped[int] = mapped_column(BigInteger)

    #  Bỏ trống = ủy quyền cho MỌI loại chứng từ. Có giá trị = chỉ loại đó —
    #  ủy quyền ký văn bản không có nghĩa là ủy quyền duyệt chi tiền.
    entity: Mapped[str] = mapped_column(String(50), default="")

    from_date: Mapped[date] = mapped_column(Date)
    to_date: Mapped[date] = mapped_column(Date)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    reason: Mapped[str] = mapped_column(String(500), default="")
