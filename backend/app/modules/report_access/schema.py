"""Schema cấp/thu quyền XEM TỪNG BÁO CÁO — `POST/DELETE /api/report-access/...`.

`max_length` khớp ĐÚNG `String(500)` của `model.py` (không tin SQLite ở test —
SQLite không ép độ dài VARCHAR, nên trần phải chặn ở tầng Pydantic, cùng luật
`.claude/rules/backend-input-limits.md`).
"""
from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.core.subject_match import EFFECT_ALLOW, EFFECT_DENY, SUBJECT_LABELS

#  Trần đối tượng một lượt CẤP — đủ cho cả một phòng ban lớn, cùng trần
#  `MAX_BULK_ACCESS_SUBJECTS` của `doc_catalog/folder_access_schema.py`.
MAX_GRANT_SUBJECTS = 200


class ReportAccessSubjectIn(BaseModel):
    """Một đối tượng trong danh sách chọn nhiều — không mang chiều tác động
    riêng, cả lô dùng CHUNG một `effect` (`ReportAccessGrantIn.effect`)."""

    subject_kind: int
    subject_id: int = Field(gt=0)


class ReportAccessGrantIn(BaseModel):
    """`POST /api/report-access/{key}/grants` — cấp/cấm CÙNG một chiều cho cả
    danh sách chủ thể trong một giao dịch. Trùng chủ thể (đã có dòng còn hiệu
    lực CÙNG chiều) → service SỬA dòng đó; chủ thể không tồn tại → bị SKIP,
    không chặn cả lô (xem `grant_service.grant`)."""

    subjects: list[ReportAccessSubjectIn] = Field(min_length=1, max_length=MAX_GRANT_SUBJECTS)
    effect: int = Field(default=EFFECT_ALLOW)
    reason: str = Field(default="", max_length=500)
    #  Giữ cột hạn dù UI chưa mở nhập (Q2 của plan phân quyền báo cáo) — để
    #  trống là không hạn, không bắt buộc nhập.
    valid_from: date | None = None
    valid_to: date | None = None

    @model_validator(mode="after")
    def _check_ranges(self) -> "ReportAccessGrantIn":
        if self.effect not in (EFFECT_ALLOW, EFFECT_DENY):
            raise ValueError(f"Chiều tác động không hợp lệ: {self.effect}")
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("Ngày hết hạn phải sau ngày bắt đầu")
        for subject in self.subjects:
            if subject.subject_kind not in SUBJECT_LABELS:
                raise ValueError(f"Loại đối tượng không hợp lệ: {subject.subject_kind}")
        return self


class ReportAccessRevokeIn(BaseModel):
    """`DELETE /api/report-access/grants/{id}` — thu hồi là ĐÁNH DẤU, không xóa
    dòng (G19, G20 — cùng luật văn bản/thư mục)."""

    reason: str = Field(default="", max_length=500)
