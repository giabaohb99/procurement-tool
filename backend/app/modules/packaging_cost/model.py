"""Định mức bao bì theo mã hàng hóa (duoc-CR-784): mỗi mã HH ghép từ chai + nắp + nhãn + nhãn thùng + thùng.

Hai bảng nối nhau bằng ID (chuẩn hóa ngày 25/11/2026, chủ dự án chốt "thêm cột loại rồi gắn id"):
- `tab_packaging_bom`      — ĐẦU phiếu: một dòng mỗi mã HH (tên, tên pháp lý, quy cách thùng).
- `tab_packaging_bom_part` — các THÀNH PHẦN: mỗi dòng = (id đầu phiếu, loại thành phần `PackagingRole`, mã vật tư).

Thêm loại thành phần mới (vd tem, màng co) = thêm một thành viên vào `PackagingRole` + nhãn — KHÔNG đổi cấu trúc bảng.
Mã vật tư nối `tab_product` bằng CHUỖI mã (không FK) — đúng nếp `product_code` của cả hệ. Lịch sử sửa xem qua nhật ký thao tác
(câu hỏi Q7 ở kế hoạch: chưa cần nhiều phiên bản theo thời gian).

Mã thành phần dạng cột phẳng (`bottle_code`, `cap_code`, ...) vẫn đọc được trên `PackagingBom` như thuộc tính CHỈ ĐỌC
(truy vấn con tương quan, dựng theo `PackagingRole`) để API danh mục lọc / xếp / trả đúng tên trường cũ; GHI luôn đi qua
`bom_parts_service.set_bom_codes`.
"""
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, SmallInteger, String, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.core.base_model import AuditMixin, Base
from app.core.packaging_price_codes import PackagingRole


def role_field(role: PackagingRole) -> str:
    """Tên trường phẳng của API danh mục cho một loại thành phần: `BOTTLE` -> `bottle_code`, `CARTON_LABEL` -> `carton_label_code`."""
    return f"{role.name.lower()}_code"


class PackagingBomPart(Base):
    """Một thành phần của định mức: loại (`PackagingRole`) + mã vật tư. Không mang cột kiểm toán — vết sửa nằm ở đầu phiếu."""

    __tablename__ = "tab_packaging_bom_part"
    #  Hiện mỗi loại một mã (như cấu trúc cột cũ). Muốn một loại có NHIỀU mã (vd hai nhãn) thì chỉ cần bỏ ràng buộc duy nhất này
    #  (và đổi `set_bom_codes` cho nhận danh sách) — các truy vấn tra ngược / đếm đã đếm theo `bom_id` riêng biệt nên không vỡ.
    __table_args__ = (
        UniqueConstraint("bom_id", "part_type", name="uq_pbom_part_bom_type"),
        #  Chỉ mục PHỦ cho tra ngược "sản phẩm nào dùng mã X, ở vai trò nào" (Tác động giá, đếm số sản phẩm dùng, cặp của Lịch sử theo
        #  sản phẩm): mọi truy vấn lọc / gom theo `part_code` chỉ đọc chỉ mục, không chạm bảng. `bom_id` đã có chỉ mục qua duy nhất ở trên.
        Index("ix_pbom_part_code", "part_code", "part_type", "bom_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bom_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tab_packaging_bom.id", ondelete="CASCADE"))
    part_type: Mapped[int] = mapped_column(SmallInteger)         # `PackagingRole`
    part_code: Mapped[str] = mapped_column(String(50))           # mã vật tư (`tab_product.code`), không FK


class PackagingBom(Base, AuditMixin):
    __tablename__ = "tab_packaging_bom"
    __table_args__ = (Index("ix_pbom_import_batch", "import_batch_id"),)     # tra "định mức của lô nhập X" (xóa theo lô)

    fg_code: Mapped[str] = mapped_column(String(50), unique=True)       # mã hàng hóa thành phẩm
    fg_name: Mapped[str] = mapped_column(String(255), default="")
    legal_name: Mapped[str] = mapped_column(String(255), default="")    # tên pháp lý
    carton_qty: Mapped[int] = mapped_column(Integer, default=0)         # quy cách thùng (chai / thùng), 0 = chưa có
    # Lô nhập Excel (`tab_import_batch.id`, module 4) TẠO hoặc SỬA dòng này lần cuối; 0 = nhập tay / form. Form sửa tay KHÔNG đổi cột này
    # (duoc-CR-784 phase 07) — dùng để xem trước và xóa dữ liệu theo lô (`batch_purge_service.py`).
    import_batch_id: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")

    #  Xóa đầu phiếu thì xóa luôn các dòng thành phần (ORM lo cả khi DB không bật khóa ngoại — SQLite của bộ test).
    parts: Mapped[list[PackagingBomPart]] = relationship(cascade="all, delete-orphan", lazy="select",
                                                         order_by=PackagingBomPart.part_type)

    #  Khóa xếp phía máy chủ được `apply_sort` chấp nhận ngoài cột thật của bảng (xem `core/base_controller.apply_sort`).
    SORTABLE_COMPUTED = frozenset(role_field(role) for role in PackagingRole)


def _install_flat_code_properties() -> None:
    """Gắn `PackagingBom.<role>_code` = mã thành phần của loại đó (chuỗi rỗng nếu chưa khai), CHỈ ĐỌC.

    Mỗi thuộc tính là một truy vấn con tương quan tra chỉ mục `(bom_id, part_type)` nên lọc / xếp ở danh sách vẫn chạy ở máy chủ
    như khi còn là cột thật. Chỉ danh sách / chi tiết của `bom_controller` nạp thực thể `PackagingBom`; các dịch vụ tính toán đọc
    thẳng bảng thành phần (`bom_parts_service.load_bom_rows`) nên không phải trả giá năm truy vấn con này.
    """
    for role in PackagingRole:
        subquery = (select(PackagingBomPart.part_code)
                    .where(PackagingBomPart.bom_id == PackagingBom.id, PackagingBomPart.part_type == int(role))
                    .correlate(PackagingBom).scalar_subquery())
        setattr(PackagingBom, role_field(role), column_property(func.coalesce(subquery, "")))


_install_flat_code_properties()
