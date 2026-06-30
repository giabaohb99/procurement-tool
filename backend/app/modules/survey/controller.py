from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import Survey
from .schema import (ProductSurveyCreate, ProductSurveyUpdate, RejectIn,
                     SupplierSurveyCreate, SupplierSurveyUpdate)


def _dict(obj) -> dict:
    d = {}
    for c in sa_inspect(obj).mapper.column_attrs:
        v = getattr(obj, c.key)
        d[c.key] = float(v) if isinstance(v, Decimal) else v
    return d


def _out(db: Session, s: Survey) -> dict:
    base = _dict(s)
    lines = service.lines_of(db, s.survey_type, s.id)
    base["lines"] = [_dict(x) for x in lines]
    base["count"] = len(lines)
    if s.survey_type == "product":
        base["subtotal"] = round(sum(float(x.amount or 0) for x in lines), 2)
        base["main"] = lines[0].product_name if lines else ""
    else:
        base["main"] = lines[0].supplier_name or lines[0].supplier_code if lines else ""
    return base


def _build_router(survey_type: str, prefix: str, CreateSchema, UpdateSchema):
    router = APIRouter(prefix=prefix, tags=[f"survey_{survey_type}"])

    @router.get("")
    def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
              user=Depends(require("survey", "read"))):
        q = apply_filters(db.query(Survey), Survey, request, service.FILTERABLE)
        total, items = service.list_surveys(db, survey_type, q, pg)
        return success({"total": total, "items": [_dict(x) for x in items]})

    @router.get("/{sid}")
    def get_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey", "read"))):
        return success(_out(db, service.get_survey(db, sid)))

    @router.post("")
    def create_(data: CreateSchema, db: Session = Depends(get_db),
                user=Depends(require("survey", "create"))):
        return success(_out(db, service.create_survey(db, data, survey_type, user.id)), "Đã tạo", 201)

    @router.patch("/{sid}")
    def update_(sid: int, data: UpdateSchema, db: Session = Depends(get_db),
                user=Depends(require("survey", "write"))):
        return success(_out(db, service.update_survey(db, sid, data, survey_type, user.id)), "Đã cập nhật")

    @router.delete("/{sid}")
    def delete_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey", "delete"))):
        service.delete_survey(db, sid, survey_type, user.id)
        return success(None, "Đã xóa")

    @router.post("/{sid}/submit")
    def submit_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey", "write"))):
        return success(_out(db, service.set_status(db, sid, "submitted", user.id)), "Đã gửi duyệt")

    @router.post("/{sid}/approve")
    def approve_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey", "approve"))):
        return success(_out(db, service.set_status(db, sid, "approved", user.id)), "Đã duyệt")

    @router.post("/{sid}/reject")
    def reject_(sid: int, data: RejectIn, db: Session = Depends(get_db), user=Depends(require("survey", "approve"))):
        return success(_out(db, service.set_status(db, sid, "rejected", user.id, data.reason)), "Đã từ chối")

    return router


supplier_survey_router = _build_router("supplier", "/api/surveys-supplier", SupplierSurveyCreate, SupplierSurveyUpdate)
product_survey_router = _build_router("product", "/api/surveys-product", ProductSurveyCreate, ProductSurveyUpdate)
