"""SỔ THUẬT NGỮ của công ty cho Trợ lý AI (ai-CR-077).

Đại ca 05/10/2026: *"các thuật ngữ chắc lưu ở đâu đó trong memory thôi… còn nhiều thuật ngữ nữa và mình có thể dạy nó
trong khung chat luôn"*. Ví dụ đầu tiên: «nhà máy» = phòng Dego Organic — Trợ lý không biết nên trả đơn của cả công ty.

  - Lưu ở `tab_setting` khóa `assistant_glossary` (JSON) qua `setting.service._upsert` → có sẵn nhật ký trước/sau
    (bao-CR-461), không cần bảng mới, không migration.
  - Mỗi câu hỏi chỉ chèn những thuật ngữ CÓ XUẤT HIỆN trong câu (so không dấu) — sổ dài mấy trăm từ vẫn không làm lời nhắc
    phình ra. Áp cho cả Trợ lý trên web lẫn trên Telegram (cùng đi qua `assistant.service.ask`).
  - Dạy / xóa bằng câu nhắn ở chat đại ca (`agent_hub/service.py`), không có màn hình riêng.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime

from sqlalchemy.orm import Session

KEY = "assistant_glossary"
MAX_TERMS = 500
MAX_MATCHED = 15
TERM_MAX = 60
MEANING_MAX = 300


def fold(text: str) -> str:
    """Hạ chữ + bỏ dấu + gộp khoảng trắng: «Nhà  Máy» → «nha may»."""
    s = (text or "").replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()
    return " ".join(re.sub(r"[^\w()\-]+", " ", s).split())


def _read_raw(db: Session, key: str) -> str:
    """Chuỗi JSON của một khóa `tab_setting`. ai-CR-128: ở DỊCH VỤ AI (DB riêng, không có `tab_setting`) đọc qua cổng B —
    08/10 vòng tự học (`learning.tick`) đổ lỗi «Table 'agent_hub.tab_setting' doesn't exist» mỗi 5 phút."""
    from app.core.config import settings

    if settings.agent_is_service:
        from app.modules.agent_hub import erp

        return erp.setting_raw_get(db, key)
    from app.modules.setting.model import Setting

    row = db.query(Setting).filter(Setting.skey == key).first()
    return row.svalue if row is not None and row.svalue else ""


def _write_raw(db: Session, key: str, value: str, user_id: int) -> None:
    from app.core.config import settings

    if settings.agent_is_service:
        from app.modules.agent_hub import erp

        erp.setting_raw_put(db, key, value, user_id)
        return
    from app.modules.setting import service as setting_service

    setting_service._upsert(db, key, value, user_id)
    db.commit()


def load(db: Session) -> list[dict]:
    raw = _read_raw(db, KEY)
    if not raw:
        return []
    try:
        items = json.loads(raw)
    except ValueError:
        return []
    return [i for i in items if isinstance(i, dict) and i.get("term") and i.get("meaning")]


def _save(db: Session, items: list[dict], user_id: int) -> None:
    _write_raw(db, KEY, json.dumps(items, ensure_ascii=False), user_id)


def find(items: list[dict], term: str) -> dict | None:
    key = fold(term)
    return next((i for i in items if fold(i["term"]) == key), None)


def upsert(db: Session, term: str, meaning: str, user_id: int = 0) -> tuple[dict, str]:
    """Thêm hoặc thay nghĩa. Trả (mục, nghĩa cũ — rỗng nếu mới)."""
    term = " ".join((term or "").split()).strip(" :«»\"'")[:TERM_MAX]
    meaning = " ".join((meaning or "").split()).strip(" .«»\"'")[:MEANING_MAX]
    if not term or not meaning:
        raise ValueError("thiếu thuật ngữ hoặc nghĩa")
    items = load(db)
    cur = find(items, term)
    old = ""
    if cur is not None:
        old = cur["meaning"]
        cur.update(meaning=meaning, at=datetime.now().strftime("%Y-%m-%d %H:%M"), by=user_id)
    else:
        if len(items) >= MAX_TERMS:
            raise ValueError(f"sổ đã đủ {MAX_TERMS} thuật ngữ — xóa bớt rồi dạy thêm")
        cur = {"term": term, "meaning": meaning, "at": datetime.now().strftime("%Y-%m-%d %H:%M"), "by": user_id}
        items.append(cur)
    _save(db, items, user_id)
    return cur, old


def remove(db: Session, term: str, user_id: int = 0) -> bool:
    items = load(db)
    cur = find(items, term)
    if cur is None:
        return False
    items.remove(cur)
    _save(db, items, user_id)
    return True


def match(items: list[dict], *texts: str) -> list[dict]:
    """Thuật ngữ có trong các câu (so không dấu, nguyên cụm chữ). Cụm dài khớp trước."""
    hay = " " + " ".join(fold(t) for t in texts if t) + " "
    out = []
    for item in sorted(items, key=lambda i: -len(i["term"])):
        key = fold(item["term"])
        if key and f" {key} " in hay:
            out.append(item)
        if len(out) >= MAX_MATCHED:
            break
    return out


def prompt_block(db: Session | None, *texts: str) -> str | None:
    """Đoạn chèn vào lời nhắc của Trợ lý: chỉ những thuật ngữ có trong câu hỏi đang xét."""
    if db is None:
        return None
    try:
        found = match(load(db), *texts)
    except Exception:  # noqa: BLE001 — sổ hỏng không được làm sập câu trả lời
        return None
    if not found:
        return None
    return ("THUẬT NGỮ CỦA CÔNG TY (do quản lý dạy — hiểu đúng như vậy, ưu tiên hơn suy đoán; dùng nghĩa này khi chọn "
            "bộ lọc của công cụ):\n" + "\n".join(f"- «{i['term']}»: {i['meaning']}" for i in found))


def listing(items: list[dict]) -> list[str]:
    return [f"«{i['term']}»: {i['meaning']}" for i in sorted(items, key=lambda i: fold(i["term"]))]


# ---------------------------------------------------------------------------
# Đề xuất thuật ngữ chờ đại ca duyệt (ai-CR-078: bot tự học từ lời sửa + tự dò nghĩa từ dữ liệu)
# ---------------------------------------------------------------------------
PENDING_KEY = "assistant_glossary_pending"
MAX_PENDING = 50


def owner_user_id(db: Session) -> int:
    """Tài khoản ERP đang nối với chat của đại ca (AGENT_TELEGRAM_CHAT_ID) — 0 nếu chưa nối."""
    from app.core.config import settings
    from app.modules.agent_hub.model import AgentChatLink

    chat = str(settings.AGENT_TELEGRAM_CHAT_ID or "")
    if not chat:
        return 0
    row = db.query(AgentChatLink).filter(AgentChatLink.chat_id == chat, AgentChatLink.revoked_at.is_(None)) \
        .order_by(AgentChatLink.id.desc()).first()
    return int(row.user_id) if row is not None and row.user_id else 0


def _load_json(db: Session, key: str) -> list[dict]:
    raw = _read_raw(db, key)
    try:
        items = json.loads(raw) if raw else []
    except ValueError:
        items = []
    return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []


def _save_json(db: Session, key: str, items: list[dict], user_id: int) -> None:
    _write_raw(db, key, json.dumps(items, ensure_ascii=False), user_id)


def load_pending(db: Session, *, only_open: bool = True) -> list[dict]:
    items = _load_json(db, PENDING_KEY)
    return [i for i in items if i.get("status") == "cho"] if only_open else items


def propose(db: Session, term: str, meaning: str, *, evidence: str = "", source: str = "", user_id: int = 0) -> dict:
    """Ghi một đề xuất (trùng thuật ngữ + nghĩa đang chờ thì trả lại cái cũ). Bot trên dev nhắn đại ca duyệt."""
    term = " ".join((term or "").split()).strip(" :«»\"'")[:TERM_MAX]
    meaning = " ".join((meaning or "").split()).strip(" .«»\"'")[:MEANING_MAX]
    if not term or not meaning:
        raise ValueError("thiếu thuật ngữ hoặc nghĩa")
    items = _load_json(db, PENDING_KEY)
    for i in items:
        if i.get("status") == "cho" and fold(i["term"]) == fold(term) and fold(i["meaning"]) == fold(meaning):
            return i
    cur = find(load(db), term)
    if cur is not None and fold(cur["meaning"]) == fold(meaning):
        return {**cur, "id": 0, "status": "da_co"}
    pid = max([int(i.get("id") or 0) for i in items] or [0]) + 1
    item = {"id": pid, "term": term, "meaning": meaning, "evidence": (evidence or "")[:300],
            "source": (source or "")[:120], "by": user_id, "status": "cho", "notified": False,
            "at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    items = [i for i in items if i.get("status") == "cho"][-(MAX_PENDING - 1):] + [item]
    _save_json(db, PENDING_KEY, items, user_id)
    return item


def mark_notified(db: Session, pid: int) -> None:
    items = _load_json(db, PENDING_KEY)
    for i in items:
        if int(i.get("id") or 0) == pid:
            i["notified"] = True
    _save_json(db, PENDING_KEY, items, 0)


def decide(db: Session, pid: int, *, accept: bool, user_id: int = 0) -> dict | None:
    """Duyệt (ghi vào sổ) hoặc bỏ một đề xuất đang chờ. Trả đề xuất, None nếu không còn chờ."""
    items = _load_json(db, PENDING_KEY)
    item = next((i for i in items if int(i.get("id") or 0) == pid and i.get("status") == "cho"), None)
    if item is None:
        return None
    item["status"] = "da_duyet" if accept else "bo"
    _save_json(db, PENDING_KEY, items, user_id)
    if accept:
        upsert(db, item["term"], item["meaning"], user_id)
    return item
