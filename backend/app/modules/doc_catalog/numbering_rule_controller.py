"""API CRUD cho trang Quy tắc đánh số."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import numbering_rule_service as service
from .numbering_rule_schema import (DocumentNumberingRuleCreate,
                                    DocumentNumberingRuleUpdate)

router = APIRouter(prefix="/api/document-numbering-rules", tags=["document-numbering-rule"])


@router.get("")
def list_rules(
    direction: int | None = Query(default=None, ge=1, le=3),
    db: Session = Depends(get_db),
    user=Depends(require("doc_type", "read")),
):
    rows = service.list_rules(db, direction)
    return success({"total": len(rows), "items": [service.serialize(db, row) for row in rows]})


@router.get("/{rule_id}")
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("doc_type", "read")),
):
    return success(service.serialize(db, service.get_rule(db, rule_id)))


@router.post("")
def create_rule(
    data: DocumentNumberingRuleCreate,
    db: Session = Depends(get_db),
    user=Depends(require("doc_type", "create")),
):
    rule = service.create_rule(db, data, user.id)
    record(db, user.id, "document_numbering_rule", rule.id, "create")
    return success(service.serialize(db, rule), "Đã tạo quy tắc đánh số", 201)


@router.patch("/{rule_id}")
def update_rule(
    rule_id: int,
    data: DocumentNumberingRuleUpdate,
    db: Session = Depends(get_db),
    user=Depends(require("doc_type", "write")),
):
    rule = service.update_rule(db, rule_id, data, user.id)
    record(db, user.id, "document_numbering_rule", rule.id, "update")
    return success(service.serialize(db, rule), "Đã cập nhật quy tắc đánh số")


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("doc_type", "delete")),
):
    service.delete_rule(db, rule_id)
    record(db, user.id, "document_numbering_rule", rule_id, "delete")
    return success(None, "Đã xóa quy tắc đánh số")
