"""Nghiệp vụ QUY TẮC QUAN HỆ (E01).

Việc thật của tệp này chỉ có một: **ép ba cột khóa cứng của dòng "trích từ"**
(E11) trước khi ghi. Giao diện có tắt ô hay không cũng không quan trọng — bài
kiểm gọi thẳng API để canh chỗ này.
"""
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .link_rule_model import (EXCERPT_LOCKED_FIELDS, RELATION_EXCERPT,
                              RELATION_LABELS, DocTypeLinkRule)
from .link_rule_schema import DocTypeLinkRuleCreate, DocTypeLinkRuleUpdate
from .model import DocType


def list_rules(db: Session) -> list[DocTypeLinkRule]:
    #  `sort_order` đứng ngay sau loại nguồn: trong một loại, thứ tự người khai
    #  xếp là thứ tự phải đọc ("trước C là A rồi B"). Dòng chưa xếp (0) lên
    #  trước theo `relation` như cũ — bảng cũ không có cột này nên tất cả là 0.
    return (
        db.query(DocTypeLinkRule)
        .order_by(DocTypeLinkRule.source_type_id.asc(),
                  DocTypeLinkRule.sort_order.asc(),
                  DocTypeLinkRule.relation.asc(),
                  DocTypeLinkRule.id.asc())
        .all()
    )


def get_or_404(db: Session, rule_id: int) -> DocTypeLinkRule:
    rule = db.get(DocTypeLinkRule, rule_id)
    if not rule:
        raise HTTPException(404, "Không tìm thấy quy tắc quan hệ")
    return rule


def _ap_khoa_trich_tu(values: dict) -> dict:
    """Dòng "trích từ" luôn mang đúng ba giá trị này, người khai không đổi được.

    Vì sao không cho khai: bản trích là CÙNG nội dung với gốc, chỉ ít hơn. Cho
    phép đặt "cha đổi thì không làm gì" nghĩa là cho phép một bản trích nói sai
    tồn tại hợp lệ; cho phép bỏ thừa kế mức mật nghĩa là cho phép phần nội dung
    ít hơn lại lỏng hơn phần đầy đủ.
    """
    if values.get("relation") == RELATION_EXCERPT:
        values.update(EXCERPT_LOCKED_FIELDS)
    return values


def _kiem_loai(db: Session, values: dict):
    if not db.get(DocType, values["source_type_id"]):
        raise HTTPException(400, "Loại văn bản nguồn không tồn tại")
    if values.get("target_type_id") and not db.get(DocType, values["target_type_id"]):
        raise HTTPException(400, "Loại văn bản đích không tồn tại")


def create_rule(db: Session, data: DocTypeLinkRuleCreate, actor: int) -> DocTypeLinkRule:
    values = _ap_khoa_trich_tu(data.model_dump())
    _kiem_loai(db, values)

    rule = DocTypeLinkRule(**values, created_by=actor, updated_by=actor)
    db.add(rule)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            400,
            f"Đã có quy tắc «{RELATION_LABELS.get(values['relation'], '')}» cho cặp "
            "loại này. Sửa dòng cũ thay vì thêm dòng thứ hai — hai dòng mâu thuẫn "
            "nhau thì không biết tin dòng nào.",
        )
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule: DocTypeLinkRule, data: DocTypeLinkRuleUpdate,
                actor: int) -> DocTypeLinkRule:
    values = _ap_khoa_trich_tu(data.model_dump())
    _kiem_loai(db, values)

    for key, value in values.items():
        setattr(rule, key, value)
    rule.updated_by = actor
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Trùng với một quy tắc đã có cho cặp loại này")
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule: DocTypeLinkRule):
    #  Quan hệ đã khai vẫn còn (`tab_document_link.rule_id` cho phép rỗng) — xóa
    #  quy tắc chỉ nghĩa là từ nay không khai thêm được nữa, không phải xóa dữ
    #  liệu lịch sử.
    db.delete(rule)
    db.commit()


def serialize(db: Session, rule: DocTypeLinkRule) -> dict:
    source = db.get(DocType, rule.source_type_id)
    target = db.get(DocType, rule.target_type_id) if rule.target_type_id else None
    return {
        "id": rule.id,
        "source_type_id": rule.source_type_id,
        "source_type_name": source.name if source else "",
        "relation": rule.relation,
        "relation_label": RELATION_LABELS.get(rule.relation, str(rule.relation)),
        "target_type_id": rule.target_type_id,
        #  Rỗng nghĩa là loại nào cũng được — nói thẳng ra cho người đọc bảng.
        "target_type_name": target.name if target else "Loại bất kỳ",
        "is_required": rule.is_required,
        "min_count": rule.min_count,
        "max_count": rule.max_count,
        "sort_order": rule.sort_order,
        "on_parent_obsolete": rule.on_parent_obsolete,
        "on_parent_new_version": rule.on_parent_new_version,
        "inherit_code": rule.inherit_code,
        "inherit_secrecy": rule.inherit_secrecy,
        "is_active": rule.is_active,
        "is_locked": rule.relation == RELATION_EXCERPT,
    }
