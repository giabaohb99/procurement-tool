"""Tự rút ghi nhớ (ai-CR-137, phase 13.3 — đại ca duyệt 09/10/2026).

Chạy cùng vòng tóm tắt cuối buổi (`sessions.tick`, ai-CR-102): buổi chat RIÊNG nào vừa được tóm tắt thì một lượt model rẻ
(`AGENT_MANAGER_MODEL`, khóa của chính người đó) đọc bản tóm tắt + vài dòng đếm từ sổ ý định + lõi sổ nhớ hiện có, rồi đề
xuất tối đa MAX_FACTS điều BỀN về người đó (vai trò, thói quen, cách muốn được trả lời, điều đã chốt) — xếp vào một trong
bốn mục của lõi. Mỗi điều là một dòng `tab_agent_memory_candidate`, đếm số lần gặp lại:

  · gặp lần đầu      → chỉ đếm, KHÔNG ghi (điều nói một lần không bao giờ vào sổ);
  · ≥ MIN_HITS lần trên ≥ MIN_DAYS ngày khác nhau → GHI NGAY vào lõi, đuôi «(tự rút)» + hạn WRITTEN_TTL_DAYS ngày; gặp
    lại khi sắp hết hạn thì gia hạn; không gặp lại thì tự rút khỏi lõi khi tới hạn (cơ chế «(đến dd/mm/yyyy)» sẵn có);
  · chưa đủ lần mà PENDING_TTL_DAYS ngày không gặp lại → hết hạn, bỏ;
  · người dùng «quên: …» → bia mộ TOMBSTONE_DAYS ngày, không rút lại điều đó.

Ba hàng rào của sổ nhớ dùng lại nguyên: không ghi bí mật (`personal_memory.is_secret`) · trùng thì không thêm ·
`user_id` lấy từ chat đã đăng nhập, không bao giờ do model điền. KHÔNG BAO GIỜ rút từ tin NHÓM. Lần đầu bot tự ghi cho một
người thì báo người đó MỘT lần (con trỏ `auto_memory_notice:<user_id>`).
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import date, timedelta
from enum import IntEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.assistant.glossary import fold
from app.modules.assistant.provider.base import ChatMessage

from . import intent_ledger, personal_memory, user_keys
from .constants import STAGE_MEMORY
from .model import AgentCursor, AgentMemoryCandidate
from .timeutil import now_utc, to_local

log = logging.getLogger("app.agent_hub.auto_memory")

MIN_HITS = 3
MIN_DAYS = 2
MAX_FACTS = 5
PENDING_TTL_DAYS = 45
WRITTEN_TTL_DAYS = 120
RENEW_BEFORE_DAYS = 30
TOMBSTONE_DAYS = 90
AUTO_TAG = "(tự rút)"
FACT_MAX = personal_memory.LINE_MAX - 40          # chừa chỗ cho đuôi «(tự rút) (đến dd/mm/yyyy)»
NOTICE_CURSOR = "auto_memory_notice:"
SOURCE_AUTO = 1                                   # «tự rút» — chỗ chừa cho nguồn khác về sau


class CandidateStatus(IntEnum):
    PENDING = 1      # đang đếm
    WRITTEN = 2      # đã ghi vào lõi
    EXPIRED = 3      # không gặp lại, hết hạn
    FORGOTTEN = 4    # người dùng «quên» — bia mộ


STATUS_LABELS = {CandidateStatus.PENDING: "Đang để ý", CandidateStatus.WRITTEN: "Đã ghi vào sổ",
                 CandidateStatus.EXPIRED: "Hết hạn", CandidateStatus.FORGOTTEN: "Đã quên"}
SECTION_NUM = {key: i + 1 for i, key in enumerate(personal_memory.SECTION_KEYS)}
SECTION_KEY = {v: k for k, v in SECTION_NUM.items()}

_UNTIL_TAIL = re.compile(r"\s*\(đến \d{1,2}/\d{1,2}/\d{4}\)\s*$")

EXTRACT_SYSTEM = (
    "Bạn giúp trợ lý ghi nhớ điều BỀN VỮNG về MỘT người dùng sau một buổi trò chuyện. Đầu vào: bản tóm tắt buổi, thống kê "
    "người đó hay hỏi gì, sổ nhớ hiện có, và các điều đang theo dõi (có số thứ tự). Chỉ đề xuất điều còn đúng nhiều tuần: "
    "vai trò / phòng / pháp nhân người đó hay làm việc, thói quen, cách muốn được trả lời, điều đã chốt lâu dài. KHÔNG đề "
    "xuất việc một lần, con số của riêng buổi này, chuyện của người khác, mật khẩu / khóa / số thẻ / số tài khoản. Điều "
    "nào TRÙNG Ý với một điều đang theo dõi thì trả đúng số thứ tự của nó thay vì viết lại. Điều đã có trong sổ nhớ thì bỏ. "
    "Trả DUY NHẤT JSON: {\"facts\": [{\"id\": số} hoặc {\"section\": \"ban_than|so_thich|cach_lam_viec|da_chot\", "
    "\"fact\": \"một câu ngắn tiếng Việt, ngôi thứ ba, không quá 200 ký tự\"}]}, tối đa 5 mục; không có gì thì "
    "{\"facts\": []}."
)


def key_of(line: str) -> str:
    return hashlib.sha1(fold(strip_tags(line)).encode("utf-8")).hexdigest()


def strip_tags(line: str) -> str:
    """Bỏ đuôi hạn «(đến …)» và đuôi «(tự rút)» — để so một dòng trong lõi với điều gốc."""
    s = _UNTIL_TAIL.sub("", line or "").strip()
    if s.endswith(AUTO_TAG):
        s = s[: -len(AUTO_TAG)].strip()
    return " ".join(s.split()).strip(" .")


def enabled() -> bool:
    from app.core import app_settings

    try:
        return bool(app_settings.get("agent_auto_memory_enabled"))
    except Exception:  # noqa: BLE001 — sổ cấu hình hỏng thì theo .env
        return bool(settings.AGENT_AUTO_MEMORY_ENABLED)


def _today(now) -> date:
    local = to_local(now)
    return (local or now).date()


def _core_keys(db: Session, user_id: int) -> set[str]:
    sections = personal_memory.parse(personal_memory.load_core(db, user_id))
    return {key_of(ln) for lines in sections.values() for ln in lines}


def active(db: Session, user_id: int, limit: int = 40) -> list[AgentMemoryCandidate]:
    return list(db.scalars(select(AgentMemoryCandidate).where(
        AgentMemoryCandidate.user_id == int(user_id),
        AgentMemoryCandidate.status.in_((CandidateStatus.PENDING, CandidateStatus.WRITTEN)))
        .order_by(AgentMemoryCandidate.last_seen_at.desc()).limit(limit)))


def build_prompt(summary: str, habits: list[str], core: str, tracked: list[AgentMemoryCandidate]) -> str:
    parts = [f"BẢN TÓM TẮT BUỔI:\n{summary.strip()[:4000]}"]
    if habits:
        parts.append("NGƯỜI NÀY HAY HỎI (30 ngày):\n" + "\n".join(habits))
    parts.append("SỔ NHỚ HIỆN CÓ:\n" + (core.strip()[:3000] or "(trống)"))
    if tracked:
        parts.append("ĐANG THEO DÕI:\n" + "\n".join(f"{c.id}. {c.line}" for c in tracked))
    return "\n\n".join(parts)


def parse_facts(text: str) -> list[dict]:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`").split("\n", 1)[-1]
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return []
    try:
        data = json.loads(raw[start:end + 1])
    except ValueError:
        return []
    items = data.get("facts") if isinstance(data, dict) else None
    return [x for x in items if isinstance(x, dict)][:MAX_FACTS] if isinstance(items, list) else []


def _renew(db: Session, user_id: int, cand: AgentMemoryCandidate, until: date) -> None:
    """Dòng tự rút đã ở lõi, gặp lại khi sắp hết hạn → thay đuôi hạn. Không thấy dòng (người dùng đã sửa tay) thì thôi."""
    sections = personal_memory.parse(personal_memory.load_core(db, user_id))
    for key, lines in sections.items():
        for i, ln in enumerate(lines):
            if AUTO_TAG in ln and key_of(ln) == cand.key_hash:
                lines[i] = f"{cand.line} {AUTO_TAG} (đến {until:%d/%m/%Y})"
                personal_memory._save_core(db, user_id, personal_memory.render(sections))
                return


def observe(db: Session, user_id: int, items: list[dict], *, now=None) -> dict:
    """Đếm các điều model vừa đề xuất cho MỘT người; đủ ngưỡng thì ghi vào lõi. Trả {seen, written: [dòng]}."""
    uid = int(user_id or 0)
    now = now or now_utc()
    today = _today(now)
    day = today.isoformat()
    written: list[str] = []
    if uid <= 0:
        return {"seen": 0, "written": written}
    in_core = _core_keys(db, uid)
    counted: set[int] = set()
    for item in items[:MAX_FACTS]:
        cand = None
        if item.get("id") not in (None, ""):
            try:
                cand = db.get(AgentMemoryCandidate, int(item["id"]))
            except (TypeError, ValueError):
                cand = None
            if cand is None or cand.user_id != uid:       # số của người khác / bịa → bỏ
                continue
        else:
            line = " ".join(str(item.get("fact") or "").split()).strip(" .")
            if not line or len(line) > FACT_MAX or personal_memory.is_secret(line):
                continue
            key = key_of(line)
            cand = db.scalar(select(AgentMemoryCandidate).where(
                AgentMemoryCandidate.user_id == uid, AgentMemoryCandidate.key_hash == key))
            if cand is None:
                if key in in_core:
                    continue
                section = str(item.get("section") or "")
                if section not in SECTION_NUM:
                    section = personal_memory.guess_section(line)
                cand = AgentMemoryCandidate(user_id=uid, section=SECTION_NUM[section], line=line, key_hash=key,
                                            hits=0, day_count=0, status=CandidateStatus.PENDING, source=SOURCE_AUTO,
                                            created_by=uid, updated_by=uid)
                db.add(cand)
                db.flush()
        if cand.id in counted:
            continue
        if cand.status != CandidateStatus.WRITTEN and cand.key_hash in in_core:
            continue                                       # người dùng tự ghi điều này rồi — không ghi đôi
        counted.add(cand.id)
        if cand.status == CandidateStatus.FORGOTTEN:
            if cand.expires_at is not None and cand.expires_at > now:
                continue                                   # bia mộ còn hạn — không rút lại
            cand.status, cand.hits, cand.day_count, cand.last_day = CandidateStatus.PENDING, 0, 0, ""
        elif cand.status == CandidateStatus.EXPIRED:
            cand.status, cand.hits, cand.day_count, cand.last_day = CandidateStatus.PENDING, 0, 0, ""
        cand.hits += 1
        if cand.last_day != day:
            cand.day_count += 1
            cand.last_day = day
        cand.last_seen_at = now
        cand.confidence = round(min(1.0, cand.hits / MIN_HITS) * min(1.0, cand.day_count / MIN_DAYS), 2)
        if cand.status == CandidateStatus.PENDING:
            cand.expires_at = now + timedelta(days=PENDING_TTL_DAYS)
            if cand.hits >= MIN_HITS and cand.day_count >= MIN_DAYS:
                until = today + timedelta(days=WRITTEN_TTL_DAYS)
                res = personal_memory.remember(db, uid, f"{cand.line} {AUTO_TAG}", SECTION_KEY.get(cand.section, ""),
                                               until=until)
                if res.get("ok"):
                    cand.status = CandidateStatus.WRITTEN
                    cand.written_at = now
                    cand.expires_at = now + timedelta(days=WRITTEN_TTL_DAYS)
                    if not res.get("duplicate"):
                        written.append(cand.line)
                else:
                    log.info("agent_hub: chưa ghi được điều tự rút cho user %s: %s", uid, res.get("message"))
        elif cand.status == CandidateStatus.WRITTEN:
            if cand.expires_at is None or cand.expires_at - now < timedelta(days=RENEW_BEFORE_DAYS):
                until = today + timedelta(days=WRITTEN_TTL_DAYS)
                _renew(db, uid, cand, until)
                cand.expires_at = now + timedelta(days=WRITTEN_TTL_DAYS)
        cand.updated_by = uid
    db.commit()
    return {"seen": len(counted), "written": written}


def tombstone(db: Session, user_id: int, needle: str, removed: list[str] | None = None, *, now=None) -> int:
    """Người dùng «quên: …» → mọi điều đang theo dõi / đã ghi khớp `needle` (hoặc đúng dòng vừa xóa) thành bia mộ."""
    uid = int(user_id or 0)
    f = fold(needle or "")
    if uid <= 0 or not f:
        return 0
    now = now or now_utc()
    keys = {key_of(x) for x in removed or []}
    n = 0
    for cand in db.scalars(select(AgentMemoryCandidate).where(
            AgentMemoryCandidate.user_id == uid,
            AgentMemoryCandidate.status.in_((CandidateStatus.PENDING, CandidateStatus.WRITTEN)))):
        if cand.key_hash in keys or f in fold(cand.line):
            cand.status = CandidateStatus.FORGOTTEN
            cand.expires_at = now + timedelta(days=TOMBSTONE_DAYS)
            n += 1
    if n:
        db.flush()
    return n


def expire(db: Session, *, now=None) -> int:
    """Vòng dọn hằng ngày: điều đang đếm quá hạn → hết hạn; điều đã ghi quá hạn (đã tự rút khỏi lõi) → hết hạn."""
    now = now or now_utc()
    n = 0
    for cand in db.scalars(select(AgentMemoryCandidate).where(
            AgentMemoryCandidate.status.in_((CandidateStatus.PENDING, CandidateStatus.WRITTEN)),
            AgentMemoryCandidate.expires_at.is_not(None), AgentMemoryCandidate.expires_at < now)):
        cand.status = CandidateStatus.EXPIRED
        n += 1
    db.commit()
    return n


def _notice_once(db: Session, user_id: int, chat_id: str, lines: list[str]) -> bool:
    name = f"{NOTICE_CURSOR}{int(user_id)}"
    cur = db.scalar(select(AgentCursor).where(AgentCursor.name == name))
    if cur is not None and cur.value:
        return False
    if cur is None:
        cur = AgentCursor(name=name, value=0)
        db.add(cur)
    cur.value = 1
    db.commit()
    from . import service
    from .telegram import esc

    sample = " · ".join(f"«{esc(x)}»" for x in lines[:3])
    service.reply(db, chat_id, (
        f"Em vừa tự ghi vào sổ nhớ của mình: {sample}. Từ nay điều gì nhắc lại từ {MIN_HITS} lần trên {MIN_DAYS} ngày "
        f"khác nhau em sẽ tự ghi như vậy (đuôi «tự rút», {WRITTEN_TTL_DAYS} ngày không nhắc lại thì tự bỏ). "
        "Xem sổ: «sổ nhớ». Bỏ một dòng: «quên: …». Tin nhắn trong nhóm em không bao giờ rút."))
    db.commit()
    return True


def extract(db: Session, chat_id: str, user_id: int, summary: str, *, now=None) -> dict:
    """Một lượt rút sau buổi chat RIÊNG đã tóm tắt. Không bao giờ chạy cho chat nhóm. Trả {ok, seen, written | reason}."""
    from . import manager, service

    uid = int(user_id or 0)
    if not enabled():
        return {"ok": False, "reason": "đang tắt"}
    if uid <= 0 or intent_ledger.is_group_chat(chat_id):
        return {"ok": False, "reason": "không phải chat riêng đã đăng nhập"}
    if not (summary or "").strip():
        return {"ok": False, "reason": "buổi không có bản tóm tắt"}
    tracked = active(db, uid)
    prompt = build_prompt(summary, intent_ledger.habit_lines(db, uid), personal_memory.load_core(db, uid), tracked)
    with user_keys.for_chat(db, chat_id):
        if not user_keys.active_key():
            return {"ok": False, "reason": "chưa có khóa AI"}
        run = service.start_run(db, 0, STAGE_MEMORY)
        try:
            result = manager.get_provider().ask([ChatMessage(role="user", content=prompt)], system=EXTRACT_SYSTEM,
                                                model=settings.AGENT_MANAGER_MODEL, max_tokens=500, temperature=0.1)
        except Exception as e:  # noqa: BLE001 — rút hỏng thì thôi, không phiền người dùng
            service.finish_run(db, run, error=str(e))
            db.commit()
            return {"ok": False, "reason": str(e)[:200]}
        service.finish_run(db, run, result=result)
        db.commit()
    out = observe(db, uid, parse_facts(result.text), now=now)
    if out["written"]:
        _notice_once(db, uid, chat_id, out["written"])
    return {"ok": True, **out}
