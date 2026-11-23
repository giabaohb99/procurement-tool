"""Sổ giá sản phẩm + báo giá + ngưỡng giá (duoc-CR-784, tính năng Tác động giá bao bì).

`tab_product` là bảng VARIANT, KHÔNG được gắn cột giá (`mo-hinh-du-lieu-san-pham.md` §11) — nên mọi bảng giá là bảng
riêng, nối bằng CHUỖI `product_code` (không FK), đúng nếp bảy bảng ở §2 của tài liệu đó.

- `ProductPriceLedger` — sổ giá ĐÃ GIAO DỊCH (dẫn xuất, dựng lại được bằng `scripts/backfill_product_price_ledger.py`).
  Báo giá KHÔNG vào đây: báo giá là giá dự kiến, trộn vào thì min / max và "lần mua gần nhất" sai nghĩa.
- `ProductPriceQuote` — báo giá của nhà cung cấp theo ngày hiệu lực (nhiều dòng mỗi mã).
- `ProductPriceLimit` — ngưỡng sàn / trần đặt tay, MỘT dòng mỗi mã.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Index, Numeric, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class ProductPriceLedger(Base):
    """Một giao dịch giá của một mã hàng. Bảng do MÁY ghi nên không có `AuditMixin`, chỉ có `synced_at`."""

    __tablename__ = "tab_product_price_ledger"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id", name="uq_ppl_source"),
        # Chỉ mục PHỦ cho mọi truy vấn của màn giá (duoc-CR-784, đo trên sổ 650 nghìn dòng): `(mã, ngày, doc_id, id)` đúng thứ tự
        # "lần mua gần nhất" nên truy vấn con `ORDER BY ... LIMIT 1 OFFSET n-1` chỉ đọc chỉ mục; `price` + `company_id` nằm
        # sẵn trong chỉ mục nên điều kiện giá > 0 và phạm vi pháp nhân không phải chạm bảng. Thay `ix_ppl_code_date`.
        # `source_type` nằm cuối chỉ mục để điều kiện mốc sổ Misa (`misa_cutoff.py`) cũng đọc được từ chỉ mục.
        Index("ix_ppl_code_latest", "product_code", "price_date", "doc_id", "id", "price", "company_id", "source_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # PriceSourceType: 1 = tab_purchase_history.id · 2 = tab_po_item.id · 3 = id dòng sổ chi tiết mua hàng Misa
    source_type: Mapped[int] = mapped_column(SmallInteger)
    source_id: Mapped[int] = mapped_column(BigInteger)
    # Id ĐMH (0 với dữ liệu cũ không có ĐMH) — để đồng bộ theo đơn và mở ngược chứng từ.
    doc_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    product_code: Mapped[str] = mapped_column(String(50))
    supplier_code: Mapped[str] = mapped_column(String(50), default="")
    # Tên nhà cung cấp chép theo dòng (chỉ nguồn Misa: mã Misa không nằm trong `tab_supplier`); NULL = tra theo `supplier_code`.
    supplier_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # TÊN kho nhập hàng chép theo dòng (Misa: cột kho của sổ chi tiết; nguồn 1 / 2: tên kho tra từ mã kho của dòng ĐMH, không có
    # trong danh mục thì giữ chính mã). NULL = không biết kho.
    warehouse_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Pháp nhân của giao dịch — phạm vi dữ liệu của khóa `packaging_cost` đo trên cột này.
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    price_date: Mapped[date] = mapped_column(Date)
    # VNĐ, CHƯA VAT = giá dòng x tỉ giá của dòng.
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    vat: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)       # % VAT của dòng
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=0)
    unit: Mapped[str] = mapped_column(String(25), default="")             # ĐVT lúc mua — cảnh báo lệch ĐVT danh mục
    synced_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), default=datetime.utcnow)


class ProductPriceQuote(Base, AuditMixin):
    """Báo giá của nhà cung cấp cho một mã hàng, hiệu lực từ `valid_from`. Giá VNĐ, chưa VAT."""

    __tablename__ = "tab_product_price_quote"
    __table_args__ = (Index("ix_ppq_code_from", "product_code", "valid_from", "id"),)

    product_code: Mapped[str] = mapped_column(String(50))
    supplier_code: Mapped[str] = mapped_column(String(50), default="")
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    vat: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    valid_from: Mapped[date] = mapped_column(Date)
    note: Mapped[str] = mapped_column(String(500), default="")


class ProductPriceLimit(Base, AuditMixin):
    """Ngưỡng sàn / trần đặt tay của một mã — bảng riêng, một giá trị mỗi mã (không gắn vào báo giá)."""

    __tablename__ = "tab_product_price_limit"

    product_code: Mapped[str] = mapped_column(String(50), unique=True)
    floor_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    ceiling_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    note: Mapped[str] = mapped_column(String(500), default="")
