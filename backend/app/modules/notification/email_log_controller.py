"""Nhật ký email — `/api/email-logs` (bao-CR-721) + nút Gửi lại (bao-CR-727).

`tab_email_log` ghi mọi thư hệ gửi (sự kiện, người nhận, tiêu đề, trạng thái, lỗi, hộp thư gửi) nhưng tới 03/11/2026 không
có API hay màn nào đọc (prod 6.170 dòng) — người quản trị không tra được "đã gửi thư cho ai chưa, lỗi gì". Màn
`/system/email-logs` của phân hệ Quản trị đọc qua đây.

- Quyền: `audit.read` (khóa Nhật ký hệ thống có sẵn, không thêm entity). Đường ghi duy nhất là
  `POST /{id}/resend` (bao-CR-727), đòi `audit.write` — cùng khóa, cùng kiểu `sync_log.write` = nút Chạy lại.
- Gửi lại sinh DÒNG MỚI (`resent_from_id` = dòng đã bấm), không sửa dòng cũ. Chỉ gửi lại được thư có lưu nội dung
  (`html_body`, lưu từ bao-CR-727); thư đặt lại mật khẩu / cấp tài khoản không bao giờ lưu nên không gửi lại được.
- `status` giữ nguyên chuỗi cũ của cột (`pending` / `sent` / `failed` / `disabled`), nhãn tiếng Việt trả kèm.
- Nhãn sự kiện lấy từ danh mục mẫu email (`email_template_service.event_display`); sự kiện không có trong danh mục (thư
  gửi thẳng, thư thử) trả nguyên mã.
- Đường này nằm trong `logging_policy.SKIP_PATH_PREFIXES`: màn đọc nhật ký không đẻ thêm dòng nhật ký để đọc (NT-5).
"""
from datetime import datetime, time, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import ENTITY_LABELS
from app.core.response import success

from . import email_template_service
from . import service as notification_service
from .model import EmailLog, is_secret_email_event

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


#  Chặn bấm liên tục: cùng một thư (dòng gốc hay các bản gửi lại của nó) đã gửi lại trong khoảng này thì từ chối.
RESEND_COOLDOWN_SECONDS = 60
SECRET_BLOCK_REASON = ("Thư đặt lại mật khẩu / cấp tài khoản chứa liên kết đặt mật khẩu nên hệ không lưu nội dung và "
                       "không gửi lại được. Người nhận tự bấm Quên mật khẩu ở màn đăng nhập để nhận liên kết mới.")


def _first_kept_body_at(db: Session) -> datetime | None:
    """Lúc ghi của thư SỚM NHẤT có lưu nội dung — mốc "thư gửi trước ngày này không lưu nội dung".

    Đi từ id nhỏ lên và dừng ở dòng đầu tiên có nội dung: số dòng phải lướt qua chỉ bằng số thư cũ trước đợt
    bao-CR-727 (cố định), không lớn dần theo bảng.
    """
    row = (db.query(EmailLog.created_at).filter(EmailLog.html_body.isnot(None))
           .order_by(EmailLog.id.asc()).limit(1).first())
    return row[0] if row else None


def resend_block_reason(r: EmailLog, first_kept_at: datetime | None) -> str:
    """Vì sao dòng này KHÔNG gửi lại được; rỗng = gửi lại được."""
    if is_secret_email_event(r.event):
        return SECRET_BLOCK_REASON
    if r.html_body == "":
        #  bao-CR-731: "" = đã lưu rồi bị việc dọn đêm xóa nội dung (NULL mới là chưa bao giờ lưu).
        return (f"Thư quá {settings.EMAIL_BODY_KEEP_DAYS} ngày đã dọn nội dung (chỉ giữ người nhận, tiêu đề, trạng thái) "
                "nên không gửi lại được.")
    if not r.html_body:
        if first_kept_at and (r.created_at is None or r.created_at < first_kept_at):
            return f"Thư gửi trước ngày {first_kept_at:%d/%m/%Y} không lưu nội dung nên không gửi lại được."
        return "Thư này không lưu nội dung nên không gửi lại được."
    if not (r.to_email or "").strip():
        return "Thư không có địa chỉ người nhận nên không gửi lại được."
    return ""


class _KeptAt:
    """Tra mốc `_first_kept_body_at` TỐI ĐA một lần mỗi request, và chỉ khi có dòng thiếu nội dung cần tới nó."""

    def __init__(self, db: Session):
        self.db, self.done, self.value = db, False, None

    def get(self) -> datetime | None:
        if not self.done:
            self.value, self.done = _first_kept_body_at(self.db), True
        return self.value


def _format(r: EmailLog, kept_at: _KeptAt | None = None) -> dict:
    needs_mark = not r.html_body and not is_secret_email_event(r.event)
    reason = resend_block_reason(r, kept_at.get() if (kept_at and needs_mark) else None)
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
        #  bao-CR-727. KHÔNG trả `html_body` ở đây: danh sách 50 dòng × vài KB mỗi dòng là thừa.
        "resent_from_id": r.resent_from_id,
        "has_body": bool(r.html_body),
        "can_resend": not reason,
        "resend_block_reason": reason,
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
    kept_at = _KeptAt(db)
    return success({"total": total, "items": [_format(r, kept_at) for r in items], "page": page,
                    "page_size": page_size})


@router.get("/{log_id}")
def get_email_log(log_id: int, db: Session = Depends(get_db), user=Depends(require("audit", "read"))):
    """Một dòng đầy đủ — câu lỗi nguyên văn, không cắt."""
    row = db.get(EmailLog, log_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy dòng nhật ký email")
    return success(_format(row, _KeptAt(db)))


def _send_flags(event: str) -> tuple[bool, bool]:
    """`(force, apply_override)` của lượt gửi lại — giữ đúng cách lượt gửi gốc đã gửi.

    - Thư luồng duyệt (`workflow_*`) gốc gửi `force=True, apply_override=False`: chỉ có khi EMAIL_WORKFLOW_ENABLED,
      địa chỉ đã định tuyến về hộp thư test theo vai trò — không gộp về một địa chỉ override.
    - Thư gửi thử (`*_test`) gốc gửi `force=True`.
    - Còn lại tôn trọng công tắc `email_enabled` và địa chỉ override như lượt gốc. `EMAIL_HARD_OFF` luôn thắng.
    """
    if (event or "").startswith("workflow_"):
        return True, False
    if (event or "").endswith("_test"):
        return True, True
    return False, True


def _recent_resend(db: Session, row: EmailLog) -> EmailLog | None:
    """Bản gửi lại của CÙNG thư trong `RESEND_COOLDOWN_SECONDS` giây qua (bấm từ dòng gốc hay từ bản gửi lại)."""
    since = datetime.now() - timedelta(seconds=RESEND_COOLDOWN_SECONDS)
    family = {row.id}
    if row.resent_from_id:
        family.add(row.resent_from_id)
    return (db.query(EmailLog)
            .filter(EmailLog.created_at >= since,
                    or_(EmailLog.resent_from_id.in_(family),
                        #  Bấm Gửi lại trên chính một bản gửi lại vừa sinh ra.
                        (EmailLog.id == row.id) & EmailLog.resent_from_id.isnot(None)))
            .order_by(EmailLog.id.desc()).first())


@router.post("/{log_id}/resend")
def resend_email_log(log_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                     user=Depends(require("audit", "write"))):
    """Gửi lại y nguyên một thư đã ghi: cùng người nhận, tiêu đề, nội dung, hộp thư gửi danh nghĩa (bao-CR-727).

    - Quyền: `audit.write` (màn đọc gác `audit.read`; khóa này chỉ quản trị hệ thống có sẵn).
    - Sinh DÒNG NHẬT KÝ MỚI ở trạng thái chờ, `resent_from_id` = dòng đã bấm; dòng cũ giữ nguyên. Gửi nền qua đường
      gửi chung `send_smtp_email` nên công tắc tắt email / chặn cứng / địa chỉ override vẫn áp như thư gốc.
    - Thư hệ không có tệp đính kèm (mọi mẫu chỉ có thân HTML + liên kết) nên gửi lại là gửi trọn thư.
    - 400: thư không lưu nội dung (thư cũ trước đợt này, thư đặt lại mật khẩu / cấp tài khoản), thiếu người nhận.
    - 429: cùng thư đã được gửi lại trong 60 giây qua.
    - Ghi nhật ký thao tác `email_log` / `resend`.
    """
    row = db.get(EmailLog, log_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy dòng nhật ký email")
    reason = resend_block_reason(row, _first_kept_body_at(db) if not row.html_body else None)
    if reason:
        raise HTTPException(400, reason)
    recent = _recent_resend(db, row)
    if recent is not None:
        raise HTTPException(429, f"Thư này vừa được gửi lại (dòng #{recent.id}). "
                                 f"Đợi {RESEND_COOLDOWN_SECONDS} giây rồi hãy bấm lại.")

    actor_id = getattr(user, "id", 0) or 0
    fresh = EmailLog(event=row.event, to_email=row.to_email, subject=row.subject, status="pending",
                     mailbox_id=row.mailbox_id, from_email="", html_body=row.html_body, resent_from_id=row.id,
                     created_by=actor_id)
    db.add(fresh)
    db.flush()
    #  `record` tự commit: dòng mới có thật trong DB trước khi tác vụ nền (phiên mới) đọc nó.
    record(db, actor_id, "email_log", fresh.id, "resend",
           f"Gửi lại thư #{row.id} tới {row.to_email} (dòng mới #{fresh.id}): {row.subject}")

    from app.core.database import SessionLocal

    force, apply_override = _send_flags(row.event)
    background_tasks.add_task(notification_service.send_smtp_email, SessionLocal, fresh.id, fresh.to_email,
                              fresh.subject, fresh.html_body, force, apply_override)
    db.refresh(fresh)
    return success(_format(fresh), f"Đã xếp gửi lại thư tới {fresh.to_email}")
