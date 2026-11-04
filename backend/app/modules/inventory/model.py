from sqlalchemy import BigInteger, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin

#  bao-CR-717: tên ràng buộc dùng chung với migration `invuq717` — đổi một nơi thì đổi cả hai.
INVENTORY_KEY_CONSTRAINT = "uq_inventory_company_wh_product"


class Inventory(Base, AuditMixin):
    """Tồn kho hiện tại theo công ty + kho + sản phẩm (key duy nhất).

    bao-CR-717: khóa duy nhất được ÉP ở CSDL (trước chỉ ghi trên giấy, ba chỉ mục rời). Hai lượt ghi cùng lúc cho cùng
    bộ khóa thì lượt sau đụng ràng buộc — `service._recompute` bắt lỗi đó rồi đọc lại dòng mà lượt trước vừa chèn.
    """

    __tablename__ = "tab_inventory"
    __table_args__ = (UniqueConstraint("company_id", "warehouse_code", "product_code", name=INVENTORY_KEY_CONSTRAINT),)

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    warehouse_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    product_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    product_name: Mapped[str] = mapped_column(String(255), default="")
    unit: Mapped[str] = mapped_column(String(25), default="")
    qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    avg_cost: Mapped[float] = mapped_column(Numeric(18, 4), default=0)   # đơn giá bình quân gia quyền — 4 số lẻ theo đơn giá ĐMH
    value: Mapped[float] = mapped_column(Numeric(18, 2), default=0)      # giá trị tồn = qty × avg_cost


class InventoryMove(Base, AuditMixin):
    """Sổ phát sinh nhập/xuất kho. qty > 0 = nhập, < 0 = xuất/điều chỉnh giảm."""

    __tablename__ = "tab_inventory_move"

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    warehouse_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    product_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), default=0)  # đơn giá nhập (cho BQ gia quyền) — 4 số lẻ
    ref_type: Mapped[str] = mapped_column(String(20), default="")   # gr | adjust
    ref_id: Mapped[int] = mapped_column(BigInteger, default=0)       # delivery_id khi gr
    note: Mapped[str] = mapped_column(Text, default="")
