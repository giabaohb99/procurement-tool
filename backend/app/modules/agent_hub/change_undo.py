"""Sổ thay đổi do bot ghi + hoàn tác 24 giờ — phía Telegram (ai-CR-184, phase 15.2).

Lõi nằm ở ERP (ai-CR-182, `doc/agent-hub/18-so-thay-doi-va-hoan-tac.md`): `erp.my_changes` trả DÒNG của chính người hỏi
(mới nhất trước, mỗi dòng kèm `can_undo` + `undo_reason`), `erp.undo_change` làm ngược qua đúng service của form và
kiểm lại luật TỪ ĐẦU lúc bấm. Phía bot chỉ là ba lệnh chữ, cùng khuôn "đơn nháp của tôi" / "xóa đơn nháp 2" (ai-CR-143):

  "bot vừa làm gì" · "em vừa ghi gì" · "sổ thay đổi"   → thẻ ≤ 10 dòng mới nhất, đánh số; thứ tự id ghi vào dòng sổ ẩn
                                                          `ds_thay_doi` để "hoàn tác 2" trỏ đúng dòng số 2 của thẻ ĐÓ.
  "hoàn tác" · "hoàn tác n" · "rút lại n" · "undo"     → thẻ xác nhận một chạm (dòng sổ ẩn `cho_hoan_tac`, sống 15 phút,
                                                          dùng một lần). Không số = dòng mới nhất; dòng đó không hoàn tác
                                                          được thì nói lý do và liệt kê lại cho chọn số.
  "đúng" / "thôi" trên thẻ đó                           → `erp.undo_change` / giữ nguyên.

Chân thẻ `UNDO_FOOTER` gắn vào mỗi tin bot báo đã tạo / sửa / xóa (CREATE / UPDATE / DELETE / REUSE) — không gắn cho gửi
duyệt hay lập bộ tài khoản, hai loại đó chỉ ghi sổ (luật ở doc 18 §2). Lời bot: HTML Telegram, không dùng ký tự " ".
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import erp, telegram
from .constants import (
    ACT_CHANGES_LIST,
    ACT_COMMAND,
    ACT_DRAFT_DEL_WAIT,
    ACT_DRAFT_WAIT,
    ACT_GLOSS_WAIT,
    ACT_GRANT_WAIT,
    ACT_OP_WAIT,
    ACT_PROPOSAL,
    ACT_REMIND_WAIT,
    ACT_RESEARCH_WAIT,
    ACT_RUNNER_WAIT,
    ACT_UNDO_DONE,
    ACT_UNDO_DROPPED,
    ACT_UNDO_WAIT,
    DIR_OUT,
    SCOPE_PERSONAL,
)
from .model import AgentMessage
from .timeutil import fmt_local

log = logging.getLogger(__name__)

LIST_LIMIT = 10
UNDO_WINDOW = timedelta(minutes=15)       # thẻ xác nhận "Rút lại?" và thứ tự thẻ liệt kê sống chừng này
UNDO_FOOTER = "<i>Rút lại trong 24 giờ: nhắn hoàn tác</i>"
#  Thẻ hỏi đúng / thôi của đường khác gửi SAU thẻ hoàn tác → câu "đúng" là của thẻ mới hơn, không phải của mình.
_NEWER_CARDS = (ACT_DRAFT_WAIT, ACT_DRAFT_DEL_WAIT, ACT_PROPOSAL, ACT_GRANT_WAIT, ACT_RUNNER_WAIT, ACT_OP_WAIT,
                ACT_GLOSS_WAIT, ACT_REMIND_WAIT, ACT_RESEARCH_WAIT)

#  So trên chữ đã bỏ dấu (glossary.fold): "Bot vừa làm gì?" → "bot vua lam gi".
_LIST = re.compile(
    r"^(?:(?:bot|em|lac lac|may|no)\s+)?(?:vua|da|moi|vua moi)\s+(?:lam|ghi|sua|tao|thay doi|lam duoc)\s+"
    r"(?:nhung gi|gi|cai gi)(?:\s+(?:vay|the|a|nhi|ha|roi|do|nay|em|cho (?:toi|anh|chi)))*$")
_LIST_BOOK = re.compile(
    r"^(?:xem |mo |cho xem |cho (?:toi|anh|chi) xem )?(?:so|lich su|nhat ky) (?:thay doi|bot ghi|bot da ghi)"
    r"(?: cua (?:toi|anh|chi|em|minh))?$")
_UNDO = re.compile(
    r"^(?:hoan tac|rut lai|undo)(?:\s+(?:dong|so|cai|phieu|thay doi))?(?:\s+(?P<n>\d{1,2}))?"
    r"(?:\s+(?:di|nhe|nha|em|giup|anh|chi|gium|luon|cho (?:toi|anh|chi)))*$")


def parse_command(folded: str) -> dict | None:
    """`folded` = chữ đã bỏ dấu. → {op: list} · {op: undo, n: int | None} · None."""
    f = " ".join((folded or "").split())
    if _LIST.match(f) or _LIST_BOOK.match(f):
        return {"op": "list"}
    if m := _UNDO.match(f):
        return {"op": "undo", "n": int(m.group("n")) if m.group("n") else None}
    return None


def with_undo_footer(text: str) -> str:
    """Nối chân thẻ "Rút lại trong 24 giờ" vào một tin báo đã tạo / sửa / xóa."""
    return f"{text}\n{UNDO_FOOTER}"


def _fmt_when(iso: str) -> str:
    """ISO (giờ UTC không múi, như cột created_at của ERP) → "hh:mm dd/mm" giờ Việt Nam."""
    try:
        dt = datetime.fromisoformat(str(iso or ""))
    except ValueError:
        return ""
    if dt.tzinfo is not None:
        dt = (dt - dt.utcoffset()).replace(tzinfo=None)
    return fmt_local(dt)


def _status_line(item: dict, n: int) -> str:
    esc = telegram.esc
    if item.get("can_undo"):
        return f"   <i>hoàn tác được — nhắn <code>hoàn tác {n}</code></i>"
    if int(item.get("undo_status") or 0) == 1:
        return "   <i>đã hoàn tác</i>"
    reason = str(item.get("undo_reason") or "").strip().rstrip(".")
    return f"   <i>không hoàn tác được: {esc(reason)}</i>" if reason else "   <i>không hoàn tác được</i>"


def render_list(items: list[dict]) -> str:
    esc = telegram.esc
    if not items:
        return "Em chưa ghi thay đổi nào cho anh/chị qua chat (tạo / sửa / xóa phiếu đều vào sổ này)."
    lines = [f"<b>BOT VỪA GHI</b> ({len(items)} dòng mới nhất)"]
    for i, x in enumerate(items, 1):
        code = str(x.get("doc_code") or "").strip() or str(x.get("entity_label") or "").strip() or "(không mã)"
        when = _fmt_when(x.get("when") or "")
        head = f"{i}. <b>{esc(code)}</b> · {esc(x.get('action_label') or '')} · {esc(x.get('summary') or '')}"
        if when:
            head += f" · lúc {when}"
        lines.append(head)
        lines.append(_status_line(x, i))
    lines += ["", "Nhắn <code>hoàn tác n</code> để rút lại dòng n (trong 24 giờ)."]
    return "\n".join(lines)


def _confirm_text(item: dict) -> str:
    esc = telegram.esc
    code = str(item.get("doc_code") or "").strip()
    head = esc(item.get("summary") or "")
    if code and code not in head:
        head += f" ({esc(code)})"
    return (f"<b>Rút lại:</b> {head} — nhắn <code>đúng</code> để hoàn tác, <code>thôi</code> để giữ nguyên "
            "(thẻ sống 15 phút).")


# ---------------------------------------------------------------------------
# Sổ ẩn: thứ tự thẻ liệt kê + thẻ xác nhận
# ---------------------------------------------------------------------------
def _expired(row: AgentMessage, pending: AgentMessage) -> bool:
    return bool(row.created_at and pending.created_at and row.created_at - pending.created_at > UNDO_WINDOW)


def _pending_confirm(db: Session, chat_id: str, row: AgentMessage) -> AgentMessage | None:
    pending = db.scalar(select(AgentMessage).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_UNDO_WAIT, AgentMessage.id < row.id)
        .order_by(AgentMessage.id.desc()).limit(1))
    if pending is None or _expired(row, pending):
        return None
    newer = db.scalar(select(AgentMessage.id).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action.in_(_NEWER_CARDS), AgentMessage.id > pending.id).limit(1))
    return None if newer else pending


def _recent_list_ids(db: Session, chat_id: str, row: AgentMessage, user_id: int) -> list[int] | None:
    listed = db.scalar(select(AgentMessage).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_CHANGES_LIST, AgentMessage.id < row.id)
        .order_by(AgentMessage.id.desc()).limit(1))
    if listed is None or _expired(row, listed):
        return None
    try:
        info = json.loads(listed.body or "{}")
    except ValueError:
        return None
    if int(info.get("user_id") or 0) != int(user_id):
        return None
    return [int(x) for x in (info.get("ids") or [])]


def _send_list(db: Session, chat_id: str, user, items: list[dict], lead: str = "") -> None:
    from . import service

    text = render_list(items)
    service.reply(db, chat_id, f"{lead}\n\n{text}" if lead else text, scope=SCOPE_PERSONAL)
    if items:
        service.log_message(db, DIR_OUT, chat_id, 0, json.dumps({"user_id": int(user.id), "ids": [int(x["id"]) for x in items]}),
                            action=ACT_CHANGES_LIST)
    db.commit()


def _send_confirm(db: Session, chat_id: str, user, item: dict) -> None:
    from . import service

    #  Thẻ mới thay thẻ cũ còn treo: "đúng" luôn nói về dòng vừa hỏi.
    for old in db.scalars(select(AgentMessage).where(AgentMessage.chat_id == chat_id,
                                                     AgentMessage.action == ACT_UNDO_WAIT)):
        old.action = ACT_UNDO_DROPPED
    service.reply(db, chat_id, _confirm_text(item), scope=SCOPE_PERSONAL)
    service.log_message(db, DIR_OUT, chat_id, 0, json.dumps({
        "user_id": int(user.id), "change_id": int(item["id"]), "summary": str(item.get("summary") or "")[:300],
        "doc_code": str(item.get("doc_code") or "")}, ensure_ascii=False), action=ACT_UNDO_WAIT)
    db.commit()


# ---------------------------------------------------------------------------
# Lệnh chữ
# ---------------------------------------------------------------------------
def handle_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """"bot vừa làm gì" · "hoàn tác" · "hoàn tác n" · "đúng" / "thôi" trên thẻ Rút lại. Trả True khi đã xử."""
    from app.modules.assistant.glossary import fold

    from . import service

    low = text.strip().lower()
    pending = _pending_confirm(db, chat_id, row)
    if pending is not None and (service._YES.match(low) or service._NO.match(low)):
        return _resolve_confirm(db, chat_id, row, pending, yes=bool(service._YES.match(low)))
    cmd = parse_command(fold(text))
    if cmd is None:
        return False
    row.action = ACT_COMMAND
    row.scope = SCOPE_PERSONAL
    user = service._assistant_user(db, chat_id)
    if user is None:
        service.reply(db, chat_id, "Chat này chưa đăng nhập ERP nên em chưa có sổ thay đổi để xem. " + service._LINK_HELP,
                      scope=SCOPE_PERSONAL)
        return True
    items = erp.my_changes(db, user, LIST_LIMIT)
    if cmd["op"] == "list":
        _send_list(db, chat_id, user, items)
        return True
    esc = telegram.esc
    n = cmd.get("n")
    if n is None:
        if not items:
            _send_list(db, chat_id, user, items)
            return True
        top = items[0]
        if not top.get("can_undo"):
            code = str(top.get("doc_code") or top.get("entity_label") or "")
            reason = str(top.get("undo_reason") or "").strip().rstrip(".")
            _send_list(db, chat_id, user, items,
                       lead=f"Dòng mới nhất (<b>{esc(code)}</b> · {esc(top.get('action_label') or '')}) không hoàn tác được"
                            + (f": {esc(reason)}." if reason else ".") + " Anh/chị chọn số dòng khác bên dưới.")
            return True
        _send_confirm(db, chat_id, user, top)
        return True
    ids = _recent_list_ids(db, chat_id, row, user.id)
    if ids is None:
        _send_list(db, chat_id, user, items, lead="Em liệt kê lại để anh/chị chọn đúng số dòng:")
        return True
    if not 1 <= n <= len(ids):
        _send_list(db, chat_id, user, items, lead=f"Không có dòng số {n}.")
        return True
    target = next((x for x in items if int(x.get("id") or 0) == ids[n - 1]), None)
    if target is None:
        _send_list(db, chat_id, user, items, lead=f"Dòng số {n} đã trôi khỏi danh sách, em liệt kê lại:")
        return True
    if not target.get("can_undo"):
        reason = str(target.get("undo_reason") or "").strip().rstrip(".")
        code = str(target.get("doc_code") or target.get("entity_label") or "")
        service.reply(db, chat_id, f"Dòng {n} (<b>{esc(code)}</b>) không hoàn tác được" + (f": {esc(reason)}." if reason else "."),
                      scope=SCOPE_PERSONAL)
        return True
    _send_confirm(db, chat_id, user, target)
    return True


def _resolve_confirm(db: Session, chat_id: str, row: AgentMessage, pending: AgentMessage, *, yes: bool) -> bool:
    from fastapi import HTTPException

    from . import service

    row.action = ACT_COMMAND
    row.scope = SCOPE_PERSONAL
    try:
        info = json.loads(pending.body or "{}")
    except ValueError:
        info = {}
    if not yes:
        pending.action = ACT_UNDO_DROPPED
        db.commit()
        service.reply(db, chat_id, "Dạ, em giữ nguyên, không hoàn tác.", scope=SCOPE_PERSONAL)
        return True
    #  Chốt dấu TRƯỚC khi gọi ERP: "đúng" lần hai không chạy lại, service của form có thể rollback.
    pending.action = ACT_UNDO_DONE
    db.commit()
    user = service._assistant_user(db, chat_id)
    if user is None or int(user.id) != int(info.get("user_id") or 0):
        pending.action = ACT_UNDO_DROPPED
        db.commit()
        service.reply(db, chat_id, "Tài khoản của chat này đã đổi so với lúc hỏi, em không hoàn tác.", scope=SCOPE_PERSONAL)
        return True
    esc = telegram.esc
    summary = str(info.get("summary") or "")
    pending_id = pending.id
    try:
        done = erp.undo_change(db, user, int(info.get("change_id") or 0))
    except HTTPException as e:
        db.rollback()
        pending = db.get(AgentMessage, pending_id)
        if pending is not None:
            pending.action = ACT_UNDO_DROPPED
        db.commit()
        service.reply(db, chat_id, f"Không hoàn tác được: {esc(str(e.detail))}", scope=SCOPE_PERSONAL)
        return True
    except Exception as e:  # noqa: BLE001 — lỗi lạ cũng phải thành câu trả lời, không nuốt
        log.exception("agent_hub: hoàn tác qua chat hỏng")
        db.rollback()
        pending = db.get(AgentMessage, pending_id)
        if pending is not None:
            pending.action = ACT_UNDO_DROPPED
        db.commit()
        service.reply(db, chat_id, f"Hoàn tác gặp lỗi: {esc(str(e)[:300])}", scope=SCOPE_PERSONAL)
        return True
    text = f"<b>Đã hoàn tác:</b> {esc(summary or done.get('summary') or '')}"
    if done.get("url"):
        text += f"\nXem phiếu: {esc(telegram.absolute_url(str(done['url'])))}"
    service.reply(db, chat_id, text, scope=SCOPE_PERSONAL)
    return True
