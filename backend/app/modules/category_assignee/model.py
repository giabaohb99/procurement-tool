from sqlalchemy import BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class CategoryAssignee(Base, AuditMixin):
    """Phân công NSTM phụ trách theo phân loại VTBB: mỗi phân loại 1 người CHÍNH + 1 DỰ PHÒNG.
    Khi trưởng phòng duyệt PYC → tự điền `assignee` (mã NV) cho từng dòng theo phân loại của dòng.

    bao-CR-414 (GĐ2): mỗi PHÒNG có thể có bộ phân công riêng — `department_id` = 0 là bộ
    "Thu mua chung" (dùng cho mọi phòng chưa có bộ riêng). Khóa duy nhất là cặp
    (department_id, item_group_id)."""

    __tablename__ = "tab_category_assignee"
    __table_args__ = (
        UniqueConstraint("department_id", "item_group_id", name="uq_category_assignee_dept_group"),
    )

    department_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)   # 0 = thu mua chung
    item_group_id: Mapped[int] = mapped_column(BigInteger, index=True)              # phân loại
    primary_employee_id: Mapped[int] = mapped_column(BigInteger, default=0)   # NSTM chính
    backup_employee_id: Mapped[int] = mapped_column(BigInteger, default=0)    # NSTM dự phòng
