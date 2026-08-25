from sqlalchemy import BigInteger, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Role(Base, AuditMixin):
    __tablename__ = "tab_role"

    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), default="")

    #  THỨ TỰ HIỆN trên màn Phân quyền, người quản trị tự kéo thả (CR-172).
    #  Không phải `id`: vai trò tạo sau chưa chắc đứng cuối trong đầu người dùng,
    #  và danh sách xếp theo id thì mấy vai trò hay dùng nằm lẫn giữa vai trò
    #  hiếm dùng. Vai trò mới mặc định `0` nên nổi lên đầu; xếp lại một lần là
    #  xong. Sắp xếp luôn kèm `id` làm khóa phụ để hai vai trò cùng số không
    #  đảo chỗ nhau mỗi lần nạp.
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Permission(Base, AuditMixin):
    """Quyền chi tiết theo (vai trò x đối tượng) — các cờ hành động + phạm vi dòng."""

    __tablename__ = "tab_permission"

    role_id: Mapped[int] = mapped_column(BigInteger, index=True)
    entity: Mapped[str] = mapped_column(String(50), index=True)
    can_read: Mapped[bool] = mapped_column(Boolean, default=False)
    can_create: Mapped[bool] = mapped_column(Boolean, default=False)
    can_write: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    can_approve: Mapped[bool] = mapped_column(Boolean, default=False)
    can_cancel: Mapped[bool] = mapped_column(Boolean, default=False)
    can_print: Mapped[bool] = mapped_column(Boolean, default=False)
    can_export: Mapped[bool] = mapped_column(Boolean, default=False)
    scope: Mapped[str] = mapped_column(String(10), default="own")  # own | dept | company | all
