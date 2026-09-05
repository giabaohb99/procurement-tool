"""Mẫu email theo bước cho phân hệ Đặt xe — đọc/ghi + render + gửi.

Nguồn mặc định là `DEFAULTS` (trong code). Người dùng sửa trên `/system/settings`
thì lưu đè vào `tab_email_template`; đọc lại thì DB thắng. Không có dòng DB → dùng
mặc định. Vậy prod chạy lại seed không cần đụng bảng này.

Render dùng lại engine `render_template` của module thông báo ({{ var }}, {% if %}).
Gửi email đi qua đúng đường `EmailLog` + `send_smtp_email` như email cấp tài khoản
(tự tôn trọng công tắc `email_enabled` và cấu hình SMTP trong `app_settings`).
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from .email_template_model import EmailTemplate

logger = logging.getLogger(__name__)

#  Biến chèn được vào tiêu đề / thân cho các event Đặt xe (để màn cài đặt gợi ý).
DX_VARIABLES = [
    "code", "purpose", "creator_name", "driver_name", "vehicle_label",
    "start_time", "end_location", "reason", "recipient_name", "link",
]

#  Biến cho các event Duyệt dấu (event bắt đầu bằng `dd_`).
SEAL_VARIABLES = [
    "code", "purpose", "company_name", "creator_name", "approver_name",
    "reason", "recipient_name", "link",
]


def _variables_for(event: str) -> list[str]:
    return SEAL_VARIABLES if (event or "").startswith("dd_") else DX_VARIABLES


def _wrap(intro: str, *, show_reason: bool = False, cta: str = "Mở phiếu đặt xe") -> str:
    """Dựng thân HTML mặc định kiểu thẻ DEGO cho một event.

    `intro` là câu mở đầu; `show_reason` bật khối lý do (trả/từ chối). Người dùng
    có thể sửa toàn bộ chuỗi này trên màn cài đặt.
    """
    reason_block = (
        "{% if reason %}<div style=\"margin:16px 0; padding:12px 14px; background:#fef2f2; "
        "border:1px solid #fecaca; border-radius:6px; color:#991b1b;\">"
        "<strong>Lý do:</strong> {{ reason }}</div>{% endif %}"
        if show_reason else ""
    )
    return (
        "<div style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif; "
        "max-width:600px; margin:0 auto; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;\">"
        "<div style=\"background:#0098db; border-bottom:3px solid #f5871f; padding:16px 24px; "
        "color:#fff; font-weight:700; letter-spacing:1px;\">DEGO HOLDING — ĐẶT XE</div>"
        "<div style=\"padding:24px;\">"
        "<p style=\"margin:0 0 8px; font-size:15px;\">Kính gửi {{ recipient_name }},</p>"
        f"<p style=\"margin:0 0 16px; font-size:15px; color:#334155;\">{intro}</p>"
        "<table style=\"width:100%; font-size:14px; border-collapse:collapse;\">"
        "<tr><td style=\"padding:6px 0; color:#64748b; width:38%;\">Mã phiếu</td>"
        "<td style=\"padding:6px 0; font-weight:700; color:#0098db;\">{{ code }}</td></tr>"
        "<tr><td style=\"padding:6px 0; color:#64748b;\">Mục đích</td>"
        "<td style=\"padding:6px 0;\">{{ purpose }}</td></tr>"
        "<tr><td style=\"padding:6px 0; color:#64748b;\">Thời gian đi</td>"
        "<td style=\"padding:6px 0;\">{{ start_time }}</td></tr>"
        "<tr><td style=\"padding:6px 0; color:#64748b;\">Điểm đến</td>"
        "<td style=\"padding:6px 0;\">{{ end_location }}</td></tr>"
        "</table>"
        f"{reason_block}"
        "<div style=\"margin-top:22px;\"><a href=\"{{ link }}\" target=\"_blank\" "
        "style=\"display:inline-block; background:#0098db; color:#fff; text-decoration:none; "
        f"padding:11px 22px; border-radius:6px; font-weight:700; font-size:14px;\">{cta}</a></div>"
        "<p style=\"margin:18px 0 0; font-size:12px; color:#94a3b8;\">Email tự động từ hệ thống Đặt xe "
        "DEGO — vui lòng không trả lời email này.</p>"
        "</div></div>"
    )


def _wrap_seal(intro: str, *, show_reason: bool = False, cta: str = "Mở phiếu duyệt dấu") -> str:
    """Thân HTML mặc định cho một event DUYỆT DẤU (thẻ DEGO, rows theo con dấu)."""
    reason_block = (
        "{% if reason %}<div style=\"margin:16px 0; padding:12px 14px; background:#fef2f2; "
        "border:1px solid #fecaca; border-radius:6px; color:#991b1b;\">"
        "<strong>Lý do:</strong> {{ reason }}</div>{% endif %}"
        if show_reason else ""
    )
    return (
        "<div style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif; "
        "max-width:600px; margin:0 auto; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;\">"
        "<div style=\"background:#0098db; border-bottom:3px solid #f5871f; padding:16px 24px; "
        "color:#fff; font-weight:700; letter-spacing:1px;\">DEGO HOLDING — DUYỆT DẤU</div>"
        "<div style=\"padding:24px;\">"
        "<p style=\"margin:0 0 8px; font-size:15px;\">Kính gửi {{ recipient_name }},</p>"
        f"<p style=\"margin:0 0 16px; font-size:15px; color:#334155;\">{intro}</p>"
        "<table style=\"width:100%; font-size:14px; border-collapse:collapse;\">"
        "<tr><td style=\"padding:6px 0; color:#64748b; width:38%;\">Mã phiếu</td>"
        "<td style=\"padding:6px 0; font-weight:700; color:#0098db;\">{{ code }}</td></tr>"
        "<tr><td style=\"padding:6px 0; color:#64748b;\">Mục đích</td>"
        "<td style=\"padding:6px 0;\">{{ purpose }}</td></tr>"
        "<tr><td style=\"padding:6px 0; color:#64748b;\">Công ty</td>"
        "<td style=\"padding:6px 0;\">{{ company_name }}</td></tr>"
        "</table>"
        f"{reason_block}"
        "<div style=\"margin-top:22px;\"><a href=\"{{ link }}\" target=\"_blank\" "
        "style=\"display:inline-block; background:#0098db; color:#fff; text-decoration:none; "
        f"padding:11px 22px; border-radius:6px; font-weight:700; font-size:14px;\">{cta}</a></div>"
        "<p style=\"margin:18px 0 0; font-size:12px; color:#94a3b8;\">Email tự động từ hệ thống Duyệt dấu "
        "DEGO — vui lòng không trả lời email này.</p>"
        "</div></div>"
    )


#  Bộ mẫu mặc định — thứ tự này cũng là thứ tự hiển thị trên màn cài đặt.
#  MỖI EVENT = MỘT NHÓM NGƯỜI NHẬN (`recipient`). Hai mốc "Duyệt" và "Hoàn tất"
#  tách làm hai event vì Điều phối viên và Người tạo cần nội dung khác nhau.
DEFAULTS: list[dict] = [
    {"event": "dx_submitted", "label": "Gửi duyệt", "recipient": "Người duyệt",
     "subject": "YCĐX {{ code }} chờ bạn duyệt",
     "body_html": _wrap("Có một yêu cầu đặt xe mới cần bạn phê duyệt.", cta="Xem & duyệt phiếu")},

    {"event": "dx_approved_dispatcher", "label": "Duyệt", "recipient": "Điều phối viên",
     "subject": "Bạn có chuyến xe cần điều phối: {{ code }}",
     "body_html": _wrap("Một yêu cầu đặt xe vừa được duyệt. Vui lòng điều phối xe và tài xế.",
                        cta="Điều phối ngay")},
    {"event": "dx_approved_creator", "label": "Duyệt", "recipient": "Người tạo",
     "subject": "Yêu cầu đặt xe {{ code }} đã được duyệt",
     "body_html": _wrap("Yêu cầu đặt xe của bạn đã được duyệt, đang chờ điều phối xe và tài xế.")},

    {"event": "dx_returned", "label": "Yêu cầu chỉnh sửa", "recipient": "Người tạo",
     "subject": "YCĐX {{ code }} bị trả lại để chỉnh sửa",
     "body_html": _wrap("Yêu cầu đặt xe của bạn bị trả lại — hãy chỉnh sửa và gửi duyệt lại.",
                        show_reason=True, cta="Chỉnh sửa phiếu")},
    {"event": "dx_rejected", "label": "Từ chối", "recipient": "Người tạo",
     "subject": "YCĐX {{ code }} đã bị từ chối",
     "body_html": _wrap("Yêu cầu đặt xe của bạn đã bị từ chối.", show_reason=True)},

    {"event": "dx_dispatched", "label": "Điều phối", "recipient": "Tài xế được phân",
     "subject": "Bạn được phân chuyến {{ code }}",
     "body_html": _wrap("Bạn được phân một chuyến xe. Vui lòng xác nhận và thực hiện.",
                        cta="Xem chuyến của tôi")},
    {"event": "dx_driver_accepted", "label": "Tài xế nhận", "recipient": "Điều phối viên",
     "subject": "Tài xế đã nhận chuyến {{ code }}",
     "body_html": _wrap("Tài xế {{ driver_name }} đã nhận chuyến.")},
    {"event": "dx_driver_rejected", "label": "Tài xế từ chối", "recipient": "Điều phối viên",
     "subject": "Tài xế đã từ chối chuyến {{ code }}",
     "body_html": _wrap("Tài xế {{ driver_name }} đã từ chối chuyến — cần điều phối lại.",
                        show_reason=True, cta="Điều phối lại")},

    {"event": "dx_completed_dispatcher", "label": "Hoàn tất", "recipient": "Điều phối viên",
     "subject": "Chuyến {{ code }} đã hoàn tất",
     "body_html": _wrap("Chuyến xe đã hoàn tất.")},
    {"event": "dx_completed_creator", "label": "Hoàn tất", "recipient": "Người tạo",
     "subject": "Yêu cầu đặt xe {{ code }} đã hoàn tất",
     "body_html": _wrap("Chuyến xe của bạn đã hoàn tất. Cảm ơn bạn đã sử dụng dịch vụ đặt xe.")},

    # --- Duyệt dấu (Yêu cầu đóng dấu) ---
    {"event": "dd_submitted", "label": "Gửi duyệt", "recipient": "Trưởng bộ phận",
     "subject": "YCĐD {{ code }} chờ bạn duyệt",
     "body_html": _wrap_seal("Có một yêu cầu đóng dấu mới cần bạn phê duyệt.", cta="Xem & duyệt phiếu")},
    {"event": "dd_approved", "label": "Duyệt", "recipient": "Người tạo · Văn thư · Giám đốc",
     "subject": "Yêu cầu đóng dấu {{ code }} đã được duyệt",
     "body_html": _wrap_seal("Yêu cầu đóng dấu đã được duyệt. Văn thư vui lòng đối chiếu chứng từ "
                             "và đóng dấu.", cta="Xem phiếu")},
    {"event": "dd_returned", "label": "Yêu cầu chỉnh sửa", "recipient": "Người tạo",
     "subject": "YCĐD {{ code }} bị trả lại để chỉnh sửa",
     "body_html": _wrap_seal("Yêu cầu đóng dấu của bạn bị trả lại — hãy chỉnh sửa và gửi lại.",
                             show_reason=True, cta="Chỉnh sửa phiếu")},
    {"event": "dd_rejected", "label": "Từ chối", "recipient": "Người tạo",
     "subject": "YCĐD {{ code }} đã bị từ chối",
     "body_html": _wrap_seal("Yêu cầu đóng dấu của bạn đã bị từ chối.", show_reason=True)},
    {"event": "dd_completed", "label": "Hoàn thành", "recipient": "Người tạo",
     "subject": "Yêu cầu đóng dấu {{ code }} đã đóng dấu xong",
     "body_html": _wrap_seal("Văn thư đã đóng dấu xong yêu cầu của bạn.")},
]

_DEFAULT_MAP = {d["event"]: d for d in DEFAULTS}


def is_known(event: str) -> bool:
    return event in _DEFAULT_MAP


def event_display(event: str) -> str:
    """Nhãn hiển thị của một event, vd "Duyệt → Điều phối viên". "" = mọi mẫu."""
    if not event:
        return "Tất cả mẫu"
    d = _DEFAULT_MAP.get(event)
    if d is None:
        return event
    rec = d.get("recipient", "")
    return f"{d['label']} → {rec}" if rec else d["label"]


def get_effective(db: Session, event: str) -> dict | None:
    """Mẫu đang có hiệu lực cho một event: DB (nếu có) đè lên mặc định.

    Trả `None` nếu event không nằm trong bộ đã khai (tránh gửi email lung tung).
    """
    base = _DEFAULT_MAP.get(event)
    if base is None:
        return None
    row = db.query(EmailTemplate).filter(EmailTemplate.event == event).first()
    if row is None:
        return {**base, "enabled": True, "is_custom": False, "variables": _variables_for(event)}
    return {
        "event": event,
        "label": base["label"],
        "recipient": base.get("recipient", ""),
        "enabled": bool(row.enabled),
        "subject": row.subject or base["subject"],
        "body_html": row.body_html or base["body_html"],
        "is_custom": True,
        "variables": _variables_for(event),
    }


def list_effective(db: Session) -> list[dict]:
    """Toàn bộ mẫu theo thứ tự khai báo, đã đè DB lên mặc định."""
    return [get_effective(db, d["event"]) for d in DEFAULTS]


def upsert(db: Session, event: str, *, enabled: bool, subject: str, body_html: str,
           user) -> dict:
    """Lưu chỉnh sửa của người dùng cho một event (tạo dòng nếu chưa có)."""
    base = _DEFAULT_MAP.get(event)
    if base is None:
        from fastapi import HTTPException
        raise HTTPException(400, f"Sự kiện email không hợp lệ: {event}")
    row = db.query(EmailTemplate).filter(EmailTemplate.event == event).first()
    if row is None:
        row = EmailTemplate(event=event, created_by=getattr(user, "id", 0))
        db.add(row)
    row.label = base["label"]
    row.enabled = bool(enabled)
    row.subject = (subject or "").strip() or base["subject"]
    row.body_html = body_html or base["body_html"]
    row.updated_by = getattr(user, "id", 0)
    db.commit()
    return get_effective(db, event)


def reset(db: Session, event: str) -> dict | None:
    """Xóa bản chỉnh sửa → quay về mẫu mặc định trong code."""
    row = db.query(EmailTemplate).filter(EmailTemplate.event == event).first()
    if row is not None:
        db.delete(row)
        db.commit()
    return get_effective(db, event)


def render_event(db: Session, event: str, context: dict) -> tuple[str, str] | None:
    """(subject, html) đã render cho event; `None` nếu event tắt email hoặc không có mẫu."""
    eff = get_effective(db, event)
    if eff is None or not eff["enabled"]:
        return None
    from .service import render_template  # tránh import vòng
    subject = render_template(eff["subject"], context)
    html = render_template(eff["body_html"], context)
    return subject, html


def send_event_email(db: Session, event: str, background_tasks, recipients: list,
                     context: dict) -> None:
    """Gửi email theo mẫu tới danh sách người nhận (mỗi người một địa chỉ thật).

    Bỏ qua nếu event tắt email. Tôn trọng `email_enabled`/SMTP trong `send_smtp_email`
    (không cấu hình thì hàm đó tự bỏ, không lỗi). Best-effort — lỗi được nuốt.
    """
    eff = get_effective(db, event)
    if eff is None or not eff["enabled"]:
        return
    try:
        from app.core.database import SessionLocal

        from . import email_exclusion_service
        from .model import EmailLog
        from .service import get_user_display_name, render_template, send_smtp_email

        #  Loại trừ email theo cá nhân / phòng ban / công ty (hồ sơ nhân sự) — gồm
        #  luật áp mọi mẫu + luật riêng cho chính event này.
        recipients = email_exclusion_service.filter_recipients(db, recipients, event)

        actor_id = int(context.get("actor_id") or 0)
        seen: set[int] = set()
        queued = False
        for r in recipients:
            if not r or getattr(r, "id", None) in seen:
                continue
            seen.add(r.id)
            to_email = (getattr(r, "email", "") or "").strip()
            if not to_email:
                continue
            ctx = {**context, "recipient_name": get_user_display_name(db, r) or ""}
            subject = render_template(eff["subject"], ctx)
            html = render_template(eff["body_html"], ctx)
            log = EmailLog(event=event, to_email=to_email, subject=subject,
                           status="pending", created_by=actor_id)
            db.add(log)
            db.flush()
            if background_tasks is not None:
                background_tasks.add_task(send_smtp_email, SessionLocal, log.id, to_email, subject, html)
            else:
                send_smtp_email(SessionLocal, log.id, to_email, subject, html)
            queued = True
        if queued:
            db.commit()
    except Exception:  # noqa: BLE001 — thông báo là phụ, không được làm hỏng nghiệp vụ
        logger.exception("Gửi email sự kiện %s thất bại", event)
