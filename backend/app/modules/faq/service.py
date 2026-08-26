import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.assistant.rag.hooks import on_source_deleted, on_source_saved

from .model import Faq
from .schema import FaqCreate, FaqUpdate

AUDIT_ENTITY = "faq"


def list_faqs(db: Session, active_only: bool = False):
    """Danh sách câu hỏi theo thứ tự hiển thị. active_only dùng cho trang người dùng."""
    q = db.query(Faq)
    if active_only:
        q = q.filter(Faq.is_active.is_(True))
    return q.order_by(Faq.sort_order.asc(), Faq.id.asc()).all()


def get_faq(db: Session, faq_id: int) -> Faq:
    faq = db.get(Faq, faq_id)
    if not faq:
        raise HTTPException(404, "Không tìm thấy câu hỏi")
    return faq


def create_faq(db: Session, data: FaqCreate, user_id: int) -> Faq:
    faq = Faq(
        question=data.question,
        answer=data.answer,
        sort_order=data.sort_order,
        is_active=data.is_active,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)
    record(db, user_id, AUDIT_ENTITY, faq.id, "create", f"Tạo câu hỏi {data.question}")
    on_source_saved(db, "faq", faq.id)
    return faq


def update_faq(db: Session, faq_id: int, data: FaqUpdate, user_id: int) -> Faq:
    faq = get_faq(db, faq_id)
    changes = {}

    if data.question is not None and faq.question != data.question:
        changes["Câu hỏi"] = data.question
        faq.question = data.question
    if data.answer is not None and faq.answer != data.answer:
        changes["Câu trả lời"] = "Đã cập nhật nội dung mới"
        faq.answer = data.answer
    if data.sort_order is not None and faq.sort_order != data.sort_order:
        changes["Thứ tự hiển thị"] = data.sort_order
        faq.sort_order = data.sort_order
    if data.is_active is not None and faq.is_active != data.is_active:
        changes["Trạng thái"] = "Đang hiển thị" if data.is_active else "Đã ẩn"
        faq.is_active = data.is_active

    faq.updated_by = user_id
    db.commit()
    db.refresh(faq)

    if changes:
        record(db, user_id, AUDIT_ENTITY, faq.id, "update",
               json.dumps(changes, ensure_ascii=False))
        on_source_saved(db, "faq", faq.id)
    return faq


def delete_faq(db: Session, faq_id: int, user_id: int):
    faq = get_faq(db, faq_id)
    question = faq.question
    db.delete(faq)
    db.commit()
    record(db, user_id, AUDIT_ENTITY, faq_id, "delete", f"Xóa câu hỏi {question}")
    on_source_deleted("faq", faq_id)
