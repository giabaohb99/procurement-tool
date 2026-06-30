from sqlalchemy import BigInteger, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Inventory(Base, AuditMixin):
    """Tồn kho hiện tại theo công ty + kho + sản phẩm (key duy nhất)."""

    __tablename__ = "tab_inventory"

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    warehouse_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    product_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    product_name: Mapped[str] = mapped_column(String(255), default="")
    unit: Mapped[str] = mapped_column(String(25), default="")
    qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)


class InventoryMove(Base, AuditMixin):
    """Sổ phát sinh nhập/xuất kho. qty > 0 = nhập, < 0 = xuất/điều chỉnh giảm."""

    __tablename__ = "tab_inventory_move"

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    warehouse_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    product_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    ref_type: Mapped[str] = mapped_column(String(20), default="")   # gr | adjust
    ref_id: Mapped[int] = mapped_column(BigInteger, default=0)       # delivery_id khi gr
    note: Mapped[str] = mapped_column(Text, default="")
