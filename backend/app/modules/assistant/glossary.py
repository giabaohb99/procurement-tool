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


def load(db: Session) -> list[dict]:
    from app.modules.setting.model import Setting

    row = db.query(Setting).filter(Setting.skey == KEY).first()
    if row is None or not row.svalue:
        return []
    try:
        items = json.loads(row.svalue)
    except ValueError:
        return []
    return [i for i in items if isinstance(i, dict) and i.get("term") and i.get("meaning")]


def _save(db: Session, items: list[dict], user_id: int) -> None:
    from app.modules.setting import service as setting_service

    setting_service._upsert(db, KEY, json.dumps(items, ensure_ascii=False), user_id)
    db.commit()


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
