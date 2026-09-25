"""Ai được ra lệnh SỬA MÃ qua bot (ai-CR-051, K-01 + K-04 của `doc/agent-hub/04`).

«Cách 3», đại ca chốt 24/09/2026: quyền cấp bằng CÂU NHẮN trên chat của đại ca («cho anh Được quyền
gộp dev»), bot hỏi lại, «đúng» thì ghi `tab_agent_grant`. Không có màn web, không sửa `.env`, không
build, không khởi động lại. Chỉ chat đại ca (`AGENT_TELEGRAM_CHAT_ID`) cấp/gỡ được; chat đó không
cần dòng nào và không tự gỡ được mình.

Hai cấp, cấp trên bao cấp dưới:
  1 `duyệt kế hoạch` — hỏi tình trạng, xem chi tiết, duyệt / sửa kế hoạch, làm tiếp, sửa cho xanh,
    đóng, bỏ việc;
  2 `gộp dev`        — thêm gộp vào nhánh nền, deploy dev, thu hồi, mở PR.
Prod không cấp cho ai (bot chưa có lệnh prod, và sẽ không có qua chat).
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import AgentChatLink, AgentGrant

LEVEL_NONE = 0
LEVEL_PLAN = 1
LEVEL_MERGE = 2
LEVEL_ADMIN = 99          # chat của đại ca — không ghi sổ, luôn đủ cấp
LEVEL_LABELS = {LEVEL_PLAN: "duyệt kế hoạch", LEVEL_MERGE: "gộp dev"}
LEVEL_SCOPE = {
    LEVEL_PLAN: "hỏi tình trạng, duyệt / sửa kế hoạch, làm tiếp, đóng hoặc bỏ việc",
    LEVEL_MERGE: "như cấp duyệt kế hoạch, thêm gộp vào nhánh nền, deploy dev, thu hồi",
}
#  Cấp tối thiểu cho từng lệnh trên việc (tên lệnh = `_COMMANDS` trong service). Lệnh không có
#  trong bảng thì coi như cần cấp cao nhất — quên khai là chặn, không phải mở.
REQUIRED_LEVEL = {
    "status": LEVEL_PLAN, "detail": LEVEL_PLAN, "approve": LEVEL_PLAN, "replan": LEVEL_PLAN,
    "continue": LEVEL_PLAN, "fixgate": LEVEL_PLAN, "done": LEVEL_PLAN, "cancel": LEVEL_PLAN,
    "merge": LEVEL_MERGE, "deploy": LEVEL_MERGE, "revert": LEVEL_MERGE, "pr": LEVEL_MERGE,
    "rule_yes": LEVEL_ADMIN, "rule_no": LEVEL_ADMIN,
}
#  Lệnh mà đại ca cần biết là NGƯỜI KHÁC vừa ra (báo về chat đại ca).
NOTIFY_ACTIONS = ("approve", "replan", "merge", "deploy", "revert", "cancel", "done", "pr")

_HONORIFICS = r"(anh|chị|chi|em|bạn|ban|ông|bà|cô|chú|a|c)"
_LEVEL_WORDS = r"(gộp dev|gộp và deploy|gộp|merge|deploy|duyệt kế hoạch|duyệt)"
_TAIL = r"(\s+(nhé|nha|đi|luôn|giúp em|giúp anh|dùm em|dùm anh))*[.!]*"
#  «cho anh Được quyền gộp dev» · «cấp cho Bảo quyền duyệt kế hoạch» · «cấp quyền gộp dev cho anh Được»
_GRANT_A = re.compile(rf"^(cấp cho|mở quyền cho|mở cho|cấp|cho)\s+(?P<name>.+?)\s+quyền\s+(?P<level>{_LEVEL_WORDS})"
                      rf"{_TAIL}$")
_GRANT_B = re.compile(rf"^(cấp|cho|mở)\s+quyền\s+(?P<level>{_LEVEL_WORDS})\s+cho\s+(?P<name>.+?){_TAIL}$")
#  «gỡ quyền của anh Được» · «thu quyền sửa mã anh Được» · «bỏ quyền Bảo»
_REVOKE = re.compile(rf"^(gỡ|thu|thu hồi|bỏ|tắt|khóa)\s+quyền(\s+sửa mã)?(\s+của)?\s+(?P<name>.+?){_TAIL}$")
#  «ai đang được sửa mã» · «ai có quyền gộp» · «danh sách quyền sửa mã»
_LIST = re.compile(r"^((những\s+)?ai\s+(đang\s+)?(được|có)\s+(quyền\s+)?(sửa mã|gộp|duyệt|ra lệnh)"
                   r"|(danh sách|ds|xem)\s+quyền(\s+sửa mã)?)")


def level_of_words(words: str) -> int:
    low = words.strip().lower()
    return LEVEL_MERGE if low.startswith(("gộp", "merge", "deploy")) else LEVEL_PLAN


def clean_name(raw: str) -> str:
    """Bỏ «anh / chị / bạn…» đầu tên; «anh Được» → «Được», «anh» trơn → rỗng (không đoán)."""
    name = re.sub(rf"^{_HONORIFICS}\s+", "", raw.strip(), flags=re.IGNORECASE)
    if re.fullmatch(_HONORIFICS, name, flags=re.IGNORECASE):
        return ""
    return name.strip(" ,.:")


def parse(text: str) -> dict | None:
    """Câu cấp / gỡ / liệt kê quyền -> {"op": grant|revoke|list, "name", "level"}; không phải thì None."""
    low = text.strip().lower()
    if _LIST.match(low):
        return {"op": "list"}
    if "quyền" not in low:
        return None
    m = _GRANT_A.match(low) or _GRANT_B.match(low)
    if m:
        name = clean_name(m.group("name"))
        return {"op": "grant", "name": name, "level": level_of_words(m.group("level"))} if name else None
    m = _REVOKE.match(low)
    if m:
        name = clean_name(m.group("name"))
        return {"op": "revoke", "name": name} if name else None
    return None


def fold(s: str) -> str:
    """Bỏ dấu + thường hóa để so tên: «Trần Gia Bảo» ~ «bao», «Được» ~ «duoc»."""
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().strip()


def _names_of(db: Session, user) -> list[str]:
    from app.modules.employee.model import Employee

    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    names = [user.email or ""]
    if emp is not None:
        names += [emp.full_name or "", emp.code or "", (emp.full_name or "").split()[-1] if emp.full_name else ""]
    return [n for n in names if n]


def find_users(db: Session, name: str) -> list:
    """Tài khoản ERP đang hoạt động khớp tên: theo họ tên nhân sự, mã NV, tên đăng nhập, hoặc tên
    Telegram lúc liên kết. So không dấu. Khớp trọn tên/tên gọi thì ưu tiên; còn lại trả hết để hỏi lại."""
    from app.modules.user.model import User

    key = fold(name)
    if not key:
        return []
    now = datetime.now()
    tg_by_user: dict[int, str] = {}
    for link in db.scalars(select(AgentChatLink).where(AgentChatLink.chat_id != "", AgentChatLink.revoked_at.is_(None),
                                                       AgentChatLink.expires_at > now)):
        tg_by_user.setdefault(link.user_id, link.tg_name)
    found, exact = [], []
    for user in db.scalars(select(User).where(User.is_active.is_(True))):
        names = _names_of(db, user) + [tg_by_user.get(user.id, "")]
        folded = [fold(n) for n in names if n]
        if any(key == f for f in folded):
            exact.append(user)
        elif len(key) >= 3 and any(key in f for f in folded):
            found.append(user)
    return exact if exact else found


def is_linked(db: Session, user_id: int) -> bool:
    now = datetime.now()
    return db.scalar(select(AgentChatLink.id).where(
        AgentChatLink.user_id == user_id, AgentChatLink.chat_id != "", AgentChatLink.revoked_at.is_(None),
        AgentChatLink.expires_at > now).limit(1)) is not None


def active_grant(db: Session, user_id: int) -> AgentGrant | None:
    return db.scalar(select(AgentGrant).where(AgentGrant.user_id == user_id, AgentGrant.revoked_at.is_(None))
                     .order_by(AgentGrant.id.desc()).limit(1))


def level_for(db: Session, user_id: int) -> int:
    g = active_grant(db, user_id) if user_id else None
    return int(g.level) if g is not None else LEVEL_NONE


def grant(db: Session, user_id: int, level: int, *, by_chat: str, note: str = "") -> AgentGrant:
    """Cấp (hoặc đổi cấp): dòng đang hiệu lực bị đóng, thêm dòng mới — sổ giữ đủ lịch sử."""
    now = datetime.now()
    for old in db.scalars(select(AgentGrant).where(AgentGrant.user_id == user_id, AgentGrant.revoked_at.is_(None))):
        old.revoked_at = now
    row = AgentGrant(user_id=user_id, level=level, granted_by_chat=str(by_chat)[:50], note=note[:255],
                     created_by=0, updated_by=0)
    db.add(row)
    db.commit()
    return row


def revoke(db: Session, user_id: int) -> int:
    now = datetime.now()
    n = 0
    for old in db.scalars(select(AgentGrant).where(AgentGrant.user_id == user_id, AgentGrant.revoked_at.is_(None))):
        old.revoked_at = now
        n += 1
    db.commit()
    return n


def list_active(db: Session) -> list[AgentGrant]:
    return list(db.scalars(select(AgentGrant).where(AgentGrant.revoked_at.is_(None)).order_by(AgentGrant.id)))


def required_level(action: str) -> int:
    return REQUIRED_LEVEL.get(action, LEVEL_ADMIN)
