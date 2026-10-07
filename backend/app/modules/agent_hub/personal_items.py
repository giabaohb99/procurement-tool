"""Thẻ cá nhân (ai-CR-103, nhóm C-05): lịch trình / việc riêng, chi tiêu, danh sách mua sắm của TỪNG NGƯỜI.

Dữ liệu riêng của người dùng, không phải dữ liệu ERP: lọc cứng theo `user_id` của người gọi (model không có tham số
chọn người), không đi qua phân quyền nghiệp vụ, không ghi sổ công ty. Một bảng `tab_agent_personal_item`, `kind` là
SMALLINT + IntEnum (luật R2). Bỏ một món = `status` ĐÃ BỎ (giữ dòng), không có đường xóa (bài canh cấm tool xóa).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import IntEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assistant.glossary import fold

from .model import AgentPersonalItem
from .timeutil import now_local

TITLE_MAX = 300
CATEGORY_MAX = 60
LIST_MAX = 100
AMOUNT_MAX = 10_000_000_000      # 10 tỷ đồng — chặn gõ nhầm số


class ItemKind(IntEnum):
    SCHEDULE = 1     # lịch trình / việc riêng (có thể có giờ)
    EXPENSE = 2      # chi tiêu (số tiền, nhóm)
    SHOPPING = 3     # món cần mua


class ItemStatus(IntEnum):
    OPEN = 1
    DONE = 2
    CANCELLED = 3


KIND_BY_NAME = {"lich_trinh": ItemKind.SCHEDULE, "chi_tieu": ItemKind.EXPENSE, "mua_sam": ItemKind.SHOPPING}
KIND_LABEL = {ItemKind.SCHEDULE: "lịch trình", ItemKind.EXPENSE: "chi tiêu", ItemKind.SHOPPING: "mua sắm"}
STATUS_LABEL = {ItemStatus.OPEN: "còn", ItemStatus.DONE: "xong", ItemStatus.CANCELLED: "đã bỏ"}


def parse_when(text: str) -> datetime | None:
    """«2026-10-08 14:00» · «2026-10-08» · «14:00» (hôm nay) → giờ Việt Nam (naive). Sai dạng → None."""
    t = " ".join((text or "").split())
    if not t:
        return None
    today = now_local()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            pass
    try:
        hm = datetime.strptime(t, "%H:%M")
        return today.replace(hour=hm.hour, minute=hm.minute, second=0, microsecond=0)
    except ValueError:
        return None


def period_range(period: str) -> tuple[datetime, datetime] | None:
    """hom_nay · tuan_nay (thứ hai → chủ nhật) · thang_nay · tat_ca (None)."""
    now = now_local()
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "hom_nay":
        return start_day, start_day + timedelta(days=1)
    if period == "tuan_nay":
        start = start_day - timedelta(days=start_day.weekday())
        return start, start + timedelta(days=7)
    if period == "thang_nay":
        start = start_day.replace(day=1)
        nxt = (start + timedelta(days=32)).replace(day=1)
        return start, nxt
    return None


def add(db: Session, user_id: int, kind: ItemKind, title: str, *, amount: int = 0, category: str = "",
        when: datetime | None = None, note: str = "") -> dict:
    uid = int(user_id or 0)
    title = " ".join((title or "").split())[:TITLE_MAX]
    if uid <= 0:
        return {"ok": False, "message": "chưa đăng nhập tài khoản ERP nên chưa có thẻ riêng"}
    if not title:
        return {"ok": False, "message": "chưa có nội dung"}
    amount = int(amount or 0)
    if kind == ItemKind.EXPENSE and not 0 < amount <= AMOUNT_MAX:
        return {"ok": False, "message": "khoản chi cần số tiền lớn hơn 0 (đồng)"}
    if kind == ItemKind.EXPENSE and when is None:
        when = now_local().replace(tzinfo=None)
    #  Món mua sắm trùng tên còn mở thì không thêm dòng thứ hai.
    if kind == ItemKind.SHOPPING:
        for row in open_items(db, uid, ItemKind.SHOPPING):
            if fold(row.title) == fold(title):
                return {"ok": True, "duplicate": True, "id": row.id, "message": "đã có trong danh sách mua"}
    row = AgentPersonalItem(user_id=uid, kind=int(kind), status=int(ItemStatus.OPEN), title=title,
                            amount=amount if kind == ItemKind.EXPENSE else 0,
                            category=" ".join((category or "").split())[:CATEGORY_MAX], at=when,
                            note=(note or "")[:500], created_by=uid, updated_by=uid)
    db.add(row)
    db.flush()
    return {"ok": True, "id": row.id, "item": describe(row)}


def open_items(db: Session, user_id: int, kind: ItemKind) -> list[AgentPersonalItem]:
    return list(db.scalars(select(AgentPersonalItem).where(
        AgentPersonalItem.user_id == int(user_id), AgentPersonalItem.kind == int(kind),
        AgentPersonalItem.status == int(ItemStatus.OPEN)).order_by(AgentPersonalItem.id)))


def describe(row: AgentPersonalItem) -> dict:
    return {"id": row.id, "kind": KIND_LABEL.get(ItemKind(row.kind), ""), "title": row.title,
            "status": STATUS_LABEL.get(ItemStatus(row.status), ""),
            "amount": int(row.amount or 0) or None, "category": row.category or None,
            "at": row.at.strftime("%d/%m/%Y %H:%M") if row.at else None, "note": row.note or None}


def list_items(db: Session, user_id: int, kind: ItemKind, *, period: str = "", include_done: bool = False) -> dict:
    uid = int(user_id or 0)
    if uid <= 0:
        return {"items": [], "count": 0}
    q = select(AgentPersonalItem).where(AgentPersonalItem.user_id == uid, AgentPersonalItem.kind == int(kind),
                                        AgentPersonalItem.status != int(ItemStatus.CANCELLED))
    if not include_done and kind != ItemKind.EXPENSE:
        q = q.where(AgentPersonalItem.status == int(ItemStatus.OPEN))
    rng = period_range(period or ("thang_nay" if kind == ItemKind.EXPENSE else ""))
    if rng is not None and kind != ItemKind.SHOPPING:
        q = q.where(AgentPersonalItem.at >= rng[0], AgentPersonalItem.at < rng[1])
    order = AgentPersonalItem.at.asc() if kind == ItemKind.SCHEDULE else AgentPersonalItem.id.asc()
    rows = list(db.scalars(q.order_by(order).limit(LIST_MAX)))
    out: dict = {"items": [describe(r) for r in rows], "count": len(rows)}
    if kind == ItemKind.EXPENSE:
        by_cat: dict[str, int] = {}
        for r in rows:
            by_cat[r.category or "khác"] = by_cat.get(r.category or "khác", 0) + int(r.amount or 0)
        out["total"] = sum(by_cat.values())
        out["by_category"] = dict(sorted(by_cat.items(), key=lambda kv: -kv[1]))
    return out


def mark(db: Session, user_id: int, *, item_id: int = 0, title: str = "", kind: ItemKind | None = None,
         status: ItemStatus = ItemStatus.DONE) -> dict:
    """Đánh dấu xong / bỏ MỘT món của chính người đó — theo id, hoặc theo tên (khớp đúng một món đang mở)."""
    uid = int(user_id or 0)
    row = None
    if item_id:
        row = db.get(AgentPersonalItem, int(item_id))
        if row is None or int(row.user_id) != uid:
            return {"ok": False, "message": "không thấy món này trong thẻ của bạn"}
    else:
        f = fold(title)
        q = select(AgentPersonalItem).where(AgentPersonalItem.user_id == uid,
                                            AgentPersonalItem.status == int(ItemStatus.OPEN))
        if kind is not None:
            q = q.where(AgentPersonalItem.kind == int(kind))
        hits = [r for r in db.scalars(q) if f and f in fold(r.title)]
        if len(hits) != 1:
            return {"ok": False, "message": "không thấy món nào khớp" if not hits else "khớp nhiều món, hãy nói rõ hơn",
                    "choices": [describe(r) for r in hits[:8]]}
        row = hits[0]
    row.status = int(status)
    row.updated_by = uid
    db.flush()
    return {"ok": True, "item": describe(row)}


def today_digest(db: Session, user_id: int, day: date | None = None) -> list[str]:
    """Dòng cho bản tin sáng: lịch trình riêng hôm nay + số món còn phải mua."""
    day = day or now_local().date()
    start = datetime(day.year, day.month, day.day)
    rows = list(db.scalars(select(AgentPersonalItem).where(
        AgentPersonalItem.user_id == int(user_id), AgentPersonalItem.kind == int(ItemKind.SCHEDULE),
        AgentPersonalItem.status == int(ItemStatus.OPEN), AgentPersonalItem.at >= start,
        AgentPersonalItem.at < start + timedelta(days=1)).order_by(AgentPersonalItem.at)))
    lines = [f"{r.at:%H:%M} {r.title}" if r.at and (r.at.hour or r.at.minute) else r.title for r in rows]
    shopping = len(open_items(db, user_id, ItemKind.SHOPPING))
    if shopping:
        lines.append(f"Còn {shopping} món cần mua")
    return lines
