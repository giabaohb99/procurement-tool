from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class ReportSnapshot(Base, AuditMixin):
    """Kết quả báo cáo đã tính sẵn (precompute) — đọc nhanh, tính lại chạy nền.

    key = '{year}|{company_id or all}'. data = JSON các báo cáo ma trận.
    """

    __tablename__ = "tab_report_snapshot"

    key: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    data: Mapped[str] = mapped_column(Text, default="")     # JSON
    computed_at: Mapped[str] = mapped_column(String(30), default="")
