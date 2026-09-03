"""HỘP VIỆC DUYỆT của màn Đơn nghỉ phép — `/api/leave-requests/inbox/...` (CR-260).

Hai đường, đúng hai tab của giao diện:

* `to-approve` — đơn ĐANG chờ chính người đăng nhập ký;
* `handled`    — đơn chính họ vừa quyết định gần đây.

⚠️ **Vì sao không bắt giao diện tự ghép từ `/api/approvals/my-tasks`.** Bộ máy
duyệt chỉ biết `entity_id`, `entity_code` và một dòng tiêu đề; nó không biết ai
nghỉ, từ ngày nào, mấy ngày, loại nghỉ gì — đúng những thứ người duyệt cần để
quyết. Ghép ở giao diện nghĩa là mỗi việc lại gọi thêm một lượt lấy đơn: hai
mươi việc thành hai mươi mốt lượt gọi mạng, và nửa số đó trả 404 vì người duyệt
không có phạm vi dữ liệu tới đơn đó (xem `_can_read` ở `approval_bridge`).

⚠️ **Cả hai đường CỐ Ý không gác `require(...)`.** Quyền ở đây là *bộ máy có
giao việc cho tôi hay không*, không phải một khóa theo vai trò. Gác thêm
`leave_request.read` thì Trưởng phòng Nhân sự — người duyệt chặng 2 của mọi đơn
— lại phải được cấp thêm khóa mới thấy việc của chính mình, và ai quên cấp thì
tab hiện rỗng trong khi bộ máy vẫn gửi thông báo. Dữ liệu trả ra đã tự lọc theo
`employee_id` của người đăng nhập nên không phơi gì thêm.

Đường TĨNH hai đoạn (`/inbox/...`) chứ không phải một đoạn: đường một đoạn rơi
vào `/{rid}` khai ở `request_controller` và ăn lỗi ép kiểu số — cùng lý do với
nhóm `/tools/` bên đó.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success
from app.modules.approval import steps_service, task_service

from . import request_serializer
from .request_model import LeaveRequest

router = APIRouter(prefix="/api/leave-requests/inbox", tags=["leave"])

ENTITY = "leave_request"

#  Bao nhiêu đơn đã quyết thì đủ để "nhớ lại hôm qua mình ký cái gì". Đây không
#  phải sổ tra cứu — muốn tra đủ thì mở dấu vết của chính tờ đơn.
HANDLED_DEFAULT_DAYS = 30
HANDLED_MAX_DAYS = 365
HANDLED_MAX_LIMIT = 200


@router.get("/to-approve")
def to_approve(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Đơn ĐANG chờ chính tôi ký, kèm đủ thông tin để quyết ngay trên dòng.

    Mỗi dòng mang thêm `task` (việc của tôi trên tờ đơn đó) và `flow` (luồng
    duyệt dạng ngang). `task.instance_id` chính là thứ nút Duyệt / Trả về / Từ
    chối gọi tới — giao diện không phải đi hỏi lại phiên duyệt lần nữa.
    """
    tasks = task_service.my_tasks(db, getattr(user, "employee_id", 0) or 0, ENTITY)
    return success(_rows_from_tasks(db, tasks, key="entity_id"))


@router.get("/handled")
def handled(days: int = HANDLED_DEFAULT_DAYS, limit: int = 50,
            db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Đơn chính tôi vừa duyệt / trả về / từ chối gần đây — MỖI ĐƠN MỘT DÒNG.

    ⚠️ `handled_tasks` trả theo DẤU VẾT, nên một người ký hai chặng của cùng tờ
    đơn sẽ ra hai dòng. Trên màn này hai dòng đó **giống hệt nhau** (số đơn,
    người nghỉ, ngày, trạng thái) và đọc ra như lỗi trùng dữ liệu — dựng lại
    được ngay lần chạy thử đầu tiên với NP011.

    Gộp về lượt ký MỚI NHẤT: đây là màn *"nhớ lại hôm qua mình ký cái gì"*, và
    câu trả lời cho một tờ đơn là **một** dòng. Muốn xem đủ từng chặng ai ký lúc
    nào thì mở dấu vết trong trang chi tiết, nơi có cả những người khác.
    """
    tasks = task_service.handled_tasks(
        db, getattr(user, "employee_id", 0) or 0, ENTITY,
        days=max(1, min(days, HANDLED_MAX_DAYS)),
        limit=max(1, min(limit, HANDLED_MAX_LIMIT)))
    return success(_rows_from_tasks(db, _latest_per_request(tasks), key="entity_id"))


def _latest_per_request(tasks: list[dict]) -> list[dict]:
    """Giữ đúng MỘT việc cho mỗi tờ đơn — việc gần nhất.

    `handled_tasks` đã sắp mới nhất trước, nên bản gặp đầu tiên chính là bản
    cần giữ; `dict` giữ nguyên thứ tự chèn nên danh sách ra vẫn đúng thứ tự thời
    gian.
    """
    seen: dict[int, dict] = {}
    for task in tasks:
        seen.setdefault(task.get("entity_id"), task)
    return list(seen.values())


def _rows_from_tasks(db: Session, tasks: list[dict], key: str) -> dict:
    """Ghép «việc của bộ máy» với «tờ đơn» thành một dòng đọc được.

    Việc nào trỏ tới một tờ đơn đã xóa mềm thì BỎ HẲN dòng đó, không trả ra một
    dòng trống: người dùng bấm vào chỉ ăn 404, mà con số đếm trên tab thì vẫn
    tính nó — tab báo "2 việc" trong khi mở ra chỉ có một.
    """
    request_ids = [t.get(key) for t in tasks if t.get(key)]
    if not request_ids:
        return {"total": 0, "items": []}

    rows = {
        obj.id: obj for obj in
        db.query(LeaveRequest)
        .filter(LeaveRequest.id.in_(request_ids),
                LeaveRequest.is_deleted.is_(False))
        .all()
    }
    if not rows:
        return {"total": 0, "items": []}

    #  Tên của CẢ người nghỉ lẫn người nhận bàn giao — một lượt truy vấn.
    handover_ids = {h.employee_id for obj in rows.values() for h in obj.handovers}
    names = request_serializer.names_of(
        db, {obj.employee_id for obj in rows.values()} | handover_ids)
    types = request_serializer.type_names(db)
    flows = steps_service.steps_of_entities(db, ENTITY, list(rows))

    items = []
    for task in tasks:
        obj = rows.get(task.get(key))
        if obj is None:
            continue
        data = request_serializer.dump_request(obj, names, types)
        data["task"] = task
        data["flow"] = flows.get(obj.id)
        #  ⚠️ Người NHẬN BÀN GIAO phải đi kèm ngay ở đây, không để người duyệt
        #  mở tờ đơn ra mới thấy. *Thiếu người bàn giao* là lý do trả đơn phổ
        #  biến nhất, nên nó chính là thứ quyết định họ bấm Duyệt hay Trả về —
        #  mà cả tính năng «duyệt ngay trên dòng» sinh ra để họ khỏi phải mở.
        data["handovers"] = request_serializer.dump_handovers(obj, names)
        items.append(data)

    return {"total": len(items), "items": items}
