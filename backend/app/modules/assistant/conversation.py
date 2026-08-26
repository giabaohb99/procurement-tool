"""Lưu / đọc lịch sử hội thoại Trợ lý AI (Phase 1).

Hội thoại là RIÊNG TƯ của người tạo: mọi truy vấn đều chốt `created_by == user.id`. Entity
`assistant` khai PUBLIC ở scoping (không lọc theo dòng) nên phần riêng tư này phải tự chặn ở
đây, không dựa vào apply_scope.
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import service, usage
from .model import AssistantConversation, AssistantMessage, MessageRole

# Số lượt gần nhất nạp lại làm ngữ cảnh khi hỏi tiếp (chặn phình token + chi phí).
HISTORY_LIMIT = 20
# Độ dài tiêu đề tự đặt từ câu hỏi đầu tiên.
TITLE_MAX = 80


def _title_from(message: str) -> str:
    t = " ".join(message.split())
    return t[:TITLE_MAX] if t else "Hội thoại mới"


def list_conversations(db: Session, user) -> list[AssistantConversation]:
    """Danh sách hội thoại của chính người dùng, mới trước."""
    stmt = (
        select(AssistantConversation)
        .where(AssistantConversation.created_by == user.id)
        # MySQL 8.0 KHÔNG hỗ trợ cú pháp `NULLS LAST`; mà nó vốn xếp NULL xuống cuối khi
        # sắp DESC nên không cần nói thêm. last_message_at gần như luôn có (đặt lúc tạo).
        .order_by(
            AssistantConversation.last_message_at.desc(),
            AssistantConversation.id.desc(),
        )
    )
    return list(db.execute(stmt).scalars().all())


def get_owned(db: Session, user, conv_id: int) -> AssistantConversation | None:
    """Lấy 1 hội thoại NẾU đúng chủ; ngược lại None (chặn đọc chéo bằng cách gõ id)."""
    conv = db.get(AssistantConversation, conv_id)
    if conv is None or conv.created_by != user.id:
        return None
    return conv


def get_messages(db: Session, conv_id: int) -> list[AssistantMessage]:
    stmt = (
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conv_id)
        .order_by(AssistantMessage.id.asc())
    )
    return list(db.execute(stmt).scalars().all())


def _recent_history(db: Session, conv_id: int) -> list[dict]:
    """HISTORY_LIMIT lượt gần nhất, theo đúng thứ tự thời gian, dạng {role, content}."""
    stmt = (
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conv_id)
        .order_by(AssistantMessage.id.desc())
        .limit(HISTORY_LIMIT)
    )
    rows = list(db.execute(stmt).scalars().all())
    rows.reverse()
    out = []
    for m in rows:
        role = "assistant" if m.role == MessageRole.ASSISTANT else "user"
        out.append({"role": role, "content": m.content})
    return out


def chat(db: Session, user, body) -> dict:
    """Một lượt hỏi có LƯU LỊCH SỬ. Trả reply + conversation_id + usage.

    - conversation_id: tiếp hội thoại cũ (kiểm đúng chủ), None = mở mới.
    - Lịch sử ngữ cảnh lấy từ DB (không tin `history` client gửi khi đã có hội thoại).
    """
    # Guard chi phí: chặn TRƯỚC khi gọi model, kẻo vượt trần vẫn tốn một lượt.
    usage.check_daily_limit(db, user)

    conv: AssistantConversation | None = None
    if body.conversation_id:
        conv = get_owned(db, user, body.conversation_id)
        if conv is None:
            raise PermissionError("Không tìm thấy hội thoại hoặc không phải của bạn")

    # Ngữ cảnh: hội thoại cũ -> lấy từ DB; hội thoại mới -> dùng history client gửi (nếu có).
    if conv is not None:
        history = _recent_history(db, conv.id)
    else:
        history = [h.model_dump() for h in body.history] if body.history else None

    result = service.ask(
        body.message,
        db=db,
        user=user,
        provider=body.provider,
        model=body.model,
        kind=body.kind,
        system=body.system,
        history=history,
    )

    now = datetime.now()
    if conv is None:
        conv = AssistantConversation(
            title=_title_from(body.message),
            provider=result["provider"],
            model=result["model"],
            last_message_at=now,
            created_by=user.id,
            updated_by=user.id,
        )
        db.add(conv)
        db.flush()   # có conv.id để gắn message
    else:
        conv.provider = result["provider"]
        conv.model = result["model"]
        conv.last_message_at = now
        conv.updated_by = user.id

    usage = result.get("usage", {})
    db.add(AssistantMessage(
        conversation_id=conv.id, role=MessageRole.USER, content=body.message,
        created_by=user.id, updated_by=user.id,
    ))
    db.add(AssistantMessage(
        conversation_id=conv.id, role=MessageRole.ASSISTANT, content=result["text"],
        provider=result["provider"], model=result["model"],
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        thinking_tokens=usage.get("thinking_tokens", 0),
        cache_read_tokens=usage.get("cache_read_tokens", 0),
        cache_write_tokens=usage.get("cache_write_tokens", 0),
        created_by=user.id, updated_by=user.id,
    ))
    db.commit()

    result["conversation_id"] = conv.id
    result["title"] = conv.title
    return result


def delete_conversation(db: Session, user, conv_id: int) -> bool:
    """Xóa hội thoại + toàn bộ tin của nó. Trả False nếu không phải chủ."""
    conv = get_owned(db, user, conv_id)
    if conv is None:
        return False
    db.query(AssistantMessage).filter(
        AssistantMessage.conversation_id == conv_id
    ).delete(synchronize_session=False)
    db.delete(conv)
    db.commit()
    return True


def serialize_conversation(conv: AssistantConversation) -> dict:
    return {
        "id": conv.id,
        "title": conv.title,
        "provider": conv.provider,
        "model": conv.model,
        "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
    }


def serialize_message(m: AssistantMessage) -> dict:
    return {
        "id": m.id,
        "role": int(m.role),
        "role_name": "assistant" if m.role == MessageRole.ASSISTANT else "user",
        "content": m.content,
        "provider": m.provider,
        "model": m.model,
        "usage": {
            "input_tokens": m.input_tokens,
            "output_tokens": m.output_tokens,
            "thinking_tokens": m.thinking_tokens,
            "cache_read_tokens": m.cache_read_tokens,
            "cache_write_tokens": m.cache_write_tokens,
        },
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }
