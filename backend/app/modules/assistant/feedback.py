"""SỔ «TRỢ LÝ THIẾU CHỨC NĂNG» (ai-CR-078, mục 5 của đề xuất tự cải thiện).

Khi Trợ lý không đáp được một yêu cầu vì CÔNG CỤ thiếu tính năng (thiếu bộ lọc, thiếu cột, không có công cụ cho loại câu
hỏi đó — như vụ «đơn của nhà máy» trước ai-CR-077), nó gọi tool `report_missing_feature`. Mỗi chỗ thiếu gom theo một
khóa (chữ thường không dấu của câu mô tả). Cùng chỗ thiếu lặp từ GAP_MIN lần → bot trên dev mở một VIỆC SỬA MÃ đi
đường thường (rà soát → kế hoạch → đại ca duyệt) — giống vòng «sự cố lặp lại → việc sửa gốc rễ» (O-06).

Lưu ở `tab_setting` khóa `assistant_feature_gaps` (JSON) — không bảng mới.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from .glossary import _load_json, _save_json, fold

KEY = "assistant_feature_gaps"
GAP_MIN = 2
MAX_GAPS = 200
MAX_EXAMPLES = 3


def load(db: Session) -> list[dict]:
    return _load_json(db, KEY)


def signature(missing: str, tool: str = "") -> str:
    return (fold(tool) + ":" if tool else "") + fold(missing)[:100]


def report(db: Session, *, request: str, missing: str, tool: str = "", user_id: int = 0) -> dict:
    """Ghi (hoặc cộng dồn) một chỗ thiếu. Trả mục đã ghi."""
    missing = " ".join((missing or "").split())[:200]
    if not missing:
        raise ValueError("thiếu mô tả chức năng còn thiếu")
    items = load(db)
    sig = signature(missing, tool)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur = next((i for i in items if i.get("sig") == sig), None)
    example = " ".join((request or "").split())[:200]
    if cur is None:
        cur = {"sig": sig, "missing": missing, "tool": (tool or "")[:60], "count": 0, "examples": [],
               "first_at": now, "task_code": ""}
        items.append(cur)
    cur["count"] = int(cur.get("count") or 0) + 1
    cur["last_at"] = now
    if example and example not in cur["examples"]:
        cur["examples"] = (cur["examples"] + [example])[-MAX_EXAMPLES:]
    items = sorted(items, key=lambda i: i.get("last_at") or "")[-MAX_GAPS:]
    _save_json(db, KEY, items, user_id)
    return cur


def due(db: Session) -> list[dict]:
    """Chỗ thiếu đã lặp đủ GAP_MIN lần mà chưa có việc sửa mã."""
    return [i for i in load(db) if int(i.get("count") or 0) >= GAP_MIN and not i.get("task_code")]


def set_task(db: Session, sig: str, code: str) -> None:
    items = load(db)
    for i in items:
        if i.get("sig") == sig:
            i["task_code"] = code
    _save_json(db, KEY, items, 0)


def clear_task(db: Session, code: str) -> None:
    """Việc sửa mã đã ĐÓNG (xong / bỏ) → bỏ gắn, lần thiếu sau tính lại từ đầu."""
    items = load(db)
    changed = False
    for i in items:
        if i.get("task_code") == code:
            i["task_code"], i["count"], changed = "", 0, True
    if changed:
        _save_json(db, KEY, items, 0)

