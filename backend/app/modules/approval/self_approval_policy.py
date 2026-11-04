"""Luật CHẶN TỰ DUYỆT của trang Cài đặt nhân sự (duoc-CR-713, chép ý `prevent_self_leave_approval` của ERPNext).

Bộ máy duyệt đã có luật I08 "người nộp không duyệt phiếu của chính mình" (`instance_service.exclude_submitter_ids`)
nhưng CỐ Ý không áp cho bước khai ĐÍCH DANH người duyệt và cho người dự phòng — xem lý do ở hàm đó (CR-113, NP022).
Công tắc `leave_prevent_self_approval` siết thêm, CHỈ cho đơn nghỉ phép: người nghỉ không bao giờ là người duyệt,
kể cả ở hai chỗ đó. Bước rỗng thì rơi về `_handle_no_approver` như mọi bước rỗng khác (người dự phòng → kẹt).

Với đơn nghỉ, "người nộp" của phiên duyệt là NGƯỜI NGHỈ (`leave/approval_bridge` trình với
`submitter_employee_id=obj.employee_id`), không phải người lập hộ.
"""
from __future__ import annotations

from fastapi import HTTPException

from app.core import app_settings

LEAVE_ENTITY = "leave_request"
#  Phiếu nghỉ bù LUÔN chặn tự duyệt, bất kể công tắc: tự duyệt phiếu nghỉ bù là tự cộng ngày phép cho mình
#  (duoc-CR-715 C, review). Đơn nghỉ thường vẫn theo công tắc `leave_prevent_self_approval`.
ALWAYS_STRICT_ENTITIES = frozenset({"leave_comp_request"})

SELF_APPROVAL_MESSAGE = (
    "Cài đặt nhân sự đang chặn tự duyệt: bạn không duyệt được đơn nghỉ của chính mình."
)
SELF_APPROVAL_COMP_MESSAGE = "Bạn không được tự duyệt phiếu nghỉ bù của chính mình."


def strict_self_exclusion(entity: str | None) -> bool:
    """Có gạt người nộp khỏi MỌI kiểu bước (cả bước khai đích danh, người dự phòng) cho chứng từ này không."""
    if entity in ALWAYS_STRICT_ENTITIES:
        return True
    return entity == LEAVE_ENTITY and bool(app_settings.get("leave_prevent_self_approval"))


def ensure_not_self_approval(entity: str | None, actor_employee_id: int | None,
                             submitter_employee_id: int | None) -> None:
    """Chặn (403) người bấm Duyệt chính là người nộp — chốt cuối, phòng việc đã mở TRƯỚC khi bật công tắc."""
    if not actor_employee_id or actor_employee_id != submitter_employee_id:
        return
    if strict_self_exclusion(entity):
        raise HTTPException(403, SELF_APPROVAL_COMP_MESSAGE if entity in ALWAYS_STRICT_ENTITIES
                            else SELF_APPROVAL_MESSAGE)
