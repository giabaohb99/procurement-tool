"""Nhật ký Xuất dữ liệu (Đ-13b) — mỗi lần xuất một bảng ra CSV/XLSX ghi một dòng.

Chỉ lưu METADATA (ai xuất, bảng nào, định dạng, số dòng, tên file, dung lượng),
KHÔNG lưu nội dung file — đủ để truy vết, không phình dung lượng.
"""
from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class ExportLog(Base, AuditMixin):
    """1 lần xuất dữ liệu. created_by = người xuất; created_at = thời điểm xuất."""

    __tablename__ = "tab_export_log"

    #  Khóa đối tượng đã xuất (trùng ENTITIES: 'employee', 'department', ...).
    entity: Mapped[str] = mapped_column(String(50), index=True)
    #  Định dạng: 'csv' | 'xlsx'.
    fmt: Mapped[str] = mapped_column(String(10), default="")
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    filename: Mapped[str] = mapped_column(String(255), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    #  Trỏ tới StoredFile — file .csv/.xlsx ĐÃ XUẤT được lưu lại để tải về ở trang
    #  chi tiết (giữ đúng ảnh chụp lúc xuất, không phải sinh lại). 0 = không có file.
    file_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Tóm tắt bộ lọc lúc xuất (JSON/text). Đợt này xuất TOÀN BẢNG (theo phạm vi)
    #  nên để rỗng; dành sẵn cho khi xuất theo bộ lọc.
    filter_summary: Mapped[str] = mapped_column(Text, default="")
