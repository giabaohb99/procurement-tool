"""Sổ ghi nhớ cá nhân (ai-CR-095 — nhóm C-02): hai tầng, MỖI NGƯỜI MỘT SỔ, lọc cứng theo `user_id`.

Khung mượn của Letta/MemGPT (đại ca chốt 06/10/2026): «lõi» luôn nằm trong câu hỏi, «kho» chỉ lấy đoạn liên quan.

  Tầng 1 — LÕI  : `tab_agent_memory`, mỗi người đúng MỘT dòng; `text` là Markdown bốn mục cố định (SECTIONS), trần
                  CORE_MAX ký tự (~2.000 token). Nạp NGUYÊN VĂN vào mọi câu hỏi của người đó. Bộ đệm trong tiến trình
                  CACHE_TTL giây (như bộ đệm phân quyền), ghi sổ là xóa đệm ngay.
  Tầng 2 — KHO  : `tab_agent_note` (ghi chú dài, không trần) + vector ở collection RIÊNG của Qdrant, payload mang
                  `user_id`. Mỗi câu hỏi chỉ kéo NOTE_HITS đoạn liên quan của đúng người đó. Nhúng bằng khóa Gemini của
                  người đang chat (`user_keys`); Qdrant / khóa hỏng thì ghi chú vẫn nằm trong DB, tìm theo tiêu đề.

Ba hàng rào: KHÔNG ghi bí mật (mật khẩu, khóa, số thẻ) · trùng thì không thêm · `user_id` luôn lấy từ chat đã đăng
nhập hoặc người gọi tool, KHÔNG BAO GIỜ là tham số do model điền.
"""
from __future__ import annotations

import logging
import re
import time
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.assistant.glossary import fold

from . import user_keys
from .model import AgentMemory, AgentNote

log = logging.getLogger("app.agent_hub.personal_memory")

CORE_MAX = 8000           # trần tầng lõi (ký tự) — đại ca chốt 06/10: 4.000 ít, nâng lên 8.000
LINE_MAX = 300            # một dòng ghi nhớ
NOTE_MAX = 40_000         # một ghi chú dài
CACHE_TTL = 600           # giây — bộ đệm lõi trong tiến trình
WARN_AT = 0.8             # đầy 80% thì nhắc
NOTE_HITS = 5             # đoạn kho lấy vào mỗi câu hỏi
NOTE_CHUNK = 1200         # ký tự mỗi đoạn nhúng
NOTE_COLLECTION = "agent_personal"
MIN_SCORE = 0.5

#  Bốn mục cố định của lõi. Khóa dùng cho tool (model điền), nhãn in ra sổ.
SECTIONS = (
    ("ban_than", "Bản thân"),
    ("so_thich", "Sở thích"),
    ("cach_lam_viec", "Cách làm việc"),
    ("da_chot", "Đã chốt"),
)
SECTION_KEYS = tuple(k for k, _ in SECTIONS)
_LABEL_BY_KEY = dict(SECTIONS)
_KEY_BY_FOLD = {fold(label): key for key, label in SECTIONS}

#  Không bao giờ ghi bí mật vào sổ — dù người dùng tự nhắn «nhớ: mật khẩu wifi là …».
_SECRET_RE = re.compile(
    r"(mật khẩu|mat khau|password|passwd|token|api[\s_-]?key|secret|private key|số thẻ|so the|cvv|\botp\b|"
    r"số tài khoản|so tai khoan|\d{12,})", re.IGNORECASE)

_CACHE: dict[int, tuple[float, str]] = {}


# ---------------------------------------------------------------------------
# Tầng 1 — lõi
# ---------------------------------------------------------------------------
def _invalidate(user_id: int) -> None:
    _CACHE.pop(int(user_id), None)


def clear_cache() -> None:
    _CACHE.clear()


def _row(db: Session, user_id: int) -> AgentMemory | None:
    return db.scalar(select(AgentMemory).where(AgentMemory.user_id == int(user_id)).limit(1))


def load_core(db: Session, user_id: int) -> str:
    """Nguyên văn lõi của MỘT người; rỗng nếu chưa có. Qua bộ đệm tiến trình."""
    uid = int(user_id or 0)
    if uid <= 0:
        return ""
    hit = _CACHE.get(uid)
    now = time.monotonic()
    if hit is not None and hit[0] > now:
        return hit[1]
    row = _row(db, uid)
    text = (row.text or "") if row is not None else ""
    _CACHE[uid] = (now + CACHE_TTL, text)
    return text


def parse(text: str) -> dict[str, list[str]]:
    """Markdown bốn mục → {khóa mục: [dòng]}. Dòng ngoài mục nào thì vào «Đã chốt»."""
    out: dict[str, list[str]] = {k: [] for k in SECTION_KEYS}
    current = "da_chot"
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            current = _KEY_BY_FOLD.get(fold(line.lstrip("#").strip()), "da_chot")
            continue
        if line.startswith(("- ", "* ")):
            line = line[2:].strip()
        if line:
            out[current].append(line)
    return out


def render(sections: dict[str, list[str]]) -> str:
    parts = []
    for key, label in SECTIONS:
        lines = sections.get(key) or []
        if lines:
            parts.append(f"## {label}\n" + "\n".join(f"- {ln}" for ln in lines))
    return "\n\n".join(parts)


def guess_section(line: str) -> str:
    f = fold(line)
    if any(w in f for w in ("thich", "ghet", "khong an", "hay an", "mon ", "uong", "khau vi", "so thich")):
        return "so_thich"
    if any(w in f for w in ("noi gon", "tra loi", "dung hoi", "khong hoi", "xung ", "goi ", "cach lam", "bao cao",
                            "nhan tin", "ngan gon", "chi tiet")):
        return "cach_lam_viec"
    if any(w in f for w in ("chot", "quyet dinh", "tu nay", "thong nhat", "quy dinh")):
        return "da_chot"
    return "ban_than"


def is_secret(line: str) -> bool:
    return bool(_SECRET_RE.search(line or ""))


def _save_core(db: Session, user_id: int, text: str) -> None:
    row = _row(db, user_id)
    if row is None:
        row = AgentMemory(user_id=int(user_id), text=text)
        db.add(row)
    else:
        row.text = text
    db.flush()
    _invalidate(user_id)


def remember(db: Session, user_id: int, line: str, section: str = "") -> dict:
    """Thêm MỘT dòng vào lõi. Trả {ok, message, section, chars, max}. Không ghi bí mật, không ghi trùng."""
    uid = int(user_id or 0)
    line = " ".join((line or "").split()).strip(" .")
    if uid <= 0:
        return {"ok": False, "message": "chat này chưa đăng nhập tài khoản ERP nên chưa có sổ riêng"}
    if not line:
        return {"ok": False, "message": "chưa có nội dung để nhớ"}
    if len(line) > LINE_MAX:
        return {"ok": False, "message": f"dòng dài quá {LINE_MAX} ký tự — nội dung dài thì để «ghi chú: …» vào kho"}
    if is_secret(line):
        return {"ok": False, "message": "em không ghi mật khẩu, khóa, số thẻ hay số tài khoản vào sổ"}
    sections = parse(load_core(db, uid))
    f = fold(line)
    for key in SECTION_KEYS:
        if any(fold(x) == f for x in sections[key]):
            return {"ok": True, "message": "sổ đã có dòng này rồi", "section": key, "duplicate": True,
                    "chars": len(render(sections)), "max": CORE_MAX}
    key = section if section in SECTION_KEYS else guess_section(line)
    sections[key].append(line)
    text = render(sections)
    if len(text) > CORE_MAX:
        return {"ok": False, "message": f"sổ lõi đã đầy ({CORE_MAX} ký tự) — «quên: …» bớt dòng cũ, hoặc để nội dung "
                                        "dài vào «ghi chú: …»"}
    _save_core(db, uid, text)
    out = {"ok": True, "message": "đã ghi", "section": key, "label": _LABEL_BY_KEY[key], "chars": len(text),
           "max": CORE_MAX}
    if len(text) >= CORE_MAX * WARN_AT:
        out["warning"] = f"sổ lõi đã dùng {len(text) * 100 // CORE_MAX}% — nên dọn bớt"
    return out


def forget(db: Session, user_id: int, needle: str) -> list[str]:
    """Xóa mọi dòng lõi CHỨA `needle` (không dấu). Trả các dòng đã xóa."""
    uid = int(user_id or 0)
    f = fold(needle)
    if uid <= 0 or not f:
        return []
    sections = parse(load_core(db, uid))
    removed: list[str] = []
    for key in SECTION_KEYS:
        keep = []
        for ln in sections[key]:
            (removed if f in fold(ln) else keep).append(ln)
        sections[key] = keep
    if removed:
        _save_core(db, uid, render(sections))
    return removed


def usage(db: Session, user_id: int) -> tuple[int, int]:
    return len(load_core(db, user_id)), CORE_MAX


# ---------------------------------------------------------------------------
# Tầng 2 — kho ghi chú dài + vector theo người
# ---------------------------------------------------------------------------
def _embedder():
    from app.modules.assistant.rag.embedder import GeminiEmbedder

    key = user_keys.gemini_key()      # ai-CR-098: chuỗi có thể đang ở khóa Claude — nhúng vẫn cần Gemini
    if not key:
        return None
    return GeminiEmbedder(model=settings.AI_EMBED_MODEL, api_key=key, dim=settings.AI_EMBED_DIM)


def _store():
    from app.modules.assistant.rag.store import VectorStore

    return VectorStore(url=settings.QDRANT_URL, dim=settings.AI_EMBED_DIM, collection=NOTE_COLLECTION)


def _chunks(text: str, size: int = NOTE_CHUNK) -> list[str]:
    text = (text or "").strip()
    out: list[str] = []
    while text:
        cut = text[:size]
        if len(text) > size:
            brk = max(cut.rfind("\n"), cut.rfind(". "))
            if brk > size // 2:
                cut = text[:brk + 1]
        out.append(cut.strip())
        text = text[len(cut):].strip()
    return [c for c in out if c]


def _point_id(note_id: int, index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"agent-personal/{note_id}/{index}"))


def _index_note(note: AgentNote) -> bool:
    """Đánh chỉ mục một ghi chú. Hỏng (chưa có Qdrant, hết hạn mức) → False, ghi chú vẫn ở DB."""
    try:
        emb = _embedder()
        if emb is None:
            return False
        chunks = _chunks(note.text)
        vectors = emb.embed(chunks)
        store = _store()
        store.ensure_collection()
        store.upsert([{
            "id": _point_id(note.id, i),
            "vector": vec,
            "payload": {"user_id": int(note.user_id), "note_id": int(note.id), "title": note.title,
                        "chunk_index": i, "text": chunk, "is_active": True},
        } for i, (chunk, vec) in enumerate(zip(chunks, vectors))])
        return True
    except Exception as e:  # noqa: BLE001 — kho vector là phụ, ghi chú đã nằm trong DB
        log.warning("agent_hub: đánh chỉ mục ghi chú %s hỏng: %s", note.id, e)
        return False


def add_note(db: Session, user_id: int, title: str, text: str) -> dict:
    uid = int(user_id or 0)
    title = " ".join((title or "").split())[:200]
    text = (text or "").strip()
    if uid <= 0:
        return {"ok": False, "message": "chat này chưa đăng nhập tài khoản ERP nên chưa có kho riêng"}
    if not text:
        return {"ok": False, "message": "chưa có nội dung ghi chú"}
    if len(text) > NOTE_MAX:
        return {"ok": False, "message": f"ghi chú dài quá {NOTE_MAX} ký tự, tách bớt"}
    if is_secret(text):
        return {"ok": False, "message": "em không ghi mật khẩu, khóa, số thẻ hay số tài khoản vào kho"}
    if not title:
        title = text.splitlines()[0][:60]
    note = AgentNote(user_id=uid, title=title, text=text, chars=len(text))
    db.add(note)
    db.flush()
    indexed = _index_note(note)
    note.indexed_at = datetime.now() if indexed else None
    return {"ok": True, "message": "đã lưu vào kho", "note_id": note.id, "title": title, "chars": len(text),
            "indexed": indexed}


def list_notes(db: Session, user_id: int, limit: int = 50) -> list[AgentNote]:
    uid = int(user_id or 0)
    if uid <= 0:
        return []
    return list(db.scalars(select(AgentNote).where(AgentNote.user_id == uid, AgentNote.revoked_at.is_(None))
                           .order_by(AgentNote.id.desc()).limit(limit)))


def forget_note(db: Session, user_id: int, note_id: int) -> bool:
    uid = int(user_id or 0)
    note = db.get(AgentNote, int(note_id or 0))
    if note is None or int(note.user_id) != uid or note.revoked_at is not None:
        return False
    note.revoked_at = datetime.now()
    db.flush()
    try:
        from qdrant_client import models as qm

        _store().client.delete(collection_name=NOTE_COLLECTION, points_selector=qm.FilterSelector(filter=qm.Filter(
            must=[qm.FieldCondition(key="note_id", match=qm.MatchValue(value=int(note.id))),
                  qm.FieldCondition(key="user_id", match=qm.MatchValue(value=uid))])), wait=True)
    except Exception as e:  # noqa: BLE001
        log.warning("agent_hub: gỡ vector ghi chú %s hỏng: %s", note.id, e)
    return True


def search_notes(db: Session, user_id: int, query: str, limit: int = NOTE_HITS) -> list[dict]:
    """Đoạn kho liên quan của ĐÚNG người đó. Vector hỏng → tìm theo tiêu đề trong DB."""
    uid = int(user_id or 0)
    query = (query or "").strip()
    if uid <= 0 or not query:
        return []
    if not list_notes(db, uid, limit=1):
        return []    # chưa có ghi chú nào thì khỏi tốn một lượt nhúng cho mỗi câu hỏi
    try:
        from qdrant_client import models as qm

        emb = _embedder()
        if emb is None:
            raise RuntimeError("chưa có khóa nhúng")
        vector = emb.embed([query], is_query=True)[0]
        hits = _store().client.search(
            collection_name=NOTE_COLLECTION, query_vector=vector, limit=limit, with_payload=True,
            query_filter=qm.Filter(must=[qm.FieldCondition(key="user_id", match=qm.MatchValue(value=uid)),
                                         qm.FieldCondition(key="is_active", match=qm.MatchValue(value=True))]))
        out = []
        for h in hits:
            p = h.payload or {}
            if int(p.get("user_id") or 0) != uid or float(h.score or 0) < MIN_SCORE:
                continue   # lọc lần hai phía mình: payload lạ thì bỏ, không tin một mình bộ lọc Qdrant
            out.append({"note_id": int(p.get("note_id") or 0), "title": str(p.get("title") or ""),
                        "text": str(p.get("text") or ""), "score": round(float(h.score), 4)})
        return out
    except Exception as e:  # noqa: BLE001 — rơi về tìm tiêu đề
        log.info("agent_hub: tìm kho vector hỏng (%s), tìm theo tiêu đề", e)
    f = fold(query)
    words = [w for w in f.split() if len(w) >= 3]
    out = []
    for n in list_notes(db, uid, limit=200):
        hay = fold(n.title) + " " + fold(n.text[:2000])
        if words and sum(1 for w in words if w in hay) >= max(1, len(words) // 2):
            out.append({"note_id": n.id, "title": n.title, "text": n.text[:NOTE_CHUNK], "score": 0.0})
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# Nạp vào câu hỏi · xuất sổ
# ---------------------------------------------------------------------------
def prompt_block(db: Session, user_id: int, question: str = "") -> str:
    """Khối chèn vào system của Trợ lý: lõi nguyên văn + đoạn kho liên quan. Rỗng nếu người đó chưa có gì."""
    uid = int(user_id or 0)
    if uid <= 0:
        return ""
    parts = []
    core = load_core(db, uid)
    if core:
        parts.append("SỔ GHI NHỚ RIÊNG CỦA NGƯỜI ĐANG NHẮN (chính họ dạy bạn; dùng để trả lời đúng ý họ, không hỏi "
                     "lại điều đã có ở đây; không đọc cho người khác):\n" + core)
    hits = search_notes(db, uid, question) if question else []
    if hits:
        parts.append("GHI CHÚ RIÊNG LIÊN QUAN (của chính họ):\n" + "\n".join(
            f"- [{h['title']}] {h['text'][:600]}" for h in hits))
    return "\n\n".join(parts)


def export_md(db: Session, user_id: int) -> str:
    core = load_core(db, user_id) or "_(sổ lõi trống)_"
    notes = list_notes(db, user_id)
    out = f"# Sổ ghi nhớ\n\n{core}\n"
    if notes:
        out += "\n# Kho ghi chú\n\n" + "\n\n".join(f"## {n.title} (#{n.id})\n{n.text}" for n in notes) + "\n"
    return out
