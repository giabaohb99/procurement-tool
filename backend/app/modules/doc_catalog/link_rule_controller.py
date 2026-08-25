"""API CRUD cho trang Quy tắc quan hệ cha–con (E01).

Quyền gác theo `doc_type` như mọi danh mục nền khác của Văn thư: ai sửa được
danh mục loại văn bản thì sửa được quy tắc giữa các loại đó.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import link_rule_service as service
from .link_rule_model import (OBSOLETE_EXPIRE, OBSOLETE_NOTHING, OBSOLETE_REVIEW,
                              NEW_VERSION_ASK, NEW_VERSION_NOTHING,
                              NEW_VERSION_REVIEW, RELATION_LABELS)
from .link_rule_schema import DocTypeLinkRuleCreate, DocTypeLinkRuleUpdate

router = APIRouter(prefix="/api/doc-type-link-rules", tags=["doc-type-link-rule"])


@router.get("/options")
def list_options(user=Depends(require("doc_link_rule", "read"))):
    """Danh sách giá trị cho form — để giao diện khỏi chép cứng nhãn tiếng Việt.

    Chép cứng thì đổi nhãn ở backend mà giao diện vẫn hiện nhãn cũ, và không ai
    phát hiện ra vì cả hai đều "chạy được".
    """
    return success({
        "relations": [{"value": value, "label": label}
                      for value, label in RELATION_LABELS.items()],
        "on_parent_obsolete": [
            {"value": OBSOLETE_NOTHING, "label": "Không làm gì"},
            {"value": OBSOLETE_REVIEW, "label": "Đánh dấu con cần rà lại"},
            {"value": OBSOLETE_EXPIRE, "label": "Con hết hiệu lực theo cha"},
        ],
        "on_parent_new_version": [
            {"value": NEW_VERSION_NOTHING, "label": "Không làm gì"},
            {"value": NEW_VERSION_REVIEW, "label": "Đánh dấu con cần rà lại"},
            {"value": NEW_VERSION_ASK, "label": "Hỏi người ban hành rồi ghi nhật ký"},
        ],
    })


@router.get("")
def list_rules(
    source_type_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require("doc_link_rule", "read")),
):
    rows = service.list_rules(db)
    if source_type_id:
        rows = [row for row in rows if row.source_type_id == source_type_id]
    return success({"total": len(rows), "items": [service.serialize(db, row) for row in rows]})


@router.get("/{rule_id}")
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("doc_link_rule", "read")),
):
    return success(service.serialize(db, service.get_or_404(db, rule_id)))


@router.post("")
def create_rule(
    data: DocTypeLinkRuleCreate,
    db: Session = Depends(get_db),
    user=Depends(require("doc_link_rule", "create")),
):
    rule = service.create_rule(db, data, user.id)
    record(db, user.id, "doc_type_link_rule", rule.id, "create")
    return success(service.serialize(db, rule), "Đã tạo quy tắc quan hệ", 201)


@router.patch("/{rule_id}")
def update_rule(
    rule_id: int,
    data: DocTypeLinkRuleUpdate,
    db: Session = Depends(get_db),
    user=Depends(require("doc_link_rule", "write")),
):
    rule = service.update_rule(db, service.get_or_404(db, rule_id), data, user.id)
    record(db, user.id, "doc_type_link_rule", rule.id, "update")
    return success(service.serialize(db, rule), "Đã cập nhật quy tắc quan hệ")


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("doc_link_rule", "delete")),
):
    service.delete_rule(db, service.get_or_404(db, rule_id))
    record(db, user.id, "doc_type_link_rule", rule_id, "delete")
    return success(None, "Đã xóa quy tắc quan hệ")
