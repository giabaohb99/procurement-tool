"""Hạ tầng Import dữ liệu cũ (dùng chung Khảo sát + Đơn mua hàng).

- ImportBatch: 1 dòng / 1 lần import (file, người, trạng thái, đếm kết quả).
- ImportLog: nhiều dòng / batch (lỗi/cảnh báo/cần rà soát chi tiết từng dòng).

Các cột cố định + có thứ tự (module/mode/status/level) lưu SmallInt theo IntEnum;
riêng `category` (loại lỗi) giữ string vì danh sách còn mở rộng.
"""
from enum import IntEnum

from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class ImportModule(IntEnum):
    SURVEY = 1
    PURCHASE_ORDER = 2


class ImportMode(IntEnum):
    DRY_RUN = 0
    APPLY = 1


class ImportStatus(IntEnum):
    QUEUED = 0
    RUNNING = 1
    DONE = 2
    FAILED = 3


class LogLevel(IntEnum):
    INFO = 0
    WARNING = 1
    REVIEW = 2      # cần rà soát tay
    ERROR = 3


class ImportBatch(Base, AuditMixin):
    """1 lần import. created_by = người import; created_at = thời điểm upload."""

    __tablename__ = "tab_import_batch"

    module: Mapped[int] = mapped_column(SmallInteger, index=True)          # ImportModule
    mode: Mapped[int] = mapped_column(SmallInteger, default=ImportMode.DRY_RUN)
    filename: Mapped[str] = mapped_column(String(255), default="")
    file_id: Mapped[int] = mapped_column(BigInteger, default=0)            # -> StoredFile (file .xlsx đã lưu)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    sheet_info: Mapped[str] = mapped_column(Text, default="")             # JSON: sheet + số dòng
    status: Mapped[int] = mapped_column(SmallInteger, default=ImportStatus.QUEUED, index=True)

    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)

    error_summary: Mapped[str] = mapped_column(Text, default="")          # tóm tắt khi FAILED
    started_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)  # worker bắt đầu
    finished_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)  # worker xong


class ImportLog(Base, AuditMixin):
    """Chi tiết từng dòng có vấn đề (hoặc info) của 1 batch."""

    __tablename__ = "tab_import_log"

    batch_id: Mapped[int] = mapped_column(BigInteger, index=True)
    sheet: Mapped[str] = mapped_column(String(40), default="")            # vd 3.KS-NCC / 4.KS-SP / 6.TIENDO
    row_no: Mapped[int] = mapped_column(Integer, default=0)               # dòng trong sheet
    level: Mapped[int] = mapped_column(SmallInteger, default=LogLevel.INFO, index=True)  # LogLevel
    category: Mapped[str] = mapped_column(String(40), default="")         # mã loại (mở rộng được)
    message: Mapped[str] = mapped_column(Text, default="")
    ref_key: Mapped[str] = mapped_column(String(120), default="")         # Mã yêu cầu / Misa / Số HĐ / NCC
    target_code: Mapped[str] = mapped_column(String(50), default="")      # KS##### / PO##### tạo/cập nhật
    raw: Mapped[str] = mapped_column(Text, default="")                    # JSON vài cột gốc
