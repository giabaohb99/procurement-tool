"""«Bot đang nhớ gì về tôi» (ai-CR-138, phase 13.4): xem / sửa / xóa trí nhớ của CHÍNH MÌNH.

Mọi hàm nhận `user_id` của NGƯỜI ĐANG ĐĂNG NHẬP (controller lấy từ phiên, không bao giờ từ tham số). Không có đường nào cho
quản trị / quản lý đọc sổ người khác — kể cả admin. Thu hồi / nghỉ việc (`service.revoke_user_access`) gọi `wipe`.

Dòng lõi được chỉ bằng (mục, nguyên văn dòng cũ) chứ không bằng số thứ tự: hai tab cùng sửa thì tab sau nhận 409 thay vì
sửa nhầm dòng bên cạnh.
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import auto_memory, intent_ledger, personal_memory as pm
from .model import AgentCursor, AgentIntent, AgentMemory, AgentMemoryCandidate, AgentNote
from .timeutil import now_utc


class MemoryConflict(Exception):
    """Dòng cần sửa / xóa không còn đúng như lúc mở màn."""


def _line_view(text: str) -> dict:
    until = pm.until_of(text)
    return {"text": text, "fact": auto_memory.strip_tags(text), "auto": auto_memory.AUTO_TAG in text,
            "until": until.isoformat() if until else None}


def snapshot(db: Session, user_id: int) -> dict:
    uid = int(user_id)
    sections = pm.parse(pm.load_core(db, uid))
    chars, cap = pm.usage(db, uid)
    watching = db.scalars(select(AgentMemoryCandidate).where(
        AgentMemoryCandidate.user_id == uid, AgentMemoryCandidate.status == auto_memory.CandidateStatus.PENDING)
        .order_by(AgentMemoryCandidate.last_seen_at.desc()).limit(50))
    return {
        "sections": [{"key": key, "label": label, "lines": [_line_view(x) for x in sections.get(key, [])]}
                     for key, label in pm.SECTIONS],
        "chars": chars, "max": cap,
        "watching": [{"id": c.id, "fact": c.line, "section": auto_memory.SECTION_KEY.get(c.section, ""),
                      "hits": c.hits, "days": c.day_count, "need_hits": auto_memory.MIN_HITS,
                      "need_days": auto_memory.MIN_DAYS, "confidence": c.confidence,
                      "last_seen_at": c.last_seen_at.isoformat() if c.last_seen_at else None} for c in watching],
        "notes": [{"id": n.id, "title": n.title, "chars": n.chars,
                   "created_at": n.created_at.isoformat() if n.created_at else None}
                  for n in pm.list_notes(db, uid, limit=100)],
        "habits": intent_ledger.defaults_of(db, uid),
        "suggestions": intent_ledger.suggestions_of(db, uid),
        "auto_enabled": auto_memory.enabled(),
    }


def _find(sections: dict, section: str, old: str) -> int:
    lines = sections.get(section)
    if lines is None:
        raise ValueError("mục không hợp lệ")
    for i, ln in enumerate(lines):
        if ln == old:
            return i
    raise MemoryConflict("dòng này vừa đổi ở nơi khác — tải lại màn rồi thử lại")


def add_line(db: Session, user_id: int, section: str, text: str, until=None) -> dict:
    if section not in pm.SECTION_KEYS:
        raise ValueError("mục không hợp lệ")
    out = pm.remember(db, int(user_id), text, section, until=until)
    if out.get("ok"):
        db.commit()
    return out


def edit_line(db: Session, user_id: int, section: str, old: str, text: str) -> dict:
    """Sửa một dòng. Dòng «tự rút» người dùng sửa lại = của họ: bỏ đuôi «(tự rút)», điều gốc thành bia mộ để bot không
    rút lại câu cũ chen cạnh câu đã sửa."""
    uid = int(user_id)
    line = " ".join((text or "").split()).strip(" .")
    if not line:
        raise ValueError("chưa có nội dung")
    if len(line) > pm.LINE_MAX:
        raise ValueError(f"dòng dài quá {pm.LINE_MAX} ký tự")
    if pm.is_secret(line):
        raise ValueError("không ghi mật khẩu, khóa, số thẻ hay số tài khoản vào sổ")
    sections = pm.parse(pm.load_core(db, uid))
    i = _find(sections, section, old)
    if any(pm.fold(x) == pm.fold(line) for key, lines in sections.items() for j, x in enumerate(lines)
           if not (key == section and j == i)):
        raise ValueError("sổ đã có dòng này rồi")
    sections[section][i] = line
    text_all = pm.render(sections)
    if len(text_all) > pm.CORE_MAX:
        raise ValueError(f"sổ lõi đã đầy ({pm.CORE_MAX} ký tự)")
    pm._save_core(db, uid, text_all)
    if auto_memory.AUTO_TAG in old:
        auto_memory.tombstone(db, uid, auto_memory.strip_tags(old), [old])
    db.commit()
    return {"ok": True, "line": line}


def delete_line(db: Session, user_id: int, section: str, old: str) -> dict:
    uid = int(user_id)
    sections = pm.parse(pm.load_core(db, uid))
    i = _find(sections, section, old)
    sections[section].pop(i)
    pm._save_core(db, uid, pm.render(sections))
    auto_memory.tombstone(db, uid, auto_memory.strip_tags(old), [old])
    db.commit()
    return {"ok": True}


def drop_watching(db: Session, user_id: int, cand_id: int) -> bool:
    """Bỏ một điều bot đang để ý (chưa ghi) → bia mộ, không đếm tiếp."""
    cand = db.get(AgentMemoryCandidate, int(cand_id))
    if cand is None or int(cand.user_id) != int(user_id) or cand.status != auto_memory.CandidateStatus.PENDING:
        return False
    cand.status = auto_memory.CandidateStatus.FORGOTTEN
    cand.expires_at = now_utc() + timedelta(days=auto_memory.TOMBSTONE_DAYS)
    db.commit()
    return True


def delete_note(db: Session, user_id: int, note_id: int) -> bool:
    ok = pm.forget_note(db, int(user_id), int(note_id))
    if ok:
        db.commit()
    return ok


def wipe(db: Session, user_id: int) -> dict:
    """Xóa SẠCH trí nhớ của một người: lõi, kho ghi chú (kèm vector), điểm tự rút, sổ ý định, con trỏ báo tự rút.
    Không commit — người gọi quyết (thu hồi chạy chung giao dịch khóa tài khoản)."""
    uid = int(user_id)
    notes = [n.id for n in db.scalars(select(AgentNote).where(AgentNote.user_id == uid, AgentNote.revoked_at.is_(None)))]
    for nid in notes:
        pm.forget_note(db, uid, nid)
    core = db.execute(delete(AgentMemory).where(AgentMemory.user_id == uid)).rowcount or 0
    cands = db.execute(delete(AgentMemoryCandidate).where(AgentMemoryCandidate.user_id == uid)).rowcount or 0
    intents = db.execute(delete(AgentIntent).where(AgentIntent.user_id == uid)).rowcount or 0
    db.execute(delete(AgentCursor).where(AgentCursor.name == f"{auto_memory.NOTICE_CURSOR}{uid}"))
    db.flush()
    pm._invalidate(uid)
    return {"core": int(core), "notes": len(notes), "watching": int(cands), "intents": int(intents)}
