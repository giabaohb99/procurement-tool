"""Đường ĐỌC của ba lớp nhật ký — gộp theo `request_id` (bao-CR-407 / CR-312 P5).

Ba bảng đã ghi đủ từ P1 (`tab_request_log`), P2 (`tab_audit_log` có nhóm) và P4
(`tab_change_log`), nhưng **chưa ai đọc được**: không cửa nào nối chúng lại. Tệp
này là cái nối, và nó chỉ đi một chiều — CHỈ ĐỌC, không hàm nào ghi.

**`tab_request_log` là xương sống, không phải `tab_audit_log`.** Chọn vậy vì câu
hỏi lúc truy sự cố thường bắt đầu từ *lượt gọi*, kể cả lượt **không đẻ ra dấu vết
nào**: một cú `DELETE` ăn 403 hay một lượt 500 chết trước khi vào service thì
`tab_audit_log` trống trơn — mà đó đúng là hai dòng người ta cần nhìn nhất. Hệ
quả phải biết: dòng audit CŨ (trước P1, `request_id = NULL`) **không lên màn
này**; chúng vẫn đọc được ở dòng thời gian từng phiếu (`/api/audit-logs`).

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §8.2–8.4.
"""
from __future__ import annotations

import uuid
from datetime import datetime, time

from sqlalchemy import String, case, cast, func, select
from sqlalchemy.orm import Session

from app.core.action_catalog import label_of_action
from app.core.device_fingerprint import device_label
from app.core.logging_codes import (ACTION_GROUP_LABELS, CHANGE_OP_LABELS, SOURCE_API,
                                    SOURCE_LABELS)
from app.core.request_context import request_id_text
from app.modules.audit.model import AuditLog
from app.modules.change_log.model import ChangeLog
from app.modules.login_session.history import resolve_user_names
from app.modules.login_session.model import LoginSession
from app.modules.request_log.model import RequestLog

#  Ba giá trị của ô «Kết quả» trên thanh lọc. Để ở đây chứ không rải chuỗi trong
#  controller: bài kiểm gọi thẳng vào đây, và thêm lựa chọn thứ tư thì sửa một chỗ.
STATUS_ALL = "all"
STATUS_ERROR = "error"
STATUS_BLOCKED = "blocked"

#  «Bị chặn» KHÔNG phải là «lỗi». 401/403 là hệ thống làm đúng việc của nó, còn
#  5xx là hệ thống hỏng — trộn hai thứ vào một bộ lọc thì câu hỏi *"hôm nay hỏng
#  gì"* luôn bị vùi dưới hàng trăm lượt 403 của người thiếu quyền.
BLOCKED_CODES = (401, 403)


def parse_request_id(text: str) -> bytes | None:
    """Chuỗi UUID trên URL -> 16 byte của cột. `None` nếu không phải UUID.

    Nhận cả dạng có gạch nối lẫn 32 ký tự hex liền — người đi tra hay chép từ
    nhật ký ra, và hai dạng đó chép ra khác nhau tùy chỗ chép.
    """
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        return uuid.UUID(raw).bytes
    except (ValueError, AttributeError, TypeError):
        return None


def _parse_moment(text: str | None, end_of_day: bool) -> datetime | None:
    """`YYYY-MM-DD` hoặc `YYYY-MM-DDTHH:MM[:SS]` -> `datetime`.

    Ô «Đến» chỉ có ngày thì phải kéo tới 23:59:59, nếu không thì lọc *"hôm nay"*
    trả về đúng những gì xảy ra lúc 00:00:00 — một lỗi im lặng, vì màn vẫn có dữ
    liệu nên không ai nghi ngờ.
    """
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        if len(raw) <= 10:
            day = datetime.strptime(raw[:10], "%Y-%m-%d")
            return datetime.combine(day.date(), time.max) if end_of_day else day
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def build_query(db: Session, *, user_id: int | None = None, doc_code: str | None = None,
                route: str | None = None, ip: str | None = None, field: str | None = None,
                table: str | None = None, from_time: str | None = None,
                to_time: str | None = None, status: str = STATUS_ALL,
                action_group: int | None = None, source: int | None = None,
                request_id: bytes | None = None):
    """Truy vấn trên `tab_request_log` đã áp đủ bộ lọc — CHƯA sắp xếp, CHƯA phân trang.

    Ba bộ lọc `doc_code` / `field` / `table` nằm ở BẢNG CON. Chúng đi vào đây
    dưới dạng `IN (SELECT ...)` chứ không phải một lượt truy vấn lấy danh sách
    id rồi nhồi ngược vào — tập `request_id` khớp một mã phiếu hay một tên cột có
    thể lên hàng nghìn, nhồi ngược là dựng câu `IN` dài hàng chục nghìn ký tự và
    đúng lúc cần nhất (sự cố, dữ liệu nhiều) thì chậm nhất.
    """
    q = db.query(RequestLog)

    if request_id:
        q = q.filter(RequestLog.request_id == request_id)
    if user_id:
        q = q.filter(RequestLog.user_id == user_id)
    if ip and ip.strip():
        q = q.filter(RequestLog.ip == ip.strip())
    if route and route.strip():
        q = q.filter(RequestLog.route.like(f"%{route.strip()}%"))
    if source:
        q = q.filter(RequestLog.source == source)

    if status == STATUS_ERROR:
        q = q.filter(RequestLog.http_status >= 500)
    elif status == STATUS_BLOCKED:
        q = q.filter(RequestLog.http_status.in_(BLOCKED_CODES))

    start = _parse_moment(from_time, end_of_day=False)
    end = _parse_moment(to_time, end_of_day=True)
    if start:
        q = q.filter(RequestLog.created_at >= start)
    if end:
        q = q.filter(RequestLog.created_at <= end)

    if doc_code and doc_code.strip():
        sub = (select(AuditLog.request_id)
               .where(AuditLog.doc_code == doc_code.strip(),
                      AuditLog.request_id.is_not(None)))
        q = q.filter(RequestLog.request_id.in_(sub))
    if action_group:
        sub = (select(AuditLog.request_id)
               .where(AuditLog.action_group == action_group,
                      AuditLog.request_id.is_not(None)))
        q = q.filter(RequestLog.request_id.in_(sub))

    if (field and field.strip()) or (table and table.strip()):
        cond = [ChangeLog.request_id.is_not(None)]
        if field and field.strip():
            cond.append(ChangeLog.field == field.strip())
        if table and table.strip():
            cond.append(ChangeLog.table_name == table.strip())
        q = q.filter(RequestLog.request_id.in_(select(ChangeLog.request_id).where(*cond)))

    return q


def find_request(db: Session, request_id: bytes) -> RequestLog | None:
    """Dòng `tab_request_log` của một lượt gọi.

    Lấy dòng MỚI NHẤT chứ không `.first()` theo thứ tự tự nhiên: `request_id` là
    UUID4 nên trùng là chuyện không xảy ra, nhưng script chạy tay có thể mở
    context rồi ghi hai dòng, và khi đó dòng sau mới là dòng có kết quả.
    """
    return (db.query(RequestLog)
            .filter(RequestLog.request_id == request_id)
            .order_by(RequestLog.id.desc()).first())


def _first_audit_by_request(db: Session, request_ids: list[bytes]) -> dict[bytes, AuditLog]:
    """Dòng audit ĐẦU TIÊN của mỗi lượt gọi — cột «Lần bấm» trên màn.

    Đầu tiên chứ không phải cuối cùng: một cú Duyệt ghi `approve` rồi mới ghi vài
    dòng phụ (sinh việc, gửi chuông). Lấy dòng cuối thì cột «Lần bấm» hiện
    *"Tạo thông báo"* cho một hành động mà người ta nhớ là *"Duyệt phiếu"*.
    """
    if not request_ids:
        return {}
    rows = (db.query(AuditLog)
            .filter(AuditLog.request_id.in_(request_ids))
            .order_by(AuditLog.id.asc()).all())
    out: dict[bytes, AuditLog] = {}
    for row in rows:
        key = bytes(row.request_id)
        if key not in out:
            out[key] = row
    return out


def _change_tables_by_request(db: Session, request_ids: list[bytes]) -> dict[bytes, int]:
    """Số BẢNG khác nhau bị đụng trong mỗi lượt gọi.

    Số TRƯỜNG đã nằm sẵn ở `RequestLog.change_count`; thứ cột «Đổi» còn thiếu là
    *"đụng mấy bảng"* — con số phân biệt một cú sửa ô đơn giá với một cú Duyệt
    kéo theo bảng việc, bảng thông báo và bảng chứng từ.
    """
    if not request_ids:
        return {}
    rows = (db.query(ChangeLog.request_id,
                     func.count(func.distinct(ChangeLog.table_name)))
            .filter(ChangeLog.request_id.in_(request_ids))
            .group_by(ChangeLog.request_id).all())
    return {bytes(rid): int(n) for rid, n in rows if rid is not None}


def _actor_label(row: RequestLog, names: dict[int, str]) -> str:
    """Tên người bấm. Chưa đăng nhập thì nói thẳng là chưa đăng nhập.

    `user_id = 0` ở bảng này nghĩa là *chưa đăng nhập* (đăng nhập hỏng, gọi vào
    cửa công khai), KHÁC với `created_by = 0` của `tab_audit_log` nghĩa là *hệ
    thống làm*. Hai số 0 cùng chữ nhưng khác nghĩa — nên không dùng chung nhãn.
    """
    if row.user_id:
        return names.get(row.user_id, f"User #{row.user_id}")
    return "(chưa đăng nhập)" if row.source == SOURCE_API else "hệ thống"


def serialize_row(row: RequestLog, audit: AuditLog | None, table_count: int,
                  names: dict[int, str]) -> dict:
    """Một dòng trên bảng danh sách."""
    return {
        "request_id": request_id_text(row.request_id),
        "at": row.created_at,
        "user_id": row.user_id,
        "user_name": _actor_label(row, names),
        "device": device_label(row.device_hash),
        "ip": row.ip,
        "session_id": row.session_id,
        "source": row.source,
        "source_label": SOURCE_LABELS.get(row.source, "Không rõ"),
        "method": row.method,
        "path": row.path,
        "route": row.route,
        "http_status": row.http_status,
        "duration_ms": row.duration_ms,
        "error_code": row.error_code,
        "has_error_detail": bool(row.error_detail),
        #  Cột «Lần bấm»: câu tiếng Việt của dòng audit đầu tiên. Lượt gọi không
        #  đẻ dấu vết nào (403, 500 trước khi vào service) thì rơi về
        #  `METHOD path` — thô, nhưng đó chính là lượt cần nhìn nhất, giấu đi là
        #  mất luôn lý do bảng này lấy request_log làm xương sống.
        "summary": (audit.message if audit and audit.message
                    else f"{row.method} {row.path}"),
        "action": audit.action if audit else "",
        "action_label": label_of_action(audit.action) if audit else "",
        "action_group": audit.action_group if audit else 0,
        "action_group_label": (ACTION_GROUP_LABELS.get(audit.action_group, "")
                               if audit else ""),
        "entity": audit.entity if audit else "",
        "entity_id": audit.entity_id if audit else 0,
        "doc_code": audit.doc_code if audit else "",
        "audit_count": row.audit_count,
        "change_count": row.change_count,
        "change_table_count": table_count,
    }


def build_page(db: Session, query, offset: int, limit: int) -> list[dict]:
    """Trang danh sách — số truy vấn KHÔNG phụ thuộc số dòng.

    Ba lượt trên ba bảng nhật ký: 1 trên `tab_request_log` (đã phân trang) + 1
    `IN (...)` sang audit + 1 `IN (...)` gộp sang change_log. Cộng thêm phần tra
    tên (`resolve_user_names`, tối đa 2 lượt) là trần **năm**. Phép đếm tổng do
    controller gọi riêng — nó là giá của việc hiện số trang, không phải giá của
    việc dựng dòng.

    ⚠️ Điều đáng canh không phải con số mà là **tính hằng**: bài kiểm
    `test_man_nhat_ky_he_thong_cr407.py` đo trang 3 dòng và trang 30 dòng rồi so
    bằng nhau. Nhét một lượt tra vào vòng lặp thì màn 200 dòng đẻ 200 lượt, mà
    lúc dữ liệu ít thì không ai thấy.
    """
    rows = (query.order_by(RequestLog.id.desc()).offset(offset).limit(limit).all())
    if not rows:
        return []
    ids = [bytes(r.request_id) for r in rows]
    audits = _first_audit_by_request(db, ids)
    tables = _change_tables_by_request(db, ids)
    names = resolve_user_names(db, {r.user_id for r in rows})
    return [serialize_row(r, audits.get(bytes(r.request_id)), tables.get(bytes(r.request_id), 0),
                          names)
            for r in rows]


def serialize_audit(row: AuditLog, names: dict[int, str]) -> dict:
    return {
        "id": row.id,
        "at": row.created_at,
        "by_id": row.created_by,
        "by": names.get(row.created_by, f"User #{row.created_by}"),
        "entity": row.entity,
        "entity_id": row.entity_id,
        "action": row.action,
        "action_label": label_of_action(row.action),
        "action_group": row.action_group,
        "action_group_label": ACTION_GROUP_LABELS.get(row.action_group, ""),
        "message": row.message,
        "doc_code": row.doc_code,
        "parent_entity": row.parent_entity,
        "parent_id": row.parent_id,
        "changed_fields": row.changed_fields,
        "change_count": row.change_count,
    }


def serialize_change(row: ChangeLog) -> dict:
    return {
        "id": row.id,
        "at": row.created_at,
        "table_name": row.table_name,
        "row_id": row.row_id,
        "op": row.op,
        "op_label": CHANGE_OP_LABELS.get(row.op, ""),
        "field": row.field,
        "before_value": row.before_value,
        "after_value": row.after_value,
        "snapshot_json": row.snapshot_json,
        "is_masked": row.is_masked,
    }


def build_detail(db: Session, row: RequestLog, *, with_change_log: bool) -> dict:
    """Gói chi tiết cho ngăn bốn tab.

    `with_change_log = False` (người xem không có khóa `change_log`) thì **lược ở
    ĐÂY**, không để giao diện tự giấu: giá trị cũ và thân yêu cầu có thể chứa tên
    nhà cung cấp — đúng thứ cả cơ chế phương án dựng ra để giấu với người yêu cầu
    (§7). Giấu bằng giao diện thì mở DevTools ra là thấy.
    """
    audit_rows = (db.query(AuditLog)
                  .filter(AuditLog.request_id == row.request_id)
                  .order_by(AuditLog.id.asc()).all())
    names = resolve_user_names(db, {row.user_id} | {a.created_by for a in audit_rows})

    request_part = {
        "request_id": request_id_text(row.request_id),
        "at": row.created_at,
        "user_id": row.user_id,
        "user_name": _actor_label(row, names),
        "device": device_label(row.device_hash),
        "ip": row.ip,
        "referer": row.referer,
        "session_id": row.session_id,
        "source": row.source,
        "source_label": SOURCE_LABELS.get(row.source, "Không rõ"),
        "method": row.method,
        "path": row.path,
        "route": row.route,
        "query_string": row.query_string,
        "http_status": row.http_status,
        "error_code": row.error_code,
        "duration_ms": row.duration_ms,
        "audit_count": row.audit_count,
        "change_count": row.change_count,
    }
    if with_change_log:
        request_part["request_body"] = row.request_body
        request_part["response_body"] = row.response_body
        request_part["error_detail"] = row.error_detail

    changes = []
    if with_change_log:
        changes = [serialize_change(c) for c in
                   (db.query(ChangeLog)
                    .filter(ChangeLog.request_id == row.request_id)
                    .order_by(ChangeLog.id.asc()).all())]

    return {
        "request": request_part,
        "audit": [serialize_audit(a, names) for a in audit_rows],
        "changes": changes,
        #  Tab «Thay đổi» phải phân biệt *"lượt này không đổi gì"* với *"bạn
        #  không được xem"*. Không có cờ này thì cả hai đều là mảng rỗng.
        "can_read_changes": with_change_log,
        "session": _serialize_session(db, row.session_id),
    }


def _serialize_session(db: Session, session_id: int | None) -> dict | None:
    if not session_id:
        return None
    row = db.get(LoginSession, session_id)
    if row is None:
        return None
    return {
        "id": row.id,
        "user_id": row.user_id,
        "ip": row.ip,
        "last_seen_ip": row.last_seen_ip,
        "device_label": row.device_label,
        "os": row.os,
        "browser": row.browser,
        "login_method": row.login_method,
        "created_at": row.created_at,
        "last_seen_at": row.last_seen_at,
        "expires_at": row.expires_at,
        "revoked_at": row.revoked_at,
        "revoke_reason": row.revoke_reason,
        #  Dấu hiệu token bị mang đi máy khác (BM-003): vào từ một IP, dùng tiếp
        #  từ IP khác. Tính ở backend vì giao diện không nên tự đặt luật cảnh báo.
        "ip_changed": bool(row.last_seen_ip and row.last_seen_ip != row.ip),
    }


def build_summary(db: Session, query) -> dict:
    """Số liệu cho ba biểu đồ: theo GIỜ, theo endpoint, theo mã lỗi.

    Nhận chính `query` đã lọc của danh sách để biểu đồ và bảng **luôn nói cùng
    một chuyện** — hai đường lọc riêng là kiểu sai kinh điển: người dùng lọc bảng
    rồi tin biểu đồ bên trên, mà biểu đồ vẫn đang vẽ toàn hệ.
    """
    sub = query.with_entities(RequestLog.id, RequestLog.created_at, RequestLog.route,
                              RequestLog.http_status, RequestLog.error_code).subquery()

    #  Cắt giờ bằng `SUBSTR(CAST(... AS CHAR), 1, 13)` chứ không `DATE_FORMAT`:
    #  hàm kia chỉ có ở MySQL, mà bộ kiểm chạy trên SQLite — viết theo MySQL là
    #  đúng trên hệ thật và không bao giờ được kiểm, tức là sai lúc nào không hay.
    #  Cả hai bộ máy đều để `datetime` ra chuỗi `YYYY-MM-DD HH:MM:SS`, nên 13 ký
    #  tự đầu chính là mốc giờ.
    hour_bucket = func.substr(cast(sub.c.created_at, String), 1, 13)
    is_error = case((sub.c.http_status >= 500, 1), else_=0)
    is_failed = case((sub.c.http_status >= 400, 1), else_=0)

    by_hour = (db.query(hour_bucket, func.count(sub.c.id), func.sum(is_error))
               .group_by(hour_bucket).order_by(hour_bucket).all())

    by_route = (db.query(sub.c.route, func.count(sub.c.id), func.sum(is_failed))
                .group_by(sub.c.route)
                .order_by(func.count(sub.c.id).desc()).limit(10).all())

    by_error = (db.query(sub.c.error_code, func.count(sub.c.id))
                .filter(sub.c.error_code != "")
                .group_by(sub.c.error_code)
                .order_by(func.count(sub.c.id).desc()).limit(10).all())

    return {
        "by_hour": [{"hour": h, "total": int(n), "errors": int(e or 0)}
                    for h, n, e in by_hour],
        "by_route": [{"route": r or "", "total": int(n), "failed": int(f or 0)}
                     for r, n, f in by_route],
        "by_error": [{"error_code": c, "total": int(n)} for c, n in by_error],
    }


def default_range() -> tuple[str, str]:
    """Khoảng mặc định khi màn mở lần đầu: HÔM NAY.

    Không phải "tất cả": bảng này thêm vài nghìn dòng mỗi ngày, mở sẵn toàn bộ
    là trang đầu luôn nặng dần theo tuổi hệ thống mà không ai thấy nó nặng lên.
    """
    today = datetime.now().date().isoformat()
    #  Cả hai đầu cùng một ngày: ô «Đến» chỉ có ngày thì `_parse_moment` tự kéo
    #  tới 23:59:59, nên trả thêm một ngày là mở rộng thành hai ngày.
    return (today, today)
