from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, AuditMixin

if TYPE_CHECKING:
    from app.modules.attachment.model import StoredFile


class User(Base, AuditMixin):
    __tablename__ = "tab_user"

    email: Mapped[str] = mapped_column(String(255), default="", index=True)
    google_sub: Mapped[str] = mapped_column(String(100), default="")
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    # Ảnh đại diện = 1 file trong hệ thống (tab_file.id), 0 = chưa có. KHÔNG lưu URL
    # chuỗi nữa: mọi ảnh — kể cả ảnh Google — đều tải hẳn về storage của mình để chỉ
    # còn MỘT nguồn, và đổi ảnh thì xóa được file cũ (hết file rác). Đọc URL qua
    # property `avatar` bên dưới; ghi thì đi qua user/service.set_user_avatar().
    avatar_file_id: Mapped[int] = mapped_column(BigInteger, default=0)
    # Ảnh chữ ký cá nhân (URL trên storage) — người dùng tự tải lên ở Trang cá nhân
    signature: Mapped[str] = mapped_column(String(500), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # viewonly + lazy="selectin": danh sách nhiều user nạp gộp file trong 1 truy vấn
    # IN, khỏi N+1 ở màn danh sách nhân sự/bình luận. Không có FK cứng nên phải
    # chỉ rõ primaryjoin + foreign().
    avatar_file: Mapped[Optional["StoredFile"]] = relationship(
        "StoredFile",
        primaryjoin="foreign(User.avatar_file_id) == StoredFile.id",
        viewonly=True,
        uselist=False,
        lazy="selectin",
    )

    @property
    def avatar(self) -> str:
        """URL ảnh đại diện để hiển thị — giữ nguyên kiểu chuỗi như trước để mọi nơi
        đang đọc `user.avatar` (đăng nhập, bình luận, phiếu hỗ trợ, nhân sự) không đổi."""
        f = self.avatar_file
        return (f.url or "") if f else ""


class UserRole(Base, AuditMixin):
    __tablename__ = "tab_user_role"

    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, index=True)


class UserScope(Base, AuditMixin):
    """Phạm vi dữ liệu theo NGƯỜI DÙNG (Lớp B). Mỗi dòng = 1 giá trị được cấp/loại trừ.

    entity = ''  → áp CHUNG cho mọi chức năng (phạm vi tổng);
    entity = 'purchase_request'... → override riêng cho chức năng đó.
    dim = company (value = company_id) | department (value = tên phòng ban).
    is_exclude = True → loại trừ giá trị này.
    """

    __tablename__ = "tab_user_scope"

    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)  # phạm vi theo từng vai trò của user
    entity: Mapped[str] = mapped_column(String(50), default="", index=True)  # dự phòng override theo chức năng
    dim: Mapped[str] = mapped_column(String(20), default="company")          # company | department | employee
    value: Mapped[str] = mapped_column(String(100), default="")
    is_exclude: Mapped[bool] = mapped_column(Boolean, default=False)
