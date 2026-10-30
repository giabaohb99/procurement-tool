"""Bảng gom ngày theo CHỨC NĂNG (duoc-CR-655, D0c) — nguồn cho báo cáo "Mức dùng chức năng" (ReportKey 15).

Mức hạt `người × ngày × loại × mã × route` để đếm được "số người khác nhau trong cả kỳ"; API chỉ trả số đã gom
theo chức năng / phòng ban, KHÔNG trả `user_id` ra ngoài. Không chứa chữ người dùng gõ. Bảng hệ thống ghi, không
dùng `AuditMixin` (cùng tiền lệ `tab_usage_daily`). Giữ 3 năm.

Nghĩa các cột đếm theo `kind` (xem `core/usage_codes.FeatureKind`):
  ACTION  uses=lượt bấm · FORM uses=mở, completes=gửi, abandons=bỏ dở, duration_ms=Σ thời gian các lần gửi
  SCREEN  uses=lượt xem, duration_ms=Σ thời gian ở lại · SEARCH uses=lượt, fails=lượt không ra kết quả
  CLIENT_ERROR uses=số lỗi
"""
from datetime import date

from sqlalchemy import BigInteger, Date, Index, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base


class FeatureUsageDaily(Base):
    __tablename__ = "tab_feature_usage_daily"
    __table_args__ = (
        UniqueConstraint("day", "user_id", "kind", "code", "route", name="uq_feature_daily_day_user_feature"),
        Index("ix_feature_daily_day_kind", "day", "kind"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    day: Mapped[date] = mapped_column(Date)   # ngày theo giờ VN
    user_id: Mapped[int] = mapped_column(BigInteger)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)      # lấy từ tab_usage_daily cùng ngày (0 = không rõ)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    kind: Mapped[int] = mapped_column(SmallInteger)     # FeatureKind
    code: Mapped[int] = mapped_column(SmallInteger, default=0)   # UiAction / UiForm; 0 với màn hình, tìm kiếm, lỗi
    route: Mapped[str] = mapped_column(String(120), default="")  # route mẫu, không có id
    uses: Mapped[int] = mapped_column(Integer, default=0)
    completes: Mapped[int] = mapped_column(Integer, default=0)
    abandons: Mapped[int] = mapped_column(Integer, default=0)
    fails: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(BigInteger, default=0)
