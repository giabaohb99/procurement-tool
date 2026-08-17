"""API CLONE XUỐNG PHÁP NHÂN CON (F06–F10).

Cùng prefix `/api/documents` với `controller.py`.
"""
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import clone_notification, clone_service
from .controller import _load
from .link_serializer import summary_of

router = APIRouter(prefix="/api/documents", tags=["document-clone"])


class CloneCreate(BaseModel):
    company_ids: list[int] = Field(min_length=1)
    due_date: date | None = None
    note: str = ""


class CloneStatusUpdate(BaseModel):
    clone_status: int = Field(ge=1, le=6)


@router.get("/{document_id}/clones")
def list_clones(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """F10 — *"12 công ty con đang ở phiên bản nào của quy chế này"*.

    Trả cả danh sách pháp nhân **chưa nhận** bản clone nào: phần "ai chưa đụng
    tới" là một trong bốn câu mà màn hình này phải trả lời được.
    """
    doc = _load(db, document_id, user)
    return success({
        "items": clone_service.tracking(db, doc),
        "pending_companies": clone_service.pending_companies(db, doc),
    })


@router.post("/{document_id}/clones")
def create_clones(
    document_id: int,
    data: CloneCreate,
    db: Session = Depends(get_db),
    user=Depends(require("document", "create")),
):
    """F06–F09 — sinh bản nháp cho từng pháp nhân con và báo cho họ."""
    source = _load(db, document_id, user)
    clones = clone_service.create_clones(
        db, source, data.company_ids, data.due_date, data.note, user.id,
    )

    #  F09 — mỗi pháp nhân một thư. Gửi SAU khi clone đã commit: báo trước mà
    #  clone hỏng thì người ta đi tìm một bản nháp không tồn tại.
    for clone in clones:
        clone_notification.notify_clone_created(db, source, clone)
        record(db, user.id, "document", clone.id, "create",
               f"Clone từ {source.doc_code or source.issue_number or source.title}")
    db.commit()

    return success(
        [summary_of(db, clone) for clone in clones],
        f"Đã tạo {len(clones)} bản nháp cho pháp nhân con", 201,
    )


@router.patch("/{document_id}/clone-status")
def update_clone_status(
    document_id: int,
    data: CloneStatusUpdate,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    """Pháp nhân con cập nhật tình trạng xử lý bản clone của mình."""
    clone = _load(db, document_id, user, "write")
    clone = clone_service.mark_handled(db, clone, data.clone_status, user.id)
    record(db, user.id, "document", clone.id, "update",
           f"Bản clone: {clone_service.CLONE_STATUS_LABELS.get(clone.clone_status, '')}")
    return success(summary_of(db, clone), "Đã cập nhật tình trạng bản clone")
