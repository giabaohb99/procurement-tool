from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func, text
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


class SoftDeleteMixin:
    """Xóa MỀM dùng chung cho chứng từ (ai-CR-170, đại ca chốt 10/10/2026).

    Ba cột: `is_deleted` 0/1 · `deleted_at` thời điểm xóa · `deleted_by` id tài khoản xóa.
    Model gắn mixin này thì `core/scoping.apply_scope` / `get_scoped` TỰ thêm điều kiện
    «chưa xóa» — chỗ đọc đi qua phạm vi không phải lọc tay. Chỗ đọc thẳng (`db.get`,
    `db.query(Model).filter(code == ...)`) vẫn phải tự lọc, xem `doc/erp/20-ra-soat-xoa-cung.md` §5.

    Dòng con / đính kèm / bình luận / nhật ký của phiếu đã xóa GIỮ NGUYÊN; mã phiếu không tái
    dùng (hàm sinh mã đếm cả phiếu đã xóa).
    """

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("0"),
                                             index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[int] = mapped_column(BigInteger, default=0)


def mark_deleted(obj, user_id: int) -> None:
    """Đánh dấu xóa mềm một bản ghi có `SoftDeleteMixin` (chưa commit — nơi gọi tự commit)."""
    obj.is_deleted = True
    obj.deleted_at = datetime.utcnow()
    obj.deleted_by = int(user_id or 0)
    if hasattr(obj, "updated_by"):
        obj.updated_by = int(user_id or 0)


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
