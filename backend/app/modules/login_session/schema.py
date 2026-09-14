"""Dạng trả ra của một dòng phiên + một dòng lịch sử đăng nhập (bao-CR-395, P3b).

Chỉ có hàm dựng dict, không có lớp Pydantic: ba màn (`/system/sessions`, tab
«Thiết bị của tôi», tab «Tài khoản & thiết bị» của hồ sơ) đọc CÙNG một hình
dạng, và cả ba đều là màn chỉ-xem — không có body ghi nào cần kiểm kiểu. Mã số
(`device_type`, `login_method`, `revoke_reason`) trả kèm nhãn để giao diện khỏi
chép bảng nhãn sang TypeScript (R2/QĐ-11).
"""
from datetime import datetime

from app.modules.login_session.constants import (DEVICE_TYPE_LABELS, LOGIN_METHOD_LABELS,
                                                 REVOKE_REASON_LABELS)
from app.modules.login_session.model import LoginSession

#  Kết cục của một phiên, ngoài các lý do thu hồi. Trả chữ ở đây vì đây là một
#  cột hiển thị (cột «Kết thúc thế nào» của lịch sử), không phải mã lưu xuống DB.
ENDED_ALIVE = "Còn hiệu lực"
ENDED_EXPIRED = "Hết hạn"

#  Dòng lịch sử: hai loại — một lần đăng nhập THÀNH CÔNG (một dòng phiên) hoặc
#  một lần THẤT BẠI (một dòng `tab_audit_log` `login_failed`). Mã số theo R2.
HISTORY_KIND_LOGIN = 1
HISTORY_KIND_LOGIN_FAILED = 2


def describe_ending(row: LoginSession, now: datetime | None = None) -> str:
    """Câu «kết thúc thế nào» của một phiên: lý do thu hồi, hết hạn, hay còn sống."""
    if row.revoked_at is not None:
        return REVOKE_REASON_LABELS.get(row.revoke_reason, f"Mã {row.revoke_reason}")
    now = now or datetime.now()
    if row.expires_at is not None and row.expires_at <= now:
        return ENDED_EXPIRED
    return ENDED_ALIVE


def serialize_session(row: LoginSession, *, current_session_id: int = 0,
                      user_name: str = "", revoked_by_name: str = "",
                      now: datetime | None = None) -> dict:
    """Một dòng phiên cho cả ba màn. `is_current` = phiên đang gọi API này."""
    now = now or datetime.now()
    ending = describe_ending(row, now)
    return {
        "id": row.id,
        "user_id": row.user_id,
        "user_name": user_name,
        "ip": row.ip or "",
        "last_seen_ip": row.last_seen_ip or "",
        "device_type": row.device_type,
        "device_type_label": DEVICE_TYPE_LABELS.get(row.device_type, "Không rõ"),
        "os": row.os or "",
        "browser": row.browser or "",
        "device_label": row.device_label or "",
        "user_agent": row.user_agent or "",
        "login_method": row.login_method,
        "login_method_label": LOGIN_METHOD_LABELS.get(row.login_method, f"Mã {row.login_method}"),
        "created_at": row.created_at,
        "last_seen_at": row.last_seen_at,
        "refreshed_at": row.refreshed_at,
        "refresh_count": row.refresh_count or 0,
        "expires_at": row.expires_at,
        "revoked_at": row.revoked_at,
        "revoked_by": row.revoked_by or 0,
        "revoked_by_name": revoked_by_name,
        "revoke_reason": row.revoke_reason,
        "revoke_reason_label": (REVOKE_REASON_LABELS.get(row.revoke_reason, "")
                                if row.revoked_at is not None else ""),
        #  «Còn hiệu lực» theo nghĩa của bảng: chưa thu hồi và chưa quá `expires_at`.
        #  Vé access có thể đã hết hạn trước đó — chuyện của refresh, không phải của phiên.
        "is_alive": ending == ENDED_ALIVE,
        "ending": ending,
        "is_current": bool(current_session_id) and row.id == current_session_id,
    }


def serialize_history_login(row: LoginSession, *, revoked_by_name: str = "",
                            now: datetime | None = None) -> dict:
    """Một dòng lịch sử từ một dòng phiên (đăng nhập THÀNH CÔNG)."""
    return {
        "kind": HISTORY_KIND_LOGIN,
        "ok": True,
        "at": row.created_at,
        "session_id": row.id,
        "login_method": row.login_method,
        "login_method_label": LOGIN_METHOD_LABELS.get(row.login_method, f"Mã {row.login_method}"),
        "device_label": row.device_label or "",
        "ip": row.ip or "",
        "ending": describe_ending(row, now),
        "revoked_by_name": revoked_by_name,
        "message": "",
    }


def serialize_history_failed(audit_row) -> dict:
    """Một dòng lịch sử từ `tab_audit_log` (`action=login_failed`).

    Dòng thất bại không có phiên, không có thiết bị (P1 chưa ghi `User-Agent` vào
    audit) — chỉ có giờ, IP và câu thông báo; các ô còn lại để trống chứ không bịa.
    """
    return {
        "kind": HISTORY_KIND_LOGIN_FAILED,
        "ok": False,
        "at": audit_row.created_at,
        "session_id": 0,
        "login_method": 0,
        "login_method_label": "",
        "device_label": "",
        "ip": audit_row.ip or "",
        "ending": "",
        "revoked_by_name": "",
        "message": audit_row.message or "",
    }
