"""Sổ THAY ĐỔI do bot / Trợ lý AI ghi vào ERP + hoàn tác 24 giờ (ai-CR-182, phase 15.1).

Mỗi lần người dùng bấm xác nhận cho bot ghi phiếu (tạo nháp · sửa · xóa · dùng lại nháp · gửi duyệt ·
lập bộ tài khoản) thì thêm MỘT dòng ở đây: ảnh TRƯỚC / SAU của phần đã đổi, dấu trạng thái phiếu ngay
sau khi ghi (`after_sig`) để biết có ai sửa chen vào, và trạng thái hoàn tác.

Bảng nằm ở DB ERP (không phải DB của dịch vụ AI): web ERP đọc, ảnh phiếu là dữ liệu ERP. Vì vậy
tên bảng KHÔNG mang tiền tố `tab_agent_` (xem `core/agent_tables.py`).

Module MỚI → cột kiểu / trạng thái lưu SMALLINT theo IntEnum (R2 / QĐ-11), chữ Việt chỉ ở lớp hiển thị.
"""
from datetime import datetime
from enum import IntEnum

from sqlalchemy import JSON, BigInteger, DateTime, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class ChangeAction(IntEnum):
    """Việc bot đã làm trên phiếu."""

    CREATE = 1      # tạo phiếu nháp
    UPDATE = 2      # sửa phiếu qua thẻ đề xuất
    DELETE = 3      # xóa (mềm) phiếu
    SUBMIT = 4      # gửi duyệt
    REUSE = 5       # dùng lại phiếu nháp (thêm dòng / ghi đè / sửa đè đơn nghỉ trùng ngày)
    ACCOUNT = 6     # lập bộ tài khoản (vai trò + phạm vi)
    PUBLISH = 7     # xuất bản skill của Kho skill AI (bao-CR-634) — phiên bản chỉ thêm, không hoàn tác


class UndoStatus(IntEnum):
    NONE = 0        # chưa hoàn tác
    UNDONE = 1      # đã hoàn tác
    BLOCKED = 2     # đã thử hoàn tác nhưng bị chặn vì phiếu đã đổi / đã gửi duyệt / không còn


class ChangeSource(IntEnum):
    """Kênh người dùng bấm xác nhận."""

    UNKNOWN = 0
    TELEGRAM = 1
    WEB = 2
    ZALO = 3
    MCP = 4         # AI riêng của nhân sự qua cổng MCP (bao-CR-634)


ACTION_LABELS = {
    ChangeAction.CREATE: "Tạo",
    ChangeAction.UPDATE: "Sửa",
    ChangeAction.DELETE: "Xóa",
    ChangeAction.SUBMIT: "Gửi duyệt",
    ChangeAction.REUSE: "Dùng lại nháp",
    ChangeAction.ACCOUNT: "Lập bộ tài khoản",
    ChangeAction.PUBLISH: "Xuất bản",
}

UNDO_STATUS_LABELS = {
    UndoStatus.NONE: "",
    UndoStatus.UNDONE: "Đã hoàn tác",
    UndoStatus.BLOCKED: "Không hoàn tác được",
}

SOURCE_LABELS = {
    ChangeSource.UNKNOWN: "",
    ChangeSource.TELEGRAM: "Telegram",
    ChangeSource.WEB: "Web",
    ChangeSource.ZALO: "Zalo",
    ChangeSource.MCP: "AI riêng (MCP)",
}


class AssistantChange(Base, AuditMixin):
    """Một thay đổi bot đã ghi vào ERP sau khi người dùng xác nhận."""

    __tablename__ = "tab_assistant_change"

    #  Người bấm xác nhận (tài khoản ERP) — cũng là người được hoàn tác dòng này.
    user_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Loại phiếu: purchase_request · survey_request · leave_request · payment_request · work_task ·
    #  ticket · account_setup.
    entity: Mapped[str] = mapped_column(String(50), default="")
    entity_id: Mapped[int] = mapped_column(BigInteger, default=0)
    doc_code: Mapped[str] = mapped_column(String(50), default="")
    action: Mapped[int] = mapped_column(SmallInteger, default=int(ChangeAction.UPDATE))     # ChangeAction
    #  Câu tiếng Việt đọc được: «Sửa đơn nghỉ phép NP001: Đến ngày», «Tạo YCMH nháp YCMH00123».
    summary: Mapped[str] = mapped_column(String(300), default="")
    #  Ảnh TRƯỚC / SAU của phần đã đổi (các trường + dòng nếu có). Tạo mới: before = NULL; xóa: after = NULL.
    #  Mỗi cột tối đa 64 KB — vượt thì cắt bớt dòng và ghi `truncated: true`.
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    #  Dấu trạng thái phiếu NGAY SAU khi ghi — khác dấu hiện tại nghĩa là có người sửa chen vào.
    after_sig: Mapped[str] = mapped_column(String(64), default="")
    source: Mapped[int] = mapped_column(SmallInteger, default=int(ChangeSource.UNKNOWN))    # ChangeSource
    undo_status: Mapped[int] = mapped_column(SmallInteger, default=int(UndoStatus.NONE))    # UndoStatus
    undone_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    undone_by: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Dòng ghi việc hoàn tác trỏ về dòng bị hoàn tác; 0 với dòng thường.
    undo_of: Mapped[int] = mapped_column(BigInteger, default=0)

    __table_args__ = (
        Index("ix_assistant_change_user_created", "user_id", "created_at"),
        Index("ix_assistant_change_entity", "entity", "entity_id"),
    )
