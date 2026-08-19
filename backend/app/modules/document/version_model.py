"""PHIÊN BẢN VĂN BẢN — nơi chứa nội dung thật.

Một văn bản có nhiều phiên bản; `tab_document.current_version_id` trỏ tới bản
đang dùng. Sửa văn bản đã ban hành **không phải là sửa dòng cũ** mà là mở một
dòng mới (`van-thu/05`).

Hai ràng buộc cứng, cả hai đều ở tầng dữ liệu chứ không chỉ trong mã:

1. **Mỗi văn bản chỉ MỘT phiên bản đang mở.** Ép bằng cột sinh `open_slot` +
   UNIQUE. Kiểm bằng câu `SELECT` trong mã là không đủ: hai người bấm cùng lúc
   thì cả hai câu kiểm đều thấy trống, rồi cả hai cùng ghi.
2. **Phiên bản đã duyệt là bất biến.** `is_locked` bật rồi thì không có API nào
   tắt được — muốn sửa thì mở phiên bản mới.
"""
from datetime import date, datetime

from sqlalchemy import (BigInteger, Boolean, Computed, Date, DateTime, Index,
                        SmallInteger, String, Text, UniqueConstraint)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

VERSION_DRAFT = 1       # nháp — đang gõ, sửa được
VERSION_SUBMITTED = 2   # đang duyệt — vẫn sửa được (trả lại thì gõ tiếp)
VERSION_APPROVED = 3    # đã duyệt — KHÓA, bất biến
VERSION_SUPERSEDED = 4  # đã bị phiên bản sau thay thế

VERSION_STATUS_LABELS = {
    VERSION_DRAFT: "Nháp",
    VERSION_SUBMITTED: "Đang duyệt",
    VERSION_APPROVED: "Đã duyệt",
    VERSION_SUPERSEDED: "Đã thay thế",
}

#  Phiên bản còn "đang mở" = còn sửa được. Đúng hai trạng thái này, và đây cũng
#  là điều kiện của cột sinh `open_slot` bên dưới — sửa một chỗ phải sửa cả hai.
OPEN_STATUSES = (VERSION_DRAFT, VERSION_SUBMITTED)

CHANGE_MAJOR = 1  # sửa lớn → lên 2.0, mặc định bắt xác nhận lại
CHANGE_MINOR = 2  # sửa nhỏ → lên 1.1 (sửa lỗi chính tả, đổi số điện thoại…)

#  THỂ THỨC TRANG — Nghị định 30/2020 điều 8 khoản 3: khổ A4, lề trên 20–25mm,
#  lề dưới 20–25mm, lề trái 30–35mm, lề phải 15–20mm.
MARGIN_TOP_MM = 20
MARGIN_BOTTOM_MM = 20
MARGIN_LEFT_MIN_MM, MARGIN_LEFT_MAX_MM = 15, 60
MARGIN_RIGHT_MIN_MM, MARGIN_RIGHT_MAX_MM = 10, 60


class DocumentVersion(Base, AuditMixin):
    __tablename__ = "tab_document_version"
    __table_args__ = (
        UniqueConstraint("open_slot", name="uq_one_open_version"),
        UniqueConstraint("document_id", "major", "minor", name="uq_version_no"),
        Index("ix_version_document", "document_id", "major", "minor"),
    )

    document_id: Mapped[int] = mapped_column(BigInteger)

    #  Số phiên bản tách làm hai số nguyên chứ không phải chuỗi "2.0": chuỗi thì
    #  "10.0" đứng trước "2.0" khi sắp xếp.
    major: Mapped[int] = mapped_column(SmallInteger, default=1)
    minor: Mapped[int] = mapped_column(SmallInteger, default=0)

    status: Mapped[int] = mapped_column(SmallInteger, default=VERSION_DRAFT)
    #  Một chiều: bật khi duyệt, KHÔNG có đường tắt.
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    #  Cột SINH, không ghi tay: bằng `document_id` khi phiên bản còn mở, NULL khi
    #  đã chốt. UNIQUE trên cột này = mỗi văn bản nhiều nhất một bản đang mở
    #  (nhiều NULL thì UNIQUE vẫn cho qua, ở cả MySQL lẫn SQLite).
    open_slot: Mapped[int | None] = mapped_column(
        BigInteger,
        Computed("CASE WHEN status IN (1, 2) THEN document_id ELSE NULL END", persisted=False),
        nullable=True,
    )

    #  Thân văn bản do trình soạn thảo (tiptap) sinh ra. Soạn thẳng trên web —
    #  bản 1 không có tệp mẫu Word (quyết định 6 của plan).
    #  MEDIUMTEXT trên MySQL (~16MB): `TEXT` chỉ chứa 64KB, mà một quy chế dài
    #  kèm bảng biểu do trình soạn thảo sinh ra vượt mức đó rất dễ — và lúc vượt
    #  thì MySQL **cắt cụt nội dung** chứ không báo lỗi.
    content_html: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default="")
    #  Dấu vân tay nội dung, tính LÚC KHÓA. Để sau này ai hỏi "bản in tôi cầm có
    #  đúng bản đã duyệt không" thì còn cái mà đối chiếu.
    content_sha256: Mapped[str] = mapped_column(String(64), default="")

    #  LỀ TRANG (mm) theo Nghị định 30 điều 8: trái 30–35, phải 15–20. Lưu theo
    #  PHIÊN BẢN chứ không theo văn bản: lề là một phần thể thức của chính bản
    #  đó, sửa lề ở bản 2.0 không được đổi hình dạng bản 1.0 đã ký.
    #  Chỉ có lề ngang — lề trên/dưới là số liệu chia trang, cố định 20mm ở cả
    #  trình soạn thảo lẫn bản in (xem `MARGIN_TOP_MM`).
    margin_left_mm: Mapped[int] = mapped_column(SmallInteger, default=30)
    margin_right_mm: Mapped[int] = mapped_column(SmallInteger, default=20)

    #  1 sửa lớn · 2 sửa nhỏ. Phiên bản đầu tiên để 0 — nó không sửa gì cả.
    change_kind: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  Bắt buộc từ phiên bản THỨ HAI trở đi: sửa gì, vì sao sửa.
    change_summary: Mapped[str] = mapped_column(String(500), default="")
    change_reason: Mapped[str] = mapped_column(Text, default="")
    #  Sửa lớn thì người đã đọc bản cũ phải xác nhận đã đọc lại bản mới.
    requires_reconfirm: Mapped[bool] = mapped_column(Boolean, default=False)

    #  Ngày hiệu lực RIÊNG của phiên bản, khác ngày được duyệt: duyệt hôm nay,
    #  áp dụng từ đầu tháng sau là chuyện thường. Trong lúc chờ, bản cũ VẪN có
    #  hiệu lực (C16, C17).
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)

    prev_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #  Luôn NULL ở bản 1 — bước xin phép đã cắt (quyết định 7).
    created_from_request_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    #  Tệp bản gốc / bản PDF đã ký. Đây là ĐÍNH KÈM, không phải tệp mẫu.
    file_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    pdf_file_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[int] = mapped_column(BigInteger, default=0)

    @property
    def version_no(self) -> str:
        """`2.0` — chuỗi để hiển thị, không dùng để sắp xếp hay so sánh."""
        return f"{self.major}.{self.minor}"
