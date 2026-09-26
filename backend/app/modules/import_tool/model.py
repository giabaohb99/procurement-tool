"""Hạ tầng Import dữ liệu cũ (dùng chung Khảo sát + Đơn mua hàng).

- ImportBatch: 1 dòng / 1 lần import (file, người, trạng thái, đếm kết quả).
- ImportLog: nhiều dòng / batch (lỗi/cảnh báo/cần rà soát chi tiết từng dòng).

Các cột cố định + có thứ tự (module/mode/status/level) lưu SmallInt theo IntEnum;
riêng `category` (loại lỗi) giữ string vì danh sách còn mở rộng.
"""
from enum import IntEnum

from sqlalchemy import BigInteger, DateTime, Index, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class ImportModule(IntEnum):
    SURVEY = 1
    PURCHASE_ORDER = 2
    # Tờ khai hải quan GTT02 — phân hệ Tra cứu giá hải quan (bao-CR-470). Tệp là .xls
    # đời cũ nên KHÔNG đi đường openpyxl; tác vụ nền chuyển thẳng byte thô cho
    # `app.modules.customs.importer`. Gác bằng khóa `customs_price`, không bằng `import`.
    CUSTOMS_DECLARATION = 3
    # Danh mục nền (Đ-13d) — chừa 3..9 cho nghiệp vụ, 10+ cho danh mục.
    COMPANY = 10
    DEPARTMENT = 11
    EMPLOYEE = 12
    # Danh mục Sản xuất + Kho (CR-174).
    SUPPLIER = 13
    PRODUCT = 14
    UNIT = 15
    ITEM_GROUP = 16
    WAREHOUSE = 17
    # Chứng từ nhiều dòng (CR-175) — mẫu chuẩn (khác importer Misa của SURVEY/PO).
    SURVEY_REQUEST = 18
    PURCHASE_REQUEST = 19
    # Danh mục Đặt xe + Duyệt dấu.
    VEHICLE = 20
    DRIVER = 21
    SEAL_TYPE = 22
    # Chứng từ header-only (không có dòng) — Đặt xe + Duyệt dấu.
    VEHICLE_BOOKING = 23
    SEAL_REQUEST = 24


class ImportMode(IntEnum):
    DRY_RUN = 0
    APPLY = 1


class ImportStatus(IntEnum):
    QUEUED = 0
    RUNNING = 1
    DONE = 2
    FAILED = 3
    REVERTED = 4     # đã hoàn tác (revert)


class LogLevel(IntEnum):
    INFO = 0
    WARNING = 1
    REVIEW = 2      # cần rà soát tay
    ERROR = 3


class ImportRowStatus(IntEnum):
    """Kết cục của TỪNG DÒNG DỮ LIỆU trong tệp nạp — bao-CR-496 (luật R2).

    `NONE` = dòng nhật ký thường (cảnh báo / thông báo của lô), không phải dòng dữ liệu.
    Cố ý KHÔNG có «Cập nhật»: nguồn GTT02 không có số tờ khai nên không dựng được khóa
    để biết dòng nào là cùng một dòng cũ (02 §3.1). `DUPLICATE` chỉ ĐÁNH DẤU — dòng vẫn
    ghi vào bảng giá, vì hai dòng giống hệt có thể là hai lô hàng thật.
    """
    NONE = 0
    NEW = 1          # Thêm mới
    ERROR = 2        # Lỗi — bỏ dòng
    DUPLICATE = 3    # Trùng với một dòng khác trong CÙNG tệp (vẫn ghi)


IMPORT_ROW_STATUS_LABELS = {
    ImportRowStatus.NONE: "",
    ImportRowStatus.NEW: "Thêm mới",
    ImportRowStatus.ERROR: "Lỗi",
    ImportRowStatus.DUPLICATE: "Trùng trong lô",
}


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
    deleted_count: Mapped[int] = mapped_column(Integer, default=0)         # dòng đánh dấu __/delete/__
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
    #  bao-CR-496: đếm / lọc theo kết cục từng dòng trong MỘT lô (18.000 dòng một tệp).
    __table_args__ = (Index("ix_import_log_batch_row_status", "batch_id", "row_status"),)

    batch_id: Mapped[int] = mapped_column(BigInteger, index=True)
    sheet: Mapped[str] = mapped_column(String(40), default="")            # vd 3.KS-NCC / 4.KS-SP / 6.TIENDO
    row_no: Mapped[int] = mapped_column(Integer, default=0)               # dòng trong sheet
    level: Mapped[int] = mapped_column(SmallInteger, default=LogLevel.INFO, index=True)  # LogLevel
    category: Mapped[str] = mapped_column(String(40), default="")         # mã loại (mở rộng được)
    message: Mapped[str] = mapped_column(Text, default="")
    ref_key: Mapped[str] = mapped_column(String(120), default="")         # Mã yêu cầu / Misa / Số HĐ / NCC
    target_code: Mapped[str] = mapped_column(String(50), default="")      # KS##### / PO##### tạo/cập nhật
    raw: Mapped[str] = mapped_column(Text, default="")                    # JSON vài cột gốc
    #  bao-CR-496: kết cục từng dòng dữ liệu (ImportRowStatus); 0 = dòng nhật ký thường.
    row_status: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")


class ImportChange(Base, AuditMixin):
    """Ảnh chụp PHIẾU trước khi 1 batch Apply sửa — để REVERT (hoàn tác)."""

    __tablename__ = "tab_import_change"

    batch_id: Mapped[int] = mapped_column(BigInteger, index=True)
    survey_id: Mapped[int] = mapped_column(BigInteger, default=0)          # phiếu bị đụng (hoặc PO sau này)
    was_new: Mapped[bool] = mapped_column(SmallInteger, default=0)         # 1 = phiếu do batch này tạo -> revert xoá
    snapshot: Mapped[str] = mapped_column(Text, default="")               # JSON phiếu + dòng TRƯỚC khi sửa (rỗng nếu was_new)
