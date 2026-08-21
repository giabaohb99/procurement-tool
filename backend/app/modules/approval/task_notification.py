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
}


def _ten(db: Session, employee_id: int | None) -> str:
    employee = db.get(Employee, employee_id) if employee_id else None
    return employee.full_name if employee else ""


def _tai_khoan(db: Session, employee_ids: set[int]) -> list[User]:
    if not employee_ids:
        return []
    return (
        db.query(User)
        .filter(User.employee_id.in_(employee_ids), User.is_active.is_(True))
        .all()
    )


def _nguoi_can_biet(db: Session, instance: ApprovalInstance,
                    task: ApprovalTask) -> list[User]:
    """Người mang tên trên việc, cộng những ai đang được họ ủy quyền bấm thay."""
    can_biet = {task.assignee_employee_id}
    for row in delegation_service.nguoi_duoc_uy_quyen_boi(
            db, task.assignee_employee_id, instance.entity):
        can_biet.add(row.to_employee_id)
    return _tai_khoan(db, {row for row in can_biet if row})


def _than_thu(instance: ApprovalInstance, task: ApprovalTask,
              thay_cho: str = "") -> str:
    loai = ENTITY_LABELS.get(instance.entity, "Phiếu")
    ma = instance.entity_code or f"#{instance.entity_id}"
    buoc = task.node_name or f"bước {task.node_seq}"

    cau = f"{loai} {ma} đang chờ bạn ở «{buoc}»."
    if thay_cho:
        #  Ký thay người khác là việc khác hẳn ký cho mình, và nhật ký sẽ ghi cả
        #  hai tên — nói ra ngay trong thư chứ không để họ biết sau khi đã bấm.
        cau += f" Bạn xử lý THAY {thay_cho} theo ủy quyền."
    if task.due_at:
        cau += f" Hạn duyệt {task.due_at:%d/%m/%Y %H:%M}."
    return cau


def bao_viec_moi(db: Session, instance: ApprovalInstance,
                 tasks: list[ApprovalTask]) -> int:
    """Báo cho người duyệt của những việc VỪA MỞ. Trả về số thư đã ghi.

    Chỉ báo việc đang ở `TASK_PENDING`: bước «lần lượt» mở việc cho người đầu
    tiên thôi, báo hết cả hàng là bốn người cùng lao vào một phiếu mà ba người
    trong số đó bấm chưa tới lượt.

    ⚠️ **Nuốt lỗi có chủ ý.** Tới đây phiên duyệt đã dựng xong việc; để lỗi bay
    lên thì cả giao dịch bị hủy và phiếu không đi tiếp được — mất phiếu vì không
    gửi được thư thì tệ hơn nhiều so với việc thiếu một cái thư.
    """
    da_ghi = 0
    try:
        for task in tasks:
            if task.status != TASK_PENDING or not task.assignee_employee_id:
                continue
            link = ENTITY_LINKS.get(instance.entity, "").format(id=instance.entity_id)
            tieu_de = f"Chờ bạn duyệt: {instance.entity_title or instance.entity_code}"

            for user in _nguoi_can_biet(db, instance, task):
                thay_cho = ""
                if user.employee_id != task.assignee_employee_id:
                    thay_cho = _ten(db, task.assignee_employee_id)
                db.add(Notification(
                    user_id=user.id,
                    title=tieu_de,
                    body=_than_thu(instance, task, thay_cho),
                    link=link,
                    created_by=instance.updated_by or 0,
                ))
                da_ghi += 1
    except Exception as loi:   # noqa: BLE001 — xem ghi chú trên
        logging.getLogger(__name__).exception(
            "Không báo được việc duyệt của phiên %s: %s", instance.id, loi)
    return da_ghi
