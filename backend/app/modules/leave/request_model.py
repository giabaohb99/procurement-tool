"""ĐƠN NGHỈ PHÉP — V1-7. Chứng từ nghiệp vụ, nguồn sự thật của phân hệ.

QĐ-NP5 giải thích vì sao đây là BẢNG chứ không phải mở rộng ô JSON của giấy GNP:
*Lịch nghỉ* và mọi báo cáo phải trả lời "tuần tới ai nghỉ" và "người này năm nay
dùng bao nhiêu ngày". Trả lời được trên cột `DATE` có chỉ mục; quét
`JSON_EXTRACT` trên `tab_document.metadata` thì vừa chậm vừa không đánh chỉ mục,
và trừ quỹ phép sẽ dựa trên một ô không có ràng buộc kiểu.

Giấy GNP vẫn còn — nó là **giấy tờ hồ sơ** (có số hiệu, có chữ ký, nằm trong sổ
văn bản), sinh ra từ đơn này sau khi duyệt xong. Đơn là **chứng từ**, giấy là
**hồ sơ**. Hai thứ khác nhau, giữ cả hai và nối lại bằng `document_id`.
"""
from datetime import date, datetime

from sqlalchemy import (BigInteger, Boolean, Date, DateTime, Float, Index,
                        Integer, SmallInteger, String)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import AuditMixin, Base

from .constants import LR_DRAFT, SESSION_FULL, UNIT_DAY


class LeaveRequest(Base, AuditMixin):
    """Một đơn xin nghỉ."""

    __tablename__ = "tab_leave_request"
    __table_args__ = (
        #  Chỉ mục của màn **Lịch nghỉ**: "tuần tới ai nghỉ" là câu quét theo
        #  khoảng ngày, chạy mỗi lần mở màn. Thiếu nó thì quét toàn bảng.
        Index("ix_leave_request_range", "from_date", "to_date"),
        #  "Người này năm nay nghỉ bao nhiêu" — câu của màn Quỹ phép và báo cáo.
        Index("ix_leave_request_emp_date", "employee_id", "from_date"),
        Index("ix_leave_request_status", "status"),
    )

    #  Số đơn tự sinh (`NP-2026-0001`). Có số thì người ta gọi điện cho nhau
    #  bằng số, không phải bằng "đơn của chị Lan hôm thứ ba".
    code: Mapped[str] = mapped_column(String(30), unique=True)

    #  Chép từ hồ sơ NGƯỜI NGHỈ lúc lập đơn — hai cột này là chiều lọc phạm vi
    #  (`SCOPE_FIELDS["leave_request"]`). Chép chứ không JOIN: người chuyển
    #  phòng giữa năm thì đơn cũ phải ở lại phòng cũ, nếu không báo cáo của
    #  phòng cũ tự rỗng đi.
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)

    #  NGƯỜI NGHỈ. Khác `created_by` (tài khoản lập đơn) — hành chính lập hộ là
    #  việc có thật, và cả hai đều phải thấy được đơn ở phạm vi `own`.
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    leave_type_id: Mapped[int] = mapped_column(BigInteger, default=0)

    from_date: Mapped[date] = mapped_column(Date)
    to_date: Mapped[date] = mapped_column(Date)
    from_session: Mapped[int] = mapped_column(SmallInteger, default=SESSION_FULL)
    to_session: Mapped[int] = mapped_column(SmallInteger, default=SESSION_FULL)

    #  QĐ-NP4: bản này chỉ ghi `UNIT_DAY`. Cột khai sẵn để khi có phân hệ Lịch
    #  làm việc thì chỉ thêm cách quy đổi, không phải chạy migration đổi cấu trúc.
    unit: Mapped[int] = mapped_column(SmallInteger, default=UNIT_DAY)
    #  Tổng số ngày nghỉ. Người dùng nhập được (sửa đè gợi ý của
    #  `workday_service`) vì lịch làm việc thật luôn có ngoại lệ máy không biết.
    total_days: Mapped[float] = mapped_column(Float, default=0.0)

    reason: Mapped[str] = mapped_column(String(1000), default="")
    contact_phone: Mapped[str] = mapped_column(String(30), default="")
    contact_address: Mapped[str] = mapped_column(String(255), default="")

    status: Mapped[int] = mapped_column(SmallInteger, default=LR_DRAFT)

    #  Phiên duyệt đang/đã chạy trên bộ máy dùng chung. `0` = chưa gửi duyệt.
    approval_instance_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Giấy GNP sinh ra sau khi duyệt (QĐ-NP5). `0` = chưa sinh hoặc sinh hỏng —
    #  hỏng thì `entity_hooks.fire` đã ghi lý do vào phiếu duyệt, không nuốt im.
    document_id: Mapped[int] = mapped_column(BigInteger, default=0)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #  Lý do từ chối / trả về — chép từ phiếu duyệt để màn chi tiết không phải
    #  gọi thêm một lượt sang bộ máy duyệt chỉ để hiện một dòng chữ.
    decision_note: Mapped[str] = mapped_column(String(500), default="")

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    handovers = relationship(
        "LeaveHandover",
        primaryjoin="foreign(LeaveHandover.request_id) == LeaveRequest.id",
        order_by="LeaveHandover.sort_order",
        uselist=True,
        viewonly=True,
    )


class LeaveHandover(Base, AuditMixin):
    """Người nhận bàn giao việc trong thời gian nghỉ — `lsNhanVienBanGiao` của DT1.

    Bảng con chứ không phải một cột `handover_employee_id` như giấy GNP đang có:
    nghỉ dài thì bàn giao cho nhiều người, mỗi người một mảng việc. Một cột thì
    người thứ hai trở đi phải viết vào ô lý do, và không ai truy được.
    """

    __tablename__ = "tab_leave_handover"
    __table_args__ = (Index("ix_leave_handover_request", "request_id"),)

    request_id: Mapped[int] = mapped_column(BigInteger, default=0)
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Bàn giao CÁI GÌ. Bỏ trống được — nghỉ một ngày thì thường không cần ghi.
    content: Mapped[str] = mapped_column(String(500), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
