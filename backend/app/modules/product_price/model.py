"""Sổ giá sản phẩm + báo giá (duoc-CR-784, tính năng Tác động giá bao bì).

`tab_product` là bảng VARIANT, KHÔNG được gắn cột giá (`mo-hinh-du-lieu-san-pham.md` §11) — nên mọi bảng giá là bảng
riêng, nối bằng CHUỖI `product_code` (không FK), đúng nếp bảy bảng ở §2 của tài liệu đó.

- `ProductPriceLedger` — sổ giá ĐÃ GIAO DỊCH (dẫn xuất, dựng lại được bằng `scripts/backfill_product_price_ledger.py`).
  Báo giá KHÔNG vào đây: báo giá là giá dự kiến, trộn vào thì min / max và "lần mua gần nhất" sai nghĩa.
- `ProductPriceQuote` — báo giá của nhà cung cấp theo ngày hiệu lực (nhiều dòng mỗi mã).

Bảng ngưỡng sàn / trần (`tab_product_price_limit`) đã BỎ HẲN ở migration `cleanup784` (chủ dự án chốt C6, 25/11/2026); min / max tự
tính từ sổ giá vẫn giữ. Cần lại thì làm lại, đừng dựng lại bảng cũ.

Ba nguồn của sổ giá (`source_type`, bộ mã `PriceSourceType`):
  1 = lịch sử mua hàng nạp từ Excel cũ — `source_id` = `tab_purchase_history.id`;
  2 = dòng ĐMH — `source_id` = `tab_po_item.id` (MỘT dòng sổ suốt đời, `line_stage` đổi 1 -> 2 khi hoàn thành);
  3 = sổ chi tiết mua hàng Misa — `source_id` KHÔNG trỏ chứng từ nào: là số thứ tự trong sổ. Script HTML dùng id dòng Misa
      trong tệp, module 6 (xlsx) tự đánh `max + 1`, nên hai đường KHÔNG trộn được (xem `misa_ledger_import.ensure_no_xlsx_misa_rows`).
      Dòng Misa có `vat = NULL` (Misa không có VAT trong sổ chi tiết — NULL = không biết, KHÔNG phải 0%).
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Index, Numeric, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base
from app.core.packaging_price_codes import QuoteSourceType


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
        # Thứ tự "lần mua đầu / gần nhất" KHÔNG phân theo mã (duoc-CR-784, Lịch sử mua hàng): giá lần có giá đầu tiên / gần nhất của cả
        # tập mã là `ORDER BY price_date, doc_id, id LIMIT 1` — có chỉ mục này MySQL đọc từ đầu / cuối chỉ mục rồi dừng ở dòng đầu
        # thỏa điều kiện, thay vì xếp cả sổ (đo 2 lần x ~85 ms -> ~0 trên 11,6 nghìn dòng; sổ càng lớn càng lợi).
        Index("ix_ppl_date_latest", "price_date", "doc_id", "id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # PriceSourceType: 1 = tab_purchase_history.id (CHỈ lịch sử cũ nạp Excel, `po_item_id` trống) · 2 = tab_po_item.id (dòng ĐMH, đang mở
    # lẫn đã hoàn thành — MỘT dòng sổ suốt đời, id giữ nguyên) · 3 = id dòng sổ chi tiết mua hàng Misa
    source_type: Mapped[int] = mapped_column(SmallInteger)
    source_id: Mapped[int] = mapped_column(BigInteger)
    # LedgerLineStage: 1 = Đang mở (dòng ĐMH chưa hoàn thành, còn đổi theo ĐMH) · 2 = Đã chốt (bản chụp lúc hoàn thành, nguồn 1, nguồn 3).
    # Không có mặc định: nơi ghi phải đặt rõ (migration `srcmerge784` bỏ `server_default`).
    line_stage: Mapped[int] = mapped_column(SmallInteger)
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
    # % VAT của dòng; NULL = không biết (dòng Misa — Misa không có VAT trong sổ chi tiết, KHÔNG phải 0%): giao diện hiện trống. KHÔNG đặt `default=`: ORM coi None là chưa gán nên sẽ ghi 0 thay NULL — nơi ghi phải đặt `vat` rõ.
    vat: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=0)
    # Thành tiền của lần mua, VNĐ, CHƯA VAT: nguồn Misa = cột "Giá trị" của sổ chi tiết mua hàng (Misa làm tròn từng dòng nên có
    # thể khác giá x số lượng vài chục đồng); dòng đã chốt từ lịch sử mua = tiền của dòng lịch sử bỏ VAT, quy VNĐ. NULL = chưa có / không biết
    # -> giao diện dùng giá x số lượng (cùng luật `gia_tri ?? gia x sl` của bản mẫu HTML). Dòng ĐMH đang mở luôn NULL.
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    unit: Mapped[str] = mapped_column(String(25), default="")             # ĐVT lúc mua — cảnh báo lệch ĐVT danh mục
    # MỘT nguồn giờ: đồng hồ máy chủ CSDL (cùng nguồn với `created_at` / `updated_at` của mọi bảng khác). Lúc chèn lấy `server_default`;
    # lúc ghi đè nơi ghi phải gán `func.now()` (không dùng giờ Python — lệch múi giờ so với máy chủ CSDL).
    synced_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProductPriceQuote(Base, AuditMixin):
    """Báo giá của nhà cung cấp cho một mã hàng, hiệu lực từ `valid_from`. Giá VNĐ, chưa VAT."""

    __tablename__ = "tab_product_price_quote"
    __table_args__ = (
        Index("ix_ppq_code_from", "product_code", "valid_from", "id"),
        # Khóa của một báo giá = (mã, NCC, ngày hiệu lực) — chính khóa nhập Excel vẫn dùng (migration `quotesrc784`, chủ dự án chốt C5).
        UniqueConstraint("product_code", "supplier_code", "valid_from", name="uq_ppq_key"),
        Index("ix_ppq_source", "source_type", "source_id"),    # tra "báo giá của đợt nhập X"
    )

    product_code: Mapped[str] = mapped_column(String(50))
    supplier_code: Mapped[str] = mapped_column(String(50), default="")
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    vat: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    valid_from: Mapped[date] = mapped_column(Date)
    note: Mapped[str] = mapped_column(String(500), default="")
    # QuoteSourceType: 1 = nhập tay (`source_id` = 0) · 2 = nhập Excel (`source_id` = tab_import_batch.id của đợt ghi giá / VAT cuối).
    # NOT NULL, KHÔNG server default (migration `quotesrc784` bỏ): nơi ghi báo giá phải đặt rõ. Mặc định phía Python chỉ để đường CRUD
    # tạo tay không phải viết lại; schema ghi KHÔNG nhận hai trường này từ người dùng.
    source_type: Mapped[int] = mapped_column(SmallInteger, default=QuoteSourceType.MANUAL)
    source_id: Mapped[int] = mapped_column(BigInteger, default=0)

