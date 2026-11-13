"""CỬA QUYỀN của API gán lịch — hai đường vào, một bảng (duoc-CR-757 lượt 2).

* **Đường Nhân sự** — khóa `work_schedule.<hành động>`: gán mọi cấp (hệ thống / pháp nhân / phòng ban / nhân sự),
  luật cũ giữ nguyên từng chữ.
* **Đường Trưởng phòng** — khóa `work_schedule_personal.<hành động>` (chỉ khi KHÔNG có khóa Nhân sự ở hành động đó):
  chỉ gán lịch RIÊNG cấp Nhân sự, và chỉ cho nhân sự nằm trong phạm vi khóa đó. Giới hạn chốt với người chủ dự án:

  1. chỉ cấp Nhân sự (`WorkScheduleLevel.EMPLOYEE`) — cấp khác → 403;
  2. nhân sự đích nằm trong phạm vi `work_schedule_personal` (`dept` = phòng chính + kiêm nhiệm của người gán) — ngoài
     phạm vi → 400 "Đối tượng được gán lịch không tồn tại" (cùng câu của service, không lộ người đó có thật không);
  3. không gán / sửa / xóa lịch riêng của CHÍNH MÌNH → 403;
  4. chỉ chọn mẫu lịch đang dùng — do `assignment_service._check_schedule` ép cho CẢ hai đường;
  5. không đụng tới mẫu lịch: `template_controller` vẫn chỉ nhận khóa `work_schedule`;
  6. chỉ sửa / xóa được dòng do CHÍNH MÌNH gán (`created_by`); dòng Nhân sự hoặc người khác gán → 403. Tạo dòng mới thì
     vẫn được và có thể tự đóng / cắt đôi dòng "không thời hạn" của Nhân sự (cách đổi lịch từ một ngày trở đi); xóa dòng
     tự tạo đó thì `assignment_heal` mở lại dòng cũ;
  7. ngày hiệu lực chỉ từ hôm nay trở đi (lúc tạo, và lúc sửa mà ngày đổi) — không lùi ngày làm đổi cách đếm ngày nghỉ
     đã qua;
  8. dòng ĐÃ BẮT ĐẦU (`effective_from` < hôm nay): chỉ đặt được ngày kết thúc (và ghi chú), ngày kết thúc phải từ hôm qua
     trở đi; không xóa được (xóa là viết lại quá khứ). Mẫu lịch / đích / cấp / ngày bắt đầu không đổi được;
  9. dòng đã tự đóng một dòng khác (lúc tạo) thì không đổi đích hay ngày bắt đầu được — đổi sẽ gỡ liên kết mở lại lịch cũ;
     muốn đổi thì xóa (khi chưa bắt đầu) rồi tạo lại. Ngày KẾT THÚC thì đổi được: lịch cũ của Nhân sự tự nối lại từ ngày
     sau đó (`assignment_service.update_assignment` + `assignment_heal.move_resume`).

Khóa `work_schedule_personal` được đo trên HỒ SƠ NHÂN SỰ ĐÍCH (`SCOPE_FIELDS` khai cột của `tab_employee`), nên mọi chốt ở
đây gọi `get_scoped(db, Employee, "work_schedule_personal", ...)`.
"""
from datetime import date, timedelta

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, user_has_permission
from app.core.database import get_db
from app.core.scoping import get_scoped
from app.core.vn_time import vn_today
from app.core.work_schedule_codes import WorkScheduleLevel
from app.modules.employee.model import Employee

from .assignment_heal import closed_link_ids
from .assignment_schema import AssignmentUpdate
from .model import WorkScheduleAssignment

HR_ENTITY = "work_schedule"
PERSONAL_ENTITY = "work_schedule_personal"
#  Cùng câu với `assignment_service._check_target_exists` và `_ensure_employee_in_scope` của controller.
TARGET_NOT_FOUND = "Đối tượng được gán lịch không tồn tại"
SELF_MESSAGE = "Bạn không được tự gán, sửa hay xóa lịch làm việc riêng của chính mình"
LEVEL_MESSAGE = "Bạn chỉ được gán lịch làm việc riêng (cấp Nhân sự) cho nhân sự trong phạm vi của mình"
NOT_CREATOR_MESSAGE = "Lịch này do Nhân sự hoặc người khác gán, bạn chỉ sửa được lịch do chính mình gán"
PAST_DATE_MESSAGE = "Ngày hiệu lực phải từ hôm nay trở đi"
STARTED_EDIT_MESSAGE = "Lịch đã bắt đầu, chỉ đặt được ngày kết thúc"
STARTED_DELETE_MESSAGE = "Lịch đã bắt đầu, không xóa được — hãy đặt ngày kết thúc"
STARTED_END_MESSAGE = "Ngày kết thúc của lịch đã bắt đầu phải từ hôm qua trở đi"
LINKED_MESSAGE = "Lịch này đã thay lịch trước đó, muốn đổi hãy xóa rồi tạo lại"
_STARTED_LOCKED = ("target_level", "target_id", "schedule_id", "effective_from")   # đổi được khi CHƯA bắt đầu
_LINK_LOCKED = ("target_level", "target_id", "effective_from")                     # đổi sẽ gỡ liên kết mở lại
_VERBS = {"create": "gán", "write": "sửa", "delete": "xóa"}


def holds_hr_key(db: Session, user, action: str) -> bool:
    """Người này có khóa Nhân sự `work_schedule.<action>` (đường không giới hạn cấp)?"""
    return user_has_permission(db, user, HR_ENTITY, action)


def require_assignment_action(action: str):
    """Dependency thay `require("work_schedule", action)`: cho qua nếu có khóa Nhân sự HOẶC khóa Trưởng phòng.

    Chỉ là cổng thô; điều gì được làm với từng dòng do các hàm `check_personal_*` bên dưới chốt khi người gọi chỉ có
    khóa Trưởng phòng (`holds_hr_key` sai).
    """

    def dep(user=Depends(get_current_user), db: Session = Depends(get_db)):
        if holds_hr_key(db, user, action) or user_has_permission(db, user, PERSONAL_ENTITY, action):
            return user
        raise HTTPException(403, f"Không có quyền: {action} {HR_ENTITY}")

    return dep


def _is_self(profile: dict, employee_id: int | None) -> bool:
    own = profile.get("employee_id") or 0   # 0 = tài khoản chưa gắn hồ sơ → không bao giờ trùng
    return bool(own) and bool(employee_id) and own == employee_id


def check_personal_target(db: Session, user, profile: dict, action: str, level: int | None,
                          target_id: int | None) -> None:
    """Chốt đích MỚI của một dòng gán (tạo, hoặc giá trị sau khi sửa) trên đường Trưởng phòng."""
    if level != int(WorkScheduleLevel.EMPLOYEE):
        raise HTTPException(403, LEVEL_MESSAGE)
    if _is_self(profile, target_id):
        raise HTTPException(403, SELF_MESSAGE)
    if get_scoped(db, Employee, PERSONAL_ENTITY, target_id or 0, user, profile, action) is None:
        raise HTTPException(400, TARGET_NOT_FOUND)


def check_personal_existing_row(db: Session, user, profile: dict, action: str,
                                row: WorkScheduleAssignment) -> None:
    """Chốt dòng ĐANG CÓ trước khi sửa / xóa trên đường Trưởng phòng: chỉ dòng cấp Nhân sự của người trong phạm vi.

    Dòng cấp khác công khai nên báo 403 (nói rõ vì sao); dòng của người ngoài phạm vi báo 404 như id không tồn tại.
    Chỉ dòng do chính người gọi gán (`created_by`) mới sửa / xóa được — kiểm SAU phạm vi để người ngoài phạm vi vẫn nhận 404.
    """
    verb = _VERBS.get(action, "sửa")
    if row.target_level != int(WorkScheduleLevel.EMPLOYEE):
        raise HTTPException(403, f"Bạn chỉ được {verb} lịch làm việc riêng (cấp Nhân sự) của nhân sự trong phạm vi")
    if _is_self(profile, row.target_id):
        raise HTTPException(403, SELF_MESSAGE)
    if get_scoped(db, Employee, PERSONAL_ENTITY, row.target_id, user, profile, action) is None:
        raise HTTPException(404, "Không tìm thấy")
    if row.created_by != user.id:
        raise HTTPException(403, NOT_CREATOR_MESSAGE)


def check_personal_start_date(start: date | None) -> None:
    """Đường Trưởng phòng: ngày hiệu lực không được lùi về trước hôm nay (giờ VN, container chạy UTC)."""
    if start is not None and start < vn_today():
        raise HTTPException(422, PAST_DATE_MESSAGE)


def _changed_fields(row: WorkScheduleAssignment, data: AssignmentUpdate) -> set[str]:
    """Các trường mà PATCH này THỰC SỰ đổi giá trị (gửi lại đúng giá trị cũ không tính — form hay gửi đủ mọi ô)."""
    values = data.model_dump(exclude_unset=True)
    changed = {key for key in _STARTED_LOCKED if values.get(key) is not None and values[key] != getattr(row, key)}
    if "effective_to" in values and values["effective_to"] != row.effective_to:
        changed.add("effective_to")
    return changed


def check_personal_update(db: Session, row: WorkScheduleAssignment, data: AssignmentUpdate) -> None:
    """Chốt SỬA trên đường Trưởng phòng: dòng đã bắt đầu (chỉ đặt ngày kết thúc) + dòng đã thay lịch trước đó."""
    today = vn_today()
    changed = _changed_fields(row, data)
    started = row.effective_from < today
    if started and changed & set(_STARTED_LOCKED):
        raise HTTPException(403, STARTED_EDIT_MESSAGE)
    if changed & set(_LINK_LOCKED) and has_closed_link(db, row.id):
        raise HTTPException(400, LINKED_MESSAGE)
    if started and "effective_to" in changed and data.effective_to is not None \
            and data.effective_to < today - timedelta(days=1):
        raise HTTPException(422, STARTED_END_MESSAGE)


def check_personal_delete(row: WorkScheduleAssignment) -> None:
    """Chốt XÓA trên đường Trưởng phòng: dòng đã bắt đầu thì không xóa (kết thúc nó bằng ngày kết thúc)."""
    if row.effective_from < vn_today():
        raise HTTPException(403, STARTED_DELETE_MESSAGE)


def has_closed_link(db: Session, assignment_id: int) -> bool:
    """Dòng này đã tự đóng / nối một dòng khác lúc tạo (có dòng trỏ `linked_assignment_id` về nó)?"""
    return assignment_id in closed_link_ids(db, [assignment_id])
