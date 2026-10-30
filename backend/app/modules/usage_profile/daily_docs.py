"""Số liệu từ nhật ký thao tác / xuất dữ liệu / bấm hộ / đăng nhập của MỘT ngày (thuần) — duoc-CR-641, phase 02."""
from collections import Counter, defaultdict
from datetime import datetime

from app.core.logging_codes import ACTION_GROUP_DELETE

from .daily_activity import MOBILE, sliding_max, PARALLEL_WINDOW

#  Phiếu nghiệp vụ được đếm theo động từ (phase 02 / metric-definitions §3.3).
TRACKED_DOC_ENTITIES = frozenset({
    "purchase_request", "survey_request", "purchase_order", "goods_receipt", "payment_request",
    "document", "leave_request", "vehicle_booking", "seal_request", "labor_contract",
})
#  c lập · u sửa · s gửi · a duyệt · r từ chối · t trả về · d xóa
TASK_VERB_BY_ACTION = {
    "create": "c", "update": "u", "submit": "s", "submitted": "s",
    "approve": "a", "approved": "a", "reject": "r", "rejected": "r",
    "return": "t", "returned": "t", "delete": "d",
}
#  Quyết định trong bộ máy duyệt (không tính "gửi duyệt", "rút", "hủy").
APPROVAL_DECISION_ACTIONS = frozenset({
    "approve", "approved", "reject", "rejected", "return", "returned", "line_approve",
})


def audit_columns(audits: list, sessions: dict) -> dict:
    """audits: [(entity, action, action_group, session_id, created_at)] của một người."""
    docs: dict[str, Counter] = defaultdict(Counter)
    for entity, action, _grp, _sid, _at in audits:
        verb = TASK_VERB_BY_ACTION.get(action)
        if entity in TRACKED_DOC_ENTITIES and verb:
            docs[entity][verb] += 1
    decisions = [a for a in audits if a[1] in APPROVAL_DECISION_ACTIONS]
    deletes = sorted(a[4] for a in audits if a[2] == ACTION_GROUP_DELETE)
    return {
        "docs": {e: dict(c) for e, c in docs.items()},
        "docs_created": sum(c.get("c", 0) for c in docs.values()),
        "approvals": len(decisions),
        "approvals_mobile": sum(1 for a in decisions if sessions.get(a[3], (0, 0, 0))[2] == MOBILE),
        "deletes": len(deletes),
        "max_deletes_10min": sliding_max(deletes, PARALLEL_WINDOW) if deletes else 0,
    }


def login_columns(user_id: int, sessions: dict, day_lo: datetime, day_hi: datetime, prior: list) -> dict:
    """Đăng nhập trong ngày + IP/thiết bị chưa từng thấy trong 90 ngày trước (không có lịch sử → 0, không thể kết luận)."""
    mine = [s for s in sessions.values() if s[0] == user_id and day_lo <= s[5] < day_hi]
    seen_ips = {p[1] for p in prior if p[0] == user_id}
    seen_devs = {(p[2], p[3], p[4]) for p in prior if p[0] == user_id}
    has_history = bool(seen_ips)
    return {
        "logins": len(mine),
        "new_ip_logins": sum(1 for s in mine if s[1] not in seen_ips) if has_history else 0,
        "new_device_logins": sum(1 for s in mine if (s[2], s[3], s[4]) not in seen_devs) if has_history else 0,
    }


def proxy_columns(proxy_docs: list, approval_proxies: list, user_emp: dict, emp_user: dict) -> tuple[Counter, Counter]:
    """`(đã bấm hộ, được bấm hộ)` theo user_id. Nguồn: phiếu người đề nghị ≠ người tạo + duyệt thay theo ủy quyền."""
    done: Counter = Counter()
    received: Counter = Counter()
    for creator_user, requester_emp in proxy_docs:
        creator_emp = user_emp.get(creator_user, 0)
        if requester_emp and creator_emp and requester_emp != creator_emp:
            done[creator_user] += 1
            if requester_emp in emp_user:
                received[emp_user[requester_emp]] += 1
    for actor_emp, behalf_emp in approval_proxies:
        if actor_emp in emp_user:
            done[emp_user[actor_emp]] += 1
        if behalf_emp in emp_user:
            received[emp_user[behalf_emp]] += 1
    return done, received
