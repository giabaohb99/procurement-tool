"""Ai được ĐỌC skill nào (doc 21 §4.2) — hàm duy nhất `visible_skills`, cổng MCP / màn «AI của tôi» đều gọi nó.

Luật:
  1. Skill đọc được khi BỘ của nó đọc được và skill không bị thu hẹp. Skill có dòng quyền RIÊNG (bất kỳ chủ thể nào)
     thì quyền riêng đó THAY quyền bộ — chỉ ai khớp dòng riêng mới đọc.
  2. Chủ thể phòng ban có `include_children` → phòng con (cột `parent`, đi lên tối đa MAX_TREE_DEPTH cấp) cũng nhận.
     Đổi phòng là đổi skill: quyền tính theo hồ sơ LÚC GỌI, không chép vào khóa.
  3. Cấm thắng cho phép — cấm ở bộ cũng chặn skill có dòng cho phép riêng.
  4. Chỉ skill ĐANG DÙNG (có phiên bản xuất bản) trong bộ ĐANG DÙNG mới lộ ra.

Chủ thể: người · phòng ban · pháp nhân · vai trò (`core/subject_match.py`) + chức vụ · cấp bậc (`constants.py`).
"""
from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_perm_profile
from app.core.subject_match import (EFFECT_ALLOW, EFFECT_DENY, SUBJECT_COMPANY, SUBJECT_DEPARTMENT,
                                    SUBJECT_EMPLOYEE, SUBJECT_LABELS, SUBJECT_ROLE, subject_names, subject_pairs,
                                    still_live_condition)

from .constants import (ACCESS_TARGET_LABELS, ENTITY, MAX_TREE_DEPTH, SECURITY_LEVEL_LABELS, SUBJECT_JOB_LEVEL,
                        SUBJECT_POSITION, AccessTarget, SkillSetStatus, SkillStatus)
from .model import AiSkill, AiSkillAccess, AiSkillSet, AiSkillVersion

AUDIT_ACCESS = "ai_skill_access"
EXTRA_SUBJECT_LABELS = {SUBJECT_POSITION: "Chức vụ", SUBJECT_JOB_LEVEL: "Cấp bậc"}


def subject_label(kind: int) -> str:
    return SUBJECT_LABELS.get(kind) or EXTRA_SUBJECT_LABELS.get(kind, "?")


# ---------------------------------------------------------------------------
# Chủ thể của người hỏi
# ---------------------------------------------------------------------------

def _employee_extras(db: Session, employee_id: int) -> tuple[int, int]:
    """(chức vụ, cấp bậc) của nhân sự — 0 khi chưa khai."""
    if not employee_id:
        return 0, 0
    from app.modules.employee.model import Employee

    emp = db.get(Employee, employee_id)
    if emp is None:
        return 0, 0
    return int(emp.position_id or 0), int(emp.job_level or 0)


def department_ancestors(db: Session, dept_ids: list[int]) -> set[int]:
    """Mọi phòng TỔ TIÊN của các phòng đã cho (không gồm chính chúng) — để khớp dòng «kể cả phòng con»."""
    from app.modules.department.model import Department

    out: set[int] = set()
    for start in dept_ids:
        seen = {start}
        dept = db.get(Department, start) if start else None
        for _ in range(MAX_TREE_DEPTH):
            parent = int(getattr(dept, "parent", 0) or 0) if dept is not None else 0
            if not parent or parent in seen:
                break
            seen.add(parent)
            out.add(parent)
            dept = db.get(Department, parent)
    return out


def _match_condition(db: Session, user, profile: dict):
    """Điều kiện SQL: dòng access khớp người hỏi (trước khi xét cấm / cho phép)."""
    pairs = subject_pairs(profile)
    dept_ids = [sid for kind, sid in pairs if kind == SUBJECT_DEPARTMENT]
    ancestors = department_ancestors(db, dept_ids)
    position_id, job_level = _employee_extras(db, int(profile.get("employee_id") or 0))
    conds = []
    for kind, sid in pairs:
        if kind == SUBJECT_DEPARTMENT:
            continue
        conds.append(and_(AiSkillAccess.subject_kind == kind, AiSkillAccess.subject_id == sid))
    if dept_ids:
        conds.append(and_(AiSkillAccess.subject_kind == SUBJECT_DEPARTMENT, AiSkillAccess.subject_id.in_(dept_ids)))
    if ancestors:
        conds.append(and_(AiSkillAccess.subject_kind == SUBJECT_DEPARTMENT, AiSkillAccess.include_children.is_(True),
                          AiSkillAccess.subject_id.in_(ancestors)))
    if position_id:
        conds.append(and_(AiSkillAccess.subject_kind == SUBJECT_POSITION, AiSkillAccess.subject_id == position_id))
    if job_level:
        conds.append(and_(AiSkillAccess.subject_kind == SUBJECT_JOB_LEVEL, AiSkillAccess.subject_id == job_level))
    return or_(*conds) if conds else None


# ---------------------------------------------------------------------------
# Skill người hỏi đọc được
# ---------------------------------------------------------------------------

def visible_skills(db: Session, user, profile: dict | None = None) -> list[dict]:
    """Danh sách skill người này (AI của họ) được đọc — chỉ phiên bản ĐÃ XUẤT BẢN."""
    prof = profile if profile is not None else get_perm_profile(db, user)
    cond = _match_condition(db, user, prof)
    if cond is None:
        return []
    live = still_live_condition(AiSkillAccess)
    mine = db.query(AiSkillAccess.target_kind, AiSkillAccess.target_id, AiSkillAccess.effect).filter(live, cond).all()
    set_allow = {tid for k, tid, e in mine if k == AccessTarget.SKILL_SET and e == EFFECT_ALLOW}
    set_deny = {tid for k, tid, e in mine if k == AccessTarget.SKILL_SET and e == EFFECT_DENY}
    skill_allow = {tid for k, tid, e in mine if k == AccessTarget.SKILL and e == EFFECT_ALLOW}
    skill_deny = {tid for k, tid, e in mine if k == AccessTarget.SKILL and e == EFFECT_DENY}
    #  Skill bị THU HẸP = có ít nhất một dòng quyền riêng còn hiệu lực (của bất kỳ ai).
    narrowed = {tid for (tid,) in db.query(AiSkillAccess.target_id)
                .filter(live, AiSkillAccess.target_kind == AccessTarget.SKILL).distinct()}
    skill_allow_sets = ({sid for (sid,) in db.query(AiSkill.skill_set_id).filter(AiSkill.id.in_(skill_allow))}
                        if skill_allow else set())
    candidate_sets = (set_allow | skill_allow_sets) - set_deny
    if not candidate_sets:
        return []
    sets = {s.id: s for s in db.query(AiSkillSet).filter(
        AiSkillSet.id.in_(candidate_sets), AiSkillSet.is_deleted.is_(False),
        AiSkillSet.status == int(SkillSetStatus.ACTIVE))}
    if not sets:
        return []
    rows = (db.query(AiSkill, AiSkillVersion)
            .join(AiSkillVersion, AiSkillVersion.id == AiSkill.current_version_id)
            .filter(AiSkill.skill_set_id.in_(sets), AiSkill.is_deleted.is_(False),
                    AiSkill.status == int(SkillStatus.ACTIVE))
            .order_by(AiSkill.skill_set_id, AiSkill.sort_order, AiSkill.id).all())
    out = []
    for skill, version in rows:
        if skill.id in skill_deny:
            continue
        ok = (skill.id in skill_allow) if skill.id in narrowed else (skill.skill_set_id in set_allow)
        if not ok:
            continue
        skill_set = sets[skill.skill_set_id]
        out.append({
            "skill_id": skill.id, "slug": skill.slug, "title": version.title or skill.title,
            "summary": version.summary or skill.summary, "version_no": version.version_no,
            "version_id": version.id, "updated_at": version.published_at,
            "skill_set_id": skill_set.id, "skill_set": skill_set.name,
            "security_level": int(skill_set.security_level),
            "security_level_label": SECURITY_LEVEL_LABELS.get(skill_set.security_level, ""),
        })
    return out


def can_read_skill(db: Session, user, skill_id: int, profile: dict | None = None) -> dict | None:
    """Bản tóm tắt skill nếu người này đọc được, không thì None."""
    for row in visible_skills(db, user, profile):
        if row["skill_id"] == skill_id:
            return row
    return None


# ---------------------------------------------------------------------------
# Cấp / thu hồi quyền đọc
# ---------------------------------------------------------------------------

def _subject_exists(db: Session, kind: int, sid: int) -> bool:
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.constants import JOB_LEVEL_LABELS
    from app.modules.employee.model import Employee
    from app.modules.employee.position_model import JobPosition
    from app.modules.role.model import Role

    if kind == SUBJECT_JOB_LEVEL:
        return sid in JOB_LEVEL_LABELS and sid != 0
    model = {SUBJECT_EMPLOYEE: Employee, SUBJECT_DEPARTMENT: Department, SUBJECT_COMPANY: Company,
             SUBJECT_ROLE: Role, SUBJECT_POSITION: JobPosition}.get(kind)
    return model is not None and db.get(model, sid) is not None


def _subject_names(db: Session, rows: list[AiSkillAccess]) -> dict[tuple[int, int], str]:
    from app.modules.employee.constants import JOB_LEVEL_LABELS
    from app.modules.employee.position_model import JobPosition

    names = subject_names(db, [r for r in rows if r.subject_kind in SUBJECT_LABELS])
    pos_ids = {r.subject_id for r in rows if r.subject_kind == SUBJECT_POSITION}
    if pos_ids:
        for p in db.query(JobPosition).filter(JobPosition.id.in_(pos_ids)):
            names[(SUBJECT_POSITION, p.id)] = p.name
    for r in rows:
        if r.subject_kind == SUBJECT_JOB_LEVEL:
            names[(SUBJECT_JOB_LEVEL, r.subject_id)] = JOB_LEVEL_LABELS.get(r.subject_id, str(r.subject_id))
    return names


def serialize_access(row: AiSkillAccess, names: dict) -> dict:
    return {
        "id": row.id, "target_kind": row.target_kind, "target_kind_label": ACCESS_TARGET_LABELS.get(row.target_kind, ""),
        "target_id": row.target_id, "subject_kind": row.subject_kind, "subject_kind_label": subject_label(row.subject_kind),
        "subject_id": row.subject_id, "subject_name": names.get((row.subject_kind, row.subject_id), ""),
        "include_children": bool(row.include_children), "effect": row.effect,
        "effect_label": "Cho phép" if row.effect == EFFECT_ALLOW else "Không cho phép",
        "valid_from": row.valid_from.isoformat() if row.valid_from else None,
        "valid_to": row.valid_to.isoformat() if row.valid_to else None, "reason": row.reason,
    }


def list_access(db: Session, target_kind: int, target_id: int) -> list[dict]:
    rows = (db.query(AiSkillAccess).filter(AiSkillAccess.target_kind == target_kind,
                                           AiSkillAccess.target_id == target_id,
                                           AiSkillAccess.revoked_at.is_(None))
            .order_by(AiSkillAccess.effect, AiSkillAccess.subject_kind, AiSkillAccess.id).all())
    names = _subject_names(db, rows)
    return [serialize_access(r, names) for r in rows]


def grant(db: Session, data, actor) -> dict:
    """Thêm / sửa dòng quyền cho cả lô chủ thể. Trùng (cùng đích, chủ thể, chiều, còn sống) → sửa dòng đó."""
    created = updated = skipped = 0
    seen: set[tuple[int, int]] = set()
    for subject in data.subjects:
        key = (subject.subject_kind, subject.subject_id)
        if key in seen:
            continue
        seen.add(key)
        if not _subject_exists(db, *key):
            skipped += 1
            continue
        if data.effect == EFFECT_DENY and subject.subject_kind == SUBJECT_ROLE:
            from app.modules.role.model import Role

            role = db.get(Role, subject.subject_id)
            if role is not None and role.code in ("admin", "ADMINISTRATOR"):
                raise HTTPException(400, "Không cấm vai trò quản trị — quản trị luôn thấy kho để quản lý")
        row = (db.query(AiSkillAccess).filter(
            AiSkillAccess.target_kind == data.target_kind, AiSkillAccess.target_id == data.target_id,
            AiSkillAccess.subject_kind == key[0], AiSkillAccess.subject_id == key[1],
            AiSkillAccess.effect == data.effect, AiSkillAccess.revoked_at.is_(None)).first())
        if row is None:
            row = AiSkillAccess(target_kind=data.target_kind, target_id=data.target_id, subject_kind=key[0],
                                subject_id=key[1], effect=data.effect, created_by=actor.id)
            db.add(row)
            created += 1
        else:
            updated += 1
        row.include_children = bool(data.include_children)
        row.valid_from, row.valid_to = data.valid_from, data.valid_to
        row.reason = data.reason
        row.updated_by = actor.id
    db.commit()
    record(db, actor.id, AUDIT_ACCESS, int(data.target_id), "update",
           f"{ACCESS_TARGET_LABELS.get(data.target_kind, '')} #{data.target_id}: cấp quyền đọc "
           f"(thêm {created}, sửa {updated}, bỏ qua {skipped})")
    return {"created": created, "updated": updated, "skipped": skipped}


def revoke(db: Session, access_id: int, reason: str, actor) -> AiSkillAccess:
    row = db.get(AiSkillAccess, access_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy dòng phân quyền")
    if row.revoked_at is not None:
        raise HTTPException(400, "Dòng phân quyền này đã thu hồi rồi")
    row.revoked_at = datetime.now()
    row.revoked_by = actor.id
    row.revoke_reason = reason or ""
    row.updated_by = actor.id
    db.commit()
    record(db, actor.id, AUDIT_ACCESS, int(row.target_id), "update",
           f"Thu hồi quyền đọc #{row.id} ({subject_label(row.subject_kind)} {row.subject_id})")
    return row


__all__ = ["visible_skills", "can_read_skill", "grant", "revoke", "list_access", "department_ancestors", "ENTITY"]
