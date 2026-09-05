from sqlalchemy import BigInteger, Boolean, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin

# ---------------------------------------------------------------------------
# Bộ mã (R2/QĐ-11): cột nghĩa trạng thái lưu SMALLINT + hằng số nguyên; tiếng
# Việt chỉ ở tầng hiển thị (dict nhãn), API trả kèm số + nhãn. Cùng khuôn với
# module `vehicle_booking`. KHÔNG lưu chữ tiếng Việt vào cột `status`.
# ---------------------------------------------------------------------------

# Trạng thái phiếu — luồng 2 cổng: Trưởng bộ phận duyệt → Văn thư đóng dấu.
SEAL_DRAFT = 1      # Nháp — người tạo còn sửa, chưa gửi duyệt
SEAL_PENDING = 2    # Chờ duyệt (Trưởng bộ phận)
SEAL_APPROVED = 3   # Đã duyệt — chờ Văn thư đóng dấu
SEAL_COMPLETED = 4  # Hoàn thành — Văn thư đã đóng dấu ngoài thực tế
SEAL_REJECTED = 5   # Từ chối (TBP hoặc Văn thư) — khóa
SEAL_CANCELLED = 6  # Đã hủy — kết thúc
SEAL_RETURNED = 7   # Yêu cầu chỉnh sửa — trả người tạo sửa rồi gửi lại
SEAL_STATUS_LABELS = {
    SEAL_DRAFT: "Nháp",
    SEAL_PENDING: "Chờ duyệt",
    SEAL_APPROVED: "Đã duyệt",
    SEAL_COMPLETED: "Hoàn thành",
    SEAL_REJECTED: "Từ chối",
    SEAL_CANCELLED: "Đã hủy",
    SEAL_RETURNED: "Yêu cầu chỉnh sửa",
}
# Chỉ sửa được nội dung phiếu khi chưa vào luồng hoặc bị trả về.
EDITABLE_STATUSES = (SEAL_DRAFT, SEAL_RETURNED)


class SealType(Base, AuditMixin):
    """Loại con dấu (Master data)."""
    __tablename__ = "tab_seal_type"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SealRequest(Base, AuditMixin):
    """Yêu cầu đóng dấu (Duyệt dấu)."""
    __tablename__ = "tab_seal_request"

    __table_args__ = (Index("ix_seal_created_by", "created_by"),)

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    purpose: Mapped[str] = mapped_column(Text, default="")

    seal_type_id: Mapped[int] = mapped_column(BigInteger, index=True)
    #  company_id = CÔNG TY CỦA CON DẤU (người tạo chọn, có thể khác công ty phòng
    #  ban của họ) — quyết định phạm vi Văn thư/Giám đốc và người nhận thông báo.
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    # Số bản cần đóng dấu (VD "Đóng dấu 2 bản").
    copies: Mapped[int] = mapped_column(SmallInteger, default=1)

    # Nguoi tao (Luu log)
    requester: Mapped[str] = mapped_column(String(255), default="")
    requester_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    # Submitter choice — Trưởng bộ phận sẽ duyệt (cổng 1).
    first_approver_id: Mapped[int] = mapped_column(BigInteger, default=0)

    #  R2: SMALLINT + hằng số SEAL_* (không lưu chữ tiếng Việt).
    status: Mapped[int] = mapped_column(SmallInteger, default=SEAL_DRAFT)
    note: Mapped[str] = mapped_column(Text, default="")

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
