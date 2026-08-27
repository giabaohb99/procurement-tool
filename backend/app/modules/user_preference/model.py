from sqlalchemy import BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class UserPreference(Base, AuditMixin):
    """Tuỳ chọn CÁ NHÂN của một người dùng, dạng khoá-giá trị.

    Khác `tab_setting` ở chỗ `tab_setting` là cấu hình TOÀN HỆ (một bản ghi cho
    cả công ty, cần quyền `setting.write`), còn bảng này là của riêng từng người
    và ai cũng tự sửa được phần của mình — không gác bằng phân quyền, vì gác thì
    người dùng thường không đổi nổi màu giao diện của chính họ.

    Để dạng khoá-giá trị chứ không thêm cột vào `tab_user`: tuỳ chọn giao diện
    còn đẻ thêm (bảng màu, độ dày bảng, ghim cột...), mỗi thứ một cột thì mỗi
    thứ một migration.

    KHÔNG chứa dữ liệu nhạy cảm — nội dung ở đây đi kèm hồ sơ `/api/auth/me`.
    """

    __tablename__ = "tab_user_preference"
    __table_args__ = (
        UniqueConstraint("user_id", "pref_key", name="uq_user_preference_user_key"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    pref_key: Mapped[str] = mapped_column(String(64))
    pref_value: Mapped[str] = mapped_column(Text, default="")
