"""API đề xuất kế hoạch AI — `prefix=/api/ai-plans` (kh-AI1-3, doc/erp/tai-lieu-ai/22 §5.2).

Gác `work_task` (read xem, create sửa / duyệt — duyệt là tạo việc Dự án). Không `apply_scope`: đề xuất là của RIÊNG người
hỏi AI, mọi truy vấn lọc cứng `owner_user_id = người gọi` trong `service.get_mine` / `list_mine` (A1 chốt 22/10: người duyệt
là chính người hỏi). Của người khác và không tồn tại trả CÙNG 404.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.ai_plan_codes import AiPlanStatus
from app.core.auth import require
from app.core.database import get_db
from app.core.response import error, success
from app.modules.ai_plan import service
from app.modules.ai_plan.schema import PlanApproveIn, PlanEditIn, PlanRejectIn

router = APIRouter(prefix="/api/ai-plans", tags=["ai-plan"])
NOT_FOUND = "Không thấy đề xuất kế hoạch này."


def _mine(db: Session, user, proposal_id: int):
    row = service.get_mine(db, user, proposal_id)
    if row is None:
        raise HTTPException(404, NOT_FOUND)
    return row


def _invalid(e: service.PlanInvalid):
    return error("Kế hoạch chưa hợp lệ", code="PLAN_INVALID", status_code=422, details={"problems": e.problems})


@router.get("")
def list_ai_plans(status: int | None = Query(None, ge=1, le=99), page: int = Query(1, ge=1, le=10_000),
                  page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db),
                  user=Depends(require("work_task", "read"))):
    if status is not None and status not in {int(s) for s in AiPlanStatus}:
        raise HTTPException(422, "Trạng thái không hợp lệ")
    return success(service.list_mine(db, user, status=status, page=page, page_size=page_size))


@router.get("/{proposal_id}")
def get_ai_plan(proposal_id: int, db: Session = Depends(get_db), user=Depends(require("work_task", "read"))):
    return success(service.serialize(_mine(db, user, proposal_id), detail=True))


@router.put("/{proposal_id}")
def edit_ai_plan(proposal_id: int, body: PlanEditIn, db: Session = Depends(get_db),
                 user=Depends(require("work_task", "create"))):
    row = _mine(db, user, proposal_id)
    try:
        service.save_edit(db, user, row, body.plan)
    except service.PlanInvalid as e:
        return _invalid(e)
    except service.NotPending as e:
        raise HTTPException(409, str(e)) from None
    return success(service.serialize(row, detail=True), "Đã lưu bản sửa")


@router.post("/{proposal_id}/approve")
def approve_ai_plan(proposal_id: int, body: PlanApproveIn, db: Session = Depends(get_db),
                    user=Depends(require("work_task", "create"))):
    row = _mine(db, user, proposal_id)
    try:
        service.approve(db, user, row, body.plan)
    except service.PlanInvalid as e:
        db.rollback()
        return _invalid(e)
    except service.NotPending as e:
        raise HTTPException(409, str(e)) from None
    return success({"id": row.id, "list_id": row.list_id, "list_url": service.LIST_PATH.format(id=row.list_id)},
                   "Đã duyệt — kế hoạch đã tạo trong Dự án")


@router.post("/{proposal_id}/reject")
def reject_ai_plan(proposal_id: int, body: PlanRejectIn, db: Session = Depends(get_db),
                   user=Depends(require("work_task", "read"))):
    row = _mine(db, user, proposal_id)
    try:
        service.reject(db, user, row, body.reason)
    except service.NotPending as e:
        raise HTTPException(409, str(e)) from None
    return success(service.serialize(row, detail=True), "Đã từ chối đề xuất")
