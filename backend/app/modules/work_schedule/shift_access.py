"""CỬA QUYỀN của XẾP CA THEO NGÀY (duoc-CR-761) — hai đường vào, một bảng, kiểm TỪNG ô (người × ngày).

* **Đường Nhân sự** — khóa `work_schedule.<hành động>`: xếp ca cho mọi người trong phạm vi `employee.read`, MỌI ngày
  (kể cả quá khứ — HR sửa lại ca đã qua khi chốt công), TRỪ chính mình.
* **Đường Trưởng phòng** — khóa `work_schedule_personal.<hành động>` (chỉ khi KHÔNG có khóa Nhân sự ở hành động đó): chỉ
  nhân sự nằm trong phạm vi khóa này (đo trên HỒ SƠ NHÂN SỰ ĐÍCH, gồm luật ô "Phòng ban được xem" cùng công ty) và chỉ
  ngày ≥ hôm nay (giờ VN) — cùng lý do `assignment_access`: lùi ca quá khứ là mở đường xin nghỉ bù.
* **KHÔNG AI tự xếp ca cho chính mình** (chủ dự án chốt 16/11/2026), kể cả Nhân sự; ngoại lệ duy nhất là quản trị hệ thống
  (`is_system_admin`, cùng quy ước các chốt tự-xử-lý khác như `leave/policy_assignment_controller`).

Hành động: `write` cho đặt / áp hàng loạt / chép tuần, `delete` cho gỡ ca về mẫu tuần. Ngoài phạm vi và không tồn tại
cùng một câu (không lộ người đó có thật không). Ghi hàng loạt kiểm TOÀN BỘ ô trước, sai một ô là không ghi ô nào.
"""
from dataclasses import dataclass
from datetime import date

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, user_has_permission
from app.core.database import get_db
from app.core.privilege_escalation import is_system_admin
from app.core.scoping import apply_scope
from app.core.vn_time import vn_today
from app.modules.employee.model import Employee

from .assignment_access import HR_ENTITY, PERSONAL_ENTITY, holds_hr_key

NOT_FOUND_MESSAGE = "Nhân sự được xếp ca không tồn tại hoặc ngoài phạm vi của bạn"
SELF_MESSAGE = "Bạn không được tự xếp ca cho chính mình"
PAST_MESSAGE = "Chỉ xếp ca từ hôm nay trở đi"
#  Mã lý do từng ô bị từ chối + mã HTTP tương ứng; ghi hàng loạt trả mã của lý do NẶNG NHẤT (403 > 400 > 422).
REASONS = {"self": (403, SELF_MESSAGE), "not_found": (400, NOT_FOUND_MESSAGE), "past_date": (422, PAST_MESSAGE),
           "leave_conflict": (409, "Ngày này đã có đơn nghỉ — sửa / hủy đơn trước rồi xếp ca")}
_PRIORITY = ("self", "not_found", "past_date", "leave_conflict")


@dataclass(frozen=True)
class Rejection:
    """Một ô (hoặc cả một nhân sự khi `work_date` None) bị từ chối, kèm mã + câu lý do.

    `leave_conflict` (ngày đã có đơn nghỉ chờ duyệt / đã duyệt) mang thêm `request_code` + `status_label` của đơn.
    """

    employee_id: int
    work_date: date | None
    code: str
    request_code: str = ""
    status_label: str = ""

    @property
    def message(self) -> str:
        if self.code == "leave_conflict" and self.work_date:
            return leave_conflict_message(self.work_date, self.request_code, self.status_label)
        return REASONS[self.code][1]

    def as_dict(self) -> dict:
        out = {"employee_id": self.employee_id, "work_date": self.work_date.isoformat() if self.work_date else None,
               "code": self.code, "message": self.message}
        if self.code == "leave_conflict":
            out["request_code"] = self.request_code
        return out


def leave_conflict_message(day: date, request_code: str, status_label: str) -> str:
    """Câu báo ngày đã có đơn nghỉ. Không có mã đơn (người hỏi không xem được đơn theo phạm vi) thì chỉ nói có đơn."""
    if not request_code:
        return f"Ngày {day:%d/%m} đã có đơn nghỉ của nhân viên này — liên hệ Nhân sự để sửa đơn trước."
    return f"Ngày {day:%d/%m} đã có đơn nghỉ {request_code} ({status_label}) — sửa / hủy đơn trước rồi xếp ca."


def worst_status(rejections: list[Rejection]) -> int:
    """Mã HTTP của lý do nặng nhất trong danh sách (403 tự xếp > 400 ngoài phạm vi > 422 ngày quá khứ)."""
    for code in _PRIORITY:
        if any(r.code == code for r in rejections):
            return REASONS[code][0]
    return 422


def require_shift_action(action: str):
    """Dependency: cho qua nếu có khóa Nhân sự HOẶC khóa Trưởng phòng ở hành động đó (cổng thô — từng ô do `check_cells`)."""

    def dep(user=Depends(get_current_user), db: Session = Depends(get_db)):
        if holds_hr_key(db, user, action) or user_has_permission(db, user, PERSONAL_ENTITY, action):
            return user
        raise HTTPException(403, f"Không có quyền: {action} {HR_ENTITY}")

    return dep


def check_cells(db: Session, user, profile: dict, action: str, employee_ids, cells) -> list[Rejection]:
    """Kiểm quyền cho một lượt ghi; `[]` = được phép. `cells` = các `(employee_id, work_date)` sẽ đổi.

    Mọi `employee_ids` đều phải trong phạm vi (kể cả người chưa có ô nào đổi: chép tuần đọc ca của họ). Thứ tự chốt:
    ngoài phạm vi / không tồn tại → tự xếp cho mình (mọi đường, trừ quản trị hệ thống) → ngày quá khứ (chỉ Trưởng
    phòng, từng ô). Chốt đơn nghỉ đang giữ ngày nằm ở `shift_leave_conflicts`, chạy SAU khi quyền đã qua.
    """
    ids = sorted({int(i) for i in employee_ids})
    hr_path = holds_hr_key(db, user, action)
    #  Nhân sự: đo trên phạm vi ĐỌC hồ sơ (`employee`); Trưởng phòng: đo trên khóa riêng của chính hành động đó.
    query = apply_scope(db.query(Employee.id).filter(Employee.id.in_(ids)), Employee,
                        "employee" if hr_path else PERSONAL_ENTITY, user, profile, "read" if hr_path else action)
    visible = {row.id for row in query.all()}
    out = [Rejection(i, None, "not_found") for i in ids if i not in visible]
    own = int(profile.get("employee_id") or 0)   # 0 = tài khoản chưa gắn hồ sơ → không bao giờ trùng
    self_blocked = bool(own) and own in visible and not is_system_admin(db, user.id)
    if self_blocked:
        out.append(Rejection(own, None, "self"))
    if not hr_path:
        today = vn_today()
        out += [Rejection(emp, day, "past_date") for emp, day in cells
                if day < today and emp in visible and not (self_blocked and emp == own)]
    return out


def raise_for_single(rejections: list[Rejection]) -> None:
    """Đường một ô: ném `HTTPException` theo lý do nặng nhất (400 / 403 / 422)."""
    if rejections:
        status = worst_status(rejections)
        raise HTTPException(status, next(r.message for r in rejections if REASONS[r.code][0] == status))
