from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AuditMixin:
    """Cột chuẩn cho mọi bảng (theo quy ước DB)."""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_by: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[int] = mapped_column(BigInteger, default=0)


class LegacyIdMixin:
    """Khóa của bản ghi tương ứng bên app đặt xe cũ (Firebase Realtime DB).

    Giá trị là khóa đẩy Firebase, vd `aFIQKCJMuLaG5geoO9qAy`. RỖNG nghĩa là bản
    ghi do ERP tự sinh, không có bản đối ứng bên app cũ — phần lớn hàng sẽ rỗng.

    CỐ Ý KHÔNG đặt UNIQUE: MySQL coi mỗi chuỗi rỗng là một giá trị thật nên
    ràng buộc sẽ chặn ngay bản ghi ERP thứ hai. Chống trùng làm ở tầng mã — tra
    theo `legacy_id` trước rồi mới tạo mới (xem `scripts/legacy_sync/`). Ở đây
    chỉ đánh index để việc tra đó không phải quét bảng.

    Khóa app cũ mới là nguồn khớp bản ghi, KHÔNG khớp theo tên hay mã số thuế:
    tên bên app cũ đã trôi thật (phòng `dept_kinh_doanh` giờ mang tên "Pháp Lý"),
    và `tab_company` đang có hai hàng cùng mã số thuế 1801722464.
    """

    legacy_id: Mapped[str] = mapped_column(String(64), default="", index=True)
