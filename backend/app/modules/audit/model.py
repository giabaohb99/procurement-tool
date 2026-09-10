from sqlalchemy import BINARY, BigInteger, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin
from app.core.logging_codes import ACTION_GROUP_UNKNOWN, ACTOR_KIND_UNKNOWN


class AuditLog(Base, AuditMixin):
    """Nhật ký thao tác: ai (created_by) làm gì (action) trên đối tượng nào, lúc nào (created_at).

    Bốn cột `entity` · `entity_id` · `action` · `message` **giữ nguyên tên** —
    213 lời gọi `record(...)` đang truyền đúng bốn thứ đó, đổi tên là sửa hết.
    Phần còn lại là cột NGỮ CẢNH thêm ở bao-CR-312 (P1): máy tự điền từ
    `core/request_context`, lời gọi cũ không phải sửa dòng nào.

    NT-1: thứ gì cần LỌC được thì phải là CỘT. `message` chỉ là câu cho người
    đọc — hôm nay IP đang bị nhồi trong đó dưới dạng chữ, nên câu hỏi "IP này
    thử bao nhiêu tài khoản" phải `LIKE '%IP%'` trên `TEXT`.

    Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.2.
    """

    __tablename__ = "tab_audit_log"

    entity: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, index=True)
    action: Mapped[str] = mapped_column(String(20))  # create | update | delete
    message: Mapped[str] = mapped_column(Text, default="")

    # -- ngữ cảnh: MÁY điền (middleware / ContextVar) -----------------------
    #  `created_by = 0` hôm nay vừa nghĩa "hệ thống làm" vừa nghĩa "không biết",
    #  nên phải có cột riêng để phân biệt.
    actor_kind: Mapped[int] = mapped_column(SmallInteger, default=ACTOR_KIND_UNKNOWN)
    session_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)  # P3
    #  QĐ-B (§4.5) — nối sang `tab_request_log` và `tab_change_log`.
    request_id: Mapped[bytes | None] = mapped_column(BINARY(16), nullable=True, index=True)
    #  Giữ riêng dù tra được qua `request_id`: việc nền và script KHÔNG có request.
    ip: Mapped[str] = mapped_column(String(45), default="")

    # -- ngữ cảnh: LỜI GỌI truyền (tùy chọn, làm dần) ----------------------
    on_behalf_of: Mapped[int] = mapped_column(BigInteger, default=0)  # hành chính lập hộ ai
    #  Số phiếu TẠI THỜI ĐIỂM ĐÓ: phiếu xóa rồi thì `entity_id` không tra ngược
    #  ra được cái gì nữa, còn số phiếu thì người ta vẫn nhớ và vẫn đi hỏi.
    doc_code: Mapped[str] = mapped_column(String(50), default="")
    parent_entity: Mapped[str] = mapped_column(String(50), default="")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0)

    # -- suy ra / lớp ORM điền ---------------------------------------------
    action_group: Mapped[int] = mapped_column(SmallInteger, default=ACTION_GROUP_UNKNOWN)
    #  Cố ý LẶP dữ liệu của `tab_change_log` (P4): dòng thời gian của một phiếu
    #  cần hiện "Sửa: đơn giá, số lượng" cho vài chục dòng một lúc, đọc cột
    #  phẳng rẻ hơn join sang bảng vài triệu dòng.
    changed_fields: Mapped[str] = mapped_column(String(500), default="")
    change_count: Mapped[int] = mapped_column(SmallInteger, default=0)
