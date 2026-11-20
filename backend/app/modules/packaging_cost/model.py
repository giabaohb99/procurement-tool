"""Định mức bao bì theo mã hàng hóa (duoc-CR-784): mỗi mã HH ghép từ chai + nắp + nhãn + nhãn thùng + thùng.

Nối `tab_product` bằng CHUỖI mã (không FK) — đúng nếp `product_code` của cả hệ. Một dòng mỗi mã HH; lịch sử sửa xem
qua nhật ký thao tác (câu hỏi Q7 ở kế hoạch: chưa cần nhiều phiên bản theo thời gian).
"""
from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class PackagingBom(Base, AuditMixin):
    __tablename__ = "tab_packaging_bom"
    #  Tra ngược "sản phẩm nào dùng mã X" — màn Tác động giá lọc theo từng cột mã thành phần.
    __table_args__ = (
        Index("ix_pbom_bottle", "bottle_code"),
        Index("ix_pbom_cap", "cap_code"),
        Index("ix_pbom_label", "label_code"),
        Index("ix_pbom_carton_label", "carton_label_code"),
        Index("ix_pbom_carton", "carton_code"),
    )

    hh_code: Mapped[str] = mapped_column(String(50), unique=True)       # mã hàng hóa thành phẩm
    hh_name: Mapped[str] = mapped_column(String(255), default="")
    legal_name: Mapped[str] = mapped_column(String(255), default="")    # tên pháp lý
    bottle_code: Mapped[str] = mapped_column(String(50), default="")
    cap_code: Mapped[str] = mapped_column(String(50), default="")
    label_code: Mapped[str] = mapped_column(String(50), default="")
    carton_label_code: Mapped[str] = mapped_column(String(50), default="")
    carton_code: Mapped[str] = mapped_column(String(50), default="")
    carton_qty: Mapped[int] = mapped_column(Integer, default=0)         # quy cách thùng (chai / thùng), 0 = chưa có
