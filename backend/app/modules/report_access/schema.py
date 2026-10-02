"""Schema cấp/thu quyền XEM TỪNG BÁO CÁO — `POST/DELETE /api/report-access/...`.

`max_length` khớp ĐÚNG `String(500)` của `model.py` (không tin SQLite ở test —
SQLite không ép độ dài VARCHAR, nên trần phải chặn ở tầng Pydantic, cùng luật
`.claude/rules/backend-input-limits.md`).
"""
from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.core.report_period import MAX_REPORT_YEAR, MIN_REPORT_YEAR
from app.core.subject_match import EFFECT_ALLOW, EFFECT_DENY, SUBJECT_LABELS

#  Trần đối tượng một lượt CẤP — đủ cho cả một phòng ban lớn, cùng trần
#  `MAX_BULK_ACCESS_SUBJECTS` của `doc_catalog/folder_access_schema.py`.
MAX_GRANT_SUBJECTS = 200

#  Trần BigInteger SIGNED của MySQL (cột `subject_id` là `BigInteger`, xem `model.py`) — một
#  id vượt mốc này không khớp bản ghi thật nào ở bất kỳ danh mục nào, cho lọt tới tầng DB chỉ
#  đổi một câu 422 rõ nghĩa thành lỗi tràn số khó hiểu hơn (cùng luật
#  `.claude/rules/backend-input-limits.md` — trần hợp lý thì chặn ở tầng schema).
MAX_SUBJECT_ID = 2**63 - 1


class ReportAccessSubjectIn(BaseModel):
    """Một đối tượng trong danh sách chọn nhiều — không mang chiều tác động
    riêng, cả lô dùng CHUNG một `effect` (`ReportAccessGrantIn.effect`)."""

    subject_kind: int
    subject_id: int = Field(gt=0, le=MAX_SUBJECT_ID)


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
        #  Dải năm hợp lý — cùng trần `MIN/MAX_REPORT_YEAR` của `core/report_period.py`
        #  (ngày NGHIỆP VỤ báo cáo, không phải ngày sinh): chặn `0001-01-01`/`9999-12-31`
        #  lọt xuống DB thay vì một câu 422 rõ nghĩa.
        for field_name, value in (("valid_from", self.valid_from), ("valid_to", self.valid_to)):
            if value is not None and not (MIN_REPORT_YEAR <= value.year <= MAX_REPORT_YEAR):
                raise ValueError(
                    f"{field_name} phải trong khoảng năm {MIN_REPORT_YEAR}-{MAX_REPORT_YEAR}")
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("Ngày hết hạn phải sau ngày bắt đầu")
        #  Hạn đã QUA KHỨ là một lượt cấp vô dụng ngay khi lưu (hiệu lực xét theo
        #  `still_live_condition` — xem `core/subject_match.py`) — chặn ở đây để người
        #  cấu hình biết ngay, không phải đi dò tại sao chủ thể vừa gán vẫn không xem được.
        if self.valid_to is not None and self.valid_to < date.today():
            raise ValueError("Ngày hết hạn phải từ hôm nay trở đi")
        for subject in self.subjects:
            if subject.subject_kind not in SUBJECT_LABELS:
                raise ValueError(f"Loại đối tượng không hợp lệ: {subject.subject_kind}")
        return self


class ReportAccessRevokeIn(BaseModel):
    """`DELETE /api/report-access/grants/{id}` — thu hồi là ĐÁNH DẤU, không xóa
    dòng (G19, G20 — cùng luật văn bản/thư mục)."""

    reason: str = Field(default="", max_length=500)
