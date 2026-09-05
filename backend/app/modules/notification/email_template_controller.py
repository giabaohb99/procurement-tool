"""API mẫu email theo bước — dùng ở Cấu hình hệ thống (/system/settings).

Gác bằng entity **`setting`** (đây là một mục của Cấu hình hệ thống, không đẻ quyền
mới). Cho phép: liệt kê, xem, sửa (bật/tắt + tiêu đề + thân HTML), khôi phục mặc
định, xem trước (render thử) và gửi thử về email người đang thao tác.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import email_template_service as svc

router = APIRouter(prefix="/api/email-templates", tags=["email-template"])

#  Ngữ cảnh mẫu để xem trước / gửi thử (không đụng dữ liệu thật).
_SAMPLE = {
    "code": "DX007",
    "purpose": "Đưa đón đối tác đi công tác",
    "creator_name": "Nguyễn Văn A",
    "driver_name": "Trần Văn B",
    "vehicle_label": "51A-123.45 — Toyota Innova",
    "start_time": "2026-09-10T08:00",
    "end_location": "KCN Sóng Thần, Bình Dương",
    "reason": "Thiếu thông tin người nhận hàng",
    "recipient_name": "Anh/Chị",
    "link": "https://thumua.degoholding.vn/vehicle-booking/7",
}


class TemplateIn(BaseModel):
    enabled: bool = True
    subject: str = ""
    body_html: str = ""


class PreviewIn(BaseModel):
    subject: str | None = None
    body_html: str | None = None


@router.get("")
def list_templates(db: Session = Depends(get_db),
                   user=Depends(require("setting", "read"))):
    return success(svc.list_effective(db))


@router.get("/{event}")
def get_template(event: str, db: Session = Depends(get_db),
                 user=Depends(require("setting", "read"))):
    eff = svc.get_effective(db, event)
    if eff is None:
        raise HTTPException(404, f"Không có mẫu email cho sự kiện: {event}")
    return success(eff)


@router.put("/{event}")
def update_template(event: str, data: TemplateIn, db: Session = Depends(get_db),
                    user=Depends(require("setting", "write"))):
    eff = svc.upsert(db, event, enabled=data.enabled, subject=data.subject,
                     body_html=data.body_html, user=user)
    return success(eff, "Đã lưu mẫu email")


@router.post("/{event}/reset")
def reset_template(event: str, db: Session = Depends(get_db),
                   user=Depends(require("setting", "write"))):
    eff = svc.reset(db, event)
    if eff is None:
        raise HTTPException(404, f"Không có mẫu email cho sự kiện: {event}")
    return success(eff, "Đã khôi phục mẫu mặc định")


@router.post("/{event}/preview")
def preview_template(event: str, data: PreviewIn, db: Session = Depends(get_db),
                     user=Depends(require("setting", "read"))):
    """Render thử bản ĐANG SOẠN (nếu client gửi kèm) hoặc bản đã lưu, với dữ liệu mẫu."""
    eff = svc.get_effective(db, event)
    if eff is None:
        raise HTTPException(404, f"Không có mẫu email cho sự kiện: {event}")
    from .service import render_template
    subject_tpl = data.subject if data.subject is not None else eff["subject"]
    body_tpl = data.body_html if data.body_html is not None else eff["body_html"]
    return success({
        "subject": render_template(subject_tpl, _SAMPLE),
        "html": render_template(body_tpl, _SAMPLE),
    })


@router.post("/{event}/test-send")
def test_send(event: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("setting", "write"))):
    """Gửi thử email của bước này về đúng địa chỉ của người đang bấm."""
    eff = svc.get_effective(db, event)
    if eff is None:
        raise HTTPException(404, f"Không có mẫu email cho sự kiện: {event}")
    to_email = (getattr(user, "email", "") or "").strip()
    if not to_email:
        raise HTTPException(400, "Tài khoản của bạn chưa có email để gửi thử")
    from app.core.database import SessionLocal

    from .model import EmailLog
    from .service import render_template, send_smtp_email
    subject = "[GỬI THỬ] " + render_template(eff["subject"], _SAMPLE)
    html = render_template(eff["body_html"], _SAMPLE)
    log = EmailLog(event=f"{event}_test", to_email=to_email, subject=subject,
                   status="pending", created_by=getattr(user, "id", 0))
    db.add(log)
    db.flush()
    background_tasks.add_task(send_smtp_email, SessionLocal, log.id, to_email, subject, html, True)
    db.commit()
    return success({"to_email": to_email}, f"Đã gửi email thử tới {to_email}")
