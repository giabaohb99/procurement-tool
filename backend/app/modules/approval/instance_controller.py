"""API PHIÊN DUYỆT — Việc của tôi, thao tác trên phiếu, bản in dấu vết.

⚠️ **THỨ TỰ ĐĂNG KÝ ROUTE**: `/api/approvals/my-tasks` và `/api/approvals/handover`
là đường TĨNH, phải đứng trước `/{instance_id}` — cùng cái bẫy đã làm chết ba
endpoint văn bản ngày 17/08 (`test_thu_tu_route_van_ban.py`). Ở đây chúng khai
trước trong cùng một tệp nên đúng thứ tự sẵn.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.scoping import has_global_scope
from app.core.database import get_db
from app.core.response import success

from . import action_service, entity_hooks, serializer, task_service
from .concurrency import run_with_contention_retry
from .instance_model import ApprovalInstance, ApprovalTask

router = APIRouter(prefix="/api/approvals", tags=["approval"])


def _acting_employee_id(db: Session, user, action: str) -> int | None:
    """Người đang bấm, để tầng dịch vụ kiểm "anh có tư cách gì với người này".

    `None` = quản trị toàn hệ trên khóa `approval_flow` (grant phạm vi *tất cả*)
    -> được bàn giao hộ người khác. Phạm vi hẹp thì không: quyền khai luồng của
    một phòng không đồng nghĩa với quyền bốc việc của giám đốc về tay mình.
    """
    if has_global_scope(get_perm_profile(db, user), "approval_flow", action):
        return None
    return getattr(user, "employee_id", 0) or 0


#  Bằng ĐÚNG bề rộng cột `tab_approval_instance.finish_reason`. Không khai giới
#  hạn ở đây thì một đoạn nhận xét dài đi thẳng xuống CSDL và nổ
#  `Data too long for column 'finish_reason'` → người duyệt nhận `500` trần
#  (dựng lại được 24/08/2026 với lý do 5000 ký tự). Chặn ở cửa thì ra `422` kèm
#  câu chỉ rõ ô nào quá dài.
MAX_REASON_LEN = 1000
#  `comment` nằm ở cột `Text` nên rộng hơn nhiều, nhưng vẫn phải có trần: không
#  ai gõ tay 20 nghìn ký tự vào ô ý kiến, mà dán nhầm cả tệp thì có.
MAX_COMMENT_LEN = 5000


class ActionIn(BaseModel):
    comment: str = Field("", max_length=MAX_COMMENT_LEN)
    #  Bối cảnh phiếu để tính điều kiện rẽ nhánh của bước kế. Module chứng từ
    #  gửi lên; bộ máy duyệt cố ý không biết đọc bảng của chứng từ.
    subject: dict = {}


class ReasonIn(BaseModel):
    reason: str = Field("", max_length=MAX_REASON_LEN)
    subject: dict = {}
    to_seq: int | None = None


class ReassignIn(BaseModel):
    to_employee_id: int = Field(gt=0)
    reason: str = ""


class HandoverIn(BaseModel):
    from_employee_id: int = Field(gt=0)
    to_employee_id: int = Field(gt=0)
    reason: str = ""


def _context(db: Session, instance: ApprovalInstance, payload: dict) -> dict:
    """Bối cảnh phiếu — LẤY TỪ MÁY CHỦ khi loại chứng từ tự dựng được.

    ⚠️ Đây không phải chuyện gọn gàng. `subject` quyết định hai thứ nặng: bước
    kế chạy NHÁNH nào (`condition_service`), và với cách chọn người duyệt «lấy
    từ ô trên phiếu» thì nó quyết định luôn AI duyệt bước kế
    (`approver_resolver._tu_o_tren_phieu`). Mà dict ấy trước đây đi thẳng từ
    thân request của **chính người đang bấm Duyệt** xuống bộ máy, không ai đối
    chiếu với chứng từ.

    Nghĩa là người duyệt bước 1 gửi kèm `{"nguoi_ky": <id người quen>}` là tự chỉ
    định người duyệt bước 2, hoặc `{"total": 0}` để phiếu né nhánh phải trình
    giám đốc — vẫn đủ chữ ký, vẫn đúng luồng trên giấy tờ (25/08/2026).

    `entity_hooks.boi_canh` đọc thẳng chứng từ nên không sửa được từ ngoài. Loại
    chứng từ CHƯA khai hàm dựng bối cảnh thì vẫn dùng dict gửi lên — siết tới
    mức khóa luôn các phân hệ chưa tới lượt là đổi thứ đang chạy.
    """
    server_context = entity_hooks.entity_context(db, instance.entity, instance.entity_id)
    return server_context if server_context else (payload or {})


def _employee_id(user) -> int:
    if not getattr(user, "employee_id", None):
        raise HTTPException(
            400, "Tài khoản chưa gắn hồ sơ nhân sự nên không tham gia duyệt được")
    return user.employee_id


# ── Đường TĨNH — phải đứng trước /{instance_id} ─────────────────────────────

@router.get("/my-tasks")
def my_tasks(entity: str = "", db: Session = Depends(get_db),
             user=Depends(get_current_user)):
    """I17 — mọi thứ đang chờ tôi, của cả văn thư lẫn thu mua, gom một chỗ.

    Ai đăng nhập cũng mở được: đây là hộp việc của chính họ, không phải dữ liệu
    của người khác. Tài khoản chưa gắn nhân sự thì trả rỗng chứ không báo lỗi.
    """
    if not getattr(user, "employee_id", None):
        return success({"total": 0, "items": []})
    items = task_service.my_tasks(db, user.employee_id, entity)
    return success({"total": len(items), "items": items})


@router.get("/my-history")
def my_history(entity: str = "", days: int = 30, limit: int = 50,
               db: Session = Depends(get_db), user=Depends(get_current_user)):
    """ĐÃ DUYỆT GẦN ĐÂY — nhìn lại những phiếu chính tôi vừa quyết định.

    Cùng lý do mở cửa như `/my-tasks`: đây là việc của chính người đăng nhập,
    không phải dữ liệu của người khác.

    ⚠️ Đây là màn "nhớ lại xem hôm qua mình ký cái gì", **không phải sổ tra
    cứu** — nên chặn `days` và `limit` ở mức vừa phải. Muốn tra đủ lịch sử thì
    mở dấu vết của chính văn bản, nơi có cả những người khác đã làm gì.
    """
    if not getattr(user, "employee_id", None):
        return success({"total": 0, "items": []})
    items = task_service.handled_tasks(
        db, user.employee_id, entity,
        days=max(1, min(days, 365)), limit=max(1, min(limit, 200)))
    return success({"total": len(items), "items": items})


@router.get("/of/{entity}/{entity_id}")
def instances_of_entity(entity: str, entity_id: int, db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    """Phiên duyệt MỚI NHẤT của một chứng từ — `null` nếu nó chưa vào bộ máy.

    Trang chi tiết chứng từ cần câu trả lời này để biết phiếu đang nằm ở bước
    nào và ai đang giữ. Thiếu nó thì màn văn bản chỉ hiện được chữ «Đang duyệt»
    trơ trọi, còn hai nút ban hành một bước thì vẫn bày ra như chưa hề có luồng.

    Trả cả phiên ĐÃ kết thúc, vì `finish_reason` là chỗ duy nhất nói được câu
    "đã duyệt hết các bước nhưng chưa ban hành được vì …".

    ⚠️ Ai đăng nhập cũng GỌI được, nhưng chỉ người ĐỌC ĐƯỢC CHỨNG TỪ mới nhận
    được dữ liệu. Câu cũ ở đây ghi "quyền đọc chứng từ do module của nó gác" —
    mà module của nó không gác đường này, nên văn thư pháp nhân khác mở
    `/api/documents/507` ăn 404 vẫn đọc được tên văn bản, tên luồng và tên người
    đang duyệt qua đây (25/08/2026).

    Không được đọc thì trả `null` y như chứng từ chưa vào bộ máy: đó đã là câu
    trả lời đúng với họ, và không lộ thêm việc "có phiếu nhưng anh không được xem".
    """
    instance = (
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.entity == entity,
                ApprovalInstance.entity_id == entity_id)
        .order_by(ApprovalInstance.id.desc())
        .first()
    )
    if instance is None or not entity_hooks.can_read(db, instance, user):
        return success(None)
    return success(serializer.instance_out(db, instance, with_details=True))


@router.post("/handover")
def handover(data: HandoverIn, db: Session = Depends(get_db),
             user=Depends(require("approval_flow", "write"))):
    """I23 — nghỉ việc: chuyển hết việc đang chờ sang người khác trong một lần."""
    task_count = action_service.bulk_handover(
        db, data.from_employee_id, data.to_employee_id, user.id, data.reason,
        actor_employee_id=_acting_employee_id(db, user, "write"))
    record(db, user.id, "approval_flow", 0, "update",
           f"Bàn giao {task_count} việc duyệt")
    return success({"count": task_count}, f"Đã chuyển {task_count} việc đang chờ")


# ── Đường động ──────────────────────────────────────────────────────────────

@router.get("/{instance_id}")
def get_instance(instance_id: int, db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    return success(serializer.instance_out(db, _load(db, instance_id, user), with_details=True))


@router.get("/{instance_id}/trail")
def trail(instance_id: int, db: Session = Depends(get_db),
          user=Depends(get_current_user)):
    """I20 — bản in dấu vết duyệt.

    *"khi kiểm toán hoặc thanh tra hỏi «ai duyệt cái này», câu trả lời phải là
    một tờ giấy in ra được, không phải một ảnh chụp màn hình"*. Câu chữ dựng ở
    backend để bản in trên web và bản xuất ra tệp không bao giờ lệch nhau.
    """
    instance = _load(db, instance_id, user)
    return success({
        "instance": serializer.instance_out(db, instance),
        "lines": [serializer.action_out(db, row)
                  for row in serializer.actions_of(db, instance.id)],
        "tasks": [serializer.task_out(db, row)
                  for row in serializer.instance_service_tasks(db, instance.id)],
    })


@router.post("/{instance_id}/approve")
def approve(instance_id: int, data: ActionIn, db: Session = Depends(get_db),
            user=Depends(get_current_user)):
    """Không dùng `require(...)`: quyền ở đây là **có việc đang chờ mình hay
    không**, chuyện đó do `viec_dang_cho_cua` xét. Gắn thêm một quyền theo vai
    trò nữa thì người được giao việc lại không bấm được."""
    #  Nạp lại phiếu BÊN TRONG hàm: hai người bấm cùng lúc thì lượt thua bị
    #  cuộn lại và chạy lại, mà chạy lại trên một đối tượng ORM đã hết hạn là
    #  ghi đè bằng trạng thái của lượt hỏng — xem `concurrency.py`.
    def run():
        instance = _load(db, instance_id)
        return action_service.approve(db, instance, _employee_id(user), user.id,
                                    _context(db, instance, data.subject), data.comment)

    return success(serializer.instance_out(db, run_with_contention_retry(db, run)), "Đã duyệt")


@router.post("/{instance_id}/reject")
def reject(instance_id: int, data: ReasonIn, db: Session = Depends(get_db),
           user=Depends(get_current_user)):
    instance = run_with_contention_retry(db, lambda: action_service.reject(
        db, _load(db, instance_id), _employee_id(user), user.id, data.reason))
    return success(serializer.instance_out(db, instance), "Đã từ chối")


@router.post("/{instance_id}/return")
def return_(instance_id: int, data: ReasonIn, db: Session = Depends(get_db),
            user=Depends(get_current_user)):
    def run():
        instance = _load(db, instance_id)
        return action_service.send_back(db, instance, _employee_id(user), user.id,
                                      data.reason, _context(db, instance, data.subject),
                                      data.to_seq)

    return success(serializer.instance_out(db, run_with_contention_retry(db, run)), "Đã trả lại")


@router.post("/{instance_id}/withdraw")
def withdraw(instance_id: int, data: ReasonIn, db: Session = Depends(get_db),
             user=Depends(get_current_user)):
    instance = run_with_contention_retry(db, lambda: action_service.withdraw(
        db, _load(db, instance_id), _employee_id(user), user.id, data.reason))
    return success(serializer.instance_out(db, instance), "Đã rút lại")


@router.post("/{instance_id}/comment")
def comment(instance_id: int, data: ActionIn, db: Session = Depends(get_db),
            user=Depends(get_current_user)):
    """I16 — trao đổi ngay trên phiếu, không qua chat riêng."""
    run_with_contention_retry(db, lambda: action_service.give_comment(
        db, _load(db, instance_id, user), _employee_id(user), user.id, data.comment))
    return success(None, "Đã ghi ý kiến")


@router.patch("/tasks/{task_id}/reassign")
def reassign(task_id: int, data: ReassignIn, db: Session = Depends(get_db),
             user=Depends(require("approval_flow", "write"))):
    task = db.get(ApprovalTask, task_id)
    if task is None:
        raise HTTPException(404, "Không tìm thấy việc này")
    task = action_service.reassign(db, task, data.to_employee_id,
                                             user.id, data.reason,
                                             actor_employee_id=_acting_employee_id(db, user, "write"))
    return success(serializer.task_out(db, task), "Đã chuyển người xử lý")


def _load(db: Session, instance_id: int, user=None) -> ApprovalInstance:
    """Lấy phiên duyệt. Truyền `user` để kiểm luôn quyền ĐỌC CHỨNG TỪ của phiếu.

    ⚠️ `user` không phải tùy chọn cho vui: bốn đường đọc/ghi phiếu trước đây chỉ
    đòi đăng nhập, nên người của pháp nhân khác — mở chính văn bản đó thì ăn 404
    — vẫn đọc được tên văn bản, tên luồng, tên người đang duyệt, và ghi được ý
    kiến vào dấu vết (25/08/2026). Bỏ trống chỉ ở những đường đã tự kiểm bằng
    "có việc đang chờ mình hay không" (duyệt · trả lại · từ chối · rút).

    Trả **404**, không phải 403: nói "có phiếu này nhưng anh không được xem" thì
    chính câu đó đã lộ thứ cần giấu — cùng lý lẽ với `document.ensure_can`.
    """
    instance = db.get(ApprovalInstance, instance_id)
    if instance is None:
        raise HTTPException(404, "Không tìm thấy phiên duyệt")
    if user is not None and not entity_hooks.can_read(db, instance, user):
        raise HTTPException(404, "Không tìm thấy phiên duyệt")
    return instance
