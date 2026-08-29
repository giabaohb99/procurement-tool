"""Phân hệ Công việc — cụm nhãn tùy biến của từng list.

Quy ước chung của phân hệ nằm ở đầu `model.py`. Thiết kế:
`doc/erp/cong-viec/02-bang-du-lieu.md` §4.

**Độ ưu tiên NAY LÀ MỘT TRƯỜNG TÙY BIẾN**, không còn là cột cứng `tab_work_task.
priority` (bỏ ở migration `b2f7c1d94a30`). Mỗi list được nạp sẵn một trường
`system_key = "priority"` kèm bốn giá trị P1…P4, rồi muốn đổi tên, đổi màu, thêm
bậc P5 hay xóa hẳn đều được — bậc ưu tiên của phòng kinh doanh không nhất thiết
giống phòng kỹ thuật. Cột cứng cũ không cho làm gì trong số đó.

**TAG cũng vậy** — hai bảng `tab_work_tag` / `tab_work_task_tag` đã bị bỏ ở
migration `c8a1d4f60b72`. Tag nay chỉ là một trường tùy biến kiểu CHỌN NHIỀU tên
"Tag", nạp sẵn cho list mới nhưng KHÔNG mang `system_key`: đổi tên, đổi bộ giá
trị hay xóa hẳn đều được như mọi trường khác. Giữ bảng riêng chỉ để phục vụ đúng
một trường thì mọi thứ (lọc, sắp xếp, vẽ trên thẻ, ô nhập ở panel chi tiết) phải
viết hai lần — một cho tag, một cho trường tùy biến — và hai bản ấy đã bắt đầu
lệch nhau.
"""
from decimal import Decimal

from sqlalchemy import (BigInteger, ForeignKey, Index, Numeric, SmallInteger,
                        String, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base
from app.modules.work.model import WorkLabelFieldType


class WorkLabelField(Base, AuditMixin):
    """Một TRƯỜNG nhãn của list — "Phiên bản", "Độ ưu tiên", "Tag"… (B-08).

    Trường THUỘC LIST, không dùng chung toàn hệ. Chuyển task sang list khác
    (B-10) là mất hết giá trị nhãn cũ — trường của list nguồn không có nghĩa ở
    list đích.
    """

    __tablename__ = "tab_work_label_field"
    __table_args__ = (UniqueConstraint("list_id", "name", name="uq_work_label_field"),)

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    list_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_list.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100), default="")
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Kiểu của trường (B-13). Mặc định `SINGLE` để mọi trường khai TRƯỚC B-13
    #  giữ nguyên hành vi cũ mà không phải vá dữ liệu.
    field_type: Mapped[int] = mapped_column(
        SmallInteger, default=int(WorkLabelFieldType.SINGLE)
    )
    #  Trường do HỆ nạp sẵn lúc tạo list: `"priority"` = Độ ưu tiên. Rỗng = do
    #  người dùng tự khai.
    #
    #  Chỉ là một CÁI MÓC để mã nguồn tìm lại đúng trường ấy (tô màu thanh Gantt,
    #  đếm biểu đồ ở Tổng quan) — không khóa gì cả: tên, bộ giá trị, màu và cả
    #  việc xóa trường đều do từng dự án tự quyết, y như mọi trường tùy biến
    #  khác. Không có móc này thì phải dò theo TÊN, mà tên thì người dùng đổi
    #  được ngay trong menu «Tùy chỉnh».
    system_key: Mapped[str] = mapped_column(String(30), default="", index=True)


class WorkLabelOption(Base, AuditMixin):
    """Một giá trị trong bộ giá trị của trường nhãn ("Thumua", "v2"…)."""

    __tablename__ = "tab_work_label_option"
    __table_args__ = (UniqueConstraint("field_id", "name", name="uq_work_label_option"),)

    field_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_label_field.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100), default="")
    color: Mapped[str] = mapped_column(String(20), default="")
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0)


class WorkTaskLabel(Base, AuditMixin):
    """Giá trị của một TRƯỜNG tùy biến trên một task (B-08 + B-13).

    Một dòng = một giá trị. Kiểu **chọn nhiều** đẻ nhiều dòng cùng
    `(task_id, field_id)`; các kiểu còn lại đúng một dòng.

    ⚠️ **Unique `(task_id, field_id)` đã bị GỠ ở B-13.** Trước đó chính nó là
    ràng buộc "chọn một", nhưng ràng buộc ấy không diễn đạt nổi kiểu chọn nhiều.
    Nay luật "kiểu này chỉ được một giá trị" do `set_label` giữ — nó xóa sạch
    dòng cũ của trường rồi mới ghi. Bỏ tầng service đó ra là task lặng lẽ mọc
    hai giá trị cho một trường chọn-một.

    Cột `value_*` chỉ MỘT cái có nghĩa, tùy `field.field_type`; các cột kia để
    rỗng. Cố ý làm bảng bẹt thay vì mỗi kiểu một bảng: sáu bảng con thì mọi query
    đọc nhãn đều thành sáu lần join.
    """

    __tablename__ = "tab_work_task_label"
    __table_args__ = (Index("ix_work_task_label_task_field", "task_id", "field_id"),)

    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_task.id", ondelete="CASCADE"), index=True
    )
    field_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_label_field.id", ondelete="CASCADE"), index=True
    )
    #  Rỗng với bốn kiểu không có bộ giá trị (chữ · số · ngày · người).
    option_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tab_work_label_option.id", ondelete="CASCADE"), nullable=True
    )
    value_text: Mapped[str] = mapped_column(String(500), default="")
    #  `Numeric` chứ không `Float`: số tiền/số lượng gõ tay mà để dấu phẩy động
    #  thì 0.1 + 0.2 hiện ra 0.30000000000000004 ngay trên thẻ.
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    #  Ngày lưu CHUỖI `YYYY-MM-DD`, đúng như `start_date`/`due_date` của task —
    #  cả phân hệ dùng một khuôn, không trộn hai kiểu ngày.
    value_date: Mapped[str] = mapped_column(String(10), default="")
    value_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
