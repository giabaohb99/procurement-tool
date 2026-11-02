"""Sổ VIỆC CHẠY NGẦM (bao-CR-703): mỗi lần một task Celery chạy là một dòng — lúc bắt đầu, lúc xong, bao lâu, kết cục.

Ghi bằng tín hiệu Celery (`signals.py`), không sửa từng task. Không mang AuditMixin: dòng do máy ghi, không ai sửa.
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base


class JobRun(Base):
    __tablename__ = "tab_job_run"
    __table_args__ = (Index("ix_job_run_task_started", "task_name", "started_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_name: Mapped[str] = mapped_column(String(120), default="")
    task_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)          # JobRunStatus
    result_summary: Mapped[str] = mapped_column(Text, default="")        # kết quả trả về, cắt 2000 ký tự
    error: Mapped[str] = mapped_column(Text, default="")                 # dòng lỗi cuối, cắt 2000 ký tự
    worker: Mapped[str] = mapped_column(String(120), default="")
