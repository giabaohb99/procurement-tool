"""Bốn dấu hiệu bất thường đọc từ nhật ký, báo lên chuông quản trị (bao-CR-448, CR-312 P6).

Chạy trong MỘT việc nền theo nhịp (`system_log.detect_anomalies`), đọc lại
`tab_login_session` · `tab_request_log` · `tab_change_log` · `tab_audit_log`
của một cửa sổ ngắn vừa qua. Cố ý KHÔNG đặt phép so nào vào middleware hay vào
`/api/auth/login`: mỗi phép so ở đó là một truy vấn thêm cho mọi lượt gọi, còn
ở đây là vài truy vấn gộp cho cả cửa sổ.

Bốn dấu hiệu (§10 P6 của `nhat-ky-va-phien-dang-nhap.md`) và cách đọc:

1. **Đăng nhập từ IP lạ** — phiên mới mở mà IP chưa từng xuất hiện ở phiên nào
   của CHÍNH người đó trong `ANOMALY_KNOWN_IP_DAYS` ngày trước. Lần đăng nhập
   đầu tiên của tài khoản không tính: chưa có gì để so.
2. **Đổi thiết bị giữa phiên** — cùng một `session_id` mà `tab_request_log`
   ghi hơn một `device_hash` trong cửa sổ. Đây là dấu MẠNH: dấu thiết bị đã
   chuẩn hóa (`chrome|windows|desktop`) không đổi khi đổi mạng, nên hai dấu
   trong một phiên nghĩa là vé đang được dùng ở hai máy. Riêng **đổi IP giữa
   phiên** cố ý KHÔNG báo chuông: đổi wifi sang 4G là chuyện mỗi ngày của
   người đi đường; nó đã có dòng `refresh_ip_changed` trong nhật ký và cờ
   `ip_changed` trên màn Phiên đăng nhập — báo chuông nữa là chuông kêu trăm
   lần vào ngày không có gì xảy ra. Trong thư báo đổi thiết bị vẫn nêu IP.
3. **Xóa hàng loạt trong một `request_id`** — một lượt gọi mà xóa từ
   `ANOMALY_BULK_DELETE_MIN` dòng trở lên, đếm ở CẢ lớp thay đổi (`op = xóa`)
   lẫn lớp dấu vết (nhóm XÓA), lấy số lớn hơn.
4. **Dồn dập 403** — từ `ANOMALY_FORBIDDEN_MIN` lượt bị chặn quyền trong cửa
   sổ, gom theo người (chưa đăng nhập thì gom theo IP).

**Chống báo trùng** bằng chính `tab_audit_log`: mỗi lần báo ghi một dòng
`anomaly_alert` với `created_by = 0`, `entity = auth`, `entity_id` = người bị
nhắc tới, `doc_code` = khóa của dấu hiệu. Lần chạy sau tra khóa đó trước — cửa
sổ quét dài gấp đôi nhịp chạy nên cùng một sự kiện được nhìn thấy hai lần, và
không có khóa thì báo hai lần. Cùng cách `file_access_log` đã dùng.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.core.audit import record, resolve_actor
from app.core.logging_codes import ACTION_GROUP_DELETE, CHANGE_OP_DELETE
from app.core.logging_policy import (ANOMALY_BULK_DELETE_MIN, ANOMALY_COOLDOWN_MINUTES,
                                     ANOMALY_FORBIDDEN_MIN, ANOMALY_KNOWN_IP_DAYS,
                                     ANOMALY_WINDOW_MINUTES)
from app.modules.audit.model import AuditLog
from app.modules.change_log.model import ChangeLog
from app.modules.login_session.model import LoginSession
from app.modules.notification.model import Notification
from app.modules.request_log.model import RequestLog

log = logging.getLogger("app.system_log.anomaly")

ACTION_ANOMALY = "anomaly_alert"

KIND_NEW_IP = "new_ip"
KIND_DEVICE_CHANGED = "device_changed"
KIND_BULK_DELETE = "bulk_delete"
KIND_FORBIDDEN = "forbidden_burst"

#  Màn mà người nhận sẽ mở ra để xem tiếp. Đường của giao diện v2
#  (`shared/constants/app-routes.ts`).
LINK_SESSIONS = "/system/sessions"
LINK_LOGS = "/system/logs"

#  `doc_code` là `String(50)` — khóa phải nằm gọn trong đó, kể cả khi ghép IPv6.
MAX_KEY = 50


@dataclass
class Anomaly:
    kind: str
    key: str
    user_id: int
    title: str
    body: str
    link: str


# ---------------------------------------------------------------------------
# Đồng hồ và khóa
# ---------------------------------------------------------------------------
def db_now(db: Session) -> datetime:
    """Giờ hiện tại theo ĐỒNG HỒ CỦA CSDL — cùng đồng hồ với `created_at`.

    Lấy giờ Python thì máy chủ CSDL chạy giờ Việt Nam mà worker chạy UTC là cửa
    sổ lệch 7 tiếng, và lệch đúng chiều gây báo động giả (xem `file_access_log`).
    """
    now = db.execute(select(func.now())).scalar()
    if isinstance(now, str):  # SQLite trả chuỗi
        now = datetime.fromisoformat(now)
    return now or datetime.now()


def _key(*parts) -> str:
    return ":".join(str(p) for p in parts)[:MAX_KEY]


def already_alerted(db: Session, key: str, since: datetime | None = None) -> bool:
    """Đã báo về khóa này chưa — toàn thời gian, hoặc chỉ trong một cửa sổ."""
    query = db.query(AuditLog.id).filter(AuditLog.action == ACTION_ANOMALY,
                                         AuditLog.doc_code == key)
    if since is not None:
        query = query.filter(AuditLog.created_at >= since)
    return query.first() is not None


# ---------------------------------------------------------------------------
# Bốn phép dò — hàm thuần trên một phiên CSDL, không ghi gì
# ---------------------------------------------------------------------------
def detect_new_ip_logins(db: Session, since: datetime) -> list[Anomaly]:
    """Phiên mở trong cửa sổ mà IP chưa từng thấy ở người đó trong N ngày trước."""
    found: list[Anomaly] = []
    fresh = (db.query(LoginSession)
             .filter(LoginSession.created_at >= since, LoginSession.ip != "")
             .order_by(LoginSession.id.asc()).all())
    for session in fresh:
        known_from = session.created_at - timedelta(days=ANOMALY_KNOWN_IP_DAYS)
        earlier = (db.query(LoginSession.id, LoginSession.ip, LoginSession.last_seen_ip,
                            LoginSession.created_at)
                   .filter(LoginSession.user_id == session.user_id,
                           LoginSession.id != session.id,
                           LoginSession.created_at < session.created_at)
                   .all())
        if not earlier:
            continue  # lần đăng nhập đầu tiên — không có gì để so
        seen = {row.ip for row in earlier if row.created_at >= known_from}
        seen |= {row.last_seen_ip for row in earlier if row.created_at >= known_from}
        if session.ip in seen:
            continue
        name = resolve_actor(db, session.user_id)
        found.append(Anomaly(
            kind=KIND_NEW_IP, key=_key("new_ip", "s", session.id), user_id=session.user_id,
            title=f"Bất thường: {name} đăng nhập từ IP lạ {session.ip}",
            body=(f"{name} vừa đăng nhập từ IP {session.ip} bằng {session.device_label or 'thiết bị không rõ'}. "
                  f"IP này chưa xuất hiện ở phiên nào của người đó trong {ANOMALY_KNOWN_IP_DAYS} ngày qua. "
                  f"Nếu không phải chính chủ, mở màn Phiên đăng nhập để đá phiên."),
            link=LINK_SESSIONS))
    return found


def detect_device_changes(db: Session, since: datetime) -> list[Anomaly]:
    """Một phiên mà lượt gọi trong cửa sổ mang hơn một dấu thiết bị."""
    rows = (db.query(RequestLog.session_id,
                     func.count(distinct(RequestLog.device_hash)).label("hashes"))
            .filter(RequestLog.created_at >= since,
                    RequestLog.session_id.isnot(None),
                    RequestLog.device_hash.isnot(None))
            .group_by(RequestLog.session_id)
            .having(func.count(distinct(RequestLog.device_hash)) > 1)
            .all())
    found: list[Anomaly] = []
    for session_id, hashes in rows:
        session = db.get(LoginSession, int(session_id))
        if session is None:
            continue
        name = resolve_actor(db, session.user_id)
        ip_note = (f" IP lúc mở phiên {session.ip}, gần nhất {session.last_seen_ip}."
                   if session.last_seen_ip and session.last_seen_ip != session.ip else "")
        found.append(Anomaly(
            kind=KIND_DEVICE_CHANGED, key=_key("device", "s", session_id), user_id=session.user_id,
            title=f"Bất thường: phiên của {name} dùng trên {hashes} thiết bị khác nhau",
            body=(f"Cùng một phiên đăng nhập của {name} (mở bằng {session.device_label or 'thiết bị không rõ'}) "
                  f"vừa gửi lượt gọi từ {hashes} dấu thiết bị khác nhau trong {ANOMALY_WINDOW_MINUTES} phút qua.{ip_note} "
                  f"Vé đăng nhập có thể đã sang tay — mở màn Phiên đăng nhập để đá phiên."),
            link=LINK_SESSIONS))
    return found


def _bulk_delete_counts(db: Session, since: datetime) -> dict[bytes, tuple[int, int]]:
    """{request_id: (số dòng xóa, người bấm)} — lấy số LỚN HƠN giữa hai lớp nhật ký."""
    counts: dict[bytes, tuple[int, int]] = {}
    change_rows = (db.query(ChangeLog.request_id, func.count(ChangeLog.id), func.max(ChangeLog.created_by))
                   .filter(ChangeLog.created_at >= since, ChangeLog.op == CHANGE_OP_DELETE,
                           ChangeLog.request_id.isnot(None))
                   .group_by(ChangeLog.request_id)
                   .having(func.count(ChangeLog.id) >= ANOMALY_BULK_DELETE_MIN).all())
    audit_rows = (db.query(AuditLog.request_id, func.count(AuditLog.id), func.max(AuditLog.created_by))
                  .filter(AuditLog.created_at >= since, AuditLog.action_group == ACTION_GROUP_DELETE,
                          AuditLog.request_id.isnot(None))
                  .group_by(AuditLog.request_id)
                  .having(func.count(AuditLog.id) >= ANOMALY_BULK_DELETE_MIN).all())
    for request_id, total, actor in list(change_rows) + list(audit_rows):
        key = bytes(request_id)
        best = counts.get(key, (0, 0))
        if int(total) > best[0]:
            counts[key] = (int(total), int(actor or 0))
    return counts


def detect_bulk_deletes(db: Session, since: datetime) -> list[Anomaly]:
    found: list[Anomaly] = []
    for request_id, (total, actor) in _bulk_delete_counts(db, since).items():
        name = resolve_actor(db, actor)
        found.append(Anomaly(
            kind=KIND_BULK_DELETE, key=_key("bulk", request_id.hex()), user_id=actor,
            title=f"Bất thường: {name} xóa {total} dòng trong một lượt gọi",
            body=(f"Một lượt gọi API của {name} vừa xóa {total} dòng dữ liệu trong {ANOMALY_WINDOW_MINUTES} phút qua. "
                  f"Mở Nhật ký hệ thống, tra mã lượt gọi {request_id.hex()} để xem xóa những gì."),
            link=f"{LINK_LOGS}/{request_id.hex()}"))
    return found


def detect_forbidden_bursts(db: Session, since: datetime) -> list[Anomaly]:
    rows = (db.query(RequestLog.user_id, RequestLog.ip, func.count(RequestLog.id))
            .filter(RequestLog.created_at >= since, RequestLog.http_status == 403)
            .group_by(RequestLog.user_id, RequestLog.ip)
            .having(func.count(RequestLog.id) >= ANOMALY_FORBIDDEN_MIN).all())
    found: list[Anomaly] = []
    for user_id, ip, total in rows:
        user_id = int(user_id or 0)
        if user_id:
            name = resolve_actor(db, user_id)
            key = _key("403", "u", user_id)
            who = f"{name} (IP {ip})"
        else:
            key = _key("403", "ip", ip)
            who = f"IP {ip} (chưa đăng nhập)"
        found.append(Anomaly(
            kind=KIND_FORBIDDEN, key=key, user_id=user_id,
            title=f"Bất thường: {who} bị chặn quyền {total} lần liên tiếp",
            body=(f"{who} vừa nhận {total} lượt từ chối quyền (403) trong {ANOMALY_WINDOW_MINUTES} phút qua — "
                  f"giống đang dò xem tài khoản với tới được gì. Mở Nhật ký hệ thống, lọc mã 403 để xem các đường bị gọi."),
            link=LINK_LOGS))
    return found


# ---------------------------------------------------------------------------
# Người nhận và gửi
# ---------------------------------------------------------------------------
def alert_recipients(db: Session) -> list[int]:
    """Ai nhận chuông: mọi tài khoản ĐỌC được màn Phiên đăng nhập ở phạm vi
    toàn hệ — đúng nhóm sẽ bấm nút đá phiên. Không có ai như thế thì lùi về vai
    trò `admin`, để cảnh báo không rơi vào hư không mà không ai biết."""
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import User, UserRole

    role_ids = [row[0] for row in
                db.query(Permission.role_id)
                .filter(Permission.entity == "login_session", Permission.can_read.is_(True),
                        Permission.scope == "all").all()]
    if not role_ids:
        role_ids = [row[0] for row in db.query(Role.id).filter(Role.code == "admin").all()]
    if not role_ids:
        return []
    rows = (db.query(User.id).join(UserRole, UserRole.user_id == User.id)
            .filter(UserRole.role_id.in_(role_ids), User.is_active.is_(True))
            .distinct().all())
    return [int(row[0]) for row in rows]


def raise_alert(db: Session, anomaly: Anomaly, recipients: list[int]) -> int:
    """Gửi chuông cho từng người (trừ chính người bị nhắc tới) rồi ghi dòng đánh dấu."""
    sent = 0
    for uid in recipients:
        if uid == anomaly.user_id:
            continue  # họ đã biết mình vừa làm gì; cảnh báo là để người khác biết
        db.add(Notification(user_id=uid, title=anomaly.title, body=anomaly.body,
                            link=anomaly.link, created_by=0))
        sent += 1
    #  `record` tự commit — chuông ở trên đi cùng giao dịch đó.
    record(db, 0, "auth", anomaly.user_id, ACTION_ANOMALY,
           f"{anomaly.title} — đã báo cho {sent} người", doc_code=anomaly.key)
    return sent


def run_detection(db: Session, now: datetime | None = None) -> dict:
    """Quét một cửa sổ, báo những gì chưa báo. Trả về số lượng theo từng dấu hiệu."""
    now = now or db_now(db)
    since = now - timedelta(minutes=ANOMALY_WINDOW_MINUTES)
    cooldown_from = now - timedelta(minutes=ANOMALY_COOLDOWN_MINUTES)

    candidates: list[Anomaly] = []
    candidates += detect_new_ip_logins(db, since)
    candidates += detect_device_changes(db, since)
    candidates += detect_bulk_deletes(db, since)
    candidates += detect_forbidden_bursts(db, since)

    recipients = alert_recipients(db) if candidates else []
    counts = {KIND_NEW_IP: 0, KIND_DEVICE_CHANGED: 0, KIND_BULK_DELETE: 0, KIND_FORBIDDEN: 0}
    for anomaly in candidates:
        #  Dồn dập 403 là dấu hiệu LẶP: cùng người dò tiếp thì sau thời gian
        #  nguội lại báo. Ba dấu hiệu kia gắn với một sự kiện cụ thể (một phiên,
        #  một lượt gọi) nên báo đúng một lần trọn đời.
        since_for_key = cooldown_from if anomaly.kind == KIND_FORBIDDEN else None
        if already_alerted(db, anomaly.key, since_for_key):
            continue
        raise_alert(db, anomaly, recipients)
        counts[anomaly.kind] += 1
    total = sum(counts.values())
    if total:
        log.warning("Đã báo %s cảnh báo bất thường cho %s người: %s", total, len(recipients), counts)
    return {"status": "success", "window_from": since.isoformat(), "alerted": total,
            "recipients": len(recipients), **counts}
