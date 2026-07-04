from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class CategoryAssignee(Base, AuditMixin):
    """Phân công NSTM phụ trách theo phân loại VTBB: mỗi phân loại 1 người CHÍNH + 1 DỰ PHÒNG.
    Khi trưởng phòng duyệt PYC → tự điền `assignee` (mã NV) cho từng dòng theo phân loại của dòng."""

    __tablename__ = "tab_category_assignee"

    item_group_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)  # phân loại
    primary_employee_id: Mapped[int] = mapped_column(BigInteger, default=0)   # NSTM chính
    backup_employee_id: Mapped[int] = mapped_column(BigInteger, default=0)    # NSTM dự phòng
