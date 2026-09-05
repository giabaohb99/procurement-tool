"""Bắn CHUÔNG + EMAIL cho các bước của phiếu Duyệt dấu (best-effort).

Ai NHẬN là luật nghiệp vụ nằm ở đây, KHÔNG cho sửa trên UI (tránh gửi nhầm). Nội
dung email lấy từ mẫu sửa được `tab_email_template` theo event; chuông in-app luôn
được tạo. Mọi lỗi thông báo được NUỐT — không để hỏng việc chuyển trạng thái phiếu.

Người nhận theo event:
  dd_submitted → Trưởng bộ phận (phòng của người tạo)
  dd_approved  → Người tạo + Văn thư (vai trò seal_clerk, LỌC THEO công ty con dấu) + Giám đốc công ty
  dd_returned  → Người tạo
  dd_rejected  → Người tạo
  dd_completed → Người tạo
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from .model import SealRequest

logger = logging.getLogger(__name__)

#  Vai trò Văn thư đóng dấu (nhận phiếu đã duyệt để đóng dấu).
_CLERK_ROLE_CODES = ["seal_clerk"]
#  Vai trò "Giám đốc duyệt dấu" — CHỈ NHẬN THÔNG BÁO, không tham gia phê duyệt.
#  Ai được gán vai trò này + đúng công ty thì nhận email/chuông khi phiếu được duyệt.
_DIRECTOR_ROLE_CODES = ["seal_director"]

_BELL_BODY = {
    "dd_submitted": "Có yêu cầu đóng dấu mới cần bạn phê duyệt.",
    "dd_approved": "Yêu cầu đóng dấu đã được duyệt — Văn thư vui lòng đối chiếu chứng từ và đóng dấu.",
    "dd_returned": "Yêu cầu đóng dấu của bạn bị trả lại để chỉnh sửa.",
    "dd_rejected": "Yêu cầu đóng dấu của bạn đã bị từ chối.",
    "dd_completed": "Yêu cầu đóng dấu của bạn đã được đóng dấu xong.",
}


def _creator(db: Session, req: SealRequest):
    from app.modules.user.model import User
    if not req.requester_id:
        return None
    return db.get(User, req.requester_id)


def _company_ids(db: Session, req: SealRequest) -> set:
    from .service import get_company_ids
    return set(get_company_ids(db, req.id))


def _by_companies(db: Session, users: list, company_ids: set) -> list:
    """Giữ người thuộc BẤT KỲ công ty nào trong danh sách (theo hồ sơ nhân sự)."""
    if not company_ids:
        return []
    from app.modules.employee.model import Employee
    out = []
    for u in users:
        emp = db.get(Employee, u.employee_id) if getattr(u, "employee_id", 0) else None
        if emp and emp.company_id in company_ids:
            out.append(u)
    return out


def _clerks(db: Session, req: SealRequest) -> list:
    from app.modules.notification.service import get_users_by_role_codes
    return _by_companies(db, get_users_by_role_codes(db, _CLERK_ROLE_CODES), _company_ids(db, req))


def _directors(db: Session, req: SealRequest) -> list:
    from app.modules.notification.service import get_users_by_role_codes
    return _by_companies(db, get_users_by_role_codes(db, _DIRECTOR_ROLE_CODES), _company_ids(db, req))


def _approvers(db: Session, req: SealRequest) -> list:
    from app.modules.notification.service import (
        get_approvers_for_entity,
        get_dept_approver_recipients,
    )
    people = get_dept_approver_recipients(db, "", req.department_id or 0)
    if not people:
        people = get_approvers_for_entity(db, "seal_request")
    return people


def _recipients_for(db: Session, event: str, req: SealRequest) -> list:
    if event == "dd_submitted":
        return _approvers(db, req)
    if event == "dd_approved":
        return [_creator(db, req), *_clerks(db, req), *_directors(db, req)]
    if event in ("dd_returned", "dd_rejected", "dd_completed"):
        return [_creator(db, req)]
    return []


def _context(db: Session, req: SealRequest, reason: str = "") -> dict:
    from app.modules.company.model import Company
    from app.modules.notification.service import _abs_link
    from app.modules.user.model import User

    cids = list(_company_ids(db, req))
    names = [c.name for c in db.query(Company).filter(Company.id.in_(cids)).all()] if cids else []
    company_name = ", ".join(names)
    approver_name = ""
    if req.first_approver_id:
        from app.modules.employee.model import Employee
        u = db.get(User, req.first_approver_id)
        emp = db.get(Employee, u.employee_id) if u and u.employee_id else None
        approver_name = emp.full_name if emp else ""
    return {
        "code": req.code or "",
        "purpose": req.purpose or "",
        "company_name": company_name,
        "creator_name": req.requester or "",
        "approver_name": approver_name,
        "reason": (reason or "").strip(),
        "link": _abs_link(f"/approval-seal/{req.id}"),
    }


def notify(db: Session, event: str, req: SealRequest, background_tasks=None,
           actor=None, reason: str = "") -> None:
    """Tạo chuông cho người liên quan + gửi email theo mẫu. Nuốt mọi lỗi."""
    try:
        recipients = [r for r in _recipients_for(db, event, req) if r]
        if not recipients:
            return
        ctx = _context(db, req, reason)

        from app.modules.notification.email_template_service import (
            get_effective,
            send_event_email,
        )
        from app.modules.notification.model import Notification
        from app.modules.notification.service import render_template

        eff = get_effective(db, event)
        title = render_template(eff["subject"], ctx) if eff else (req.code or "Duyệt dấu")
        body = _BELL_BODY.get(event, "")
        actor_id = int(getattr(actor, "id", 0) or 0)

        seen: set[int] = set()
        for r in recipients:
            if getattr(r, "id", None) in seen:
                continue
            seen.add(r.id)
            db.add(Notification(user_id=r.id, title=title, body=body,
                                link=ctx["link"], created_by=actor_id))
        db.commit()

        ctx["actor_id"] = actor_id
        send_event_email(db, event, background_tasks, recipients, ctx)
    except Exception:  # noqa: BLE001 — thông báo không được làm hỏng nghiệp vụ
        logger.exception("notify %s thất bại cho phiếu %s", event, getattr(req, "id", None))
