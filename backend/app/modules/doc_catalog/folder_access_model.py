"""QUYỀN TRÊN TỪNG THƯ MỤC — `tab_doc_folder_access` (phase 04, duoc-CR-475).

Cùng HÌNH DẠNG với `document/access_model.DocumentAccess` (bốn chủ thể, cấm
thắng cho phép, thu hồi là đánh dấu, có hạn) — CỐ Ý, để dùng lại được
`core/subject_match.py` thay vì chép luật khớp chủ thể một lần nữa. Khác đúng
MỘT điểm: thay vì bốn cờ `can_read/write/delete`, ở đây là MỘT cột `level`
(`FolderAccessLevel`, R2/QĐ-11) vì quyền thư mục có BA MỨC đặt CHỒNG lên nhau
(Xem ⊂ Đóng góp ⊂ Quản lý), không phải ba hành động độc lập.

`level` chỉ có nghĩa với dòng CHO PHÉP (`effect=EFFECT_ALLOW`); dòng CẤM
(`effect=EFFECT_DENY`) khóa toàn bộ khả năng thấy thư mục bất kể `level` ghi
gì — xem `folder_access_service.effective_levels` (CẤM thắng, không có "cấm
một phần"). `folder_access_grant_service.grant()` ép `level=PRIVATE(0)` khi
lưu dòng cấm để tránh đọc nhầm một con số vô nghĩa.

Kế thừa XUỐNG nhánh con qua `path` của `DocFolder` (không lưu lặp lại ở đây) —
`folder_access_service` tự đi bộ `path` để gom dòng của thư mục VÀ tổ tiên.
"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base
from app.core.subject_match import SUBJECT_EMPLOYEE

from .folder_constants import FolderAccessLevel


class DocFolderAccess(Base, AuditMixin):
    __tablename__ = "tab_doc_folder_access"
    __table_args__ = (
        Index("ix_doc_folder_access_subject", "subject_kind", "subject_id"),
        Index("ix_doc_folder_access_folder", "folder_id", "effect"),
    )
    #  ⚠️ Cùng lý do KHÔNG có UNIQUE với `tab_document_access` (xem chú thích ở
    #  đó): `revoked_at IS NULL` không chặn được trùng bằng UNIQUE thường. Chống
    #  trùng làm ở `folder_access_grant_service.grant()` — có dòng còn sống thì
    #  SỬA dòng đó chứ không thêm dòng mới.

    folder_id: Mapped[int] = mapped_column(BigInteger)

    #  1 người (id NHÂN SỰ) · 2 phòng ban · 3 pháp nhân · 4 vai trò — cùng bốn
    #  số với `document/access_model.SUBJECT_*`.
    subject_kind: Mapped[int] = mapped_column(SmallInteger, default=SUBJECT_EMPLOYEE)
    subject_id: Mapped[int] = mapped_column(BigInteger)

    #  1 cho phép · 2 cấm — cùng hai số với `document/access_model.EFFECT_*`.
    effect: Mapped[int] = mapped_column(SmallInteger, default=1)

    #  `FolderAccessLevel`: 0 Riêng tư · 1 Xem · 2 Đóng góp · 3 Quản lý. Chỉ có
    #  nghĩa khi `effect=CHO PHÉP` — xem chú thích đầu tệp.
    level: Mapped[int] = mapped_column(SmallInteger, default=int(FolderAccessLevel.VIEW))

    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    #  Trống = không hạn.
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    reason: Mapped[str] = mapped_column(String(500), default="")

    #  Thu hồi: ghi mốc, KHÔNG xóa dòng (G19, G20 — cùng luật với văn bản).
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_by: Mapped[int] = mapped_column(BigInteger, default=0)
    revoke_reason: Mapped[str] = mapped_column(String(500), default="")
