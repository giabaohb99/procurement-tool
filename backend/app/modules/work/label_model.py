"""Phân hệ Công việc — cụm nhãn: tag đa trị và nhãn tùy biến theo list.

Quy ước chung của phân hệ nằm ở đầu `model.py`. Thiết kế:
`doc/erp/cong-viec/02-bang-du-lieu.md` §4.

Vì sao Tag và Độ ưu tiên KHÔNG mô hình hóa thành nhãn tùy biến: chúng có mặt ở
mọi list và cần logic riêng (sắp xếp theo ưu tiên, lọc nhanh theo tag), nên để
cột cứng / bảng riêng. Nhãn tùy biến là chỗ cho những trường CHỈ list đó cần.
"""
from sqlalchemy import (BigInteger, ForeignKey, String, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class WorkTag(Base, AuditMixin):
    """Tag của một list (B-05). Tag THUỘC LIST, không dùng chung toàn hệ.

    Chuyển task sang list khác (B-10) là gỡ tag cũ — tag của list nguồn không có
    nghĩa ở list đích.
    """

    __tablename__ = "tab_work_tag"
    __table_args__ = (UniqueConstraint("list_id", "name", name="uq_work_tag_name"),)

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    list_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_list.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100), default="")
    color: Mapped[str] = mapped_column(String(20), default="")
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0)


class WorkTaskTag(Base, AuditMixin):
    """Nối task ↔ tag (đa trị: một task nhiều tag)."""

    __tablename__ = "tab_work_task_tag"
    __table_args__ = (UniqueConstraint("task_id", "tag_id", name="uq_work_task_tag"),)

    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_task.id", ondelete="CASCADE"), index=True
    )
    tag_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_tag.id", ondelete="CASCADE"), index=True
    )


class WorkLabelField(Base, AuditMixin):
    """Một TRƯỜNG nhãn do list tự đặt — ví dụ "Phiên bản" (B-08).

    Khác Tag ở chỗ: Tag là một trường đa trị có sẵn ở mọi list, còn đây là người
    dùng đặt THÊM TRƯỜNG mới cho riêng list của mình.
    """

    __tablename__ = "tab_work_label_field"
    __table_args__ = (UniqueConstraint("list_id", "name", name="uq_work_label_field"),)

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    list_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_list.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100), default="")
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0)


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
    """Giá trị nhãn của một task — CHỌN MỘT giá trị mỗi trường.

    Unique `(task_id, field_id)` chính là ràng buộc "single-select" (B-08 bản
    đầu). Sau này B-13 mở sang kiểu chữ/số/ngày thì THÊM cột
    `value_text` / `value_number` vào chính bảng này, không đập lại mô hình.
    """

    __tablename__ = "tab_work_task_label"
    __table_args__ = (UniqueConstraint("task_id", "field_id", name="uq_work_task_label"),)

    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_task.id", ondelete="CASCADE"), index=True
    )
    field_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_label_field.id", ondelete="CASCADE"), index=True
    )
    option_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_label_option.id", ondelete="CASCADE")
    )
