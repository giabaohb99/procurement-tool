"""YÊU CẦU VĂN BẢN — bảng **cố ý để rỗng** ở bản 1.

Chốt 14/08/2026 (quyết định 7 của plan): bỏ bước xin phép, ai có quyền
`document.create` thì tạo văn bản trực tiếp. Bảng này **không có service, không
có router, không có màn hình** — không dòng nào ghi vào đây.

Vậy tạo làm gì? Vì bước xin phép là chốt chặn mà `van-thu/00` mục 4.1 coi là
quan trọng nhất (ngăn ai cũng đẻ ra một quy trình rồi không ai biết cái nào đang
hiệu lực), và khả năng bật lại là có thật. Tạo bảng rỗng bây giờ mất một phút;
thêm bảng + hai khóa ngoại vào một hệ đang chạy thì phải canh giờ dừng.

Trong lúc chưa bật: `tab_document.document_request_id` và
`tab_document_version.created_from_request_id` luôn NULL, `doc_type.needs_request`
luôn FALSE và bị ẩn khỏi form loại văn bản.
"""
from datetime import date

from sqlalchemy import BigInteger, Date, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

REQUEST_NEW = 1       # xin soạn văn bản mới
REQUEST_AMEND = 2     # xin sửa văn bản đang có
REQUEST_REVOKE = 3    # xin bãi bỏ


class DocumentRequest(Base, AuditMixin):
    __tablename__ = "tab_document_request"

    kind: Mapped[int] = mapped_column(SmallInteger, default=REQUEST_NEW)
    #  Xin sửa / bãi bỏ thì trỏ tới văn bản đang có; xin soạn mới thì rỗng.
    target_document_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    doc_type_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    company_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    department_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    requester_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    title: Mapped[str] = mapped_column(String(500), default="")
    #  Lý do là ô BẮT BUỘC của form (B01) — không có lý do thì không phân biệt
    #  được yêu cầu thật với yêu cầu bấm nhầm.
    reason: Mapped[str] = mapped_column(Text, default="")
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    #  1 nháp · 2 đang duyệt · 3 đã duyệt · 4 từ chối · 5 đã soạn xong.
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    approved_by: Mapped[int] = mapped_column(BigInteger, default=0)
    approved_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    reject_reason: Mapped[str] = mapped_column(Text, default="")
