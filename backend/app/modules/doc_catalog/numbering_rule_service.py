"""CRUD và chọn quy tắc đánh số phù hợp cho một văn bản."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .book_model import DocumentBook, NumberSequence
from .model import DocType
from .numbering_rule_model import (DocumentNumberingRule,
                                   DocumentNumberingRuleBook,
                                   DocumentNumberingRuleDocType)
from .numbering_rule_schema import (DocumentNumberingRuleCreate,
                                    DocumentNumberingRuleUpdate)

DIRECTION_LABELS = {1: "Văn bản đến", 2: "Văn bản đi", 3: "Văn bản nội bộ"}
DOC_TYPE_ALL = 1
DOC_TYPE_SELECTED = 2
BOOK_ALL = 1
BOOK_SELECTED = 2
BOOK_NONE = 3


def _replace_ids(
    db: Session,
    model,
    rule_id: int,
    field_name: str,
    values: list[int],
    actor: int,
) -> None:
    db.query(model).filter(model.rule_id == rule_id).delete(synchronize_session=False)
    for value in dict.fromkeys(values):
        db.add(model(
            rule_id=rule_id,
            **{field_name: value},
            created_by=actor,
            updated_by=actor,
        ))


def _ids(db: Session, model, rule_id: int, field_name: str) -> list[int]:
    field = getattr(model, field_name)
    return [row[0] for row in db.query(field).filter(model.rule_id == rule_id).all()]


def _validate_references(
    db: Session,
    direction: int,
    doc_type_mode: int,
    doc_type_ids: list[int],
    book_mode: int,
    book_ids: list[int],
) -> None:
    if doc_type_mode == DOC_TYPE_SELECTED:
        doc_types = db.query(DocType).filter(DocType.id.in_(doc_type_ids)).all()
        found = {row.id for row in doc_types}
        missing = sorted(set(doc_type_ids) - found)
        if missing:
            raise HTTPException(400, f"Loại văn bản không tồn tại: {', '.join(map(str, missing))}")
        permanent = [row.name for row in doc_types if row.id_scheme != 2]
        if permanent:
            raise HTTPException(
                400,
                "Loại dùng mã tài liệu bất biến không áp dụng quy tắc số hiệu: "
                + ", ".join(permanent),
            )

    if book_mode == BOOK_SELECTED:
        books = db.query(DocumentBook).filter(DocumentBook.id.in_(book_ids)).all()
        found = {book.id for book in books}
        missing = sorted(set(book_ids) - found)
        if missing:
            raise HTTPException(400, f"Sổ văn bản không tồn tại: {', '.join(map(str, missing))}")
        wrong_direction = [book.name for book in books if book.kind != direction]
        if wrong_direction:
            raise HTTPException(
                400,
                "Sổ không cùng chiều văn bản: " + ", ".join(wrong_direction),
            )


def list_rules(db: Session, direction: int | None = None) -> list[DocumentNumberingRule]:
    query = db.query(DocumentNumberingRule)
    if direction is not None:
        query = query.filter(DocumentNumberingRule.direction == direction)
    return query.order_by(
        DocumentNumberingRule.direction,
        DocumentNumberingRule.priority,
        DocumentNumberingRule.id,
    ).all()


def get_rule(db: Session, rule_id: int) -> DocumentNumberingRule:
    rule = db.get(DocumentNumberingRule, rule_id)
    if not rule:
        raise HTTPException(404, "Không tìm thấy quy tắc đánh số")
    return rule


def create_rule(
    db: Session,
    data: DocumentNumberingRuleCreate,
    actor: int,
) -> DocumentNumberingRule:
    values = data.model_dump(exclude={"doc_type_ids", "book_ids"})
    _validate_references(
        db, data.direction, data.doc_type_mode, data.doc_type_ids,
        data.book_mode, data.book_ids,
    )
    rule = DocumentNumberingRule(**values, created_by=actor, updated_by=actor)
    db.add(rule)
    db.flush()
    _replace_ids(
        db, DocumentNumberingRuleDocType, rule.id, "doc_type_id",
        data.doc_type_ids if data.doc_type_mode == DOC_TYPE_SELECTED else [], actor,
    )
    _replace_ids(
        db, DocumentNumberingRuleBook, rule.id, "book_id",
        data.book_ids if data.book_mode == BOOK_SELECTED else [], actor,
    )
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(
    db: Session,
    rule_id: int,
    data: DocumentNumberingRuleUpdate,
    actor: int,
) -> DocumentNumberingRule:
    rule = get_rule(db, rule_id)
    values = data.model_dump(
        exclude_unset=True,
        exclude={"doc_type_ids", "book_ids"},
    )
    locked_fields = {"direction", "pattern", "start_no", "reset_yearly"}
    changed_locked = any(
        key in values and values[key] != getattr(rule, key) for key in locked_fields
    )
    if changed_locked and has_issued_numbers(db, rule.id):
        raise HTTPException(
            400,
            "Quy tắc đã cấp số, không đổi được chiều, mẫu số, số bắt đầu hoặc cách đếm.",
        )

    doc_type_mode = values.get("doc_type_mode", rule.doc_type_mode)
    book_mode = values.get("book_mode", rule.book_mode)
    doc_type_ids = (
        data.doc_type_ids
        if data.doc_type_ids is not None
        else _ids(db, DocumentNumberingRuleDocType, rule.id, "doc_type_id")
    )
    book_ids = (
        data.book_ids
        if data.book_ids is not None
        else _ids(db, DocumentNumberingRuleBook, rule.id, "book_id")
    )
    if doc_type_mode != DOC_TYPE_SELECTED:
        doc_type_ids = []
    if book_mode != BOOK_SELECTED:
        book_ids = []
    if doc_type_mode == DOC_TYPE_SELECTED and not doc_type_ids:
        raise HTTPException(400, "Hãy chọn ít nhất một loại văn bản")
    if book_mode == BOOK_SELECTED and not book_ids:
        raise HTTPException(400, "Hãy chọn ít nhất một sổ văn bản")

    direction = values.get("direction", rule.direction)
    _validate_references(
        db, direction, doc_type_mode, doc_type_ids, book_mode, book_ids,
    )
    for key, value in values.items():
        setattr(rule, key, value)
    rule.updated_by = actor
    _replace_ids(
        db, DocumentNumberingRuleDocType, rule.id, "doc_type_id", doc_type_ids, actor,
    )
    _replace_ids(
        db, DocumentNumberingRuleBook, rule.id, "book_id", book_ids, actor,
    )
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule_id: int) -> None:
    rule = get_rule(db, rule_id)
    if has_issued_numbers(db, rule.id):
        raise HTTPException(
            400,
            "Quy tắc đã cấp số, không xóa được. Hãy chuyển sang Ngừng dùng.",
        )
    db.query(DocumentNumberingRuleDocType).filter(
        DocumentNumberingRuleDocType.rule_id == rule.id
    ).delete(synchronize_session=False)
    db.query(DocumentNumberingRuleBook).filter(
        DocumentNumberingRuleBook.rule_id == rule.id
    ).delete(synchronize_session=False)
    db.delete(rule)
    db.commit()


def has_issued_numbers(db: Session, rule_id: int) -> bool:
    return (
        db.query(NumberSequence.id)
        .filter(NumberSequence.scope_key.like(f"rule:{rule_id}:%"))
        .first()
        is not None
    )


def serialize(db: Session, rule: DocumentNumberingRule) -> dict:
    doc_type_ids = _ids(db, DocumentNumberingRuleDocType, rule.id, "doc_type_id")
    book_ids = _ids(db, DocumentNumberingRuleBook, rule.id, "book_id")
    doc_types = (
        db.query(DocType.id, DocType.name).filter(DocType.id.in_(doc_type_ids)).all()
        if doc_type_ids else []
    )
    books = (
        db.query(DocumentBook.id, DocumentBook.name).filter(DocumentBook.id.in_(book_ids)).all()
        if book_ids else []
    )
    type_names = {row[0]: row[1] for row in doc_types}
    book_names = {row[0]: row[1] for row in books}
    return {
        "id": rule.id,
        "direction": rule.direction,
        "direction_label": DIRECTION_LABELS.get(rule.direction, ""),
        "pattern": rule.pattern,
        "start_no": rule.start_no,
        "reset_yearly": rule.reset_yearly,
        "allow_manual": rule.allow_manual,
        "doc_type_mode": rule.doc_type_mode,
        "book_mode": rule.book_mode,
        "priority": rule.priority,
        "is_active": rule.is_active,
        "doc_type_ids": doc_type_ids,
        "book_ids": book_ids,
        "doc_type_names": [type_names[value] for value in doc_type_ids if value in type_names],
        "book_names": [book_names[value] for value in book_ids if value in book_names],
        "has_issued_numbers": has_issued_numbers(db, rule.id),
    }


def resolve_rule(
    db: Session,
    direction: int,
    doc_type_id: int,
    book_id: int | None,
) -> DocumentNumberingRule | None:
    """Chọn quy tắc theo ưu tiên, sau đó ưu tiên phạm vi cụ thể hơn."""
    rules = (
        db.query(DocumentNumberingRule)
        .filter(
            DocumentNumberingRule.direction == direction,
            DocumentNumberingRule.is_active.is_(True),
        )
        .order_by(DocumentNumberingRule.priority, DocumentNumberingRule.id)
        .all()
    )
    type_ids_by_rule = {
        rule.id: set(_ids(db, DocumentNumberingRuleDocType, rule.id, "doc_type_id"))
        for rule in rules if rule.doc_type_mode == DOC_TYPE_SELECTED
    }
    book_ids_by_rule = {
        rule.id: set(_ids(db, DocumentNumberingRuleBook, rule.id, "book_id"))
        for rule in rules if rule.book_mode == BOOK_SELECTED
    }

    matches: list[tuple[int, int, int, DocumentNumberingRule]] = []
    for rule in rules:
        if rule.doc_type_mode == DOC_TYPE_SELECTED and doc_type_id not in type_ids_by_rule[rule.id]:
            continue
        if rule.book_mode == BOOK_SELECTED and book_id not in book_ids_by_rule[rule.id]:
            continue
        if rule.book_mode == BOOK_ALL and book_id is None:
            continue
        if rule.book_mode == BOOK_NONE and book_id is not None:
            continue
        specificity = (2 if rule.doc_type_mode == DOC_TYPE_SELECTED else 0) + (
            4 if rule.book_mode == BOOK_SELECTED else 1 if rule.book_mode == BOOK_NONE else 0
        )
        matches.append((rule.priority, -specificity, rule.id, rule))
    return min(matches, default=(0, 0, 0, None))[3]
