from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.notification.service import trigger_notification

from . import service
from .model import Survey
from .schema import LineApproveCombined, RejectIn, SurveyCreate, SurveyUpdate


def _dict(obj) -> dict:
    d = {}
    for c in sa_inspect(obj).mapper.column_attrs:
        v = getattr(obj, c.key)
        d[c.key] = float(v) if isinstance(v, Decimal) else v
    return d


def _out(db: Session, s: Survey) -> dict:
    """Phiếu khảo sát GỘP: trả cả 2 bảng dòng (NCC + SP)."""
    base = _dict(s)
    sup = service.supplier_lines_of(db, s.id)
    prod = service.product_lines_of(db, s.id)
    base["supplier_lines"] = [_dict(x) for x in sup]
    base["product_lines"] = [_dict(x) for x in prod]
    base["supplier_count"] = len(sup)
    base["product_count"] = len(prod)
    base["subtotal"] = round(sum(float(x.amount or 0) for x in prod), 2)
    base["main"] = ((sup[0].supplier_name or sup[0].supplier_code) if sup
                    else (prod[0].product_name if prod else ""))
    return base


router = APIRouter(prefix="/api/surveys", tags=["survey"])


@router.get("")
def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("survey", "read"))):
    q = apply_filters(db.query(Survey), Survey, request, service.FILTERABLE)
    q = apply_scope(q, Survey, "survey", user, get_perm_profile(db, user))
    total, items = service.list_surveys(db, q, pg)
    return success({"total": total, "items": [_dict(x) for x in items]})


@router.get("/{sid}")
def get_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey", "read"))):
    s = apply_scope(db.query(Survey).filter(Survey.id == sid),
                    Survey, "survey", user, get_perm_profile(db, user)).first()
    if not s:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, s))


@router.post("")
def create_(data: SurveyCreate, db: Session = Depends(get_db), user=Depends(require("survey", "create"))):
    return success(_out(db, service.create_survey(db, data, user.id)), "Đã tạo", 201)


@router.patch("/{sid}")
def update_(sid: int, data: SurveyUpdate, db: Session = Depends(get_db), user=Depends(require("survey", "write"))):
    return success(_out(db, service.update_survey(db, sid, data, user.id)), "Đã cập nhật")


@router.delete("/{sid}")
def delete_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey", "delete"))):
    service.delete_survey(db, sid, user.id)
    return success(None, "Đã xóa")


@router.post("/{sid}/submit")
def submit_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("survey", "write"))):
    s = service.set_status(db, sid, "submitted", user.id)
    trigger_notification(db=db, event="survey_submitted", doc_type="survey", doc_code=s.code,
                         creator_id=s.created_by or user.id, background_tasks=background_tasks,
                         link=f"/surveys/{s.id}")
    return success(_out(db, s), "Đã gửi duyệt")


@router.patch("/{sid}/line-approve")
def line_approve_(sid: int, data: LineApproveCombined, db: Session = Depends(get_db),
                  user=Depends(require("survey", "approve"))):
    return success(_out(db, service.approve_lines(db, sid, data, user.id)), "Đã lưu duyệt dòng")


@router.post("/{sid}/approve")
def approve_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
             user=Depends(require("survey", "approve"))):
    s = service.set_status(db, sid, "approved", user.id)
    trigger_notification(db=db, event="survey_approved", doc_type="survey", doc_code=s.code,
                         creator_id=s.created_by or user.id, background_tasks=background_tasks,
                         approve_note=s.approve_note or "", link=f"/surveys/{s.id}")
    return success(_out(db, s), "Đã duyệt")


@router.post("/{sid}/reject")
def reject_(sid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("survey", "approve"))):
    s = service.set_status(db, sid, "rejected", user.id, data.reason)
    trigger_notification(db=db, event="survey_rejected", doc_type="survey", doc_code=s.code,
                         creator_id=s.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/surveys/{s.id}")
    return success(_out(db, s), "Đã từ chối")
