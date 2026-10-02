"""Quyền XEM TỪNG BÁO CÁO — `tab_report_access`.

Cùng HÌNH DẠNG với `tab_doc_folder_access` / `tab_document_access` (bốn chủ
thể, cấm thắng cho phép, thu hồi là đánh dấu, có hạn) — CỐ Ý, để dùng lại được
`core/subject_match.py` thay vì chép luật khớp chủ thể một lần nữa. Khác đúng
MỘT điểm: không có cột `level` — xem một báo cáo chỉ có hai trạng thái (được /
không), không có mức chồng lên nhau như quyền thư mục.

Gác KÉP, KHÔNG mở rộng dữ liệu: một dòng CHO PHÉP ở đây chỉ mở cửa vào
`/summary` + `/summary/export` của ĐÚNG báo cáo đó — quyền hành động
(`require(entity, action)`) và phạm vi dữ liệu (`apply_scope`) của phân hệ gốc
vẫn áp nguyên, không đổi. Xem `report_access/guard.py`.
"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base
from app.core.subject_match import SUBJECT_EMPLOYEE


class ReportAccess(Base, AuditMixin):
    __tablename__ = "tab_report_access"
    __table_args__ = (
        Index("ix_report_access_subject", "subject_kind", "subject_id"),
        Index("ix_report_access_key", "report_key", "effect"),
    )
    #  ⚠️ Cùng lý do KHÔNG có UNIQUE với `tab_doc_folder_access`/`tab_document_access`:
    #  `revoked_at IS NULL` không chặn trùng được bằng UNIQUE thường. Chống
    #  trùng làm ở `report_access/grant_service.py` — có dòng còn sống cùng
    #  (report_key, subject_kind, subject_id, effect) thì SỬA dòng đó chứ
    #  không thêm dòng mới.

    #  `ReportKey` (`core/report_keys.py`) — SỐ ĐÃ CẤP KHÔNG ĐỔI, KHÔNG TÁI
    #  DÙNG (xem luật bất biến ở đầu tệp đó).
    report_key: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    #  1 người (id NHÂN SỰ) · 2 phòng ban · 3 pháp nhân · 4 vai trò — cùng bốn
    #  số với `document/access_model.SUBJECT_*` (`core/subject_match.py` re-export).
    subject_kind: Mapped[int] = mapped_column(SmallInteger, default=SUBJECT_EMPLOYEE)
    subject_id: Mapped[int] = mapped_column(BigInteger)

    #  1 cho phép · 2 cấm. CẤM thắng — xem `report_access/service.viewable_keys`.
    effect: Mapped[int] = mapped_column(SmallInteger, default=1)

    #  Giữ cột hạn dù UI chưa mở nhập (câu hỏi treo Q2 của plan) — cần sẵn để
    #  dùng lại `core/subject_match.still_live_condition` không phải vá thêm
    #  cột sau này.
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    #  Trống = không hạn.
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    reason: Mapped[str] = mapped_column(String(500), default="")

    #  Thu hồi: ghi mốc, KHÔNG xóa dòng (G19, G20 — cùng luật với văn bản/thư mục).
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_by: Mapped[int] = mapped_column(BigInteger, default=0)
    revoke_reason: Mapped[str] = mapped_column(String(500), default="")
