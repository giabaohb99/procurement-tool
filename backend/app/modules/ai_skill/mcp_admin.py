"""Quản trị Kho skill BẰNG LỜI qua cổng MCP (bao-CR-634, K9 — doc/erp/21 §7.2 đợt P7).

AI riêng của người quản trị (khóa MCP «được ghi») soạn / xuất bản skill và gán / thu hồi quyền đọc theo đúng khuôn
NHÁP → XÁC NHẬN của cổng:
  1. tool `draft_skill` · `draft_skill_publish` · `draft_skill_access` KHÔNG ghi gì — trả bản xem trước cho người dùng
     đọc + một `token` (Fernet, hết hạn TOKEN_TTL, buộc vào đúng người và đúng loại việc, mang DẤU TRẠNG THÁI của đích
     lúc soạn);
  2. `confirm_draft` với đúng bản nháp đó mới ghi — và ghi qua ĐÚNG service của màn web (`service.*`,
     `access_service.grant/revoke`) nên phạm vi quản trị (`get_scoped` của bộ) + luật cấm thắng + nhật ký giữ nguyên.
     Token chỉ là «tờ đề xuất có hạn dùng», không phải giấy thông hành: quyền / phạm vi kiểm LẠI lúc xác nhận; đích đã
     đổi sau lúc soạn (dấu lệch) → từ chối, nhờ soạn lại; xác nhận lần hai cùng bản nháp cũng lệch dấu → từ chối.
Mọi lượt ghi vào sổ thay đổi của Trợ lý (`assistant/change_service`, kênh MCP) — tạo / sửa skill và gán / thu hồi quyền
hoàn tác được trong 24 giờ (`undo_check` / `undo_apply` ở cuối tệp); xuất bản chỉ ghi sổ (phiên bản chỉ thêm).

Chạy ở ERP: chế độ nhúng gọi thẳng, chế độ tách dịch vụ đi qua cổng B `/api/agent-gw/skills/admin/*`.
"""
from __future__ import annotations

import base64
import difflib
import hashlib
import json
from datetime import date, datetime

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func

from app.core.auth import get_perm_profile
from app.core.config import settings
from app.core.scoping import apply_scope
from app.core.subject_match import (EFFECT_ALLOW, EFFECT_DENY, SUBJECT_COMPANY, SUBJECT_DEPARTMENT, SUBJECT_EMPLOYEE,
                                    SUBJECT_ROLE)

from . import access_service, service
from .constants import ENTITY, SUBJECT_JOB_LEVEL, SUBJECT_POSITION, AccessTarget
from .model import AiSkill, AiSkillAccess, AiSkillSet, AiSkillVersion
from .schema import AccessGrantIn, SkillIn, SkillPatch

TOKEN_TTL = 30 * 60
KINDS = ("skill", "skill_publish", "skill_access")
#  Thực thể trong sổ thay đổi: skill (tạo / sửa) và dòng quyền đọc (gán / thu hồi — mã đích là BỘ chứa).
CHANGE_SKILL = "ai_skill"
CHANGE_ACCESS = "ai_skill_access"
SUBJECT_KEYS = {"employee": SUBJECT_EMPLOYEE, "department": SUBJECT_DEPARTMENT, "company": SUBJECT_COMPANY,
                "role": SUBJECT_ROLE, "position": SUBJECT_POSITION, "job_level": SUBJECT_JOB_LEVEL}
SUBJECT_WORDS = {SUBJECT_EMPLOYEE: "nhân sự", SUBJECT_DEPARTMENT: "phòng ban", SUBJECT_COMPANY: "pháp nhân",
                 SUBJECT_ROLE: "vai trò", SUBJECT_POSITION: "chức vụ", SUBJECT_JOB_LEVEL: "cấp bậc"}
MAX_CANDIDATES = 8
MAX_DIFF_LINES = 80
PREVIEW_CHARS = 600
CONFIRM_HINT = ("Chưa ghi gì. Đưa bản xem trước cho người dùng đọc; họ đồng ý thì gọi confirm_draft với kind=\"{kind}\" "
                "và đúng object `draft` này. Bản nháp hết hạn sau 30 phút.")


class AdminError(Exception):
    """Lỗi nói được cho AI / người dùng — trả `{"error": ...}`, không ném ra cổng."""


def _to_iso(value):
    return value.isoformat(timespec="seconds") if value else None


# ---------------------------------------------------------------------------
# Token bản nháp
# ---------------------------------------------------------------------------

def _make_fernet() -> Fernet:
    #  Khóa riêng của việc này (tiền tố khác) — token sửa phiếu của Trợ lý không dùng lẫn sang đây được.
    seed = f"ai-skill-mcp-admin|{settings.JWT_SECRET}".encode()
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(seed).digest()))


def _seal(user, kind: str, payload: dict) -> str:
    raw = json.dumps({"u": int(user.id), "k": kind, "p": payload}, ensure_ascii=False, default=str)
    return _make_fernet().encrypt(raw.encode()).decode()


def _open(user, kind: str, draft) -> dict:
    token = draft.get("token") if isinstance(draft, dict) else None
    if not isinstance(token, str) or not token:
        raise AdminError("Thiếu bản nháp: gọi tool draft_* trước, đưa người dùng xem, rồi mới xác nhận đúng bản nháp đó.")
    try:
        data = json.loads(_make_fernet().decrypt(token.encode(), ttl=TOKEN_TTL))
    except (InvalidToken, ValueError, TypeError):
        raise AdminError("Bản nháp đã hết hạn hoặc không hợp lệ — soạn lại bản nháp mới.") from None
    if not isinstance(data, dict) or data.get("u") != int(user.id):
        raise AdminError("Bản nháp này không phải của bạn.")
    if data.get("k") != kind:
        raise AdminError(f"Bản nháp này là loại «{data.get('k')}», không phải «{kind}».")
    return data.get("p") or {}


def _hash_value(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:40]


def sign_skill_state(skill: AiSkill) -> str:
    """Dấu skill: mọi thứ AI soạn được + bản hiện hành + cờ xóa. Lệch = có người sửa sau lúc soạn nháp."""
    return _hash_value([skill.title, skill.summary, skill.draft_body_md or "", skill.current_version_id, skill.status,
                    bool(skill.is_deleted), _to_iso(skill.draft_updated_at)])


def _load_live_rows(db, target_kind: int, target_id: int) -> list[AiSkillAccess]:
    return (db.query(AiSkillAccess).filter(AiSkillAccess.target_kind == target_kind,
                                           AiSkillAccess.target_id == target_id, AiSkillAccess.revoked_at.is_(None))
            .order_by(AiSkillAccess.id).all())


def sign_access_state(db, target_kind: int, target_id: int) -> str:
    return _hash_value([[r.id, r.subject_kind, r.subject_id, r.effect, bool(r.include_children), _to_iso(r.valid_from),
                     _to_iso(r.valid_to), r.reason] for r in _load_live_rows(db, target_kind, target_id)])


# ---------------------------------------------------------------------------
# Tìm bộ / skill / chủ thể theo chữ AI gửi
# ---------------------------------------------------------------------------

def _list_sets(db, user, action: str) -> list[AiSkillSet]:
    profile = get_perm_profile(db, user)
    return (apply_scope(db.query(AiSkillSet), AiSkillSet, ENTITY, user, profile, action=action)
            .order_by(AiSkillSet.sort_order, AiSkillSet.id).all())


def _describe_sets(rows: list[AiSkillSet]) -> str:
    return "; ".join(f"{s.code} — {s.name}" for s in rows[:20]) or "(không có bộ nào)"


def _find_set(db, user, ref, action: str) -> AiSkillSet:
    rows = _list_sets(db, user, action)
    text = str(ref or "").strip()
    if not text:
        raise AdminError(f"Thiếu `skill_set` (mã hoặc tên bộ). Bộ bạn được quản lý: {_describe_sets(rows)}.")
    low = text.lower()
    hit = [s for s in rows if (s.code or "").lower() == low] or [s for s in rows if (s.name or "").lower() == low]
    if not hit:
        hit = [s for s in rows if low in (s.name or "").lower()]
    if len(hit) == 1:
        return hit[0]
    if len(hit) > 1:
        raise AdminError(f"«{text}» khớp nhiều bộ: {_describe_sets(hit)} — gửi đúng mã bộ.")
    raise AdminError(f"Không thấy bộ «{text}» trong những bộ bạn được quản lý: {_describe_sets(rows)}.")


def _split_name(name: str) -> tuple[str, str]:
    """`MÃ-BỘ/slug` → (mã bộ, slug); `slug` → ("", slug)."""
    name = (name or "").strip()
    if "/" in name:
        code, _, slug = name.partition("/")
        return code.strip(), slug.strip()
    return "", name


def _find_skill(db, user, name, set_ref, action: str) -> tuple[AiSkill, AiSkillSet]:
    code, slug = _split_name(str(name or ""))
    if not slug:
        raise AdminError("Thiếu `name` của skill (tên gọi, vd quy-trinh-mua hoặc MÃ-BỘ/quy-trinh-mua).")
    if code or set_ref:
        sets = [_find_set(db, user, code or set_ref, action)]
    else:
        sets = _list_sets(db, user, action)
    hits = [(k, s) for s in sets for k in db.query(AiSkill).filter(
        AiSkill.skill_set_id == s.id, func.lower(AiSkill.slug) == slug.lower(), AiSkill.is_deleted.is_(False))]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        raise AdminError(f"Skill «{slug}» có ở nhiều bộ: {', '.join(f'{s.code}/{k.slug}' for k, s in hits)} — gửi "
                         "dạng MÃ-BỘ/tên.")
    raise AdminError(f"Không thấy skill «{name}» trong những bộ bạn được quản lý.")


def _pick_subject_model(db, kind: int):
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.employee.position_model import JobPosition
    from app.modules.role.model import Role

    model, name_col = {SUBJECT_EMPLOYEE: (Employee, Employee.full_name), SUBJECT_DEPARTMENT: (Department, Department.name),
                       SUBJECT_COMPANY: (Company, Company.name), SUBJECT_ROLE: (Role, Role.name),
                       SUBJECT_POSITION: (JobPosition, JobPosition.name)}[kind]
    return model, name_col


def _label_subject(kind: int, row) -> str:
    if kind == SUBJECT_EMPLOYEE:
        return f"{row.full_name} ({row.code})" if row.code else str(row.full_name)
    code = getattr(row, "code", "") or ""
    return f"{row.name} ({code})" if code else str(row.name)


def resolve_subject(db, spec) -> tuple[int, int, str]:
    """{kind, ref | id} → (loại, id, nhãn). `ref` khớp MÃ trước, rồi TÊN đúng, rồi tên chứa chữ (chỉ khi một kết quả)."""
    if not isinstance(spec, dict):
        raise AdminError("Mỗi đối tượng là {kind, ref} — kind: employee/department/company/role/position/job_level.")
    kind = SUBJECT_KEYS.get(str(spec.get("kind") or "").strip().lower())
    if kind is None:
        raise AdminError(f"Loại đối tượng «{spec.get('kind')}» không có — chọn: {', '.join(SUBJECT_KEYS)}.")
    ref = str(spec.get("ref") or "").strip()
    sid = spec.get("id")
    if kind == SUBJECT_JOB_LEVEL:
        from app.modules.employee.constants import JOB_LEVEL_LABELS

        for level, label in JOB_LEVEL_LABELS.items():
            if level and ((sid is not None and str(sid) == str(level)) or (ref and ref.lower() == label.lower())):
                return kind, int(level), label
        raise AdminError(f"Không có cấp bậc «{ref or sid}» — chọn: "
                         f"{', '.join(v for k, v in JOB_LEVEL_LABELS.items() if k)}.")
    model, name_col = _pick_subject_model(db, kind)
    if sid is not None and str(sid).isdigit():
        row = db.get(model, int(sid))
        if row is None:
            raise AdminError(f"Không có {SUBJECT_WORDS[kind]} mã số {sid}.")
        return kind, int(row.id), _label_subject(kind, row)
    if not ref:
        raise AdminError(f"Thiếu `ref` (mã hoặc tên {SUBJECT_WORDS[kind]}).")
    low = ref.lower()
    hit = db.query(model).filter(func.lower(model.code) == low).all()
    if not hit:
        hit = db.query(model).filter(func.lower(name_col) == low).limit(MAX_CANDIDATES + 1).all()
    if not hit:
        hit = db.query(model).filter(func.lower(name_col).contains(low)).limit(MAX_CANDIDATES + 1).all()
    if len(hit) == 1:
        return kind, int(hit[0].id), _label_subject(kind, hit[0])
    if hit:
        raise AdminError(f"«{ref}» khớp nhiều {SUBJECT_WORDS[kind]}: "
                         f"{'; '.join(_label_subject(kind, r) for r in hit[:MAX_CANDIDATES])} — gửi đúng mã.")
    raise AdminError(f"Không thấy {SUBJECT_WORDS[kind]} «{ref}».")


def resolve_people(db, user, employees: list, department) -> dict:
    """Cho tool phát / thu hồi khóa hộ (dịch vụ AI): mã / tên nhân sự + tên phòng → id. PHẠM VI phát khóa không xét ở đây
    — dịch vụ AI hỏi lại `key_admin_employees` / `key_admin_people` như màn web."""
    try:
        ids, labels = [], []
        for ref in employees or []:
            spec = ref if isinstance(ref, dict) else {"ref": str(ref)}
            _, sid, label = resolve_subject(db, {**spec, "kind": "employee"})
            if sid not in ids:
                ids.append(sid)
                labels.append(label)
        dept_id, dept_label = 0, ""
        if department:
            spec = department if isinstance(department, dict) else {"ref": str(department)}
            _, dept_id, dept_label = resolve_subject(db, {**spec, "kind": "department"})
    except AdminError as e:
        return {"error": str(e)}
    return {"employee_ids": ids, "employee_labels": labels, "department_id": dept_id, "department_label": dept_label}


# ---------------------------------------------------------------------------
# Bước 1 — soạn nháp (không ghi)
# ---------------------------------------------------------------------------

def _clip(text: str, n: int = PREVIEW_CHARS) -> str:
    text = text or ""
    return text if len(text) <= n else text[:n] + f"… (+{len(text) - n} ký tự)"


def _diff_body(old: str, new: str) -> dict:
    lines = list(difflib.unified_diff((old or "").splitlines(), (new or "").splitlines(), "trước", "sau", lineterm="", n=1))
    added = sum(1 for ln in lines if ln.startswith("+") and not ln.startswith("+++"))
    removed = sum(1 for ln in lines if ln.startswith("-") and not ln.startswith("---"))
    out = {"added_lines": added, "removed_lines": removed, "diff": "\n".join(lines[:MAX_DIFF_LINES])}
    if len(lines) > MAX_DIFF_LINES:
        out["diff_truncated"] = True
    return out


def _draft_skill(db, user, args: dict) -> dict:
    name = str(args.get("name") or "").strip()
    code, slug = _split_name(name)
    if not code and not str(args.get("skill_set") or "").strip():
        #  Chỉ có tên: sửa skill đã có nếu tên đó là duy nhất trong các bộ mình quản lý; tạo mới thì phải nói bộ nào.
        try:
            _, skill_set = _find_skill(db, user, slug, None, "write")
        except AdminError as e:
            raise AdminError(f"{e} Tạo skill mới thì gửi kèm `skill_set` (mã hoặc tên bộ).") from None
    else:
        skill_set = _find_set(db, user, code or args.get("skill_set"), "write")
    fields = {k: args[k] for k in ("title", "summary", "body_md") if isinstance(args.get(k), str)}
    existing = (db.query(AiSkill).filter(AiSkill.skill_set_id == skill_set.id, func.lower(AiSkill.slug) == slug.lower(),
                                         AiSkill.is_deleted.is_(False)).first()) if slug else None
    if existing is None:
        try:
            data = SkillIn(slug=slug, **fields)
        except ValidationError as e:
            raise AdminError(f"Bản nháp chưa hợp lệ: {e.errors()[0].get('msg', '')}") from None
        payload = {"mode": "create", "set_id": skill_set.id, "data": data.model_dump()}
        preview = {"việc": "Tạo skill mới (bản nháp, CHƯA xuất bản)", "bộ": f"{skill_set.code} — {skill_set.name}",
                   "tên gọi": data.slug, "tiêu đề": data.title or data.slug, "tóm tắt cho AI": data.summary,
                   "nội dung": _clip(data.body_md)}
        summary = f"Tạo skill {skill_set.code}/{data.slug}"
    else:
        current = {"title": existing.title or "", "summary": existing.summary or "", "body_md": existing.draft_body_md or ""}
        changes = {k: v for k, v in fields.items() if v != current[k]}
        if not changes:
            raise AdminError(f"Skill {skill_set.code}/{existing.slug} đã đúng như vậy — không có gì để sửa.")
        try:
            SkillPatch(**changes)
        except ValidationError as e:
            raise AdminError(f"Bản nháp chưa hợp lệ: {e.errors()[0].get('msg', '')}") from None
        payload = {"mode": "update", "skill_id": existing.id, "changes": changes, "sig": sign_skill_state(existing)}
        preview = {"việc": "Sửa bản nháp skill (bản AI đang đọc chỉ đổi khi XUẤT BẢN)",
                   "skill": f"{skill_set.code}/{existing.slug}"}
        for key, label in (("title", "tiêu đề"), ("summary", "tóm tắt cho AI")):
            if key in changes:
                preview[label] = {"trước": getattr(existing, key) or "", "sau": changes[key]}
        if "body_md" in changes:
            preview["nội dung"] = _diff_body(existing.draft_body_md or "", changes["body_md"])
        summary = f"Sửa nháp skill {skill_set.code}/{existing.slug}: {', '.join(changes)}"
    out = {"kind": "skill", "preview": preview, "draft": {"token": _seal(user, "skill", payload), "summary": summary},
           "note": CONFIRM_HINT.format(kind="skill")}
    if existing is not None:
        out["skill_id"] = existing.id          # nhật ký MCP ghi skill nào bị đụng (cổng bóc khóa này khỏi câu trả lời)
    return out


def _draft_publish(db, user, args: dict) -> dict:
    skill, skill_set = _find_skill(db, user, args.get("name"), args.get("skill_set"), "approve")
    body = (skill.draft_body_md or "").strip()
    if not body:
        raise AdminError("Nội dung skill đang trống — soạn nội dung (draft_skill) rồi mới xuất bản.")
    if not (skill.summary or "").strip():
        raise AdminError("Thiếu tóm tắt cho AI — AI chọn skill bằng chính câu này; thêm bằng draft_skill rồi xuất bản.")
    current = db.get(AiSkillVersion, skill.current_version_id) if skill.current_version_id else None
    if current is not None and (current.body_md or "") == (skill.draft_body_md or "") \
            and (current.summary or "") == (skill.summary or "") and (current.title or "") == (skill.title or ""):
        raise AdminError(f"Bản nháp của {skill_set.code}/{skill.slug} giống hệt phiên bản {current.version_no} đang dùng "
                         "— không có gì để xuất bản.")
    note = str(args.get("change_note") or "").strip()[:500]
    payload = {"skill_id": skill.id, "change_note": note, "sig": sign_skill_state(skill)}
    preview = {"việc": "Xuất bản skill — AI của mọi người được đọc sẽ dùng bản này từ lượt gọi sau",
               "skill": f"{skill_set.code}/{skill.slug}",
               "phiên bản": f"{(current.version_no if current else 0)} → {(current.version_no if current else 0) + 1}",
               "ghi chú": note or "(không có)", "so với bản đang dùng": _diff_body(current.body_md if current else "",
                                                                                  skill.draft_body_md or "")}
    summary = f"Xuất bản skill {skill_set.code}/{skill.slug}"
    return {"kind": "skill_publish", "preview": preview, "skill_id": skill.id,
            "draft": {"token": _seal(user, "skill_publish", payload), "summary": summary},
            "note": CONFIRM_HINT.format(kind="skill_publish")}


def _resolve_target(db, user, args: dict, action: str) -> tuple[int, int, str, AiSkillSet]:
    """(loại đích, id đích, nhãn, bộ chứa) — có `name` thì đích là SKILL, không thì là BỘ."""
    if str(args.get("name") or "").strip():
        skill, skill_set = _find_skill(db, user, args.get("name"), args.get("skill_set"), action)
        return int(AccessTarget.SKILL), skill.id, f"skill {skill_set.code}/{skill.slug}", skill_set
    skill_set = _find_set(db, user, args.get("skill_set"), action)
    return int(AccessTarget.SKILL_SET), skill_set.id, f"bộ {skill_set.code} — {skill_set.name}", skill_set


def _draft_access(db, user, args: dict) -> dict:
    op = str(args.get("action") or "grant").strip().lower()
    if op not in ("grant", "revoke"):
        raise AdminError("`action` chỉ nhận grant (gán quyền đọc) hoặc revoke (thu hồi).")
    target_kind, target_id, target_label, skill_set = _resolve_target(db, user, args, "write")
    raw = args.get("subjects")
    if not isinstance(raw, list) or not raw:
        raise AdminError("Thiếu `subjects` — danh sách {kind, ref} người / phòng / pháp nhân / vai trò / chức vụ / cấp bậc.")
    subjects = [resolve_subject(db, s) for s in raw[:200]]
    effect_word = str(args.get("effect") or "allow").strip().lower()
    if effect_word not in ("allow", "deny"):
        raise AdminError("`effect` chỉ nhận allow (cho phép) hoặc deny (không cho phép).")
    effect = EFFECT_ALLOW if effect_word == "allow" else EFFECT_DENY
    sig = sign_access_state(db, target_kind, target_id)
    if op == "revoke":
        wanted = {(k, i) for k, i, _ in subjects}
        rows = [r for r in _load_live_rows(db, target_kind, target_id) if (r.subject_kind, r.subject_id) in wanted
                and (args.get("effect") is None or r.effect == effect)]
        if not rows:
            raise AdminError(f"{target_label[0].upper()}{target_label[1:]} không có dòng quyền đang hiệu lực nào khớp các "
                             "đối tượng này.")
        names = {(k, i): label for k, i, label in subjects}
        payload = {"op": "revoke", "target_kind": target_kind, "target_id": target_id, "set_id": skill_set.id,
                   "ids": [r.id for r in rows], "reason": str(args.get("reason") or "")[:500], "sig": sig}
        preview = {"việc": f"THU HỒI quyền đọc trên {target_label}",
                   "dòng sẽ thu hồi": [f"{'Cho phép' if r.effect == EFFECT_ALLOW else 'Không cho phép'}: "
                                       f"{names.get((r.subject_kind, r.subject_id), r.subject_id)}" for r in rows]}
        summary = f"Thu hồi {len(rows)} dòng quyền đọc trên {target_label}"
    else:
        valid_to = args.get("valid_to")
        try:
            data = AccessGrantIn(target_kind=target_kind, target_id=target_id, effect=effect,
                                 subjects=[{"subject_kind": k, "subject_id": i} for k, i, _ in subjects],
                                 include_children=bool(args.get("include_children", True)),
                                 reason=str(args.get("reason") or "")[:500],
                                 valid_to=date.fromisoformat(str(valid_to)) if valid_to else None)
        except (ValidationError, ValueError) as e:
            msg = e.errors()[0].get("msg", "") if isinstance(e, ValidationError) else "valid_to phải dạng YYYY-MM-DD"
            raise AdminError(f"Bản nháp chưa hợp lệ: {msg}") from None
        payload = {"op": "grant", "set_id": skill_set.id, "data": data.model_dump(mode="json"), "sig": sig}
        preview = {"việc": f"{'GÁN' if effect == EFFECT_ALLOW else 'CẤM'} quyền đọc trên {target_label}",
                   "đối tượng": [label for _, _, label in subjects],
                   "kể cả phòng con": data.include_children, "hết hạn": _to_iso(data.valid_to) or "không",
                   "lưu ý": ("Không cho phép THẮNG cho phép: người bị cấm không đọc được kể cả khi phòng của họ được gán."
                             if effect == EFFECT_DENY else
                             "Skill có dòng quyền riêng thì quyền riêng THAY quyền của bộ.")}
        summary = f"{'Gán' if effect == EFFECT_ALLOW else 'Cấm'} quyền đọc {target_label} cho {len(subjects)} đối tượng"
    return {"kind": "skill_access", "preview": preview,
            "draft": {"token": _seal(user, "skill_access", payload), "summary": summary},
            "note": CONFIRM_HINT.format(kind="skill_access")}


DRAFTERS = {"draft_skill": _draft_skill, "draft_skill_publish": _draft_publish, "draft_skill_access": _draft_access}


def draft(db, user, tool: str, args: dict) -> dict:
    fn = DRAFTERS.get(tool)
    if fn is None:
        return {"error": f"Không có công cụ {tool}."}
    try:
        return fn(db, user, args or {})
    except AdminError as e:
        return {"error": str(e)}
    except HTTPException as e:
        return {"error": str(e.detail)}


# ---------------------------------------------------------------------------
# Bước 2 — xác nhận (ghi qua service của màn web + sổ thay đổi)
# ---------------------------------------------------------------------------

def _build_stale_error(what: str) -> AdminError:
    return AdminError(f"{what} đã đổi sau lúc soạn bản nháp (hoặc bản nháp này đã dùng rồi) — soạn lại bản nháp mới.")


def _link_skill(skill_id: int) -> str:
    return f"/ai-skill/skills/{skill_id}"


def _record_change(db, user, **kw) -> None:
    from app.modules.assistant import change_service
    from app.modules.assistant.change_model import ChangeSource

    change_service.record_change(db, user, source=int(ChangeSource.MCP), **kw)


def _confirm_skill(db, user, p: dict) -> dict:
    from app.modules.assistant.change_model import ChangeAction

    if p.get("mode") == "create":
        skill = service.create_skill(db, int(p.get("set_id") or 0), SkillIn(**(p.get("data") or {})), user)
        skill_set = db.get(AiSkillSet, skill.skill_set_id)
        code = f"{skill_set.code}/{skill.slug}"
        _record_change(db, user, entity=CHANGE_SKILL, entity_id=skill.id, doc_code=code, action=ChangeAction.CREATE,
                summary=f"Tạo skill {code} qua AI riêng", before=None, after=_read_skill_fields(skill),
                after_sig=sign_skill_state(skill))
        return {"ok": True, "message": f"Đã tạo skill {code} (bản nháp — xuất bản thì AI mới đọc được).",
                "link": _link_skill(skill.id), "skill_id": skill.id}
    skill, skill_set = service._skill_or_404(db, int(p.get("skill_id") or 0), user, "write")
    if sign_skill_state(skill) != p.get("sig"):
        raise _build_stale_error(f"Skill {skill_set.code}/{skill.slug}")
    changes = dict(p.get("changes") or {})
    before = _read_skill_fields(skill, list(changes))
    service.update_skill(db, skill.id, SkillPatch(**changes), user)
    db.refresh(skill)
    code = f"{skill_set.code}/{skill.slug}"
    _record_change(db, user, entity=CHANGE_SKILL, entity_id=skill.id, doc_code=code, action=ChangeAction.UPDATE,
            summary=f"Sửa nháp skill {code}: {', '.join(changes)}", before=before,
            after=_read_skill_fields(skill, list(changes)), after_sig=sign_skill_state(skill))
    return {"ok": True, "message": f"Đã sửa bản nháp skill {code} — xuất bản thì AI mới đọc bản mới.",
            "link": _link_skill(skill.id), "skill_id": skill.id}


def _confirm_publish(db, user, p: dict) -> dict:
    from app.modules.assistant.change_model import ChangeAction

    skill, skill_set = service._skill_or_404(db, int(p.get("skill_id") or 0), user, "approve")
    if sign_skill_state(skill) != p.get("sig"):
        raise _build_stale_error(f"Skill {skill_set.code}/{skill.slug}")
    version = service.publish_skill(db, skill.id, str(p.get("change_note") or ""), user)
    db.refresh(skill)
    code = f"{skill_set.code}/{skill.slug}"
    _record_change(db, user, entity=CHANGE_SKILL, entity_id=skill.id, doc_code=code, action=ChangeAction.PUBLISH,
            summary=f"Xuất bản skill {code} phiên bản {version.version_no}", before=None,
            after={"version_no": version.version_no}, after_sig=sign_skill_state(skill))
    return {"ok": True, "message": f"Đã xuất bản {code} phiên bản {version.version_no}.", "link": _link_skill(skill.id),
            "skill_id": skill.id}


def _check_target(db, user, target_kind: int, target_id: int, action: str) -> AiSkillSet:
    if target_kind == AccessTarget.SKILL_SET:
        return service._set_or_404(db, target_id, user, action)
    _, skill_set = service._skill_or_404(db, target_id, user, action)
    return skill_set


def _read_access_fields(row: AiSkillAccess) -> dict:
    return {"include_children": bool(row.include_children), "valid_from": _to_iso(row.valid_from),
            "valid_to": _to_iso(row.valid_to), "reason": row.reason or ""}


def _confirm_access(db, user, p: dict) -> dict:
    from app.modules.assistant.change_model import ChangeAction

    if p.get("op") == "revoke":
        target_kind, target_id = int(p.get("target_kind") or 0), int(p.get("target_id") or 0)
    else:
        data = AccessGrantIn(**(p.get("data") or {}))
        target_kind, target_id = data.target_kind, data.target_id
    skill_set = _check_target(db, user, target_kind, target_id, "write")
    if sign_access_state(db, target_kind, target_id) != p.get("sig"):
        raise _build_stale_error("Danh sách quyền đọc")
    label = (f"bộ {skill_set.code}" if target_kind == AccessTarget.SKILL_SET
             else f"skill #{target_id} của bộ {skill_set.code}")
    if p.get("op") == "revoke":
        ids = [int(i) for i in p.get("ids") or []]
        for access_id in ids:
            access_service.revoke(db, access_id, str(p.get("reason") or "Thu hồi qua AI riêng"), user)
        _record_change(db, user, entity=CHANGE_ACCESS, entity_id=skill_set.id, doc_code=skill_set.code,
                action=ChangeAction.DELETE, summary=f"Thu hồi {len(ids)} dòng quyền đọc trên {label}", before=None,
                after={"target_kind": target_kind, "target_id": target_id, "revoked": ids},
                after_sig=sign_access_state(db, target_kind, target_id))
        return {"ok": True, "message": f"Đã thu hồi {len(ids)} dòng quyền đọc.",
                "link": f"/ai-skill/sets/{skill_set.id}?tab=access"}
    before_rows = {r.id: _read_access_fields(r) for r in _load_live_rows(db, target_kind, target_id)}
    result = access_service.grant(db, data, user)
    after_rows = _load_live_rows(db, target_kind, target_id)
    created = [r.id for r in after_rows if r.id not in before_rows]
    touched = {r.id: before_rows[r.id] for r in after_rows if r.id in before_rows and _read_access_fields(r) != before_rows[r.id]}
    _record_change(db, user, entity=CHANGE_ACCESS, entity_id=skill_set.id, doc_code=skill_set.code, action=ChangeAction.CREATE,
            summary=f"Gán quyền đọc {label}: thêm {result['created']}, sửa {result['updated']}", before=None,
            after={"target_kind": target_kind, "target_id": target_id, "created": created, "updated": touched},
            after_sig=sign_access_state(db, target_kind, target_id))
    skipped = f", bỏ qua {result['skipped']} đối tượng không còn" if result["skipped"] else ""
    return {"ok": True, "message": f"Đã lưu quyền đọc: thêm {result['created']}, sửa {result['updated']}{skipped}.",
            "link": f"/ai-skill/sets/{skill_set.id}?tab=access"}


CONFIRMERS = {"skill": _confirm_skill, "skill_publish": _confirm_publish, "skill_access": _confirm_access}


def confirm(db, user, kind: str, draft_obj) -> dict:
    fn = CONFIRMERS.get(kind)
    if fn is None:
        return {"error": f"Không có loại bản nháp «{kind}»."}
    try:
        return fn(db, user, _open(user, kind, draft_obj))
    except AdminError as e:
        db.rollback()
        return {"error": str(e)}
    except HTTPException as e:
        db.rollback()
        return {"error": str(e.detail), **({"denied": True} if e.status_code in (403, 404) else {})}
    except ValidationError as e:
        db.rollback()
        return {"error": f"Bản nháp không hợp lệ: {e.errors()[0].get('msg', '')}"}


# ---------------------------------------------------------------------------
# Hoàn tác 24 giờ — `assistant/change_service.undo` gọi sang đây cho hai thực thể của kho skill
# ---------------------------------------------------------------------------

def _read_skill_fields(skill: AiSkill, keys: list[str] | None = None) -> dict:
    full = {"title": skill.title or "", "summary": skill.summary or "", "body_md": skill.draft_body_md or ""}
    return {"fields": {k: v for k, v in full.items() if keys is None or k in keys}}


def _load_undo_target(db, user, row, action):
    """Trả (đích, câu lỗi). Đích: skill (CHANGE_SKILL) hoặc (loại, id) đích quyền (CHANGE_ACCESS)."""
    from app.modules.assistant.change_model import ChangeAction

    if row.entity == CHANGE_SKILL:
        need = "delete" if action == ChangeAction.CREATE else "write"
        try:
            skill, _ = service._skill_or_404(db, int(row.entity_id or 0), user, need)
        except HTTPException:
            return None, "Skill không còn, hoặc nằm ngoài phạm vi bạn được quản lý."
        if action == ChangeAction.CREATE and skill.current_version_id:
            return None, "Skill đã được xuất bản — không hoàn tác việc tạo; muốn bỏ thì xóa tay ở màn Kho skill AI."
        if sign_skill_state(skill) != (row.after_sig or ""):
            return None, "Skill đã được sửa sau lúc AI ghi — không hoàn tác tự động, mở màn Soạn skill sửa tay."
        return skill, ""
    after = row.after or {}
    target = (int(after.get("target_kind") or 0), int(after.get("target_id") or 0))
    try:
        _check_target(db, user, *target, "write")
    except HTTPException:
        return None, "Bộ / skill không còn, hoặc nằm ngoài phạm vi bạn được quản lý."
    if sign_access_state(db, *target) != (row.after_sig or ""):
        return None, "Quyền đọc đã đổi sau lúc AI ghi — không hoàn tác tự động, sửa tay ở tab Ai được đọc."
    return target, ""


def undo_check(db, user, row, action) -> str:
    """Câu lỗi nếu không hoàn tác được ("" = được)."""
    _, err = _load_undo_target(db, user, row, action)
    return err


def undo_apply(db, user, row, action) -> str:
    """Làm ngược qua đúng service; trả dấu mới của đích (ghi vào dòng sổ ngược)."""
    from app.modules.assistant.change_model import ChangeAction

    target, err = _load_undo_target(db, user, row, action)
    if err:
        raise HTTPException(409, err)
    if row.entity == CHANGE_SKILL:
        if action == ChangeAction.CREATE:
            service.delete_skill(db, target.id, user)
            return ""
        fields = dict((row.before or {}).get("fields") or {})
        if not fields:
            raise HTTPException(409, "Dòng sổ này không có ảnh trước để ghi lại.")
        service.update_skill(db, target.id, SkillPatch(**fields), user)
        db.refresh(target)
        return sign_skill_state(target)
    after = row.after or {}
    now = datetime.now()
    if action == ChangeAction.CREATE:
        for access_id in after.get("created") or []:
            access = db.get(AiSkillAccess, int(access_id))
            if access is not None and access.revoked_at is None:
                access.revoked_at, access.revoked_by = now, user.id
                access.revoke_reason, access.updated_by = "Hoàn tác gán quyền qua AI riêng", user.id
        for access_id, fields in (after.get("updated") or {}).items():
            access = db.get(AiSkillAccess, int(access_id))
            if access is not None:
                access.include_children = bool(fields.get("include_children"))
                access.valid_from = date.fromisoformat(fields["valid_from"]) if fields.get("valid_from") else None
                access.valid_to = date.fromisoformat(fields["valid_to"]) if fields.get("valid_to") else None
                access.reason, access.updated_by = fields.get("reason") or "", user.id
    else:
        for access_id in after.get("revoked") or []:
            access = db.get(AiSkillAccess, int(access_id))
            if access is not None and access.revoked_at is not None:
                access.revoked_at, access.revoked_by, access.revoke_reason = None, 0, ""
                access.updated_by = user.id
    db.commit()
    return sign_access_state(db, *target)

