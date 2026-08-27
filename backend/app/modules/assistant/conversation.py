"""Lưu / đọc lịch sử hội thoại Trợ lý AI (Phase 1).

Hội thoại là RIÊNG TƯ của người tạo: mọi truy vấn đều chốt `created_by == user.id`. Entity
`assistant` khai PUBLIC ở scoping (không lọc theo dòng) nên phần riêng tư này phải tự chặn ở
đây, không dựa vào apply_scope.
"""
import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import attachments as attach
from . import service, usage
from .model import AssistantConversation, AssistantMessage, MessageRole

# Số lượt gần nhất nạp lại làm ngữ cảnh khi hỏi tiếp (chặn phình token + chi phí).
HISTORY_LIMIT = 20
# Số TIN cuối cùng còn được nạp lại TỆP THẬT khi hỏi tiếp (CR-204). Tin cũ hơn chỉ còn
# dòng thế chỗ "[Đã gửi kèm tệp: ...]" — ảnh/PDF base64 rất nặng token, nạp lại cả 20 lượt
# thì một hội thoại dài đốt tiền gấp chục lần.
ATTACH_REPLAY_WINDOW = 4
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


def _attachment_meta(m: AssistantMessage) -> list[dict]:
    """Danh sách tệp đính kèm của một tin (JSON trong cột `attachments`); hỏng/rỗng -> []."""
    if not m.attachments:
        return []
    try:
        meta = json.loads(m.attachments)
    except ValueError:
        return []
    return meta if isinstance(meta, list) else []


def _replay_blocks(db: Session, meta: list[dict]) -> list[dict] | None:
    """Nạp lại TỆP THẬT của một tin cũ thành block trung lập. Tệp đã bị xóa khỏi storage
    hoặc đọc hỏng -> None để rơi về dòng thế chỗ, không được sập cả lượt chat."""
    from app.modules.attachment.model import StoredFile

    files = []
    for item in meta:
        f = db.get(StoredFile, item.get("id") or 0)
        # Chỉ nạp tệp đúng thư mục chat — metadata cũ trỏ nhầm đi đâu cũng không theo.
        if not f or attach.KEY_MARK not in (f.file_key or ""):
            return None
        files.append(f)
    try:
        return attach.build_blocks(files)
    except Exception:  # noqa: BLE001 - storage lỗi thì mất tiện nghi nạp lại, không mất chat
        return None


def _recent_history(db: Session, conv_id: int) -> list[dict]:
    """HISTORY_LIMIT lượt gần nhất, theo đúng thứ tự thời gian, dạng {role, content}.

    Tin có tệp đính kèm: `ATTACH_REPLAY_WINDOW` tin cuối được nạp lại tệp thật (content
    thành list block), cũ hơn thì thay bằng dòng chữ "[Đã gửi kèm tệp: ...]".
    """
    stmt = (
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conv_id)
        .order_by(AssistantMessage.id.desc())
        .limit(HISTORY_LIMIT)
    )
    rows = list(db.execute(stmt).scalars().all())
    rows.reverse()
    out = []
    total = len(rows)
    for idx, m in enumerate(rows):
        role = "assistant" if m.role == MessageRole.ASSISTANT else "user"
        content: str | list = m.content
        meta = _attachment_meta(m) if role == "user" else []
        if meta:
            blocks = _replay_blocks(db, meta) if idx >= total - ATTACH_REPLAY_WINDOW else None
            if blocks is not None:
                if m.content:
                    blocks.append({"type": "text", "text": m.content})
                content = blocks
            else:
                mark = attach.placeholder_text(meta)
                content = f"{m.content}\n{mark}" if m.content else mark
        out.append({"role": role, "content": content})
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

    # Tệp đính kèm lượt này (CR-204): kiểm quyền SỞ HỮU từng id rồi mới đọc nội dung —
    # id lạ / tệp người khác / tệp ngoài thư mục chat là chặn cả lượt (PermissionError -> 404).
    files = attach.resolve_owned(db, user, body.attachment_ids or [])
    blocks = attach.build_blocks(files) if files else None
    attachment_meta = attach.meta_of(files)

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
        attachments=blocks,
    )

    now = datetime.now()
    if conv is None:
        # Gửi mỗi tệp không kèm chữ -> đặt tiêu đề theo tên tệp cho danh sách còn đọc được.
        title = _title_from(body.message) if body.message.strip() else (
            _title_from(f"Tệp: {files[0].filename}") if files else _title_from("")
        )
        conv = AssistantConversation(
            title=title,
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

    # KHÔNG đặt tên biến này là `usage` — trùng tên module `usage` đã import ở đầu file, khiến
    # `usage.check_daily_limit(...)` phía trên bị Python coi là biến cục bộ chưa gán (UnboundLocalError).
    usage_data = result.get("usage", {})
    db.add(AssistantMessage(
        conversation_id=conv.id, role=MessageRole.USER, content=body.message,
        attachments=json.dumps(attachment_meta, ensure_ascii=False) if attachment_meta else "",
        created_by=user.id, updated_by=user.id,
    ))
    db.add(AssistantMessage(
        conversation_id=conv.id, role=MessageRole.ASSISTANT, content=result["text"],
        provider=result["provider"], model=result["model"],
        input_tokens=usage_data.get("input_tokens", 0),
        output_tokens=usage_data.get("output_tokens", 0),
        thinking_tokens=usage_data.get("thinking_tokens", 0),
        cache_read_tokens=usage_data.get("cache_read_tokens", 0),
        cache_write_tokens=usage_data.get("cache_write_tokens", 0),
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
        "attachments": _attachment_meta(m),
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
