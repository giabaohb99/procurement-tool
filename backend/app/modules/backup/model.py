"""Sao lưu CSDL định kỳ.

DbBackup: 1 dòng / 1 lần sao lưu. File dump (.sql.gz) đẩy lên R2, chỉ lưu key +
metadata ở đây để quản lý/tải lại. Bot (celery-beat) chạy 2 lần/ngày; giữ N bản
mới nhất, cũ hơn thì xóa cả file R2 lẫn dòng này (retention).
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class DbBackup(Base, AuditMixin):
    __tablename__ = "tab_db_backup"

    source: Mapped[str] = mapped_column(String(20), default="auto")     # auto (theo lịch) | manual (bấm tay)
    status: Mapped[str] = mapped_column(String(20), default="running", index=True)  # running | success | failed
    file_key: Mapped[str] = mapped_column(String(255), default="")      # key trên R2 (backups/xxx.sql.gz)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)       # dung lượng file đã nén
    message: Mapped[str] = mapped_column(Text, default="")              # thông báo lỗi nếu FAILED
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    #  bao-CR-732: 'main' = bản chính (2 lần/ngày) | 'customs' = dữ liệu tra cứu thị trường (1 lần/ngày, bỏ qua nếu
    #  không đổi). Khôi phục = bản chính + bản 'customs' mới nhất. Không đặt tên `kind`: màn Sao lưu dùng `kind` cho
    #  dòng khôi phục thử của DB bot.
    part: Mapped[str] = mapped_column(String(20), default="main", server_default="main", index=True)
    #  Dấu vân tay dữ liệu tra cứu thị trường lúc sao lưu ('<alembic>:<sha1>'), chỉ bản 'customs' điền.
    fingerprint: Mapped[str] = mapped_column(String(120), default="", server_default="")
