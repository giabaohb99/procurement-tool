"""SỔ VĂN BẢN và BỘ ĐẾM CẤP SỐ.

Mô hình theo lối AMIS Văn thư: **sổ là một bản ghi riêng** chứ không phải một
giá trị enum trên văn bản. Mỗi sổ có người quản lý, người xem đích danh, và **bộ
đếm số của riêng nó** — sổ Công văn đến 2026 đếm 1, 2, 3… độc lập với sổ Quyết định
đi 2026.

Vì sao tách bảng thành viên (`tab_document_book_member`) thay vì nhét mảng id vào
một cột JSON: cần trả lời được câu ngược lại — *"người này đang quản lý / xem
được những sổ nào"* — mà cột JSON thì không index được, phải quét cả bảng.
"""
from sqlalchemy import (BigInteger, Boolean, Index, Integer, SmallInteger, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class DocumentBook(Base, AuditMixin):
    """Một quyển sổ: sổ văn bản đến, sổ văn bản đi hoặc sổ văn bản nội bộ."""

    __tablename__ = "tab_document_book"
    #  Danh sách sổ luôn lọc theo pháp nhân + loại sổ + còn dùng.
    __table_args__ = (Index("ix_doc_book_company", "company_id", "kind", "is_active"),)

    #  Mã sổ đi vào khóa bộ đếm (`book:{code}:{năm}`) nên phải duy nhất và
    #  KHÔNG đổi sau khi đã cấp số — đổi là mất dấu toàn bộ số đã cấp.
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    # 1 văn bản đến · 2 văn bản đi · 3 văn bản nội bộ
    kind: Mapped[int] = mapped_column(SmallInteger, default=1)
    description: Mapped[str] = mapped_column(Text, default="")

    #  Pháp nhân sở hữu sổ. 13 pháp nhân, mỗi nơi mở sổ riêng — đây cũng là
    #  chiều lọc phạm vi dữ liệu (`SCOPE_FIELDS`).
    #
    #  KHÔNG có `department_id`: quyền xem sổ cấp cho **người đích danh**
    #  (`tab_document_book_member`), không cấp theo phòng ban. Cấp theo phòng ban
    #  thì người mới vào phòng tự thấy sổ, người chuyển đi tự mất — hai hành vi
    #  ngược nhau mà người mở sổ không hề chọn.
    company_id: Mapped[int] = mapped_column(BigInteger)

    #  Tiền tố in trước số thứ tự khi hiển thị: `CVĐ` → `CVĐ 08/2026`.
    number_prefix: Mapped[str] = mapped_column(String(20), default="")
    #  Sang năm mới đếm lại từ 1. Đúng lệ hành chính, nên mặc định bật.
    reset_yearly: Mapped[bool] = mapped_column(Boolean, default=True)
    #  Số đầu tiên của sổ, cho trường hợp chuyển từ sổ giấy đang dở sang.
    start_no: Mapped[int] = mapped_column(Integer, default=1)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DocumentBookMember(Base, AuditMixin):
    """Ai quản lý và ai được xem một quyển sổ.

    `role` 1 = người quản lý (xem, sửa, xóa sổ, cấp số) · 2 = người xem.
    """

    __tablename__ = "tab_document_book_member"
    __table_args__ = (
        UniqueConstraint("book_id", "employee_id", "role", name="uq_book_member"),
        #  Trả lời câu ngược: "người này quản lý / xem được những sổ nào".
        Index("ix_doc_book_member_emp", "employee_id", "role"),
    )

    book_id: Mapped[int] = mapped_column(BigInteger)
    #  ID NHÂN SỰ (`tab_employee`), không phải id tài khoản.
    employee_id: Mapped[int] = mapped_column(BigInteger)
    role: Mapped[int] = mapped_column(SmallInteger, default=2)


class NumberSequence(Base, AuditMixin):
    """Bộ đếm cấp số — bảng nhỏ nhất nhưng quan trọng nhất của cả phân hệ.

    Một dòng cho mỗi (sổ × năm), khóa bằng `scope_key`. Cách cấp số duy nhất
    được phép nằm ở `number_service.next_number()`: khóa dòng bằng
    `SELECT ... FOR UPDATE`, **trong cùng transaction với việc ghi bản ghi**.

    Ba điều cấm, mỗi cái đều sinh ra hai văn bản trùng số hoặc thủng số:
      - lấy `MAX(số) + 1`;
      - đếm bằng Redis hay bất cứ thứ gì ngoài cơ sở dữ liệu;
      - cấp số ở một transaction riêng rồi mới ghi bản ghi.
    """

    __tablename__ = "tab_number_sequence"

    #  Ba dạng khóa đang dùng:
    #    `book:{mã sổ}:{năm}`      — số đến / số đi / số nội bộ theo từng sổ
    #    `doc:{mã pháp nhân}:{mã loại}`        — mã tài liệu bất biến
    #    `out:{mã pháp nhân}:{năm}:{mã loại}`  — số hiệu văn bản đi theo loại
    scope_key: Mapped[str] = mapped_column(String(150), unique=True)
    year: Mapped[int] = mapped_column(SmallInteger)
    #  Số đã cấp gần nhất. Số kế tiếp = giá trị này + 1.
    current_no: Mapped[int] = mapped_column(Integer, default=0)
