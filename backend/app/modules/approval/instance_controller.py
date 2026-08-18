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
from app.core.auth import get_current_user, require
from app.core.database import get_db
from app.core.response import success

from . import action_service, serializer, task_service
from .instance_model import ApprovalInstance, ApprovalTask

router = APIRouter(prefix="/api/approvals", tags=["approval"])


class ActionIn(BaseModel):
    comment: str = ""
    #  Bối cảnh phiếu để tính điều kiện rẽ nhánh của bước kế. Module chứng từ
    #  gửi lên; bộ máy duyệt cố ý không biết đọc bảng của chứng từ.
    subject: dict = {}


class ReasonIn(BaseModel):
    reason: str = ""
    subject: dict = {}
    to_seq: int | None = None


class ReassignIn(BaseModel):
    to_employee_id: int = Field(gt=0)
    reason: str = ""


class HandoverIn(BaseModel):
    from_employee_id: int = Field(gt=0)
    to_employee_id: int = Field(gt=0)
    reason: str = ""


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
    items = task_service.viec_cua_toi(db, user.employee_id, entity)
    return success({"total": len(items), "items": items})


@router.get("/of/{entity}/{entity_id}")
def phien_cua_chung_tu(entity: str, entity_id: int, db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    """Phiên duyệt MỚI NHẤT của một chứng từ — `null` nếu nó chưa vào bộ máy.

    Trang chi tiết chứng từ cần câu trả lời này để biết phiếu đang nằm ở bước
    nào và ai đang giữ. Thiếu nó thì màn văn bản chỉ hiện được chữ «Đang duyệt»
    trơ trọi, còn hai nút ban hành một bước thì vẫn bày ra như chưa hề có luồng.

    Trả cả phiên ĐÃ kết thúc, vì `finish_reason` là chỗ duy nhất nói được câu
    "đã duyệt hết các bước nhưng chưa ban hành được vì …".

    Ai đăng nhập cũng gọi được: quyền đọc chính chứng từ đó do module của nó
    gác, ở đây chỉ có tiến trình duyệt.
    """
    del user
    instance = (
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.entity == entity,
                ApprovalInstance.entity_id == entity_id)
        .order_by(ApprovalInstance.id.desc())
        .first()
    )
    if instance is None:
        return success(None)
    return success(serializer.instance_out(db, instance, kem_chi_tiet=True))


@router.post("/handover")
def handover(data: HandoverIn, db: Session = Depends(get_db),
             user=Depends(require("approval_flow", "write"))):
    """I23 — nghỉ việc: chuyển hết việc đang chờ sang người khác trong một lần."""
    so_viec = action_service.ban_giao_hang_loat(
        db, data.from_employee_id, data.to_employee_id, user.id, data.reason)
    record(db, user.id, "approval_flow", 0, "update",
           f"Bàn giao {so_viec} việc duyệt")
    return success({"count": so_viec}, f"Đã chuyển {so_viec} việc đang chờ")


# ── Đường động ──────────────────────────────────────────────────────────────

@router.get("/{instance_id}")
def get_instance(instance_id: int, db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    return success(serializer.instance_out(db, _load(db, instance_id), kem_chi_tiet=True))


@router.get("/{instance_id}/trail")
def trail(instance_id: int, db: Session = Depends(get_db),
          user=Depends(get_current_user)):
    """I20 — bản in dấu vết duyệt.

    *"khi kiểm toán hoặc thanh tra hỏi «ai duyệt cái này», câu trả lời phải là
    một tờ giấy in ra được, không phải một ảnh chụp màn hình"*. Câu chữ dựng ở
    backend để bản in trên web và bản xuất ra tệp không bao giờ lệch nhau.
    """
    instance = _load(db, instance_id)
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
    instance = action_service.duyet(db, _load(db, instance_id), _employee_id(user),
                                    user.id, data.subject, data.comment)
    return success(serializer.instance_out(db, instance), "Đã duyệt")


@router.post("/{instance_id}/reject")
def reject(instance_id: int, data: ReasonIn, db: Session = Depends(get_db),
           user=Depends(get_current_user)):
    instance = action_service.tu_choi(db, _load(db, instance_id), _employee_id(user),
                                      user.id, data.reason)
    return success(serializer.instance_out(db, instance), "Đã từ chối")


@router.post("/{instance_id}/return")
def return_(instance_id: int, data: ReasonIn, db: Session = Depends(get_db),
            user=Depends(get_current_user)):
    instance = action_service.tra_lai(db, _load(db, instance_id), _employee_id(user),
                                      user.id, data.reason, data.subject, data.to_seq)
    return success(serializer.instance_out(db, instance), "Đã trả lại")


@router.post("/{instance_id}/withdraw")
def withdraw(instance_id: int, data: ReasonIn, db: Session = Depends(get_db),
             user=Depends(get_current_user)):
    instance = action_service.rut_lai(db, _load(db, instance_id), _employee_id(user),
                                      user.id, data.reason)
    return success(serializer.instance_out(db, instance), "Đã rút lại")


@router.post("/{instance_id}/comment")
def comment(instance_id: int, data: ActionIn, db: Session = Depends(get_db),
            user=Depends(get_current_user)):
    """I16 — trao đổi ngay trên phiếu, không qua chat riêng."""
    action_service.gop_y(db, _load(db, instance_id), _employee_id(user),
                         user.id, data.comment)
    return success(None, "Đã ghi ý kiến")


@router.patch("/tasks/{task_id}/reassign")
def reassign(task_id: int, data: ReassignIn, db: Session = Depends(get_db),
             user=Depends(require("approval_flow", "write"))):
    task = db.get(ApprovalTask, task_id)
    if task is None:
        raise HTTPException(404, "Không tìm thấy việc này")
    task = action_service.chuyen_nguoi_xu_ly(db, task, data.to_employee_id,
                                             user.id, data.reason)
    return success(serializer.task_out(db, task), "Đã chuyển người xử lý")


def _load(db: Session, instance_id: int) -> ApprovalInstance:
    instance = db.get(ApprovalInstance, instance_id)
    if instance is None:
        raise HTTPException(404, "Không tìm thấy phiên duyệt")
    return instance
