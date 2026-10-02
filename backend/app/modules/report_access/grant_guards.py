"""Hai chốt chống tự nâng quyền áp riêng cho `POST /api/report-access/{key}/grants` (M3,
code review tính năng phân quyền báo cáo) — tách khỏi `grant_service.py` để tệp đó chỉ còn
lo CRUD (giữ dưới 200 dòng, cùng luật modularization của `development-rules.md`).

Cả hai đều TÁI DÙNG hàm sẵn có ở `core/privilege_escalation.py`/`core/subject_match.py`,
không chép lại luật chống tự nâng quyền lần hai — xem docstring từng hàm dưới.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.privilege_escalation import is_system_admin
from app.core.subject_match import EFFECT_ALLOW, EFFECT_DENY, SUBJECT_ROLE, subject_pairs

from .schema import ReportAccessGrantIn

#  Mã vai trò Quản trị hệ thống — CẢ hai, cùng danh sách
#  `app.seed.ensure_admin_role`/`force_resync_roles` dùng để coi hai mã này là MỘT (đời cũ
#  `ADMINISTRATOR` + đời mới `admin`).
ADMIN_ROLE_CODES = ("admin", "ADMINISTRATOR")

ADMIN_SUBJECT_DENY_MESSAGE = ("Không cấm xem báo cáo đối với vai trò Quản trị hệ thống — vai trò "
                             "này luôn đủ mọi quyền (ngoại lệ bao-CR-523, xem "
                             "`core/privilege_escalation.py`).")

SELF_GRANT_MESSAGE = ("Không tự gán quyền xem báo cáo CHO PHÉP cho chính mình được (bản thân, vai "
                     "trò bạn đang giữ, hoặc phòng ban/pháp nhân của bạn). Nhờ một quản trị khác "
                     "thao tác — đây là chốt hai người của phân quyền.")


def reject_deny_on_admin_role(db: Session, data: ReportAccessGrantIn) -> None:
    """Finding M3(a) — CẤM không áp được lên chủ thể là vai trò Quản trị hệ thống (mã
    `admin` hoặc đời cũ `ADMINISTRATOR`): vai trò này LUÔN FULL (bao-CR-523), một dòng
    CẤM nằm im trong bảng này không đổi được gì (gác kép vẫn qua `require`/`apply_scope`),
    nhưng để nó tồn tại là một câu hỏi "tại sao admin bị cấm xem X" mãi không ai trả lời
    được — chặn ngay từ cửa ghi. Chỉ xét chủ thể VAI TRÒ, người/phòng/pháp nhân không liên
    quan tới hàng này."""
    if data.effect != EFFECT_DENY:
        return
    role_ids = {s.subject_id for s in data.subjects if s.subject_kind == SUBJECT_ROLE}
    if not role_ids:
        return
    from app.modules.role.model import Role

    hit = db.query(Role.id).filter(Role.id.in_(role_ids), Role.code.in_(ADMIN_ROLE_CODES)).first()
    if hit:
        raise HTTPException(400, ADMIN_SUBJECT_DENY_MESSAGE)


def block_self_allow_grant(db: Session, data: ReportAccessGrantIn, actor) -> None:
    """Finding M3(b) — cùng TINH THẦN luật L1 của `core/privilege_escalation.py` (không tự
    sửa quyền của chính mình), áp cho cửa này theo CHỦ THỂ chứ không theo `user_id` đích
    (cửa này không nhắm vào một tài khoản cụ thể). Tái dùng hai hàm sẵn có, không chép
    luật lần hai:
      - `subject_pairs(profile)` (`core/subject_match.py`) — đã dùng để khớp ACL, ở đây
        dùng NGƯỢC để biết chủ thể nào trong lô gửi lên LÀ chính người đang thao tác
        (bản thân, phòng/pháp nhân của họ, vai trò họ đang giữ).
      - `is_system_admin(db, actor.id)` (`core/privilege_escalation.py`) — ngoại lệ
        bao-CR-523, admin được miễn mọi chốt L1.
    Chỉ chặn chiều CHO PHÉP — CẤM cho chính mình không mở rộng được gì nên không cần chặn.
    """
    if data.effect != EFFECT_ALLOW or is_system_admin(db, actor.id):
        return
    mine = set(subject_pairs(get_perm_profile(db, actor)))
    if not mine:
        return
    requested = {(s.subject_kind, s.subject_id) for s in data.subjects}
    if mine & requested:
        raise HTTPException(403, SELF_GRANT_MESSAGE)
