"""`tab_change_log` — LỚP MÁY GHI: giá trị TRƯỚC và SAU (bao-CR-402, P4).

Đây là lớp đóng **BM-005**. Hôm nay `tab_audit_log` chỉ nói *"user 24 đã sửa
purchase_order 129"* — không nói sửa ô nào, từ bao nhiêu sang bao nhiêu. Cái
giá của khoảng trống đó đã trả bằng tiền mặt: sự cố 07/09/2026 phải mở thẳng
cơ sở dữ liệu ra soi mới biết đơn giá đã bị đổi.

**Một dòng = MỘT TRƯỜNG** với thao tác sửa, chứ không phải một dòng JSON gom cả
bản ghi. Câu hỏi hay hỏi nhất lúc truy sự cố là *"đơn giá dòng này ai đổi"* —
với một dòng mỗi trường nó là `WHERE field = 'unit_price'`, có chỉ mục, chạy
trên bảng vài triệu dòng cũng xong; với JSON thì phải bới bằng hàm và quét cả
bảng. Thêm và xóa thì ngược lại: không có "trường nào đổi" để mà hỏi, chỉ có
"bản ghi đó lúc ấy trông ra sao" — nên chụp nguyên vào `snapshot_json`.

Không dùng `AuditMixin`, cùng lẽ với `tab_request_log`: bảng này CHỈ THÊM, nên
`updated_at` / `updated_by` là hai cột chết nhân với vài triệu dòng.

⚠️ Bảng này nằm trong `NO_LOG_TABLES` — lớp ORM không bao giờ được ghi chính
nó, nếu không mỗi dòng thay đổi lại đẻ ra một dòng thay đổi (bẫy 2 ở §6).

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.3.
"""
from datetime import datetime

from sqlalchemy import (BINARY, JSON, BigInteger, Boolean, DateTime, Index, SmallInteger,
                        String, Text, func)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base
from app.core.logging_codes import CHANGE_OP_UPDATE


class ChangeLog(Base):
    __tablename__ = "tab_change_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    #  Người bấm nút. Lấy từ ngữ cảnh chứ không từ tham số — tầng ORM không biết
    #  ai gọi nó, và đó chính là lý do `RequestContext` tồn tại.
    created_by: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    #  QĐ-B (§4.5): `BINARY(16)`. Đây là sợi dây nối ba bảng nhật ký — có nó thì
    #  một lần bấm nút dựng lại được đủ: lượt gọi nào, dấu vết gì, đổi những ô nào.
    request_id: Mapped[bytes | None] = mapped_column(BINARY(16), nullable=True, index=True)
    session_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    #  Tên bảng THẬT (`tab_purchase_order_item`), không phải tên entity phân
    #  quyền (`purchase_order`). Tầng ORM chỉ biết bảng; quy đổi sang entity là
    #  việc của màn đọc (P5), và quy đổi sai thì thà không quy đổi.
    table_name: Mapped[str] = mapped_column(String(64), default="", index=True)
    row_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    op: Mapped[int] = mapped_column(SmallInteger, default=CHANGE_OP_UPDATE)

    #  Chỉ có nghĩa khi `op = 2`. Thêm/xóa thì để rỗng và đọc `snapshot_json`.
    field: Mapped[str] = mapped_column(String(64), default="", index=True)
    before_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    #  Chỉ có nghĩa khi `op = 1` / `op = 3` — cả bản ghi, ĐÃ CHE. Cũng là chỗ
    #  chứa con số của dòng GỘP khi nhập liệu hàng loạt (bẫy 3 ở §6).
    snapshot_json: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)

    #  Trường bị che: có đổi, nhưng giá trị KHÔNG ghi. Phải là cột riêng chứ
    #  không để trống hai ô giá trị — "đã che" và "đổi từ rỗng sang rỗng" là hai
    #  chuyện khác nhau, mà lúc đi tra thì khác nhau rất nhiều.
    is_masked: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        #  Dựng lịch sử một dòng dữ liệu: "cột này của dòng 4412 đã qua tay ai".
        Index("ix_change_log_row", "table_name", "row_id", "id"),
    )
