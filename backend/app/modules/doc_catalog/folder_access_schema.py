"""Schema cấp / thu QUYỀN TRÊN THƯ MỤC — `POST/DELETE /api/doc-folders/{id}/access`
+ cấp HÀNG LOẠT `POST .../access/bulk` + đổi mức tại chỗ `PATCH .../access/{id}`
(phase 10B, hộp «Chia sẻ» kiểu Drive — chọn nhiều đối tượng một lượt).

`max_length` khớp ĐÚNG `String(n)` của `folder_access_model.py` (CR-316).
"""
from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.core.subject_match import EFFECT_ALLOW, EFFECT_DENY, SUBJECT_LABELS

from .folder_constants import FOLDER_ACCESS_LEVEL_LABELS, FolderAccessLevel

#  Trần đối tượng một lượt CẤP HÀNG LOẠT (phase 10B, đặc tả §C) — khác trần 500
#  của thao tác gắn/gỡ VĂN BẢN vào thư mục (`folder_link_bulk_service`), đây là
#  trần cho danh sách CHỦ THỂ nhận quyền, đủ cho cả một phòng ban lớn.
MAX_BULK_ACCESS_SUBJECTS = 200


class FolderAccessGrantIn(BaseModel):
    """`level` chỉ bắt buộc có nghĩa khi `effect=CHO PHÉP`; dòng CẤM bỏ qua
    giá trị này (service tự ép về `PRIVATE`) — xem `folder_access_model.py`."""

    subject_kind: int
    subject_id: int = Field(gt=0)
    effect: int = Field(default=EFFECT_ALLOW)
    level: int = Field(default=int(FolderAccessLevel.VIEW))
    valid_from: date | None = None
    valid_to: date | None = None
    reason: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def _check_ranges(self) -> "FolderAccessGrantIn":
        if self.subject_kind not in SUBJECT_LABELS:
            raise ValueError(f"Loại đối tượng không hợp lệ: {self.subject_kind}")
        if self.effect not in (EFFECT_ALLOW, EFFECT_DENY):
            raise ValueError(f"Chiều tác động không hợp lệ: {self.effect}")
        if self.effect == EFFECT_ALLOW and self.level not in FOLDER_ACCESS_LEVEL_LABELS:
            raise ValueError(f"Mức quyền không hợp lệ: {self.level}")
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("Ngày hết hạn phải sau ngày bắt đầu")
        return self


class FolderAccessRevokeIn(BaseModel):
    reason: str = Field(default="", max_length=500)


class FolderAccessBulkSubjectIn(BaseModel):
    """Một đối tượng trong danh sách chọn nhiều — chỉ định danh, KHÔNG mang
    mức/chiều tác động riêng: hộp «Chia sẻ» áp CÙNG một mức + một chiều cho cả
    lượt (đặc tả §C — khác `DocumentAccessDialog` vốn cho khai nhiều CỤM khác
    chiều trong một lần mở hộp)."""

    subject_kind: int
    subject_id: int = Field(gt=0)


class FolderAccessBulkGrantIn(BaseModel):
    """`POST /{folder_id}/access/bulk` — cấp/cấm CÙNG một mức cho CẢ danh sách
    đối tượng trong một giao dịch. Trùng chủ thể (đã có dòng còn hiệu lực CÙNG
    chiều tác động) → service SỬA dòng đó thay vì tạo trùng, giống `grant()`
    đơn lẻ; chủ thể không tồn tại → bị SKIP, không chặn cả lô."""

    subjects: list[FolderAccessBulkSubjectIn] = Field(
        min_length=1, max_length=MAX_BULK_ACCESS_SUBJECTS)
    effect: int = Field(default=EFFECT_ALLOW)
    level: int = Field(default=int(FolderAccessLevel.VIEW))
    valid_from: date | None = None
    valid_to: date | None = None
    reason: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def _check_ranges(self) -> "FolderAccessBulkGrantIn":
        if self.effect not in (EFFECT_ALLOW, EFFECT_DENY):
            raise ValueError(f"Chiều tác động không hợp lệ: {self.effect}")
        if self.effect == EFFECT_ALLOW and self.level not in FOLDER_ACCESS_LEVEL_LABELS:
            raise ValueError(f"Mức quyền không hợp lệ: {self.level}")
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("Ngày hết hạn phải sau ngày bắt đầu")
        for subject in self.subjects:
            if subject.subject_kind not in SUBJECT_LABELS:
                raise ValueError(f"Loại đối tượng không hợp lệ: {subject.subject_kind}")
        return self


class FolderAccessLevelPatchIn(BaseModel):
    """`PATCH /{folder_id}/access/{access_id}` — đổi MỨC tại chỗ, dòng «Người
    có quyền» của hộp «Chia sẻ». Chỉ đổi `level`; đổi đối tượng/chiều tác động
    vẫn phải thu hồi rồi cấp lại (giữ đúng luật thu hồi-là-đánh-dấu)."""

    level: int

    @model_validator(mode="after")
    def _check_level(self) -> "FolderAccessLevelPatchIn":
        if self.level not in FOLDER_ACCESS_LEVEL_LABELS:
            raise ValueError(f"Mức quyền không hợp lệ: {self.level}")
        return self
