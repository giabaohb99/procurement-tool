"""Nhật ký email — `/api/email-logs` (bao-CR-721). CHỈ ĐỌC.

`tab_email_log` ghi mọi thư hệ gửi (sự kiện, người nhận, tiêu đề, trạng thái, lỗi, hộp thư gửi) nhưng tới 03/11/2026 không
có API hay màn nào đọc (prod 6.170 dòng) — người quản trị không tra được "đã gửi thư cho ai chưa, lỗi gì". Màn
`/system/email-logs` của phân hệ Quản trị đọc qua đây.

- Quyền: `audit.read` (khóa Nhật ký hệ thống có sẵn, không thêm entity). Không có đường ghi / gửi lại.
- `status` giữ nguyên chuỗi cũ của cột (`pending` / `sent` / `failed` / `disabled`), nhãn tiếng Việt trả kèm.
- Nhãn sự kiện lấy từ danh mục mẫu email (`email_template_service.event_display`); sự kiện không có trong danh mục (thư
  gửi thẳng, thư thử) trả nguyên mã.
- Đường này nằm trong `logging_policy.SKIP_PATH_PREFIXES`: màn đọc nhật ký không đẻ thêm dòng nhật ký để đọc (NT-5).
"""
from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.permissions import ENTITY_LABELS
from app.core.response import success

from . import email_template_service
from .model import EmailLog

router = APIRouter(prefix="/api/email-logs", tags=["email-log"])

STATUS_LABELS = {"pending": "Đang chờ", "sent": "Đã gửi", "failed": "Lỗi", "disabled": "Tắt gửi"}
#  Sự kiện KHÔNG nằm trong danh mục mẫu email (ghi thẳng bằng EmailLog(...) ở nơi khác) — soát dev 04/11/2026: workflow_<loại
#  chứng từ> (luồng duyệt dùng chung, `notification/service._send_workflow_emails`), document_issued (văn thư ban hành),
#  password_reset (quên mật khẩu), <event>_test (nút Gửi thử của màn Mẫu email). Không khai thì màn in mã Anh trần.
EXTRA_EVENT_LABELS = {
    "document_issued": "Văn bản mới ban hành",
    "password_reset": "Đặt lại mật khẩu",
    "workflow_preview": "Luồng duyệt → thử mẫu",
}


def event_label(event: str) -> str:
    """Nhãn tiếng Việt của sự kiện: danh mục mẫu email trước, rồi các họ ghi thẳng; lạ thì trả nguyên mã."""
    if not event:
        return ""
    if email_template_service.is_known(event):
        return email_template_service.event_display(event)
    if event in EXTRA_EVENT_LABELS:
        return EXTRA_EVENT_LABELS[event]
    if event.startswith("workflow_"):
        doc_type = event[len("workflow_"):]
        return f"Luồng duyệt → {ENTITY_LABELS.get(doc_type, doc_type)}"
    if event.endswith("_test"):
        return f"Gửi thử → {event_label(event[:-len('_test')])}"
    return event
#  Thứ tự hiện trên ô lọc: cái người ta tra nhiều nhất đứng trước.
STATUS_ORDER = ("failed", "sent", "pending", "disabled")


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status or "", status or "")


def _format(r: EmailLog) -> dict:
    return {
        "id": r.id,
        "event": r.event or "",
        "event_label": event_label(r.event or ""),
        "to_email": r.to_email or "",
        "subject": r.subject or "",
        "status": r.status or "",
        "status_label": status_label(r.status or ""),
        "error": r.error or "",
        "sent_at": r.sent_at,
        "mailbox_id": r.mailbox_id,
        "from_email": r.from_email or "",
        "created_at": r.created_at,
        "created_by": r.created_by,
    }


def _parse_day(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "Ngày phải theo dạng YYYY-MM-DD") from None


@router.get("/meta")
def email_log_meta(db: Session = Depends(get_db), user=Depends(require("audit", "read"))):
    """Bộ chọn cho ô lọc: sự kiện (danh mục mẫu email + sự kiện lạ đã từng ghi) và trạng thái, kèm nhãn tiếng Việt."""
    known = [d["event"] for d in email_template_service.DEFAULTS]
    seen = [e for (e,) in db.query(EmailLog.event).distinct().all() if e]
    extra = sorted(e for e in set(seen) - set(known))
    events = [{"code": e, "label": event_label(e)} for e in known + extra]
    statuses = [{"code": s, "label": STATUS_LABELS[s]} for s in STATUS_ORDER]
    return success({"events": events, "statuses": statuses})


@router.get("/stats")
def email_log_stats(days: int = Query(7, ge=1, le=365), db: Session = Depends(get_db),
                    user=Depends(require("audit", "read"))):
    """Thẻ đầu màn: số thư theo trạng thái trong N ngày gần đây (mặc định 7)."""
    since = datetime.utcnow() - timedelta(days=days)
    rows = (db.query(EmailLog.status, func.count(EmailLog.id))
            .filter(EmailLog.created_at >= since).group_by(EmailLog.status).all())
    by_status = {s or "": int(n) for s, n in rows}
    return success({
        "days": days,
        "total": sum(by_status.values()),
        "failed": by_status.get("failed", 0),
        "sent": by_status.get("sent", 0),
        "pending": by_status.get("pending", 0),
        "by_status": [{"status": s, "label": status_label(s), "count": n} for s, n in by_status.items()],
    })


@router.get("")
def list_email_logs(
    q: str | None = Query(None, description="Người nhận chứa chuỗi này (không phân biệt hoa thường)"),
    event: list[str] | None = Query(None, description="Mã sự kiện, truyền nhiều lần để lọc nhiều sự kiện"),
    status: str | None = Query(None, description="pending / sent / failed / disabled"),
    from_date: str | None = Query(None, description="Từ ngày (YYYY-MM-DD) theo lúc ghi"),
    to_date: str | None = Query(None, description="Đến ngày (YYYY-MM-DD) theo lúc ghi"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(require("audit", "read")),
):
    """Danh sách thư đã ghi, mới nhất trước. Phân trang `{total, items, page, page_size}`."""
    query = db.query(EmailLog)
    if q and q.strip():
        query = query.filter(func.lower(EmailLog.to_email).like(f"%{q.strip().lower()}%"))
    events = [e for e in (event or []) if e]
    if events:
        query = query.filter(EmailLog.event.in_(events))
    if status:
        query = query.filter(EmailLog.status == status)
    fd = _parse_day(from_date)
    if fd:
        query = query.filter(EmailLog.created_at >= fd)
    td = _parse_day(to_date)
    if td:
        query = query.filter(EmailLog.created_at <= datetime.combine(td.date(), time.max))
    total = query.count()
    items = query.order_by(EmailLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return success({"total": total, "items": [_format(r) for r in items], "page": page, "page_size": page_size})


@router.get("/{log_id}")
def get_email_log(log_id: int, db: Session = Depends(get_db), user=Depends(require("audit", "read"))):
    """Một dòng đầy đủ — câu lỗi nguyên văn, không cắt."""
    row = db.get(EmailLog, log_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy dòng nhật ký email")
    return success(_format(row))
