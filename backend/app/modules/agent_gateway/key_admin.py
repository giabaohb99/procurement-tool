"""PHÍA ERP của việc phát / thu hồi khóa kết nối AI HỘ người khác (ai-CR-212, K4 doc/erp/21 §5.3).

Bảng khóa nằm ở DB dịch vụ AI (`tab_agent_mcp_key`), còn ai được phát hộ cho ai thì tính ở ERP: entity
`ai_mcp_key_admin` (read · create · delete), phạm vi đặt trên HỒ SƠ NHÂN SỰ của CHỦ KHÓA (`SCOPE_FIELDS` = pháp nhân +
phòng ban + chính mình, như entity `employee`). Dịch vụ AI hỏi qua cổng B: "trong những người này / phòng này, người phát
được đụng tới ai" — rồi mới phát / liệt kê / thu hồi.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

ENTITY = "ai_mcp_key_admin"
MAX_PEOPLE = 2000


def people_in_scope(db: Session, admin, action: str, *, user_ids: list[int] | None = None, department_id: int = 0,
                    limit: int = MAX_PEOPLE, employee_ids: list[int] | None = None) -> list[dict] | None:
    """Tài khoản ĐANG HOẠT ĐỘNG có hồ sơ nhân sự nằm trong phạm vi `action` của `admin`. None = không có quyền.

    Tài khoản chưa gắn nhân sự không có phòng ban để tính phạm vi → không bao giờ lọt vào (kể cả phạm vi "toàn hệ")."""
    from app.core.auth import get_perm_profile, user_has_permission
    from app.core.scoping import apply_scope
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    if not user_has_permission(db, admin, ENTITY, action):
        return None
    q = (db.query(User.id, Employee.id, Employee.code, Employee.full_name, Employee.department_id, Employee.company_id,
                  User.email)
         .join(Employee, Employee.id == User.employee_id).filter(User.is_active.is_(True), User.employee_id != 0))
    q = apply_scope(q, Employee, ENTITY, admin, get_perm_profile(db, admin), action=action)
    if user_ids is not None:
        ids = {int(i) for i in user_ids if i}
        if not ids:
            return []
        q = q.filter(User.id.in_(ids))
    if employee_ids is not None:
        eids = {int(i) for i in employee_ids if i}
        if not eids:
            return []
        q = q.filter(Employee.id.in_(eids))
    if department_id:
        q = q.filter(Employee.department_id == int(department_id))
    rows = q.order_by(Employee.full_name, User.id).limit(max(1, min(int(limit), MAX_PEOPLE))).all()
    dept_ids = {r[4] for r in rows if r[4]}
    names = {d.id: d.name for d in db.query(Department.id, Department.name).filter(Department.id.in_(dept_ids))} \
        if dept_ids else {}
    #  bao-CR-696: thêm họ tên / mã nhân sự / email riêng — màn Kết nối hiện cột và tìm theo ba thứ này.
    return [{"user_id": int(uid), "employee_id": int(eid), "label": f"{name} ({code})" if code else (name or f"#{uid}"),
             "department_id": int(dept or 0), "department": names.get(dept, ""), "company_id": int(comp or 0),
             "full_name": name or "", "employee_code": code or "", "email": email or ""}
            for uid, eid, code, name, dept, comp, email in rows]


def employee_accounts(db: Session, admin, action: str, employee_ids: list[int]) -> dict | None:
    """ai-CR-215: phát khóa theo HỒ SƠ NHÂN SỰ (màn danh sách nhân sự không có user_id, trưởng phòng thường không có
    `user.read`). Trả `people` (có tài khoản đang hoạt động, trong phạm vi), `no_account` (trong phạm vi nhưng chưa có tài
    khoản / tài khoản đã khóa — kèm lý do) và `outside` (id ngoài phạm vi hoặc không có thật). None = không có quyền."""
    from app.core.auth import get_perm_profile, user_has_permission
    from app.core.scoping import apply_scope
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    if not user_has_permission(db, admin, ENTITY, action):
        return None
    ids = {int(i) for i in employee_ids if i}
    if not ids:
        return {"people": [], "no_account": [], "outside": []}
    q = db.query(Employee.id, Employee.code, Employee.full_name).filter(Employee.id.in_(ids))
    in_scope = {eid: (f"{name} ({code})" if code else (name or f"#{eid}"))
                for eid, code, name in apply_scope(q, Employee, ENTITY, admin, get_perm_profile(db, admin), action=action)}
    people = people_in_scope(db, admin, action, employee_ids=sorted(in_scope)) if in_scope else []
    with_user = {p["employee_id"] for p in people}
    rest = set(in_scope) - with_user
    locked = {int(e) for (e,) in db.query(User.employee_id).filter(User.employee_id.in_(rest))} if rest else set()
    no_account = [{"user_id": 0, "employee_id": eid, "label": in_scope[eid],
                   "reason": "tài khoản ERP đã bị khóa" if eid in locked else "chưa có tài khoản ERP"} for eid in sorted(rest)]
    return {"people": people, "no_account": no_account, "outside": sorted(ids - set(in_scope))}


def skill_stats(db: Session) -> dict:
    """ai-CR-213: số bộ skill / skill ĐANG DÙNG (chưa xóa) cho màn Tổng quan Kho skill AI (G1)."""
    from app.modules.ai_skill.constants import SkillSetStatus, SkillStatus
    from app.modules.ai_skill.model import AiSkill, AiSkillSet

    sets = db.query(AiSkillSet.id).filter(AiSkillSet.status == int(SkillSetStatus.ACTIVE),
                                          AiSkillSet.is_deleted.is_(False)).count()
    skills = (db.query(AiSkill.id).join(AiSkillSet, AiSkillSet.id == AiSkill.skill_set_id)
              .filter(AiSkill.status == int(SkillStatus.ACTIVE), AiSkill.is_deleted.is_(False),
                      AiSkillSet.status == int(SkillSetStatus.ACTIVE), AiSkillSet.is_deleted.is_(False)).count())
    return {"skill_sets": int(sets), "skills": int(skills)}


def notify(db: Session, user_ids: list[int], *, title: str, body: str, link: str, by_user_id: int = 0) -> int:
    """Chuông ERP cho từng người (không email, không Telegram — doc 21 §7.1)."""
    from app.modules.notification.model import Notification

    n = 0
    for uid in {int(i) for i in user_ids if i}:
        db.add(Notification(user_id=uid, title=title[:255], body=body, link=link[:500], created_by=int(by_user_id or 0)))
        n += 1
    if n:
        db.commit()
    return n
