"""Schema vào của Kho skill AI — trần độ dài khớp ĐÚNG `String(n)` ở model (SQLite trong test không ép VARCHAR,
`.claude/rules/backend-input-limits.md`)."""
import re
from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.report_period import MAX_REPORT_YEAR, MIN_REPORT_YEAR
from app.core.subject_match import EFFECT_ALLOW, EFFECT_DENY, SUBJECT_LABELS

from .constants import (BODY_MAX_CHARS, CODE_MAX, DESC_MAX, MAX_GRANT_SUBJECTS, NAME_MAX, NOTE_MAX, SLUG_MAX,
                        SUBJECT_JOB_LEVEL, SUBJECT_POSITION, SUMMARY_MAX, TITLE_MAX, AccessTarget, SecurityLevel,
                        SkillSetStatus, SkillStatus)

SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,99}$")
SLUG_HINT = ("Tên skill 2–100 ký tự, chỉ chữ không dấu, số, gạch ngang, gạch dưới; ký tự đầu là chữ hoặc số "
             "(vd: bao-cao-mua-hang-thang).")
MAX_ID = 2**63 - 1
SUBJECT_KINDS = set(SUBJECT_LABELS) | {SUBJECT_POSITION, SUBJECT_JOB_LEVEL}


def check_slug(value: str) -> str:
    value = (value or "").strip()
    if not SLUG_RE.match(value):
        raise ValueError(SLUG_HINT)
    return value


class SkillSetIn(BaseModel):
    code: str = Field(default="", max_length=CODE_MAX)
    name: str = Field(min_length=1, max_length=NAME_MAX)
    description: str = Field(default="", max_length=DESC_MAX)
    company_id: int = Field(default=0, ge=0, le=MAX_ID)
    owner_department_id: int = Field(default=0, ge=0, le=MAX_ID)
    status: int = Field(default=int(SkillSetStatus.DRAFT))
    security_level: int = Field(default=int(SecurityLevel.OPEN))
    sort_order: int = Field(default=0, ge=0, le=100_000)

    @model_validator(mode="after")
    def _codes(self):
        if self.status not in {int(s) for s in SkillSetStatus}:
            raise ValueError(f"Trạng thái bộ skill không hợp lệ: {self.status}")
        if self.security_level not in {int(s) for s in SecurityLevel}:
            raise ValueError(f"Mức bảo mật không hợp lệ: {self.security_level}")
        return self


class SkillSetPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=NAME_MAX)
    description: str | None = Field(default=None, max_length=DESC_MAX)
    owner_department_id: int | None = Field(default=None, ge=0, le=MAX_ID)
    status: int | None = None
    security_level: int | None = None
    sort_order: int | None = Field(default=None, ge=0, le=100_000)

    @model_validator(mode="after")
    def _codes(self):
        if self.status is not None and self.status not in {int(s) for s in SkillSetStatus}:
            raise ValueError(f"Trạng thái bộ skill không hợp lệ: {self.status}")
        if self.security_level is not None and self.security_level not in {int(s) for s in SecurityLevel}:
            raise ValueError(f"Mức bảo mật không hợp lệ: {self.security_level}")
        return self


class SkillIn(BaseModel):
    slug: str = Field(max_length=SLUG_MAX)
    title: str = Field(default="", max_length=TITLE_MAX)
    summary: str = Field(default="", max_length=SUMMARY_MAX)
    body_md: str = Field(default="", max_length=BODY_MAX_CHARS)
    sort_order: int = Field(default=0, ge=0, le=100_000)

    @field_validator("slug")
    @classmethod
    def _slug(cls, value: str) -> str:
        return check_slug(value)


class SkillPatch(BaseModel):
    title: str | None = Field(default=None, max_length=TITLE_MAX)
    summary: str | None = Field(default=None, max_length=SUMMARY_MAX)
    body_md: str | None = Field(default=None, max_length=BODY_MAX_CHARS)
    status: int | None = None
    sort_order: int | None = Field(default=None, ge=0, le=100_000)

    @model_validator(mode="after")
    def _codes(self):
        if self.status is not None and self.status not in {int(s) for s in SkillStatus}:
            raise ValueError(f"Trạng thái skill không hợp lệ: {self.status}")
        return self


class PublishIn(BaseModel):
    change_note: str = Field(default="", max_length=NOTE_MAX)


class SkillFileIn(BaseModel):
    path: str = Field(min_length=1, max_length=200)
    content_text: str = Field(default="", max_length=2 * 1024 * 1024)


class AccessSubjectIn(BaseModel):
    subject_kind: int
    subject_id: int = Field(ge=0, le=MAX_ID)


class AccessGrantIn(BaseModel):
    """Cấp / cấm CÙNG một chiều cho cả danh sách chủ thể, trên MỘT bộ hoặc MỘT skill."""

    target_kind: int = Field(default=int(AccessTarget.SKILL_SET))
    target_id: int = Field(gt=0, le=MAX_ID)
    subjects: list[AccessSubjectIn] = Field(min_length=1, max_length=MAX_GRANT_SUBJECTS)
    effect: int = Field(default=EFFECT_ALLOW)
    include_children: bool = True
    reason: str = Field(default="", max_length=NOTE_MAX)
    valid_from: date | None = None
    valid_to: date | None = None

    @model_validator(mode="after")
    def _check(self):
        if self.target_kind not in {int(t) for t in AccessTarget}:
            raise ValueError(f"Đối tượng gán quyền không hợp lệ: {self.target_kind}")
        if self.effect not in (EFFECT_ALLOW, EFFECT_DENY):
            raise ValueError(f"Chiều tác động không hợp lệ: {self.effect}")
        for name, value in (("valid_from", self.valid_from), ("valid_to", self.valid_to)):
            if value is not None and not (MIN_REPORT_YEAR <= value.year <= MAX_REPORT_YEAR):
                raise ValueError(f"{name} phải trong khoảng năm {MIN_REPORT_YEAR}-{MAX_REPORT_YEAR}")
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("Ngày hết hạn phải sau ngày bắt đầu")
        if self.valid_to is not None and self.valid_to < date.today():
            raise ValueError("Ngày hết hạn phải từ hôm nay trở đi")
        for subject in self.subjects:
            if subject.subject_kind not in SUBJECT_KINDS:
                raise ValueError(f"Loại đối tượng không hợp lệ: {subject.subject_kind}")
            #  Cấp bậc 0 = "chưa khai" (JOB_LEVEL_UNKNOWN) — gán quyền cho người CHƯA khai cấp bậc là vô nghĩa.
            if subject.subject_id <= 0:
                raise ValueError("Mã đối tượng phải lớn hơn 0")
        return self


class AccessRevokeIn(BaseModel):
    reason: str = Field(default="", max_length=NOTE_MAX)
