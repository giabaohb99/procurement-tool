"""Mẫu email thông báo theo BƯỚC (event) — sửa được trên /system/settings.

Mỗi sự kiện thông báo (vd `dx_approved`) có TỐI ĐA một dòng: công tắc bật/tắt email
+ tiêu đề + thân HTML. **Không có dòng** thì dùng mẫu mặc định trong code
(`email_template_service.DEFAULTS`) — nên bảng chỉ chứa phần người dùng ĐÃ SỬA, và
prod chạy lại seed không đè lên (giống phân quyền/danh mục đã sửa trên UI).

`event` là khóa tự nhiên (unique). `body_html` là HTML đầy đủ, render bằng chung
engine `notification.service.render_template` (`{{ var }}`, `{% if cond %}…{% endif %}`).
"""
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class EmailTemplate(Base, AuditMixin):
    __tablename__ = "tab_email_template"

    #  Mã sự kiện, vd "dx_approved". Một sự kiện một dòng.
    event: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(150), default="")
    #  Công tắc EMAIL của bước này (chuông in-app không chịu ảnh hưởng).
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    subject: Mapped[str] = mapped_column(String(255), default="")
    body_html: Mapped[str] = mapped_column(Text, default="")
