"""THƯ BÁO «có việc chờ bạn duyệt».

Trước đây bộ máy duyệt **không báo cho ai cả**: việc rơi vào hộp «Việc của tôi»
và nằm im tới khi người duyệt tự nhớ ra mà mở hộp. Với văn bản thì đó là văn bản
nằm chết giữa luồng, còn người trình thì không biết phải giục ai.

Ba điều đáng ghi lại:

* **Dùng chung đường thông báo có sẵn** (`tab_notification`) — cùng cái chuông,
  cùng trang `/notifications`, cùng số chưa đọc. Không đẻ thêm hộp thư thứ hai.
* **Báo cả người được ỦY QUYỀN bấm thay.** Việc mang tên người đi vắng; báo mỗi
  họ là thư rơi vào hộp không ai đọc trong đúng khoảng thời gian mà ủy quyền
  sinh ra để chống lại.
* **Không bao giờ làm hỏng việc duyệt.** Người duyệt không có tài khoản, hay
  bảng thông báo có chuyện, thì phiên duyệt vẫn phải chạy tiếp — chỗ gọi nuốt
  lỗi có chủ ý, xem `bao_viec_moi`.
"""
import logging

from sqlalchemy.orm import Session

from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.user.model import User

from . import delegation_service
from .instance_model import TASK_PENDING, ApprovalInstance, ApprovalTask

#  Nhãn loại chứng từ. Bộ máy duyệt chỉ giữ `entity` dạng chuỗi, nên đây là chỗ
#  duy nhất phía backend dịch chuỗi đó ra tiếng người — giống vai trò của
#  `helpers/entity-link.ts` bên giao diện.
ENTITY_LABELS = {
    "document": "Văn bản",
    "purchase_request": "Yêu cầu mua hàng",
    "purchase_order": "Đơn mua hàng",
    "survey": "Phiếu khảo sát",
    "survey_request": "Yêu cầu báo giá",
    "payment_request": "Yêu cầu thanh toán",
    "leave_request": "Đơn nghỉ phép",
    "room_booking": "Phiếu đặt phòng họp",
    #  Đặt xe có ĐỦ hook (`register_hooks` + `register_subject` + `register_reader`
    #  trong `vehicle_booking/approval_bridge.py`) nhưng bị quên ở hai bảng này,
    #  nên thư báo ghi «Phiếu XE009» — mất luôn chữ nói đây là việc gì.
    "vehicle_booking": "Phiếu đặt xe",
}

#  Đường dẫn trong thư. Văn bản ghi thẳng đường của app v2; mấy loại còn lại ghi
#  đường KIỂU CŨ và để `toAppPath()` bên giao diện dịch sang tiền tố phân hệ —
#  đúng như các thư khác của hệ đang làm, đừng tự đặt ra kiểu thứ ba.
ENTITY_LINKS = {
    "document": "/document/documents/{id}",
    "purchase_request": "/purchase-requests/{id}",
    "purchase_order": "/purchase-orders/{id}",
    "survey": "/surveys/{id}",
    "survey_request": "/survey-requests/{id}",
    "payment_request": "/payment-requests/{id}",
    #  Nghỉ phép chỉ tồn tại ở app v2 nên ghi thẳng đường v2, như văn bản.
    #  ⚠️ Thiếu dòng này thì `ENTITY_LINKS.get(...)` trả chuỗi RỖNG, thư vẫn gửi
    #  nhưng bấm vào **không đi đâu cả** — người duyệt đọc "đang chờ bạn" rồi
    #  phải tự mò vào menu tìm tờ đơn. Đúng lỗi mà `notification-link.ts` đã
    #  phải vá cho phân hệ Văn thư ngày 20/08/2026, chỉ khác chỗ hỏng.
    "leave_request": "/hr/leave-requests/{id}",
    #  Đặt phòng cũng chỉ tồn tại ở app v2 — xem cảnh báo ngay trên.
    "room_booking": "/hr/room-bookings/{id}",
    #  Đặt xe cũng chỉ có ở app v2 (`appRoutes.vehicleBooking.detail`), và
    #  `/vehicle-booking` đã nằm trong `V2_PREFIXES` của `notification-link.ts`
    #  nên `toAppPath()` cho đi thẳng, không dịch tiền tố. Thiếu dòng này thì
    #  `.get(...)` trả chuỗi RỖNG ⇒ `link` rỗng, bấm vào thông báo không đi đâu
    #  cả — mà `notify_new_tasks` nuốt lỗi nên không một chỗ nào đỏ lên.
    "vehicle_booking": "/vehicle-booking/{id}",
}


def _name_of(db: Session, employee_id: int | None) -> str:
    employee = db.get(Employee, employee_id) if employee_id else None
    return employee.full_name if employee else ""


def _accounts(db: Session, employee_ids: set[int]) -> list[User]:
    if not employee_ids:
        return []
    return (
        db.query(User)
        .filter(User.employee_id.in_(employee_ids), User.is_active.is_(True))
        .all()
    )


def _recipients(db: Session, instance: ApprovalInstance,
                    task: ApprovalTask) -> list[User]:
    """Người mang tên trên việc, cộng những ai đang được họ ủy quyền bấm thay."""
    recipients = {task.assignee_employee_id}
    for row in delegation_service.delegatees_of(
            db, task.assignee_employee_id, instance.entity):
        recipients.add(row.to_employee_id)
    return _accounts(db, {row for row in recipients if row})


def _message_body(instance: ApprovalInstance, task: ApprovalTask,
              on_behalf_of: str = "") -> str:
    kind = ENTITY_LABELS.get(instance.entity, "Phiếu")
    code = instance.entity_code or f"#{instance.entity_id}"
    step = task.node_name or f"bước {task.node_seq}"

    message = f"{kind} {code} đang chờ bạn ở «{step}»."
    if on_behalf_of:
        #  Ký thay người khác là việc khác hẳn ký cho mình, và nhật ký sẽ ghi cả
        #  hai tên — nói ra ngay trong thư chứ không để họ biết sau khi đã bấm.
        message += f" Bạn xử lý THAY {on_behalf_of} theo ủy quyền."
    if task.due_at:
        message += f" Hạn duyệt {task.due_at:%d/%m/%Y %H:%M}."
    return message


def notify_new_tasks(db: Session, instance: ApprovalInstance,
                 tasks: list[ApprovalTask]) -> int:
    """Báo cho người duyệt của những việc VỪA MỞ. Trả về số thư đã ghi.

    Chỉ báo việc đang ở `TASK_PENDING`: bước «lần lượt» mở việc cho người đầu
    tiên thôi, báo hết cả hàng là bốn người cùng lao vào một phiếu mà ba người
    trong số đó bấm chưa tới lượt.

    ⚠️ **Nuốt lỗi có chủ ý.** Tới đây phiên duyệt đã dựng xong việc; để lỗi bay
    lên thì cả giao dịch bị hủy và phiếu không đi tiếp được — mất phiếu vì không
    gửi được thư thì tệ hơn nhiều so với việc thiếu một cái thư.
    """
    written = 0
    try:
        for task in tasks:
            if task.status != TASK_PENDING or not task.assignee_employee_id:
                continue
            link = ENTITY_LINKS.get(instance.entity, "").format(id=instance.entity_id)
            title = f"Chờ bạn duyệt: {instance.entity_title or instance.entity_code}"

            for user in _recipients(db, instance, task):
                on_behalf_of = ""
                if user.employee_id != task.assignee_employee_id:
                    on_behalf_of = _name_of(db, task.assignee_employee_id)
                db.add(Notification(
                    user_id=user.id,
                    title=title,
                    body=_message_body(instance, task, on_behalf_of),
                    link=link,
                    created_by=instance.updated_by or 0,
                ))
                written += 1
    except Exception as error:   # noqa: BLE001 — xem ghi chú trên
        logging.getLogger(__name__).exception(
            "Không báo được việc duyệt của phiên %s: %s", instance.id, error)
    return written
