"""Tóm tắt CUỐI BUỔI chat vào kho ghi chú riêng (ai-CR-102, nhóm C-02 đợt 2 — đại ca chốt 07/10/2026).

«Hết buổi» = chat IM LẶNG ít nhất SESSION_GAP (30 phút) sau tin hội thoại cuối. Vòng nền mỗi 10 phút (`tick`):
với mỗi chat ĐÃ ĐĂNG NHẬP, lấy các tin hỏi / trả lời / tra cứu kể từ dấu tóm tắt trước; đủ MIN_USER_TURNS câu hỏi của
người dùng thì một lượt model (khóa của chính người đó) viết 3–8 gạch đầu dòng, cất vào `tab_agent_note` (kho, có
vector) với tiêu đề «Buổi dd/mm HH:MM–HH:MM». Không nhắn gì lên Telegram. Dấu ranh giới là MỘT dòng sổ tin chiều ra
`action = tom_tat_buoi` (không gửi đi, không vào mạch hội thoại) — không cần bảng mới.

Lần sau người đó hỏi «hôm trước mình bàn gì về X», `prompt_block` / `search_notes` kéo đúng bản tóm tắt lên.
"""
from __future__ import annotations

import json
import logging
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.assistant.provider.base import ChatMessage

from . import personal_memory, user_keys
from .constants import DIR_IN, DIR_OUT, STAGE_SESSION
from .model import AgentChatLink, AgentMessage
from .timeutil import now_utc, to_local

log = logging.getLogger("app.agent_hub.sessions")

SESSION_GAP = timedelta(minutes=30)
MIN_USER_TURNS = 3
MAX_CHARS = 12_000          # chữ hội thoại đưa vào một lượt tóm tắt
ACT_SESSION_MARK = "tom_tat_buoi"
TALK_ACTIONS = ("hoi", "tra_loi", "nghien_cuu")

SUMMARY_SYSTEM = (
    "Bạn tóm tắt MỘT buổi trò chuyện giữa người dùng và trợ lý để người dùng (và trợ lý) đọc lại sau này. Viết tiếng "
    "Việt có dấu, 3–8 gạch đầu dòng ngắn: người dùng hỏi / nhờ gì; kết luận, con số, tên, ngày quan trọng trợ lý đã đưa; "
    "việc còn dở hoặc hẹn làm tiếp; điều người dùng nói về bản thân. Chỉ dùng thông tin có trong đoạn chat, không bịa, "
    "không chào hỏi, không lời dẫn. Không chép mật khẩu, khóa, số thẻ."
)


def _last_mark_id(db: Session, chat_id: str) -> int:
    return int(db.scalar(select(func.max(AgentMessage.id)).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_SESSION_MARK)) or 0)


def pending_rows(db: Session, chat_id: str) -> list[AgentMessage]:
    return list(db.scalars(select(AgentMessage).where(
        AgentMessage.chat_id == chat_id, AgentMessage.id > _last_mark_id(db, chat_id),
        AgentMessage.action.in_(TALK_ACTIONS)).order_by(AgentMessage.id)))


def _mark(db: Session, chat_id: str, last_id: int, **info) -> None:
    from . import service

    service.log_message(db, DIR_OUT, chat_id, 0, json.dumps({"until_id": last_id, **info}, ensure_ascii=False),
                        action=ACT_SESSION_MARK)
    db.commit()


def transcript(rows: list[AgentMessage]) -> str:
    lines = []
    total = 0
    for r in rows:
        who = "Người dùng" if r.direction == DIR_IN else "Trợ lý"
        line = f"{who}: {' '.join((r.body or '').split())[:1500]}"
        total += len(line)
        if total > MAX_CHARS:
            break
        lines.append(line)
    return "\n".join(lines)


def summarize(db: Session, chat_id: str, user_id: int, rows: list[AgentMessage]) -> dict:
    """Một lượt model → ghi chú trong kho. Trả {ok, note_id | reason}."""
    from . import manager, service

    first, last = to_local(rows[0].created_at), to_local(rows[-1].created_at)
    title = f"Buổi {first:%d/%m %H:%M}–{last:%H:%M}" if first and last else "Buổi trò chuyện"
    with user_keys.for_chat(db, chat_id):
        if not user_keys.active_key():
            return {"ok": False, "reason": "chưa có khóa AI"}
        run = service.start_run(db, 0, STAGE_SESSION)
        try:
            result = manager.get_provider().ask([ChatMessage(role="user", content=transcript(rows))],
                                                system=SUMMARY_SYSTEM, max_tokens=700, temperature=0.2)
        except Exception as e:  # noqa: BLE001 — tóm tắt hỏng thì thôi, không phiền người dùng
            service.finish_run(db, run, error=str(e))
            db.commit()
            return {"ok": False, "reason": str(e)[:200]}
        service.finish_run(db, run, result=result)
        db.commit()
        text = (result.text or "").strip()
        if not text:
            return {"ok": False, "reason": "model không trả chữ"}
        out = personal_memory.add_note(db, user_id, title, text)
        db.commit()
        return {"ok": bool(out.get("ok")), "note_id": out.get("note_id"), "reason": out.get("message", "")}


def tick(db: Session, *, now=None) -> dict:
    """Mỗi 10 phút: buổi nào đã im lặng ≥ 30 phút thì tóm tắt (đủ câu) hoặc chỉ đặt dấu (ít câu / không khóa)."""
    now = now or now_utc()
    done = skipped = 0
    links = db.scalars(select(AgentChatLink).where(AgentChatLink.chat_id != "", AgentChatLink.revoked_at.is_(None)))
    for link in links:
        rows = pending_rows(db, link.chat_id)
        if not rows or rows[-1].created_at is None or now - rows[-1].created_at < SESSION_GAP:
            continue
        user_turns = sum(1 for r in rows if r.direction == DIR_IN)
        if user_turns < MIN_USER_TURNS:
            _mark(db, link.chat_id, rows[-1].id, skipped="ít câu")
            skipped += 1
            continue
        res = summarize(db, link.chat_id, link.user_id, rows)
        #  Đặt dấu cả khi hỏng: không thử lại mãi mỗi 10 phút (khóa hết tiền thì lượt nào cũng hỏng).
        _mark(db, link.chat_id, rows[-1].id, note_id=res.get("note_id"), error="" if res.get("ok") else res.get("reason"))
        if res.get("ok"):
            done += 1
        else:
            skipped += 1
            log.info("agent_hub: chưa tóm tắt được buổi của chat %s: %s", link.chat_id, res.get("reason"))
    return {"summarized": done, "skipped": skipped}
