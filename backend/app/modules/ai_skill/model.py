"""Bảng của Kho skill AI (bao-CR-621, doc 21 §4.1).

  tab_ai_skill_set      — BỘ skill: nhóm theo chủ đề / phòng, mang phạm vi quản trị + mức bảo mật
  tab_ai_skill          — một skill: tên máy (slug), tóm tắt cho AI chọn, bản nháp đang soạn
  tab_ai_skill_version  — phiên bản đã XUẤT BẢN (chỉ thêm, không sửa)
  tab_ai_skill_file     — tệp đính kèm dạng chữ của skill
  tab_ai_skill_access   — ai được ĐỌC bộ / skill (khuôn `tab_report_access`: chủ thể, cấm thắng, có hạn, thu hồi là
                          đánh dấu) + cột `include_children` cho phòng ban

Phạm vi QUẢN TRỊ (ai soạn được bộ nào) đi theo entity `ai_skill` qua `SCOPE_FIELDS` trên `tab_ai_skill_set`; quyền
ĐỌC nội dung (ai được AI của mình đọc skill nào) là bảng access, hai chuyện tách hẳn.
"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Index, Integer, SmallInteger, String, Text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base, SoftDeleteMixin

from .constants import AccessTarget, SecurityLevel, SkillSetStatus, SkillStatus

#  Text của MySQL chỉ 64 KB — nội dung skill tới 200 nghìn ký tự (UTF-8 tới ~800 KB) cần MEDIUMTEXT.
LongText = Text().with_variant(mysql.MEDIUMTEXT(), "mysql")


class AiSkillSet(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "tab_ai_skill_set"

    code: Mapped[str] = mapped_column(String(50), default="", index=True)
    name: Mapped[str] = mapped_column(String(150), default="")
    description: Mapped[str] = mapped_column(String(500), default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    #  Phòng CHỦ QUẢN — trưởng phòng (phạm vi `dept`) soạn được bộ của phòng mình. 0 = bộ chung công ty.
    owner_department_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=int(SkillSetStatus.DRAFT))
    security_level: Mapped[int] = mapped_column(SmallInteger, default=int(SecurityLevel.OPEN))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class AiSkill(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "tab_ai_skill"
    __table_args__ = (Index("ix_ai_skill_set_slug", "skill_set_id", "slug"),)

    skill_set_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    #  Tên máy AI gọi: chữ không dấu, số, `-` `_`; duy nhất trong BỘ (kiểm ở service — UNIQUE thường vướng xóa mềm).
    slug: Mapped[str] = mapped_column(String(100), default="")
    title: Mapped[str] = mapped_column(String(200), default="")
    #  Một câu cho AI biết KHI NÀO dùng skill này — AI chọn skill bằng chính câu này.
    summary: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[int] = mapped_column(SmallInteger, default=int(SkillStatus.DRAFT))
    current_version_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Bản đang soạn (chưa xuất bản). Xuất bản = chép thành một dòng `tab_ai_skill_version` mới.
    draft_body_md: Mapped[str] = mapped_column(LongText, default="")
    draft_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class AiSkillVersion(Base, AuditMixin):
    __tablename__ = "tab_ai_skill_version"
    __table_args__ = (Index("ix_ai_skill_version_skill", "skill_id", "version_no"),)

    skill_id: Mapped[int] = mapped_column(BigInteger, default=0)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(200), default="")
    summary: Mapped[str] = mapped_column(String(500), default="")
    body_md: Mapped[str] = mapped_column(LongText, default="")
    change_note: Mapped[str] = mapped_column(String(500), default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_by: Mapped[int] = mapped_column(BigInteger, default=0)


class AiSkillFile(Base, AuditMixin):
    """Tệp đính kèm DẠNG CHỮ (md, json, csv…) — lưu thẳng nội dung, AI đọc qua MCP; tệp nhị phân không nhận."""

    __tablename__ = "tab_ai_skill_file"
    __table_args__ = (Index("ix_ai_skill_file_skill", "skill_id", "path"),)

    skill_id: Mapped[int] = mapped_column(BigInteger, default=0)
    path: Mapped[str] = mapped_column(String(200), default="")      # đường dẫn tương đối, vd references/guide.md
    size: Mapped[int] = mapped_column(Integer, default=0)            # byte
    sha256: Mapped[str] = mapped_column(String(64), default="")
    content_text: Mapped[str] = mapped_column(LongText, default="")


class AiSkillAccess(Base, AuditMixin):
    """Ai được ĐỌC bộ / skill. Cùng hình dạng `tab_report_access` + `target_*` + `include_children`."""

    __tablename__ = "tab_ai_skill_access"
    __table_args__ = (
        Index("ix_ai_skill_access_target", "target_kind", "target_id"),
        Index("ix_ai_skill_access_subject", "subject_kind", "subject_id"),
    )

    target_kind: Mapped[int] = mapped_column(SmallInteger, default=int(AccessTarget.SKILL_SET))
    target_id: Mapped[int] = mapped_column(BigInteger, default=0)
    subject_kind: Mapped[int] = mapped_column(SmallInteger, default=1)
    subject_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Chỉ có nghĩa với chủ thể phòng ban: True = phòng con (theo cột `parent`) cũng nhận.
    include_children: Mapped[bool] = mapped_column(Boolean, default=True)
    effect: Mapped[int] = mapped_column(SmallInteger, default=1)       # 1 cho phép · 2 cấm (cấm thắng)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    reason: Mapped[str] = mapped_column(String(500), default="")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_by: Mapped[int] = mapped_column(BigInteger, default=0)
    revoke_reason: Mapped[str] = mapped_column(String(500), default="")
