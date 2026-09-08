"""HỘP VIỆC DUYỆT của màn Phiếu đặt phòng — `/api/room-bookings/inbox/...`.

Hai đường, đúng hai tab của giao diện:

* `to-approve` — phiếu ĐANG chờ chính người đăng nhập ký;
* `handled`    — phiếu chính họ vừa quyết định gần đây.

Bám nguyên khuôn `leave/inbox_controller.py`, kể cả những chỗ *tại sao*:

⚠️ **Không bắt giao diện tự ghép từ `/api/approvals/my-tasks`.** Bộ máy duyệt chỉ
biết `entity_id`, `entity_code` và một dòng tiêu đề; nó không biết phòng nào, giờ
nào, mấy người — đúng những thứ người duyệt cần để quyết. Ghép ở giao diện nghĩa
là mỗi việc thêm một lượt gọi mạng, và nửa số đó trả 404 vì người duyệt không có
phạm vi dữ liệu tới phiếu ấy.

⚠️ **Cả hai đường CỐ Ý không gác `require(...)`.** Quyền ở đây là *bộ máy có giao
việc cho tôi hay không*, không phải một khóa theo vai trò. Gác thêm
`room_booking.read` thì người duyệt phải được cấp thêm khóa mới thấy việc của
chính mình, và ai quên cấp thì tab hiện rỗng trong khi bộ máy vẫn gửi thông báo.

Đường TĨNH hai đoạn (`/inbox/...`) chứ không phải một đoạn: đường một đoạn rơi
vào `/{bid}` khai ở `controller.py` và ăn lỗi ép kiểu số.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success
from app.modules.approval import steps_service, task_service

from . import serializer
from .model import RoomBooking

router = APIRouter(prefix="/api/room-bookings/inbox", tags=["meeting-room"])

ENTITY = "room_booking"

#  Bao nhiêu ngày là đủ để "nhớ lại hôm qua mình ký cái gì". Đây không phải sổ
#  tra cứu — muốn tra đủ thì mở dấu vết của chính tờ phiếu.
HANDLED_DEFAULT_DAYS = 30
HANDLED_MAX_DAYS = 365
HANDLED_MAX_LIMIT = 200


@router.get("/to-approve")
def to_approve(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Phiếu ĐANG chờ chính tôi ký, kèm đủ thông tin để quyết ngay trên dòng."""
    tasks = task_service.my_tasks(db, getattr(user, "employee_id", 0) or 0, ENTITY)
    return success(_rows_from_tasks(db, tasks))


@router.get("/handled")
def handled(days: int = HANDLED_DEFAULT_DAYS, limit: int = 50,
            db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Phiếu chính tôi vừa duyệt / trả về / từ chối gần đây — MỖI PHIẾU MỘT DÒNG.

    ⚠️ `handled_tasks` trả theo DẤU VẾT, nên ký hai chặng của cùng một phiếu sẽ
    ra hai dòng giống hệt nhau — đọc như lỗi trùng dữ liệu (bài học của Nghỉ
    phép, CR-260). Gộp về lượt ký mới nhất.
    """
    tasks = task_service.handled_tasks(
        db, getattr(user, "employee_id", 0) or 0, ENTITY,
        days=max(1, min(days, HANDLED_MAX_DAYS)),
        limit=max(1, min(limit, HANDLED_MAX_LIMIT)))
    return success(_rows_from_tasks(db, _latest_per_booking(tasks)))


def _latest_per_booking(tasks: list[dict]) -> list[dict]:
    """Giữ đúng MỘT việc cho mỗi phiếu — việc gần nhất.

    `handled_tasks` đã sắp mới nhất trước nên bản gặp đầu tiên là bản cần giữ;
    `dict` giữ nguyên thứ tự chèn nên danh sách ra vẫn đúng thứ tự thời gian.
    """
    seen: dict[int, dict] = {}
    for task in tasks:
        seen.setdefault(task.get("entity_id"), task)
    return list(seen.values())


def _rows_from_tasks(db: Session, tasks: list[dict]) -> dict:
    """Ghép «việc của bộ máy» với «tờ phiếu» thành một dòng đọc được.

    Việc nào trỏ tới phiếu đã xóa mềm thì BỎ HẲN dòng đó, không trả một dòng
    trống: người dùng bấm vào chỉ ăn 404, mà con số trên tab thì vẫn đếm nó.
    """
    booking_ids = [t.get("entity_id") for t in tasks if t.get("entity_id")]
    if not booking_ids:
        return {"total": 0, "items": []}

    rows = {
        obj.id: obj for obj in
        db.query(RoomBooking)
        .filter(RoomBooking.id.in_(booking_ids), RoomBooking.is_deleted.is_(False))
        .all()
    }
    if not rows:
        return {"total": 0, "items": []}

    #  Tra theo LÔ, không hỏi trong vòng lặp — xem `serializer`.
    room_map = serializer.room_map(db, {obj.room_id for obj in rows.values()})
    names = serializer.names_of(db, {obj.requester_employee_id for obj in rows.values()})
    flows = steps_service.steps_of_entities(db, ENTITY, list(rows))

    items = []
    for task in tasks:
        obj = rows.get(task.get("entity_id"))
        if obj is None:
            continue
        data = serializer.dump_booking(obj, room_map, names)
        data["task"] = task
        data["flow"] = flows.get(obj.id)
        items.append(data)

    return {"total": len(items), "items": items}
